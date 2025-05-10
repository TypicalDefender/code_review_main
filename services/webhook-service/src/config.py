"""
Configuration module for the webhook service.

This module provides configuration settings for the webhook service.
"""

import os
from functools import lru_cache
from typing import Dict, List, Optional, Any
from pydantic import BaseSettings, Field

class KafkaSettings(BaseSettings):
    """Kafka configuration settings."""
    
    bootstrap_servers: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS",
        description="Comma-separated list of Kafka bootstrap servers",
    )
    
    security_protocol: str = Field(
        default="PLAINTEXT",
        env="KAFKA_SECURITY_PROTOCOL",
        description="Security protocol for Kafka connections",
    )
    
    sasl_mechanism: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_MECHANISM",
        description="SASL mechanism for Kafka authentication",
    )
    
    sasl_username: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_USERNAME",
        description="SASL username for Kafka authentication",
    )
    
    sasl_password: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_PASSWORD",
        description="SASL password for Kafka authentication",
    )
    
    topic_prefix: str = Field(
        default="webhook",
        env="KAFKA_TOPIC_PREFIX",
        description="Prefix for Kafka topics",
    )
    
    github_raw_topic: str = Field(
        default="webhook.github.raw",
        env="KAFKA_GITHUB_RAW_TOPIC",
        description="Topic for raw GitHub webhook events",
    )
    
    github_validated_topic: str = Field(
        default="webhook.github.validated",
        env="KAFKA_GITHUB_VALIDATED_TOPIC",
        description="Topic for validated GitHub webhook events",
    )

class AuthSettings(BaseSettings):
    """Authentication configuration settings."""
    
    secret_key: str = Field(
        default="change-me-in-production",
        env="AUTH_SECRET_KEY",
        description="Secret key for signing tokens",
    )
    
    token_expire_minutes: int = Field(
        default=60,
        env="AUTH_TOKEN_EXPIRE_MINUTES",
        description="Token expiration time in minutes",
    )
    
    algorithm: str = Field(
        default="HS256",
        env="AUTH_ALGORITHM",
        description="Algorithm for signing tokens",
    )

class Settings(BaseSettings):
    """Main configuration settings."""
    
    app_name: str = Field(
        default="webhook-service",
        env="APP_NAME",
        description="Name of the application",
    )
    
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode",
    )
    
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level",
    )
    
    kafka: KafkaSettings = KafkaSettings()
    auth: AuthSettings = AuthSettings()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

@lru_cache()
def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Application settings
    """
    return Settings()
