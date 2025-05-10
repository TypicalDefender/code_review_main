"""
Chat Handler for OpenCodeReview.

This module processes chat messages from users, generating contextual responses
and handling special commands.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .llm_client import LLMClient
from .prompt_manager import PromptManager
from .command_processor import CommandProcessor
from .context_manager import ContextManager
from ..common.config import Config
from ..common.models import ChatMessage, ChatResponse, PullRequestContext

logger = logging.getLogger(__name__)

class ChatHandler:
    """Handles chat interactions with users."""

    def __init__(
        self,
        config: Config,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
        command_processor: CommandProcessor,
        context_manager: ContextManager,
    ):
        """Initialize the chat handler.

        Args:
            config: The system configuration
            llm_client: The LLM client for generating responses
            prompt_manager: The prompt manager for creating LLM prompts
            command_processor: The processor for special commands
            context_manager: The manager for conversation context
        """
        self.config = config
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.command_processor = command_processor
        self.context_manager = context_manager
        
        # Get configuration values
        self.model_name = config.get("chat.model.name", "gpt-4")
        self.temperature = config.get("chat.model.temperature", 0.7)
        self.max_tokens = config.get("chat.model.max_tokens", 2000)
        self.command_prefix = config.get("chat.commands.prefix", "@opencr")
        self.commands_enabled = config.get("chat.commands.enabled", True)

    async def process_message(
        self,
        message: ChatMessage,
        pr_context: PullRequestContext,
        conversation_history: List[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Process a chat message and generate a response.

        Args:
            message: The chat message to process
            pr_context: Context about the pull request
            conversation_history: Previous messages in the conversation

        Returns:
            A response to the chat message
        """
        logger.info(f"Processing chat message: {message.content[:50]}...")
        
        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = await self.context_manager.get_conversation_history(
                platform=pr_context.platform,
                repo_owner=pr_context.repo_owner,
                repo_name=pr_context.repo_name,
                pr_number=pr_context.pr_number,
            )
        
        # Extract the actual message content (remove the bot mention)
        content = self._extract_message_content(message.content)
        
        # Check if this is a command
        is_command, command_response = await self._process_command(content, pr_context)
        if is_command:
            return command_response
        
        # Generate a contextual response
        response = await self._generate_response(content, pr_context, conversation_history)
        
        # Update conversation history
        await self.context_manager.add_to_conversation_history(
            platform=pr_context.platform,
            repo_owner=pr_context.repo_owner,
            repo_name=pr_context.repo_name,
            pr_number=pr_context.pr_number,
            message={
                "role": "user",
                "content": content,
                "user": message.user,
                "timestamp": message.timestamp,
            },
            response={
                "role": "assistant",
                "content": response.content,
                "timestamp": response.timestamp,
            },
        )
        
        return response

    def _extract_message_content(self, content: str) -> str:
        """Extract the actual message content by removing the bot mention.

        Args:
            content: The raw message content

        Returns:
            The message content without the bot mention
        """
        # Remove the command prefix (e.g., "@opencr")
        if content.startswith(self.command_prefix):
            content = content[len(self.command_prefix):].strip()
        
        return content

    async def _process_command(
        self, content: str, pr_context: PullRequestContext
    ) -> Tuple[bool, Optional[ChatResponse]]:
        """Process a potential command in the message.

        Args:
            content: The message content
            pr_context: Context about the pull request

        Returns:
            A tuple containing:
            - A boolean indicating if the message was a command
            - The response to the command, if it was a command
        """
        if not self.commands_enabled:
            return False, None
        
        # Check if the message is a command
        command_match = re.match(r"^/(\w+)(?:\s+(.*))?$", content)
        if not command_match:
            return False, None
        
        command_name = command_match.group(1).lower()
        command_args = command_match.group(2) or ""
        
        # Process the command
        try:
            command_result = await self.command_processor.process_command(
                command_name=command_name,
                command_args=command_args,
                pr_context=pr_context,
            )
            
            # Create a response
            return True, ChatResponse(
                content=command_result.message,
                actions=command_result.actions,
                timestamp=command_result.timestamp,
            )
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return True, ChatResponse(
                content=f"Error processing command: {str(e)}",
                actions=[],
                timestamp=None,
            )

    async def _generate_response(
        self,
        content: str,
        pr_context: PullRequestContext,
        conversation_history: List[Dict[str, Any]],
    ) -> ChatResponse:
        """Generate a response to a chat message.

        Args:
            content: The message content
            pr_context: Context about the pull request
            conversation_history: Previous messages in the conversation

        Returns:
            A response to the chat message
        """
        # Get additional context about the pull request
        pr_details = await self._get_pr_details(pr_context)
        
        # Create the prompt
        prompt = self.prompt_manager.create_chat_prompt(
            message=content,
            pr_context=pr_context,
            pr_details=pr_details,
            conversation_history=conversation_history,
        )
        
        # Generate the response using the LLM
        response_text = await self.llm_client.generate(
            prompt=prompt,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # Parse the response for any actions
        response_text, actions = self._parse_response_actions(response_text)
        
        # Create the response object
        return ChatResponse(
            content=response_text.strip(),
            actions=actions,
            timestamp=None,  # Will be set by the caller
        )

    async def _get_pr_details(self, pr_context: PullRequestContext) -> Dict[str, Any]:
        """Get additional details about the pull request.

        Args:
            pr_context: Context about the pull request

        Returns:
            Additional details about the pull request
        """
        # This would typically fetch information from the Git platform
        # For simplicity, we're returning a placeholder
        return {
            "title": pr_context.title,
            "description": pr_context.description,
            "files_changed": pr_context.files_changed,
            "comments": pr_context.comments,
            "reviews": pr_context.reviews,
        }

    def _parse_response_actions(self, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse the response for any actions.

        Args:
            response: The raw response from the LLM

        Returns:
            A tuple containing:
            - The cleaned response text
            - A list of actions to perform
        """
        actions = []
        cleaned_response = response
        
        # Look for action blocks in the response
        action_blocks = re.findall(r"<action>(.*?)</action>", response, re.DOTALL)
        for block in action_blocks:
            # Remove the action block from the response
            cleaned_response = cleaned_response.replace(f"<action>{block}</action>", "")
            
            # Parse the action
            try:
                action_lines = block.strip().split("\n")
                action_type = action_lines[0].strip()
                action_params = {}
                
                for line in action_lines[1:]:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        action_params[key.strip()] = value.strip()
                
                actions.append({
                    "type": action_type,
                    "params": action_params,
                })
            except Exception as e:
                logger.error(f"Error parsing action block: {e}")
        
        return cleaned_response, actions
