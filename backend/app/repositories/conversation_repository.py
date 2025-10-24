"""
Repository for Conversation CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import Conversation, Turn


class ConversationRepository:
    """Repository for managing Conversation documents in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.conversations
    
    async def create(self, conversation: Conversation) -> Conversation:
        """
        Create a new conversation in the database.
        
        Args:
            conversation: Conversation object to create
            
        Returns:
            Created Conversation object
        """
        conversation_dict = conversation.model_dump()
        await self.collection.insert_one(conversation_dict)
        return conversation
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by its ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation object if found, None otherwise
        """
        conv_dict = await self.collection.find_one({"conversation_id": conversation_id})
        if conv_dict:
            conv_dict.pop("_id", None)
            return Conversation(**conv_dict)
        return None
    
    async def get_by_call_id(self, call_id: str) -> Optional[Conversation]:
        """
        Get a conversation by call ID.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Conversation object if found, None otherwise
        """
        conv_dict = await self.collection.find_one({"call_id": call_id})
        if conv_dict:
            conv_dict.pop("_id", None)
            return Conversation(**conv_dict)
        return None
    
    async def get_by_call_sid(self, call_sid: str) -> Optional[Conversation]:
        """
        Get a conversation by Twilio call SID.
        
        This method looks up the call by call_sid first, then finds the conversation.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Conversation object if found, None otherwise
        """
        # Note: This is a simplified version. In production, you might want to
        # join with the calls collection or store call_sid in conversation
        from app.database import database
        from app.repositories.call_repository import CallRepository
        
        db = database.get_database()
        call_repo = CallRepository(db)
        call = await call_repo.get_by_call_sid(call_sid)
        
        if call:
            return await self.get_by_call_id(call.call_id)
        return None
    
    async def append_turn(self, conversation_id: str, turn: Turn) -> Optional[Conversation]:
        """
        Append a new turn to the conversation.
        
        Args:
            conversation_id: Conversation identifier
            turn: Turn object to append
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        turn_dict = turn.model_dump()
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$push": {"turns": turn_dict},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
    
    async def add_turn(self, conversation_id: str, turn: Turn) -> Optional[Conversation]:
        """
        Alias for append_turn for consistency with webhook handler.
        
        Args:
            conversation_id: Conversation identifier
            turn: Turn object to append
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        return await self.append_turn(conversation_id, turn)
    
    async def update_state(self, conversation_id: str, state: str) -> Optional[Conversation]:
        """
        Update the current state of the conversation.
        
        Args:
            conversation_id: Conversation identifier
            state: New state
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "current_state": state,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
    
    async def update_collected_data(
        self,
        conversation_id: str,
        data: dict
    ) -> Optional[Conversation]:
        """
        Update collected data in the conversation.
        
        Args:
            conversation_id: Conversation identifier
            data: Dictionary of data to merge with collected_data
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    f"collected_data.{key}": value for key, value in data.items()
                } | {"updated_at": datetime.utcnow()},
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
    
    async def increment_negative_turn_count(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """
        Increment the negative turn counter.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$inc": {"negative_turn_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
    
    async def increment_clarification_count(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """
        Increment the clarification counter.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$inc": {"clarification_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
    
    async def trigger_escalation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Mark escalation as triggered.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "escalation_triggered": True,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return Conversation(**result)
        return None
