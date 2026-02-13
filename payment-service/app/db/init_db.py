import logging
from app.db.base import Base, engine
from app.db.models import Payment  # noqa: F401

logger = logging.getLogger(__name__)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

if __name__ == "__main__":
    init_db()