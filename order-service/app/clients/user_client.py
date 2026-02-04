"""HTTP client for User Service"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserClient:
    """Client for User Service"""
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
    
    def get_user(self, user_id: int, token: str = None) -> Optional[Dict[str, Any]]:
        """
        Get user details from user service.
        
        Args:
            user_id: User ID
            token: JWT token for authentication
            
        Returns:
            User data dict or None if not found
        """
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            with httpx.Client(timeout=10.0) as client:
                # Try profile endpoint first (uses auth)
                response = client.get(
                    f"{self.base_url}/api/users/profile/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                
                logger.warning(f"User service returned {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None


user_client = UserClient()
