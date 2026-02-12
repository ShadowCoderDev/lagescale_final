"""HTTP client for User Service with retry and circuit breaker"""
import httpx
import logging
import time
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for user service"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("User service circuit breaker: OPEN -> HALF_OPEN")
                return True
            return False
        # HALF_OPEN
        return True
    
    def record_success(self):
        if self.state == "HALF_OPEN":
            logger.info("User service circuit breaker: HALF_OPEN -> CLOSED")
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(
                    f"User service circuit breaker OPENED after {self.failures} failures"
                )
            self.state = "OPEN"


class UserClient:
    """Client for User Service with retry and circuit breaker"""
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    def _make_request(self, method: str, url: str, **kwargs):
        """Make HTTP request with retry logic"""
        with httpx.Client(timeout=10.0) as client:
            response = getattr(client, method)(url, **kwargs)
            return response
    
    def get_user(self, user_id: int, token: str = None) -> Optional[Dict[str, Any]]:
        """
        Get user details from user service.
        
        Args:
            user_id: User ID
            token: JWT token for authentication
            
        Returns:
            User data dict or None if not found
        """
        if not self.circuit_breaker.can_execute():
            logger.warning("User service circuit breaker is OPEN, skipping request")
            return None
        
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = self._make_request(
                "get",
                f"{self.base_url}/api/users/profile/",
                headers=headers
            )
            
            if response.status_code == 200:
                self.circuit_breaker.record_success()
                return response.json()
            
            logger.warning(f"User service returned {response.status_code}")
            self.circuit_breaker.record_success()  # Non-network errors don't trigger CB
            return None
                
        except (httpx.RequestError, httpx.TimeoutException) as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Error getting user {user_id} (network/timeout): {e}")
            return None
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Error getting user {user_id}: {e}")
            return None


user_client = UserClient()
