"""
Configuration for the git-integration service.
This module provides functionality to load and access configuration.
"""

import os
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration for the git-integration service.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            config_file: Path to a JSON configuration file
        """
        self.config = {}
        
        # Load configuration from environment variables
        self._load_from_env()
        
        # Load configuration from file if provided
        if config_file:
            self._load_from_file(config_file)
    
    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables.
        """
        # GitHub configuration
        self.config["git.github.webhook_secret"] = os.environ.get("GITHUB_WEBHOOK_SECRET")
        self.config["git.github.token"] = os.environ.get("GITHUB_TOKEN")
        
        # Chat configuration
        self.config["chat.commands.prefix"] = os.environ.get("CHAT_COMMANDS_PREFIX", "@opencr")
    
    def _load_from_file(self, config_file: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_file: Path to a JSON configuration file
        """
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                
                # Update configuration with values from file
                for key, value in file_config.items():
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error loading configuration from file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The configuration value
        """
        self.config[key] = value
