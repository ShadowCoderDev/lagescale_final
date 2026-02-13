from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.config import settings
from app.services.email_service import email_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    event_type: str  # order_created, payment_success, payment_failed, order_canceled
    order_id: int
    total_amount: Optional[float] = None
    transaction_id: Optional[str] = None
    reason: Optional[str] = None


@router.get("/status/")
async def get_status():
    return {
        "email_service": "active",
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "rabbitmq_host": settings.RABBITMQ_HOST,
        "rabbitmq_port": settings.RABBITMQ_PORT
    }


@router.post("/test/")
async def send_test_email(request: TestEmailRequest):
    try:
        success = False
        
        if request.event_type == "order_created":
            success = email_service.send_order_created(
                request.to_email,
                request.order_id,
                request.total_amount or 0
            )
        elif request.event_type == "payment_success":
            success = email_service.send_payment_success(
                request.to_email,
                request.order_id,
                request.transaction_id or "N/A"
            )
        elif request.event_type == "payment_failed":
            success = email_service.send_payment_failed(
                request.to_email,
                request.order_id,
                request.reason or "Unknown error"
            )
        elif request.event_type == "order_canceled":
            success = email_service.send_order_canceled(
                request.to_email,
                request.order_id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown event type: {request.event_type}")
        
        if success:
            return {"message": "Test email sent successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

