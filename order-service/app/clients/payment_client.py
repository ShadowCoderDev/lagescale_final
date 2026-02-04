"""HTTP client for Payment Service with Retry and Circuit Breaker"""
import httpx
import logging
import time
from typing import Dict, Any
from decimal import Decimal
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple Circuit Breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0
    
    def record_success(self):
        """Reset on success"""
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Track failure and potentially open circuit"""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPENED after {self.failures} failures")
    
    def can_execute(self) -> bool:
        """Check if request is allowed"""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker HALF_OPEN, allowing test request")
                return True
            return False
        return True  # HALF_OPEN allows one request


class PaymentClient:
    """Client for Payment Service with fault tolerance"""
    
    def __init__(self):
        self.base_url = settings.PAYMENT_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    def _make_request(self, order_id: int, user_id: int, amount: Decimal) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/api/payments/process/",
                json={
                    "order_id": order_id,
                    "user_id": user_id,
                    "amount": float(amount)
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
            # Non-retryable error (business logic failure)
            return {
                "transaction_id": None,
                "status": "failed",
                "message": "Payment rejected"
            }
    
    def process_payment(self, order_id: int, user_id: int, amount: Decimal) -> Dict[str, Any]:
        """Process payment for order with circuit breaker"""
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting payment request")
            return {
                "transaction_id": None,
                "status": "failed",
                "message": "Payment service unavailable (circuit open)"
            }
        
        try:
            result = self._make_request(order_id, user_id, amount)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            logger.error(f"Payment service request failed: {e}")
            self.circuit_breaker.record_failure()
            return {
                "transaction_id": None,
                "status": "failed",
                "message": f"Payment service error: {str(e)}"
            }

    def refund(self, transaction_id: str, reason: str = None) -> Dict[str, Any]:
        """
        Refund a payment (Saga Compensation).
        Called when stock confirmation fails after payment.
        """
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting refund request")
            return {
                "success": False,
                "message": "Payment service unavailable (circuit open)"
            }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/api/payments/refund/",
                    json={
                        "transaction_id": transaction_id,
                        "reason": reason or "Saga compensation - order failed"
                    }
                )
                if response.status_code in [200, 201]:
                    self.circuit_breaker.record_success()
                    result = response.json()
                    logger.info(f"Payment refunded: {transaction_id}")
                    return {"success": True, "refund_id": result.get("transaction_id")}
                else:
                    logger.error(f"Refund failed: {response.status_code} - {response.text}")
                    return {"success": False, "message": response.text}
        except Exception as e:
            logger.error(f"Refund request failed: {e}")
            self.circuit_breaker.record_failure()
            return {"success": False, "message": str(e)}


payment_client = PaymentClient()
