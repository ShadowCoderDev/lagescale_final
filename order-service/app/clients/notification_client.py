import json
import logging
import pika
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationPublisher:
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = settings.NOTIFICATION_QUEUE
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((pika.exceptions.AMQPConnectionError, ConnectionError)),
        reraise=True
    )
    def _create_connection(self):
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
    
    def _get_connection(self):
        try:
            if self.connection and self.connection.is_open:
                return self.connection
            self._create_connection()
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ after retries: {e}")
            return None
    
    def publish(self, event_type: str, data: dict, queue: str = None) -> bool:
        try:
            if not self._get_connection():
                logger.warning("RabbitMQ not available, skipping notification")
                return False
            
            target_queue = queue or self.queue_name
            
            self.channel.queue_declare(queue=target_queue, durable=True)
            
            message = {
                "event_type": event_type,
                "data": data
            }
            
            self.channel.basic_publish(
                exchange="",
                routing_key=target_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            
            logger.info(f"Published event: {event_type} to queue: {target_queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            # Reset connection on error
            self.connection = None
            self.channel = None
            return False
    
    def send_order_created(self, email: str, order_id: int, total_amount: float) -> bool:
        return self.publish("order_created", {
            "email": email,
            "order_id": order_id,
            "total_amount": total_amount
        })
    
    def send_payment_success(self, email: str, order_id: int, transaction_id: str) -> bool:
        return self.publish("payment_success", {
            "email": email,
            "order_id": order_id,
            "transaction_id": transaction_id
        })
    
    def send_payment_failed(self, email: str, order_id: int, reason: str) -> bool:
        return self.publish("payment_failed", {
            "email": email,
            "order_id": order_id,
            "reason": reason
        })
    
    def send_order_canceled(self, email: str, order_id: int) -> bool:
        return self.publish("order_canceled", {
            "email": email,
            "order_id": order_id
        })
    
    def send_stock_update(self, product_id: str, quantity: int, order_id: int) -> bool:
        return self.publish("stock_update", {
            "product_id": product_id,
            "quantity": quantity,
            "order_id": order_id,
            "action": "decrease"
        }, queue=settings.STOCK_QUEUE)
    
    def send_stock_restore(self, product_id: str, quantity: int, order_id: int) -> bool:
        return self.publish("stock_update", {
            "product_id": product_id,
            "quantity": quantity,
            "order_id": order_id,
            "action": "increase"
        }, queue=settings.STOCK_QUEUE)
    
    def close(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


notification_publisher = NotificationPublisher()
