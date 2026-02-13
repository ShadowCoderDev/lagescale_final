import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_database

logger = logging.getLogger(__name__)


class ProductRepository:
    
    def __init__(self):
        self.db = get_database()
    

    @staticmethod
    def to_object_id(product_id: str) -> Optional[ObjectId]:
        try:
            return ObjectId(product_id)
        except InvalidId:
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════════════
    
    async def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        product_dict = {
            **product_data,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if "price" in product_dict:
            product_dict["price"] = float(product_dict["price"])
        
        result = await self.db.products.insert_one(product_dict)
        product_dict["_id"] = result.inserted_id
        
        return product_dict
    
    # ═══════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════
    
    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        oid = self.to_object_id(product_id)
        if not oid:
            return None
        return await self.db.products.find_one({"_id": oid})
    
    async def get_active_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        oid = self.to_object_id(product_id)
        if not oid:
            return None
        return await self.db.products.find_one({"_id": oid, "isActive": True})
    
    async def get_by_sku(self, sku: str, exclude_id: str = None) -> Optional[Dict[str, Any]]:
        query = {"sku": sku}
        if exclude_id:
            oid = self.to_object_id(exclude_id)
            if oid:
                query["_id"] = {"$ne": oid}
        return await self.db.products.find_one(query)
    
    async def list(
        self,
        filter_query: Dict[str, Any],
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        total = await self.db.products.count_documents(filter_query)
        
        cursor = (
            self.db.products.find(filter_query)
            .sort("createdAt", -1)
            .skip(skip)
            .limit(limit)
        )
        products = await cursor.to_list(length=limit)
        
        return products, total
    
    async def search(
        self,
        query: str,
        is_admin: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        filter_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }
        
        if not is_admin:
            filter_query["isActive"] = True
        
        return await self.list(filter_query, skip, limit)
    
    # ═══════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════
    
    async def update(self, product_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = self.to_object_id(product_id)
        if not oid:
            return None
        
        update_data["updatedAt"] = datetime.utcnow()
        
        if "price" in update_data:
            update_data["price"] = float(update_data["price"])
        
        await self.db.products.update_one({"_id": oid}, {"$set": update_data})
        return await self.db.products.find_one({"_id": oid})
    
    async def soft_delete(self, product_id: str) -> bool:
        oid = self.to_object_id(product_id)
        if not oid:
            return False
        
        result = await self.db.products.update_one(
            {"_id": oid},
            {"$set": {"isActive": False, "updatedAt": datetime.utcnow()}}
        )
        return result.modified_count > 0
    

    async def reserve_stock(
        self,
        product_id: str,
        quantity: int,
        order_id: str,
        reservation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Atomic stock reservation for standalone MongoDB (no transactions)."""
        oid = self.to_object_id(product_id)
        if not oid:
            return None
        
        now = datetime.utcnow()
        
        # Atomic decrement - only succeeds if stock >= quantity
        result = await self.db.products.update_one(
            {"_id": oid, "stockQuantity": {"$gte": quantity}},
            {"$inc": {"stockQuantity": -quantity}}
        )
        
        if result.modified_count == 0:
            return None
        
        # Create reservation record
        reservation = {
            "reservation_id": reservation_id,
            "product_id": product_id,
            "quantity": quantity,
            "order_id": order_id,
            "status": "reserved",
            "reserved_at": now,
            "expires_at": None
        }
        await self.db.stock_reservations.insert_one(reservation)
        
        return reservation
    
    async def release_stock(
        self,
        reservation_id: str,
        reason: str = None
    ) -> Optional[Dict[str, Any]]:
        """Releases stock for both 'reserved' and 'confirmed' reservations (no transactions)."""
        reservation = await self.db.stock_reservations.find_one({
            "reservation_id": reservation_id,
            "status": {"$in": ["reserved", "confirmed"]}
        })
        
        if not reservation:
            # Already released or not found
            return await self.db.stock_reservations.find_one({
                "reservation_id": reservation_id
            })
        
        oid = self.to_object_id(reservation["product_id"])
        if not oid:
            return None
        
        # Restore stock
        await self.db.products.update_one(
            {"_id": oid},
            {"$inc": {"stockQuantity": reservation["quantity"]}}
        )
        
        # Mark as released
        await self.db.stock_reservations.update_one(
            {"reservation_id": reservation_id},
            {
                "$set": {
                    "status": "released",
                    "released_at": datetime.utcnow(),
                    "release_reason": reason
                }
            }
        )
        
        reservation["status"] = "released"
        return reservation
    
    async def confirm_stock(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        await self.db.stock_reservations.update_one(
            {"reservation_id": reservation_id},
            {
                "$set": {
                    "status": "confirmed",
                    "confirmed_at": datetime.utcnow()
                }
            }
        )
        return await self.db.stock_reservations.find_one({
            "reservation_id": reservation_id
        })
    
    async def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.stock_reservations.find_one({
            "reservation_id": reservation_id
        })
