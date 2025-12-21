"""Product API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from decimal import Decimal
from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_database
from app.core.auth import get_admin_user, get_optional_user
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductStockResponse,
    PaginatedResponse,
)

router = APIRouter()


def product_to_response(product: dict) -> dict:
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


def to_list_response(products: list) -> list:
    """Convert products to list response"""
    return [
        ProductListResponse(
            id=str(p["_id"]),
            name=p["name"],
            price=Decimal(str(p["price"])),
            stockQuantity=p["stockQuantity"],
            category=p["category"],
            sku=p["sku"],
            isActive=p.get("isActive", True),
        ).model_dump()
        for p in products
    ]


@router.get("/", response_model=PaginatedResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """List all products with pagination. Non-admin users only see active products."""
    db = get_database()
    
    # Admin sees all, others see only active products
    is_admin = current_user and current_user.get("is_admin", False)
    filter_query = {} if is_admin else {"isActive": True}
    
    total = await db.products.count_documents(filter_query)
    skip = (page - 1) * page_size
    
    cursor = db.products.find(filter_query).sort("createdAt", -1).skip(skip).limit(page_size)
    products = await cursor.to_list(length=page_size)
    
    return PaginatedResponse(
        count=total,
        next=f"?page={page+1}&page_size={page_size}" if skip + page_size < total else None,
        previous=f"?page={page-1}&page_size={page_size}" if page > 1 else None,
        results=to_list_response(products),
    )


@router.get("/search/", response_model=PaginatedResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Search products by name or description. Non-admin users only see active products."""
    db = get_database()
    
    is_admin = current_user and current_user.get("is_admin", False)
    
    filter_query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    }
    
    # Add isActive filter for non-admin users
    if not is_admin:
        filter_query["isActive"] = True
    
    total = await db.products.count_documents(filter_query)
    skip = (page - 1) * page_size
    
    cursor = db.products.find(filter_query).sort("createdAt", -1).skip(skip).limit(page_size)
    products = await cursor.to_list(length=page_size)
    
    return PaginatedResponse(
        count=total,
        next=f"?page={page+1}&page_size={page_size}&q={q}" if skip + page_size < total else None,
        previous=f"?page={page-1}&page_size={page_size}&q={q}" if page > 1 else None,
        results=to_list_response(products),
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    admin_user: dict = Depends(get_admin_user),
):
    """Create a new product. Requires admin."""
    db = get_database()
    
    existing = await db.products.find_one({"sku": product.sku})
    if existing:
        raise HTTPException(status_code=400, detail="A product with this SKU already exists")
    
    now = datetime.utcnow()
    product_dict = {
        **product.model_dump(),
        "price": float(product.price),
        "createdAt": now,
        "updatedAt": now,
    }
    
    result = await db.products.insert_one(product_dict)
    product_dict["_id"] = result.inserted_id
    
    return product_to_response(product_dict)


@router.get("/{product_id}/stock/", response_model=ProductStockResponse)
async def get_product_stock(product_id: str):
    """Get product stock information."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"_id": oid, "isActive": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductStockResponse(
        product_id=str(product["_id"]),
        stock_quantity=product["stockQuantity"],
        in_stock=product["stockQuantity"] > 0,
        available=product.get("isActive", True) and product["stockQuantity"] > 0,
    )


@router.get("/{product_id}/", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get product by ID."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product_to_response(product)


@router.put("/{product_id}/", response_model=ProductResponse)
@router.patch("/{product_id}/", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    admin_user: dict = Depends(get_admin_user),
):
    """Update a product. Requires admin."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    
    if "sku" in update_data:
        existing = await db.products.find_one({"sku": update_data["sku"], "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(status_code=400, detail="A product with this SKU already exists")
    
    if "price" in update_data:
        update_data["price"] = float(update_data["price"])
    
    update_data["updatedAt"] = datetime.utcnow()
    
    await db.products.update_one({"_id": oid}, {"$set": update_data})
    updated = await db.products.find_one({"_id": oid})
    
    return product_to_response(updated)


@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin_user: dict = Depends(get_admin_user),
):
    """Soft delete a product. Requires admin."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.products.update_one(
        {"_id": oid},
        {"$set": {"isActive": False, "updatedAt": datetime.utcnow()}}
    )
    
    return None
