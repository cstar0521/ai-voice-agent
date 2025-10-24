"""
Database initialization script for creating collections and indexes.
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import database

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Create indexes for all collections to optimize queries.
    
    Args:
        db: MongoDB database instance
    """
    logger.info("Creating database indexes...")
    
    # Leads collection indexes
    await db.leads.create_index("lead_id", unique=True)
    await db.leads.create_index("phone")
    await db.leads.create_index("status")
    await db.leads.create_index("created_at")
    await db.leads.create_index([("status", 1), ("created_at", -1)])
    logger.info("Created indexes for 'leads' collection")
    
    # Calls collection indexes
    await db.calls.create_index("call_id", unique=True)
    await db.calls.create_index("lead_id")
    await db.calls.create_index("call_sid")
    await db.calls.create_index("status")
    await db.calls.create_index("created_at")
    await db.calls.create_index([("lead_id", 1), ("created_at", -1)])
    logger.info("Created indexes for 'calls' collection")
    
    # Conversations collection indexes
    await db.conversations.create_index("conversation_id", unique=True)
    await db.conversations.create_index("call_id")
    await db.conversations.create_index("lead_id")
    await db.conversations.create_index("created_at")
    logger.info("Created indexes for 'conversations' collection")
    
    # Configuration collection indexes
    await db.configurations.create_index("prompt_id", unique=True, sparse=True)
    await db.configurations.create_index("flow_id", unique=True, sparse=True)
    await db.configurations.create_index([("state", 1), ("language", 1)], sparse=True)
    logger.info("Created indexes for 'configurations' collection")
    
    logger.info("All indexes created successfully")


async def initialize_database() -> None:
    """
    Initialize the database by connecting and creating indexes.
    """
    try:
        logger.info("Initializing database...")
        
        # Connect to database
        await database.connect()
        
        # Get database instance
        db = database.get_database()
        
        # Create indexes
        await create_indexes(db)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        # Keep connection open for application use
        pass


async def cleanup_database() -> None:
    """
    Cleanup database connection.
    """
    await database.disconnect()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run initialization
    asyncio.run(initialize_database())
    asyncio.run(cleanup_database())
