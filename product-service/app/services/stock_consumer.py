"""RabbitMQ Consumer for Stock Updates"""
import json
import logging
import pika
from bson import ObjectId
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.database import get_sync_database

logger = logging.getLogger(__name__)


class StockConsumer:
    """RabbitMQ consumer for stock updates from order-service"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = settings.STOCK_QUEUE
    
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
            
            # Only process stock_update events
            if event_type == "stock_update":
                logger.info(f"Processing stock_update: {data}")
                self._handle_stock_update(data)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _handle_stock_update(self, data: dict):
        """Handle stock update event - decrease or increase product stock"""
        product_id = data.get("product_id")
        quantity = data.get("quantity", 0)
        order_id = data.get("order_id")
        action = data.get("action", "decrease")  # Default to decrease for backward compatibility
        
        if not product_id or quantity <= 0:
            logger.error(f"Invalid stock update data: {data}")
            return
        
        try:
            db = get_sync_database()
            oid = ObjectId(product_id)
            
            if action == "increase":
                # Restore stock (for order cancellation)
                result = db.products.update_one(
                    {"_id": oid},
                    {"$inc": {"stockQuantity": quantity}}
                )
                if result.modified_count > 0:
                    logger.info(f"Stock RESTORED for product {product_id} by {quantity} (order #{order_id} canceled)")
                else:
                    logger.warning(f"Could not restore stock for product {product_id} - not found")
            else:
                # Decrease stock (for order payment)
                result = db.products.update_one(
                    {"_id": oid, "stockQuantity": {"$gte": quantity}},
                    {"$inc": {"stockQuantity": -quantity}}
                )
                if result.modified_count > 0:
                    logger.info(f"Stock DECREASED for product {product_id} by {quantity} (order #{order_id})")
                else:
                    logger.warning(f"Could not decrease stock for product {product_id} - insufficient stock or not found")
                
        except Exception as e:
            logger.error(f"Failed to update stock for product {product_id}: {e}")
    
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
        
        logger.info(f"Waiting for stock updates on queue: {self.queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        finally:
            self.disconnect()


stock_consumer = StockConsumer()

