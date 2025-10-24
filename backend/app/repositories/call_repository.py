"""
Repository for Call CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.call import Call


class CallRepository:
    """Repository for managing Call documents in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.calls
    
    async def create(self, call: Call) -> Call:
        """
        Create a new call in the database.
        
        Args:
            call: Call object to create
            
        Returns:
            Created Call object
        """
        call_dict = call.model_dump()
        await self.collection.insert_one(call_dict)
        return call
    
    async def get_by_id(self, call_id: str) -> Optional[Call]:
        """
        Get a call by its ID.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Call object if found, None otherwise
        """
        call_dict = await self.collection.find_one({"call_id": call_id})
        if call_dict:
            call_dict.pop("_id", None)
            return Call(**call_dict)
        return None
    
    async def get_by_call_sid(self, call_sid: str) -> Optional[Call]:
        """
        Get a call by Twilio call SID.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Call object if found, None otherwise
        """
        call_dict = await self.collection.find_one({"call_sid": call_sid})
        if call_dict:
            call_dict.pop("_id", None)
            return Call(**call_dict)
        return None
    
    async def get_by_lead_id(self, lead_id: str) -> List[Call]:
        """
        Get all calls for a specific lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            List of Call objects
        """
        cursor = self.collection.find({"lead_id": lead_id}).sort("created_at", -1)
        calls = []
        async for call_dict in cursor:
            call_dict.pop("_id", None)
            calls.append(Call(**call_dict))
        return calls
    
    async def update(self, call_id: str, updates: dict) -> Optional[Call]:
        """
        Update a call with new data.
        
        Args:
            call_id: Call identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated Call object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"call_id": call_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Call(**result)
        return None
    
    async def update_status(self, call_id: str, status: str) -> Optional[Call]:
        """
        Update call status.
        
        Args:
            call_id: Call identifier
            status: New status
            
        Returns:
            Updated Call object if found, None otherwise
        """
        return await self.update(call_id, {"status": status})
    
    async def list(
        self,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Call]:
        """
        List calls with optional filtering and pagination.
        
        Args:
            status: Filter by status
            direction: Filter by direction
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Call objects
        """
        query = {}
        if status:
            query["status"] = status
        if direction:
            query["direction"] = direction
        
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        calls = []
        async for call_dict in cursor:
            call_dict.pop("_id", None)
            calls.append(Call(**call_dict))
        return calls
    
    async def increment_retry_count(self, call_id: str) -> Optional[Call]:
        """
        Increment the retry count for a call.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Updated Call object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"call_id": call_id},
            {"$inc": {"retry_count": 1}},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Call(**result)
        return None
