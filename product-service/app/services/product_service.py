"""
Product Service - Business Logic Layer
Handles all business logic for product operations
"""
import logging
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)


class ProductServiceError(Exception):
    """Base exception for product service errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProductService:
    """
    Product Service - Business Logic Layer
    
    Responsibilities:
    - Validate business rules
    - Handle product CRUD
    - Manage stock reservations (Saga Pattern)
    """
    
    def __init__(self):
        self.repository = ProductRepository()
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def to_response(product: dict) -> dict:
        """Convert MongoDB document to response format"""
        return {
            "id": str(product["_id"]),
            "name": product["name"],
            "description": product.get("description"),
            "price": Decimal(str(product["price"])),
            "stockQuantity": product["stockQuantity"],
            "category": product["category"],
            "sku": product["sku"],
            "isActive": product.get("isActive", True),
            "createdAt": product["createdAt"],
            "updatedAt": product["updatedAt"],
        }
    
    @staticmethod
    def to_list_item(product: dict) -> dict:
        """Convert product to list item format"""
        return {
            "id": str(product["_id"]),
            "name": product["name"],
            "price": Decimal(str(product["price"])),
            "stockQuantity": product["stockQuantity"],
            "category": product["category"],
            "sku": product["sku"],
            "isActive": product.get("isActive", True),
        }
    
    # ═══════════════════════════════════════════════════════════════
    # PRODUCT CRUD
    # ═══════════════════════════════════════════════════════════════
    
    async def create_product(self, data: ProductCreate) -> dict:
        """Create a new product"""
        # Check SKU uniqueness
        existing = await self.repository.get_by_sku(data.sku)
        if existing:
            raise ProductServiceError("A product with this SKU already exists")
        
        product_dict = data.model_dump()
        product = await self.repository.create(product_dict)
        
        logger.info(f"Product created: {product['_id']}")
        return self.to_response(product)
    
    async def get_product(self, product_id: str) -> dict:
        """Get product by ID"""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise ProductServiceError("Product not found", 404)
        return self.to_response(product)
    
    async def list_products(
        self,
        is_admin: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[dict], int]:
        """List products with pagination"""
        filter_query = {} if is_admin else {"isActive": True}
        skip = (page - 1) * page_size
        
        products, total = await self.repository.list(filter_query, skip, page_size)
        
        return [self.to_list_item(p) for p in products], total
    
    async def search_products(
        self,
        query: str,
        is_admin: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[dict], int]:
        """Search products by name or description"""
        skip = (page - 1) * page_size
        products, total = await self.repository.search(query, is_admin, skip, page_size)
        return [self.to_list_item(p) for p in products], total
    
    async def update_product(self, product_id: str, data: ProductUpdate) -> dict:
        """Update a product"""
        # Check product exists
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise ProductServiceError("Product not found", 404)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check SKU uniqueness if updating
        if "sku" in update_data:
            existing = await self.repository.get_by_sku(update_data["sku"], product_id)
            if existing:
                raise ProductServiceError("A product with this SKU already exists")
        
        updated = await self.repository.update(product_id, update_data)
        return self.to_response(updated)
    
    async def delete_product(self, product_id: str) -> bool:
        """Soft delete a product"""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise ProductServiceError("Product not found", 404)
        
        success = await self.repository.soft_delete(product_id)
        if success:
            logger.info(f"Product deleted: {product_id}")
        return success
    
    # ═══════════════════════════════════════════════════════════════
    # STOCK
    # ═══════════════════════════════════════════════════════════════
    
    async def get_stock(self, product_id: str) -> dict:
        """Get stock information for a product"""
        product = await self.repository.get_active_by_id(product_id)
        if not product:
            raise ProductServiceError("Product not found", 404)
        
        return {
            "product_id": str(product["_id"]),
            "stock_quantity": product["stockQuantity"],
            "in_stock": product["stockQuantity"] > 0,
            "available": product.get("isActive", True) and product["stockQuantity"] > 0,
        }
    
    # ═══════════════════════════════════════════════════════════════
    # STOCK RESERVATION (Saga Pattern)
    # ═══════════════════════════════════════════════════════════════
    
    async def reserve_stock(
        self,
        product_id: str,
        quantity: int,
        order_id: str,
        reservation_id: str = None
    ) -> dict:
        """
        Reserve stock for an order (Step 1 of Saga).
        """
        # Check for existing reservation (idempotency)
        if reservation_id:
            existing = await self.repository.get_reservation(reservation_id)
            if existing:
                return self._reservation_to_response(existing)
        
        # Check product exists and has stock
        product = await self.repository.get_active_by_id(product_id)
        if not product:
            raise ProductServiceError("Product not found", 404)
        
        if product["stockQuantity"] < quantity:
            raise ProductServiceError(
                f"Insufficient stock. Available: {product['stockQuantity']}, Requested: {quantity}"
            )
        
        # Generate reservation ID
        res_id = reservation_id or str(uuid.uuid4())
        
        # Reserve atomically
        reservation = await self.repository.reserve_stock(
            product_id, quantity, order_id, res_id
        )
        
        if not reservation:
            raise ProductServiceError("Insufficient stock (concurrent modification)")
        
        logger.info(f"Stock reserved: {res_id} for order {order_id}")
        return self._reservation_to_response(reservation)
    
    async def release_stock(self, reservation_id: str, reason: str = None) -> dict:
        """
        Release reserved stock (Compensation step of Saga).
        """
        reservation = await self.repository.release_stock(reservation_id, reason)
        
        if not reservation:
            raise ProductServiceError("Reservation not found", 404)
        
        if reservation.get("status") == "released":
            logger.info(f"Stock released: {reservation_id}")
        
        return {
            "message": f"Reservation {reservation['status']}",
            "reservation_id": reservation_id,
            "quantity_restored": reservation.get("quantity", 0)
        }
    
    async def confirm_stock(self, reservation_id: str) -> dict:
        """
        Confirm stock deduction (Final step of Saga).
        """
        existing = await self.repository.get_reservation(reservation_id)
        
        if not existing:
            raise ProductServiceError("Reservation not found", 404)
        
        if existing["status"] == "confirmed":
            return {"message": "Already confirmed", "reservation_id": reservation_id}
        
        if existing["status"] == "released":
            raise ProductServiceError("Cannot confirm released reservation")
        
        await self.repository.confirm_stock(reservation_id)
        
        logger.info(f"Stock confirmed: {reservation_id}")
        return {"message": "Stock confirmed successfully", "reservation_id": reservation_id}
    
    async def get_reservation(self, reservation_id: str) -> dict:
        """Get reservation status"""
        reservation = await self.repository.get_reservation(reservation_id)
        
        if not reservation:
            raise ProductServiceError("Reservation not found", 404)
        
        return self._reservation_to_response(reservation)
    
    @staticmethod
    def _reservation_to_response(reservation: dict) -> dict:
        """Convert reservation to response format"""
        return {
            "reservation_id": reservation["reservation_id"],
            "product_id": reservation["product_id"],
            "quantity": reservation["quantity"],
            "order_id": reservation["order_id"],
            "status": reservation["status"],
            "reserved_at": reservation["reserved_at"]
        }
