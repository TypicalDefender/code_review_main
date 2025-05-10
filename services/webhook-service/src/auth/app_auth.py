"""
App-based authentication for the webhook service.

This module provides functionality for authenticating apps that use the webhook service.
"""

import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Any, Union

from fastapi import Request, HTTPException, Depends
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import Settings, get_settings
from src.models.app import App, AppPermission

logger = logging.getLogger(__name__)

class AppAuthManager:
    """Manager for app-based authentication."""
    
    def __init__(self, settings: Settings):
        """Initialize the app auth manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        # In a real implementation, this would be stored in a database
        self._apps: Dict[str, App] = {}
    
    async def register_app(self, app: App) -> App:
        """Register a new app.
        
        Args:
            app: The app to register
            
        Returns:
            The registered app
            
        Raises:
            HTTPException: If the app ID is already registered
        """
        if app.id in self._apps:
            raise HTTPException(status_code=400, detail=f"App ID {app.id} already registered")
        
        self._apps[app.id] = app
        logger.info(f"Registered app: {app.id}")
        return app
    
    async def get_app(self, app_id: str) -> Optional[App]:
        """Get an app by ID.
        
        Args:
            app_id: The app ID
            
        Returns:
            The app, or None if not found
        """
        return self._apps.get(app_id)
    
    async def authenticate_app(self, app_id: str, request: Request) -> Optional[App]:
        """Authenticate an app based on the request.
        
        Args:
            app_id: The app ID
            request: The incoming request
            
        Returns:
            The authenticated app, or None if authentication fails
        """
        app = await self.get_app(app_id)
        if not app:
            logger.warning(f"App not found: {app_id}")
            return None
        
        # Check for webhook signature
        if "X-Hub-Signature-256" in request.headers:
            return await self._authenticate_webhook_signature(app, request)
        
        # Check for API key
        if "X-App-Key" in request.headers:
            return await self._authenticate_api_key(app, request)
        
        # Check for JWT token
        if "Authorization" in request.headers:
            return await self._authenticate_jwt(app, request)
        
        logger.warning(f"No authentication method found for app: {app_id}")
        return None
    
    async def _authenticate_webhook_signature(self, app: App, request: Request) -> Optional[App]:
        """Authenticate using webhook signature.
        
        Args:
            app: The app to authenticate
            request: The incoming request
            
        Returns:
            The authenticated app, or None if authentication fails
        """
        signature_header = request.headers.get("X-Hub-Signature-256")
        if not signature_header:
            logger.warning("No signature header in request")
            return None
        
        if not signature_header.startswith("sha256="):
            logger.warning("Invalid signature format")
            return None
        
        signature = signature_header[7:]  # Remove 'sha256=' prefix
        
        # Get the request body
        body = await request.body()
        
        # Compute the expected signature
        expected_signature = hmac.new(
            app.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid signature")
            return None
        
        return app
    
    async def _authenticate_api_key(self, app: App, request: Request) -> Optional[App]:
        """Authenticate using API key.
        
        Args:
            app: The app to authenticate
            request: The incoming request
            
        Returns:
            The authenticated app, or None if authentication fails
        """
        api_key = request.headers.get("X-App-Key")
        if not api_key:
            logger.warning("No API key in request")
            return None
        
        if api_key != app.api_key:
            logger.warning("Invalid API key")
            return None
        
        return app
    
    async def _authenticate_jwt(self, app: App, request: Request) -> Optional[App]:
        """Authenticate using JWT token.
        
        Args:
            app: The app to authenticate
            request: The incoming request
            
        Returns:
            The authenticated app, or None if authentication fails
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("No Authorization header in request")
            return None
        
        if not auth_header.startswith("Bearer "):
            logger.warning("Invalid Authorization header format")
            return None
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                self.settings.auth.secret_key,
                algorithms=[self.settings.auth.algorithm]
            )
            
            # Check if the token is for the correct app
            if payload.get("sub") != app.id:
                logger.warning("Token subject does not match app ID")
                return None
            
            return app
        except JWTError:
            logger.warning("Invalid JWT token")
            return None
    
    async def create_access_token(self, app_id: str) -> str:
        """Create an access token for an app.
        
        Args:
            app_id: The app ID
            
        Returns:
            The access token
            
        Raises:
            HTTPException: If the app is not found
        """
        app = await self.get_app(app_id)
        if not app:
            raise HTTPException(status_code=404, detail=f"App not found: {app_id}")
        
        # Create token data
        expires_delta = timedelta(minutes=self.settings.auth.token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": app.id,
            "exp": expire,
            "name": app.name,
            "permissions": [p.value for p in app.permissions]
        }
        
        # Create the token
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.auth.secret_key,
            algorithm=self.settings.auth.algorithm
        )
        
        return encoded_jwt

@lru_cache()
def get_app_auth_manager(settings: Settings = Depends(get_settings)) -> AppAuthManager:
    """Get the app auth manager.
    
    Args:
        settings: Application settings
        
    Returns:
        The app auth manager
    """
    return AppAuthManager(settings)
