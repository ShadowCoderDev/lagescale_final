from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.auth import get_admin_user, get_optional_user
from app.services.product_service import ProductService, ProductServiceError
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductStockResponse,
    PaginatedResponse,
    StockReserveRequest,
    StockReserveResponse,
    StockReleaseRequest,
    StockConfirmRequest,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    service = ProductService()
    
    is_admin = current_user and current_user.get("is_admin", False)
    products, total = await service.list_products(is_admin, page, page_size)
    
    skip = (page - 1) * page_size
    return PaginatedResponse(
        count=total,
        next=f"?page={page+1}&page_size={page_size}" if skip + page_size < total else None,
        previous=f"?page={page-1}&page_size={page_size}" if page > 1 else None,
        results=products,
    )


@router.get("/search/", response_model=PaginatedResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    service = ProductService()
    
    is_admin = current_user and current_user.get("is_admin", False)
    products, total = await service.search_products(q, is_admin, page, page_size)
    
    skip = (page - 1) * page_size
    return PaginatedResponse(
        count=total,
        next=f"?page={page+1}&page_size={page_size}&q={q}" if skip + page_size < total else None,
        previous=f"?page={page-1}&page_size={page_size}&q={q}" if page > 1 else None,
        results=products,
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    admin_user: dict = Depends(get_admin_user),
):
    service = ProductService()
    
    try:
        return await service.create_product(product)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{product_id}/stock/", response_model=ProductStockResponse)
async def get_product_stock(product_id: str):
    service = ProductService()
    
    try:
        return await service.get_stock(product_id)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{product_id}/", response_model=ProductResponse)
async def get_product(product_id: str):
    service = ProductService()
    
    try:
        return await service.get_product(product_id)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{product_id}/", response_model=ProductResponse)
@router.patch("/{product_id}/", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    admin_user: dict = Depends(get_admin_user),
):
    service = ProductService()
    
    try:
        return await service.update_product(product_id, product_update)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin_user: dict = Depends(get_admin_user),
):
    service = ProductService()
    
    try:
        await service.delete_product(product_id)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None


@router.post("/stock/reserve/", response_model=StockReserveResponse, status_code=status.HTTP_201_CREATED)
async def reserve_stock(request: StockReserveRequest):
    service = ProductService()
    
    try:
        return await service.reserve_stock(
            request.product_id,
            request.quantity,
            request.order_id,
            request.reservation_id
        )
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/stock/release/", status_code=status.HTTP_200_OK)
async def release_stock(request: StockReleaseRequest):
    service = ProductService()
    
    try:
        return await service.release_stock(request.reservation_id, request.reason)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/stock/confirm/", status_code=status.HTTP_200_OK)
async def confirm_stock(request: StockConfirmRequest):
    service = ProductService()
    
    try:
        return await service.confirm_stock(request.reservation_id)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/stock/reservation/{reservation_id}/", response_model=StockReserveResponse)
async def get_reservation(reservation_id: str):
    service = ProductService()
    
    try:
        return await service.get_reservation(reservation_id)
    except ProductServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
