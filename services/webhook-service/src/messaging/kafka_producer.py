"""
Kafka producer for the webhook service.

This module provides functionality to produce messages to Kafka topics.
"""

import json
import logging
from functools import lru_cache
from typing import Dict, Any, Optional

import aiokafka
from fastapi import Depends
from pydantic import BaseModel

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

class KafkaProducer:
    """Producer for sending messages to Kafka topics."""
    
    def __init__(self, settings: Settings):
        """Initialize the Kafka producer.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.producer = None
    
    async def start(self):
        """Start the Kafka producer."""
        if self.producer is not None:
            return
        
        # Configure Kafka producer
        config = {
            "bootstrap_servers": self.settings.kafka.bootstrap_servers,
            "security_protocol": self.settings.kafka.security_protocol,
        }
        
        # Add SASL configuration if needed
        if self.settings.kafka.sasl_mechanism:
            config["sasl_mechanism"] = self.settings.kafka.sasl_mechanism
            config["sasl_plain_username"] = self.settings.kafka.sasl_username
            config["sasl_plain_password"] = self.settings.kafka.sasl_password
        
        # Create the producer
        self.producer = aiokafka.AIOKafkaProducer(**config)
        await self.producer.start()
        logger.info("Kafka producer started")
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer is None:
            return
        
        await self.producer.stop()
        self.producer = None
        logger.info("Kafka producer stopped")
    
    async def send_message(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send a message to a Kafka topic.
        
        Args:
            topic: The topic to send the message to
            message: The message to send
            key: The message key (optional)
            headers: The message headers (optional)
            
        Returns:
            True if the message was sent successfully
            
        Raises:
            RuntimeError: If the producer is not started
        """
        if self.producer is None:
            raise RuntimeError("Kafka producer not started")
        
        # Convert message to JSON
        value = json.dumps(message).encode("utf-8")
        
        # Convert key to bytes if provided
        key_bytes = key.encode("utf-8") if key else None
        
        # Convert headers to list of tuples if provided
        headers_list = None
        if headers:
            headers_list = [(k, v.encode("utf-8")) for k, v in headers.items()]
        
        try:
            # Send the message
            await self.producer.send_and_wait(
                topic=topic,
                value=value,
                key=key_bytes,
                headers=headers_list
            )
            logger.info(f"Message sent to topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Error sending message to topic {topic}: {e}")
            return False
    
    async def send_github_raw_event(self, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Send a raw GitHub event to the appropriate topic.
        
        Args:
            message: The message to send
            key: The message key (optional)
            
        Returns:
            True if the message was sent successfully
        """
        return await self.send_message(
            topic=self.settings.kafka.github_raw_topic,
            message=message,
            key=key
        )
    
    async def send_github_validated_event(self, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Send a validated GitHub event to the appropriate topic.
        
        Args:
            message: The message to send
            key: The message key (optional)
            
        Returns:
            True if the message was sent successfully
        """
        return await self.send_message(
            topic=self.settings.kafka.github_validated_topic,
            message=message,
            key=key
        )

@lru_cache()
def get_kafka_producer(settings: Settings = Depends(get_settings)) -> KafkaProducer:
    """Get the Kafka producer.
    
    Args:
        settings: Application settings
        
    Returns:
        The Kafka producer
    """
    return KafkaProducer(settings)
