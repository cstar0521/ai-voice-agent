"""
MongoDB database connection and configuration using Motor (async driver).
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager with connection pooling."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB with connection pooling.
        
        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_uri}")
            
            # Create client with connection pooling configuration
            cls.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                serverSelectionTimeoutMS=5000,
            )
            
            # Test connection
            await cls.client.admin.command('ping')
            
            # Get database name from URI or use default
            db_name = settings.mongodb_uri.split('/')[-1].split('?')[0] or 'voice_agent'
            cls.db = cls.client[db_name]
            
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionFailure(f"Could not connect to MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection and cleanup resources."""
        if cls.client:
            logger.info("Closing MongoDB connection")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the database instance.
        
        Returns:
            AsyncIOMotorDatabase: The database instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db
    
    @classmethod
    async def ping(cls) -> bool:
        """
        Check if database connection is alive.
        
        Returns:
            bool: True if connection is alive, False otherwise
        """
        try:
            if cls.client:
                await cls.client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
        return False


# Global database instance
database = Database()
