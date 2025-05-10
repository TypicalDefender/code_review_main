"""
Kafka consumer for the git-integration service.

This module provides functionality to consume messages from Kafka topics.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Callable, List, Optional

import aiokafka
from aiokafka.errors import KafkaError

from .config import Config

logger = logging.getLogger(__name__)

class KafkaConsumer:
    """Consumer for receiving messages from Kafka topics."""
    
    def __init__(self, config: Config):
        """Initialize the Kafka consumer.
        
        Args:
            config: The system configuration
        """
        self.config = config
        self.consumer = None
        self.running = False
        self.handlers = {}
    
    async def start(self):
        """Start the Kafka consumer."""
        if self.consumer is not None:
            return
        
        # Get Kafka configuration
        bootstrap_servers = self.config.get("kafka.bootstrap_servers", "localhost:9092")
        group_id = self.config.get("kafka.consumer_group_id", "git-integration")
        auto_offset_reset = self.config.get("kafka.auto_offset_reset", "earliest")
        
        # Configure Kafka consumer
        config = {
            "bootstrap_servers": bootstrap_servers,
            "group_id": group_id,
            "auto_offset_reset": auto_offset_reset,
        }
        
        # Add SASL configuration if needed
        security_protocol = self.config.get("kafka.security_protocol")
        if security_protocol:
            config["security_protocol"] = security_protocol
            
            sasl_mechanism = self.config.get("kafka.sasl_mechanism")
            if sasl_mechanism:
                config["sasl_mechanism"] = sasl_mechanism
                config["sasl_plain_username"] = self.config.get("kafka.sasl_username")
                config["sasl_plain_password"] = self.config.get("kafka.sasl_password")
        
        # Create the consumer
        self.consumer = aiokafka.AIOKafkaConsumer(**config)
        
        # Subscribe to topics
        topics = []
        for topic in self.handlers.keys():
            topics.append(topic)
        
        if not topics:
            logger.warning("No topics to subscribe to")
            return
        
        self.consumer.subscribe(topics)
        await self.consumer.start()
        self.running = True
        
        logger.info(f"Kafka consumer started, subscribed to topics: {topics}")
        
        # Start the consumer loop
        asyncio.create_task(self._consume_loop())
    
    async def stop(self):
        """Stop the Kafka consumer."""
        if self.consumer is None:
            return
        
        self.running = False
        await self.consumer.stop()
        self.consumer = None
        logger.info("Kafka consumer stopped")
    
    async def _consume_loop(self):
        """Main consumer loop."""
        try:
            while self.running:
                try:
                    # Get messages
                    async for message in self.consumer:
                        try:
                            # Parse the message
                            value = json.loads(message.value.decode("utf-8"))
                            
                            # Get the handler for this topic
                            handlers = self.handlers.get(message.topic, [])
                            if not handlers:
                                logger.warning(f"No handler for topic {message.topic}")
                                continue
                            
                            # Call the handlers
                            for handler in handlers:
                                try:
                                    await handler(value, message.key.decode("utf-8") if message.key else None)
                                except Exception as e:
                                    logger.error(f"Error in message handler: {e}")
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding message: {message.value}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                except KafkaError as e:
                    logger.error(f"Kafka error: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            if self.running:
                await self.stop()
    
    def register_handler(self, topic: str, handler: Callable[[Dict[str, Any], Optional[str]], None]):
        """Register a handler for a topic.
        
        Args:
            topic: The topic to handle
            handler: The handler function
        """
        if topic not in self.handlers:
            self.handlers[topic] = []
        
        self.handlers[topic].append(handler)
        logger.info(f"Registered handler for topic {topic}")
        
        # If the consumer is already running, subscribe to the new topic
        if self.consumer is not None and self.running:
            self.consumer.subscribe(list(self.handlers.keys()))
    
    def unregister_handler(self, topic: str, handler: Callable[[Dict[str, Any], Optional[str]], None]):
        """Unregister a handler for a topic.
        
        Args:
            topic: The topic to unhandle
            handler: The handler function
        """
        if topic in self.handlers and handler in self.handlers[topic]:
            self.handlers[topic].remove(handler)
            logger.info(f"Unregistered handler for topic {topic}")
            
            # If there are no more handlers for this topic, unsubscribe
            if not self.handlers[topic]:
                del self.handlers[topic]
                
                # If the consumer is already running, update the subscription
                if self.consumer is not None and self.running:
                    self.consumer.subscribe(list(self.handlers.keys()))
