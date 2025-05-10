"""
Message queue for the git-integration service.
This module provides functionality to interact with a message queue.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MessageQueue:
    """
    Simple message queue for the git-integration service.
    In a real implementation, this would use a message broker like RabbitMQ or Kafka.
    """
    
    def __init__(self):
        """
        Initialize the message queue.
        """
        self.subscribers = {}
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to
            message: The message to publish
            
        Returns:
            True if the message was published successfully
        """
        logger.info(f"Publishing message to {topic}: {message}")
        
        # In a real implementation, this would publish to a message broker
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
        
        return True
    
    def subscribe(self, topic: str, callback) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: The topic to subscribe to
            callback: The callback to call when a message is published to the topic
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        self.subscribers[topic].append(callback)
        logger.info(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from
            callback: The callback to unsubscribe
        """
        if topic in self.subscribers and callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            logger.info(f"Unsubscribed from topic: {topic}")
