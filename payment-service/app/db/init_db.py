"""Initialize database tables"""
import logging
from app.db.base import Base, engine
# مدل Payment باید import شود تا Base.metadata آن را بشناسد
from app.db.models import Payment  # noqa: F401

logger = logging.getLogger(__name__)

def init_db():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

if __name__ == "__main__":
    init_db()