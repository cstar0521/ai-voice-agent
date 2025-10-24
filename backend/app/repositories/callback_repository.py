"""
Repository for Callback CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.callback import Callback


class CallbackRepository:
    """Repository for managing Callback documents in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.callbacks
    
    async def create(self, callback: Callback) -> Callback:
        """
        Create a new callback in the database.
        
        Args:
            callback: Callback object to create
            
        Returns:
            Created Callback object
        """
        callback_dict = callback.model_dump()
        await self.collection.insert_one(callback_dict)
        return callback
    
    async def get_by_id(self, callback_id: str) -> Optional[Callback]:
        """
        Get a callback by its ID.
        
        Args:
            callback_id: Callback identifier
            
        Returns:
            Callback object if found, None otherwise
        """
        callback_dict = await self.collection.find_one({"callback_id": callback_id})
        if callback_dict:
            callback_dict.pop("_id", None)
            return Callback(**callback_dict)
        return None
    
    async def get_by_lead_id(self, lead_id: str) -> List[Callback]:
        """
        Get all callbacks for a specific lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            List of Callback objects
        """
        cursor = self.collection.find({"lead_id": lead_id}).sort("created_at", -1)
        callbacks = []
        async for callback_dict in cursor:
            callback_dict.pop("_id", None)
            callbacks.append(Callback(**callback_dict))
        return callbacks
    
    async def update(self, callback_id: str, updates: dict) -> Optional[Callback]:
        """
        Update a callback with new data.
        
        Args:
            callback_id: Callback identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated Callback object if found, None otherwise
        """
        updates["updated_at"] = datetime.utcnow()
        result = await self.collection.find_one_and_update(
            {"callback_id": callback_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Callback(**result)
        return None
    
    async def update_status(self, callback_id: str, status: str) -> Optional[Callback]:
        """
        Update callback status.
        
        Args:
            callback_id: Callback identifier
            status: New status
            
        Returns:
            Updated Callback object if found, None otherwise
        """
        updates = {"status": status}
        if status == "completed":
            updates["completed_at"] = datetime.utcnow()
        return await self.update(callback_id, updates)
    
    async def list(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Callback]:
        """
        List callbacks with optional filtering and pagination.
        
        Args:
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Callback objects
        """
        query = {}
        if status:
            query["status"] = status
        
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("scheduled_time", 1)
        callbacks = []
        async for callback_dict in cursor:
            callback_dict.pop("_id", None)
            callbacks.append(Callback(**callback_dict))
        return callbacks
    
    async def get_pending_callbacks(self, before_time: datetime) -> List[Callback]:
        """
        Get pending callbacks scheduled before a specific time.
        
        Args:
            before_time: Get callbacks scheduled before this time
            
        Returns:
            List of Callback objects
        """
        query = {
            "status": "pending",
            "scheduled_time": {"$lte": before_time}
        }
        
        cursor = self.collection.find(query).sort("scheduled_time", 1)
        callbacks = []
        async for callback_dict in cursor:
            callback_dict.pop("_id", None)
            callbacks.append(Callback(**callback_dict))
        return callbacks
