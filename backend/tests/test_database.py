"""
Unit tests for database connection and error handling.
"""
import pytest
from pymongo.errors import ConnectionFailure

from app.database import Database


class TestDatabase:
    """Tests for Database connection manager."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful database connection."""
        db = Database()
        try:
            await db.connect()
            assert db.client is not None
            assert db.db is not None
            
            # Test ping
            is_alive = await db.ping()
            assert is_alive is True
        finally:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_database_before_connect(self):
        """Test that getting database before connect raises error."""
        db = Database()
        db.client = None
        db.db = None
        
        with pytest.raises(RuntimeError):
            db.get_database()
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test database disconnection."""
        db = Database()
        await db.connect()
        await db.disconnect()
        
        assert db.client is None
        assert db.db is None
    
    @pytest.mark.asyncio
    async def test_ping_when_not_connected(self):
        """Test ping returns False when not connected."""
        db = Database()
        db.client = None
        
        is_alive = await db.ping()
        assert is_alive is False
    
    @pytest.mark.asyncio
    async def test_connect_with_invalid_uri(self):
        """Test connection with invalid URI raises error."""
        from config import settings
        original_uri = settings.mongodb_uri
        
        try:
            settings.mongodb_uri = "mongodb://invalid:99999"
            db = Database()
            
            with pytest.raises(ConnectionFailure):
                await db.connect()
        finally:
            settings.mongodb_uri = original_uri
