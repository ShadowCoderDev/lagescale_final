import httpx
import logging
import uuid
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0
    
    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        import time
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPENED after {self.failures} failures")
    
    def can_execute(self) -> bool:
        import time
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker HALF_OPEN, allowing test request")
                return True
            return False
        return True  # HALF_OPEN allows one request


class ProductClient:
    
    def __init__(self):
        self.base_url = settings.PRODUCT_SERVICE_URL
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    def _make_request(self, method: str, endpoint: str, json_data: dict = None) -> Optional[Dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            if method == "GET":
                response = client.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = client.post(f"{self.base_url}{endpoint}", json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                raise ValueError(error_data.get("detail", "Bad request"))
            return None
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting request")
            return None
        
        try:
            result = self._make_request("GET", f"/api/products/{product_id}/")
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            logger.error(f"Product service request failed: {e}")
            self.circuit_breaker.record_failure()
            return None
    
    def check_stock(self, product_id: str, quantity: int) -> bool:
        product = self.get_product(product_id)
        if not product:
            return False
        return product.get("isActive", False) and product.get("stockQuantity", 0) >= quantity

    def reserve_stock(self, product_id: str, quantity: int, order_id: int, reservation_id: str = None) -> Optional[Dict[str, Any]]:
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting reserve request")
            return None
        
        try:
            result = self._make_request("POST", "/api/products/stock/reserve/", {
                "product_id": product_id,
                "quantity": quantity,
                "order_id": order_id,
                "reservation_id": reservation_id or str(uuid.uuid4())
            })
            self.circuit_breaker.record_success()
            logger.info(f"Stock reserved: product={product_id}, qty={quantity}, reservation={result.get('reservation_id')}")
            return result
        except ValueError as e:
            logger.warning(f"Stock reservation failed (business error): {e}")
            return None
        except Exception as e:
            logger.error(f"Stock reservation failed: {e}")
            self.circuit_breaker.record_failure()
            return None
    
    def release_stock(self, reservation_id: str, reason: str = None) -> bool:
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting release request")
            return False
        
        try:
            result = self._make_request("POST", "/api/products/stock/release/", {
                "reservation_id": reservation_id,
                "reason": reason
            })
            self.circuit_breaker.record_success()
            logger.info(f"Stock released: reservation={reservation_id}")
            return result is not None
        except Exception as e:
            logger.error(f"Stock release failed: {e}")
            self.circuit_breaker.record_failure()
            return False
    
    def confirm_stock(self, reservation_id: str) -> bool:
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN, rejecting confirm request")
            return False
        
        try:
            result = self._make_request("POST", "/api/products/stock/confirm/", {
                "reservation_id": reservation_id
            })
            self.circuit_breaker.record_success()
            logger.info(f"Stock confirmed: reservation={reservation_id}")
            return result is not None
        except Exception as e:
            logger.error(f"Stock confirmation failed: {e}")
            self.circuit_breaker.record_failure()
            return False
    
    def reserve_multiple(self, items: List[Dict], order_id: int) -> tuple[List[Dict], List[Dict]]:
        successful = []
        failed = []
        
        for item in items:
            reservation = self.reserve_stock(
                product_id=item["product_id"],
                quantity=item["quantity"],
                order_id=order_id
            )
            if reservation:
                successful.append({
                    **item,
                    "reservation_id": reservation["reservation_id"]
                })
            else:
                failed.append(item)
                # Release all successful reservations (compensation)
                for res in successful:
                    self.release_stock(res["reservation_id"], "Partial reservation failed")
                return [], [item]  # Return immediately on first failure
        
        return successful, failed
    
    def release_multiple(self, reservations: List[Dict], reason: str = None) -> None:
        for res in reservations:
            if "reservation_id" in res:
                self.release_stock(res["reservation_id"], reason)


product_client = ProductClient()
