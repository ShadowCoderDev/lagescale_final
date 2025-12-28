"""Email Service"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings
from app.db.base import get_db_session
from app.db import crud
from app.db.models import NotificationType, NotificationStatus

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service using SMTP"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        event_type: Optional[str] = None,
        order_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Send an email and log to database.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (optional)
            event_type: Type of event (order_created, payment_success, etc.)
            order_id: Associated order ID
            user_id: Associated user ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Create log entry first
        db = get_db_session()
        log_entry = None
        try:
            log_entry = crud.create_notification_log(
                db=db,
                notification_type=NotificationType.EMAIL,
                recipient=to_email,
                subject=subject,
                content=body_text or body_html[:500],
                event_type=event_type,
                order_id=order_id,
                user_id=user_id,
                status=NotificationStatus.PENDING
            )
        except Exception as e:
            logger.error(f"Failed to create notification log: {e}")
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Add plain text part
            if body_text:
                part1 = MIMEText(body_text, "plain")
                msg.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(body_html, "html")
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent to {to_email}: {subject}")
            
            # Update log entry to SENT
            if log_entry:
                crud.update_notification_status(db, log_entry.id, NotificationStatus.SENT)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            
            # Update log entry to FAILED
            if log_entry:
                crud.update_notification_status(db, log_entry.id, NotificationStatus.FAILED, str(e))
            
            return False
        finally:
            db.close()
    
    def send_order_created(self, to_email: str, order_id: int, total_amount: float, user_id: Optional[int] = None) -> bool:
        """Send order created notification"""
        subject = f"سفارش #{order_id} - ثبت شد"
        
        body_html = f"""
        <html>
        <body dir="rtl" style="font-family: Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">✓ سفارش شما ثبت شد</h1>
            </div>
            <div style="padding: 25px; background: #fff; border: 1px solid #e0e0e0;">
                <p style="font-size: 16px;">با تشکر از خرید شما!</p>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>شماره سفارش:</strong> #{order_id}</p>
                    <p style="margin: 5px 0;"><strong>مبلغ کل:</strong> ${total_amount:,.2f}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p>سفارش شما با موفقیت ثبت شده و در حال پردازش است.</p>
            </div>
            <div style="background: #333; color: #fff; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">فروشگاه آنلاین</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        سفارش شما ثبت شد!
        
        با تشکر از خرید شما!
        
        شماره سفارش: #{order_id}
        مبلغ کل: ${total_amount:,.2f}
        
        سفارش شما با موفقیت ثبت شده و در حال پردازش است.
        """
        
        return self.send_email(
            to_email, subject, body_html, body_text,
            event_type="order_created", order_id=order_id, user_id=user_id
        )
    
    def send_payment_success(self, to_email: str, order_id: int, transaction_id: str, user_id: Optional[int] = None) -> bool:
        """Send payment success notification"""
        subject = f"سفارش #{order_id} - پرداخت موفق"
        
        body_html = f"""
        <html>
        <body dir="rtl" style="font-family: Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">💳 پرداخت موفق</h1>
            </div>
            <div style="padding: 25px; background: #fff; border: 1px solid #e0e0e0;">
                <p style="font-size: 16px; color: #4CAF50;">✓ پرداخت شما با موفقیت انجام شد!</p>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>شماره سفارش:</strong> #{order_id}</p>
                    <p style="margin: 5px 0;"><strong>شناسه تراکنش:</strong> {transaction_id}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p>سفارش شما در حال آماده‌سازی برای ارسال است.</p>
                <p style="color: #666; font-size: 14px;">از خرید شما متشکریم!</p>
            </div>
            <div style="background: #333; color: #fff; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">فروشگاه آنلاین</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        پرداخت موفق!
        
        پرداخت شما با موفقیت انجام شد!
        
        شماره سفارش: #{order_id}
        شناسه تراکنش: {transaction_id}
        
        سفارش شما در حال آماده‌سازی برای ارسال است.
        """
        
        return self.send_email(
            to_email, subject, body_html, body_text,
            event_type="payment_success", order_id=order_id, user_id=user_id
        )
    
    def send_payment_failed(self, to_email: str, order_id: int, reason: str, user_id: Optional[int] = None) -> bool:
        """Send payment failed notification"""
        subject = f"سفارش #{order_id} - پرداخت ناموفق"
        
        body_html = f"""
        <html>
        <body dir="rtl" style="font-family: Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #f44336, #d32f2f); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">✗ پرداخت ناموفق</h1>
            </div>
            <div style="padding: 25px; background: #fff; border: 1px solid #e0e0e0;">
                <p style="font-size: 16px;">متأسفانه پرداخت شما انجام نشد.</p>
                <div style="background: #fff3f3; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #ffcdd2;">
                    <p style="margin: 5px 0;"><strong>شماره سفارش:</strong> #{order_id}</p>
                    <p style="margin: 5px 0;"><strong>دلیل:</strong> {reason}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p>لطفاً دوباره تلاش کنید یا از روش پرداخت دیگری استفاده کنید.</p>
            </div>
            <div style="background: #333; color: #fff; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">فروشگاه آنلاین</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        پرداخت ناموفق
        
        متأسفانه پرداخت شما انجام نشد.
        
        شماره سفارش: #{order_id}
        دلیل: {reason}
        
        لطفاً دوباره تلاش کنید یا از روش پرداخت دیگری استفاده کنید.
        """
        
        return self.send_email(
            to_email, subject, body_html, body_text,
            event_type="payment_failed", order_id=order_id, user_id=user_id
        )
    
    def send_order_canceled(self, to_email: str, order_id: int, user_id: Optional[int] = None) -> bool:
        """Send order canceled notification"""
        subject = f"سفارش #{order_id} - لغو شد"
        
        body_html = f"""
        <html>
        <body dir="rtl" style="font-family: Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #9E9E9E, #757575); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">سفارش لغو شد</h1>
            </div>
            <div style="padding: 25px; background: #fff; border: 1px solid #e0e0e0;">
                <p style="font-size: 16px;">سفارش شما لغو شده است.</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>شماره سفارش:</strong> #{order_id}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p>مبلغ پرداختی به حساب شما برگشت داده خواهد شد.</p>
                <p style="color: #666; font-size: 14px;">اگر شما این لغو را درخواست نکرده‌اید، لطفاً با پشتیبانی تماس بگیرید.</p>
            </div>
            <div style="background: #333; color: #fff; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">فروشگاه آنلاین</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        سفارش لغو شد
        
        سفارش شما لغو شده است.
        
        شماره سفارش: #{order_id}
        
        مبلغ پرداختی به حساب شما برگشت داده خواهد شد.
        اگر شما این لغو را درخواست نکرده‌اید، لطفاً با پشتیبانی تماس بگیرید.
        """
        
        return self.send_email(
            to_email, subject, body_html, body_text,
            event_type="order_canceled", order_id=order_id, user_id=user_id
        )


email_service = EmailService()
