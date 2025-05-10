"""
LLM Client for OpenCodeReview.

This module provides a client for interacting with Large Language Models (LLMs)
from different providers.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Union
import asyncio

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from ...common.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with Large Language Models."""

    def __init__(self, config: Config):
        """Initialize the LLM client.

        Args:
            config: The system configuration
        """
        self.config = config
        self.provider = config.get("ai.provider", "openai")
        
        # Set up API keys
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
        
        # Set up API endpoints
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        self.anthropic_api_url = "https://api.anthropic.com/v1/messages"
        self.huggingface_api_url = "https://api-inference.huggingface.co/models/"
        
        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate the configuration."""
        if self.provider == "openai" and not self.openai_api_key:
            logger.warning("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
        elif self.provider == "anthropic" and not self.anthropic_api_key:
            logger.warning("Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable.")
        elif self.provider == "huggingface" and not self.huggingface_api_key:
            logger.warning("HuggingFace API key not set. Set HUGGINGFACE_API_KEY environment variable.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        model: str = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        stop: List[str] = None,
    ) -> str:
        """Generate text using the configured LLM.

        Args:
            prompt: The prompt to send to the LLM (string or chat messages)
            model: The model to use (overrides config)
            temperature: The temperature to use (overrides config)
            max_tokens: The maximum number of tokens to generate (overrides config)
            stop: A list of strings to stop generation at

        Returns:
            The generated text

        Raises:
            Exception: If there is an error generating text
        """
        # Use config values if not provided
        model = model or self.config.get(f"ai.model.name", "gpt-4")
        temperature = temperature or self.config.get(f"ai.model.temperature", 0.2)
        max_tokens = max_tokens or self.config.get(f"ai.model.max_tokens", 4000)
        
        # Call the appropriate provider
        if self.provider == "openai":
            return await self._generate_openai(prompt, model, temperature, max_tokens, stop)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, model, temperature, max_tokens, stop)
        elif self.provider == "huggingface":
            return await self._generate_huggingface(prompt, model, temperature, max_tokens, stop)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def _generate_openai(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop: List[str] = None,
    ) -> str:
        """Generate text using OpenAI's API.

        Args:
            prompt: The prompt to send to the LLM (string or chat messages)
            model: The model to use
            temperature: The temperature to use
            max_tokens: The maximum number of tokens to generate
            stop: A list of strings to stop generation at

        Returns:
            The generated text

        Raises:
            Exception: If there is an error generating text
        """
        # Convert string prompt to chat format if needed
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if stop:
            payload["stop"] = stop
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }
        
        # Make the request
        async with aiohttp.ClientSession() as session:
            async with session.post(self.openai_api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {error_text}")
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract the generated text
                try:
                    return response_data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing OpenAI response: {e}")
                    logger.error(f"Response data: {response_data}")
                    raise Exception(f"Error parsing OpenAI response: {e}")

    async def _generate_anthropic(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop: List[str] = None,
    ) -> str:
        """Generate text using Anthropic's API.

        Args:
            prompt: The prompt to send to the LLM (string or chat messages)
            model: The model to use
            temperature: The temperature to use
            max_tokens: The maximum number of tokens to generate
            stop: A list of strings to stop generation at

        Returns:
            The generated text

        Raises:
            Exception: If there is an error generating text
        """
        # Convert string prompt to chat format if needed
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        
        # Convert to Anthropic's format
        anthropic_messages = []
        for message in messages:
            role = "user" if message["role"] in ["user", "system"] else "assistant"
            anthropic_messages.append({
                "role": role,
                "content": message["content"],
            })
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if stop:
            payload["stop_sequences"] = stop
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }
        
        # Make the request
        async with aiohttp.ClientSession() as session:
            async with session.post(self.anthropic_api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Anthropic API error: {error_text}")
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract the generated text
                try:
                    return response_data["content"][0]["text"]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing Anthropic response: {e}")
                    logger.error(f"Response data: {response_data}")
                    raise Exception(f"Error parsing Anthropic response: {e}")

    async def _generate_huggingface(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        model: str,
        temperature: float,
        max_tokens: int,
        stop: List[str] = None,
    ) -> str:
        """Generate text using HuggingFace's API.

        Args:
            prompt: The prompt to send to the LLM (string or chat messages)
            model: The model to use
            temperature: The temperature to use
            max_tokens: The maximum number of tokens to generate
            stop: A list of strings to stop generation at

        Returns:
            The generated text

        Raises:
            Exception: If there is an error generating text
        """
        # Convert chat messages to string if needed
        if isinstance(prompt, list):
            prompt_str = ""
            for message in prompt:
                role = message["role"]
                content = message["content"]
                if role == "system":
                    prompt_str += f"System: {content}\n\n"
                elif role == "user":
                    prompt_str += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt_str += f"Assistant: {content}\n\n"
            prompt = prompt_str.strip()
        
        # Prepare the request payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            }
        }
        
        if stop:
            payload["parameters"]["stop"] = stop
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.huggingface_api_key}",
        }
        
        # Make the request
        api_url = f"{self.huggingface_api_url}{model}"
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"HuggingFace API error: {error_text}")
                    raise Exception(f"HuggingFace API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract the generated text
                try:
                    return response_data[0]["generated_text"]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing HuggingFace response: {e}")
                    logger.error(f"Response data: {response_data}")
                    raise Exception(f"Error parsing HuggingFace response: {e}")

    async def get_embedding(self, text: str, model: str = None) -> List[float]:
        """Get an embedding for the given text.

        Args:
            text: The text to embed
            model: The model to use (overrides config)

        Returns:
            The embedding vector

        Raises:
            Exception: If there is an error getting the embedding
        """
        # Use config values if not provided
        model = model or self.config.get("ai.embedding.model", "text-embedding-ada-002")
        
        # Call the appropriate provider
        if self.provider == "openai":
            return await self._get_embedding_openai(text, model)
        elif self.provider == "huggingface":
            return await self._get_embedding_huggingface(text, model)
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")

    async def _get_embedding_openai(self, text: str, model: str) -> List[float]:
        """Get an embedding using OpenAI's API.

        Args:
            text: The text to embed
            model: The model to use

        Returns:
            The embedding vector

        Raises:
            Exception: If there is an error getting the embedding
        """
        # Prepare the request payload
        payload = {
            "model": model,
            "input": text,
        }
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }
        
        # Make the request
        api_url = "https://api.openai.com/v1/embeddings"
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {error_text}")
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract the embedding
                try:
                    return response_data["data"][0]["embedding"]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing OpenAI embedding response: {e}")
                    logger.error(f"Response data: {response_data}")
                    raise Exception(f"Error parsing OpenAI embedding response: {e}")

    async def _get_embedding_huggingface(self, text: str, model: str) -> List[float]:
        """Get an embedding using HuggingFace's API.

        Args:
            text: The text to embed
            model: The model to use

        Returns:
            The embedding vector

        Raises:
            Exception: If there is an error getting the embedding
        """
        # Prepare the request payload
        payload = {
            "inputs": text,
        }
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.huggingface_api_key}",
        }
        
        # Make the request
        api_url = f"{self.huggingface_api_url}{model}"
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"HuggingFace API error: {error_text}")
                    raise Exception(f"HuggingFace API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract the embedding
                try:
                    return response_data[0]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing HuggingFace embedding response: {e}")
                    logger.error(f"Response data: {response_data}")
                    raise Exception(f"Error parsing HuggingFace embedding response: {e}")
