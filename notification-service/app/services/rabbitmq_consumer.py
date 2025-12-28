"""RabbitMQ Consumer for Order Events with Retry"""
import json
import logging
import time
import pika
from typing import Callable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class NotificationConsumer:
    """RabbitMQ consumer for order notifications"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = settings.ORDER_QUEUE
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((pika.exceptions.AMQPConnectionError, ConnectionError)),
        reraise=True
    )
    def _connect_with_retry(self):
        """Connect to RabbitMQ with retry logic"""
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        logger.info(f"Connected to RabbitMQ at {settings.RABBITMQ_HOST}")
    
    def connect(self) -> bool:
        """Connect to RabbitMQ with retry"""
        try:
            self._connect_with_retry()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ after retries: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from RabbitMQ"""
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    def process_message(self, ch, method, properties, body):
        """Process incoming message"""
        try:
            message = json.loads(body)
            event_type = message.get("event_type")
            data = message.get("data", {})
            
            logger.info(f"Processing event: {event_type}")
            
            # Route to appropriate handler - returns True if successful
            success = False
            if event_type == "order_created":
                success = self._handle_order_created(data)
            elif event_type == "payment_success":
                success = self._handle_payment_success(data)
            elif event_type == "payment_failed":
                success = self._handle_payment_failed(data)
            elif event_type == "order_canceled":
                success = self._handle_order_canceled(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                success = True  # Don't requeue unknown events
            
            if success:
                # Success - acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Failed - requeue with delay (will retry later)
                logger.warning(f"Email sending failed, requeuing message for event: {event_type}")
                time.sleep(5)  # Wait 5 seconds before requeue to avoid tight loop
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _handle_order_created(self, data: dict) -> bool:
        """Handle order created event - returns True if successful"""
        email = data.get("email")
        order_id = data.get("order_id")
        total_amount = data.get("total_amount", 0)
        
        if not email or not order_id:
            logger.error("Missing email or order_id in order_created event")
            return True  # Don't requeue invalid messages
        
        success = email_service.send_order_created(email, order_id, total_amount)
        if success:
            logger.info(f"Order created email sent for order #{order_id}")
        else:
            logger.error(f"Failed to send order created email for order #{order_id}")
        return success
    
    def _handle_payment_success(self, data: dict) -> bool:
        """Handle payment success event - returns True if successful"""
        email = data.get("email")
        order_id = data.get("order_id")
        transaction_id = data.get("transaction_id", "N/A")
        
        if not email or not order_id:
            logger.error("Missing email or order_id in payment_success event")
            return True  # Don't requeue invalid messages
        
        success = email_service.send_payment_success(email, order_id, transaction_id)
        if success:
            logger.info(f"Payment success email sent for order #{order_id}")
        else:
            logger.error(f"Failed to send payment success email for order #{order_id}")
        return success
    
    def _handle_payment_failed(self, data: dict) -> bool:
        """Handle payment failed event - returns True if successful"""
        email = data.get("email")
        order_id = data.get("order_id")
        reason = data.get("reason", "Unknown error")
        
        if not email or not order_id:
            logger.error("Missing email or order_id in payment_failed event")
            return True  # Don't requeue invalid messages
        
        success = email_service.send_payment_failed(email, order_id, reason)
        if success:
            logger.info(f"Payment failed email sent for order #{order_id}")
        else:
            logger.error(f"Failed to send payment failed email for order #{order_id}")
        return success
    
    def _handle_order_canceled(self, data: dict) -> bool:
        """Handle order canceled event - returns True if successful"""
        email = data.get("email")
        order_id = data.get("order_id")
        
        if not email or not order_id:
            logger.error("Missing email or order_id in order_canceled event")
            return True  # Don't requeue invalid messages
        
        success = email_service.send_order_canceled(email, order_id)
        if success:
            logger.info(f"Order canceled email sent for order #{order_id}")
        else:
            logger.error(f"Failed to send order canceled email for order #{order_id}")
        return success
    
    def start_consuming(self):
        """Start consuming messages"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot connect to RabbitMQ")
        
        # Set prefetch count
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.process_message
        )
        
        logger.info(f"Waiting for messages on queue: {self.queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        finally:
            self.disconnect()


notification_consumer = NotificationConsumer()
