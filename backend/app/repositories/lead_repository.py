"""
Repository for Lead CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.models.lead import Lead


class LeadRepository:
    """Repository for managing Lead documents in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.leads
    
    async def create(self, lead: Lead) -> Lead:
        """
        Create a new lead in the database.
        
        Args:
            lead: Lead object to create
            
        Returns:
            Created Lead object
            
        Raises:
            DuplicateKeyError: If lead_id already exists
        """
        lead_dict = lead.model_dump()
        await self.collection.insert_one(lead_dict)
        return lead
    
    async def get_by_id(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by its ID.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Lead object if found, None otherwise
        """
        lead_dict = await self.collection.find_one({"lead_id": lead_id})
        if lead_dict:
            lead_dict.pop("_id", None)
            return Lead(**lead_dict)
        return None
    
    async def get_by_phone(self, phone: str) -> Optional[Lead]:
        """
        Get a lead by phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            Lead object if found, None otherwise
        """
        lead_dict = await self.collection.find_one({"phone": phone})
        if lead_dict:
            lead_dict.pop("_id", None)
            return Lead(**lead_dict)
        return None
    
    async def update(self, lead_id: str, updates: dict) -> Optional[Lead]:
        """
        Update a lead with new data.
        
        Args:
            lead_id: Lead identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated Lead object if found, None otherwise
        """
        updates["updated_at"] = datetime.utcnow()
        result = await self.collection.find_one_and_update(
            {"lead_id": lead_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Lead(**result)
        return None
    
    async def delete(self, lead_id: str) -> bool:
        """
        Delete a lead from the database.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"lead_id": lead_id})
        return result.deleted_count > 0
    
    async def list(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lead]:
        """
        List leads with optional filtering and pagination.
        
        Args:
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Lead objects
        """
        query = {}
        if status:
            query["status"] = status
        
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        leads = []
        async for lead_dict in cursor:
            lead_dict.pop("_id", None)
            leads.append(Lead(**lead_dict))
        return leads
    
    async def count(self, status: Optional[str] = None) -> int:
        """
        Count leads with optional filtering.
        
        Args:
            status: Filter by status
            
        Returns:
            Count of leads
        """
        query = {}
        if status:
            query["status"] = status
        return await self.collection.count_documents(query)
    
    async def update_status(self, lead_id: str, status: str) -> Optional[Lead]:
        """
        Update lead status.
        
        Args:
            lead_id: Lead identifier
            status: New status
            
        Returns:
            Updated Lead object if found, None otherwise
        """
        return await self.update(lead_id, {"status": status})
