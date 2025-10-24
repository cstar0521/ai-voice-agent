"""
Repository for Configuration CRUD operations.
"""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.configuration import VoicePrompt, ConversationFlow


class ConfigurationRepository:
    """Repository for managing Configuration documents in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db.voice_prompts  # Changed from configurations to voice_prompts
        self.flows_collection = db.conversation_flows
    
    async def create_prompt(self, prompt: VoicePrompt) -> VoicePrompt:
        """
        Create a new voice prompt.
        
        Args:
            prompt: VoicePrompt object to create
            
        Returns:
            Created VoicePrompt object
        """
        prompt_dict = prompt.model_dump()
        await self.collection.insert_one(prompt_dict)
        return prompt
    
    async def get_prompt(
        self,
        state: str,
        language: str
    ) -> Optional[VoicePrompt]:
        """
        Get a voice prompt by state and language.
        
        Args:
            state: Conversation state
            language: Language code
            
        Returns:
            VoicePrompt object if found, None otherwise
        """
        prompt_dict = await self.collection.find_one({
            "state": state,
            "language": language
        })
        if prompt_dict:
            prompt_dict.pop("_id", None)
            return VoicePrompt(**prompt_dict)
        return None
    
    async def get_prompts_by_language(self, language: str) -> List[VoicePrompt]:
        """
        Get all prompts for a specific language.
        
        Args:
            language: Language code
            
        Returns:
            List of VoicePrompt objects
        """
        cursor = self.collection.find({"language": language})
        prompts = []
        async for prompt_dict in cursor:
            prompt_dict.pop("_id", None)
            prompts.append(VoicePrompt(**prompt_dict))
        return prompts
    
    async def update_prompt(
        self,
        prompt_id: str,
        updates: dict
    ) -> Optional[VoicePrompt]:
        """
        Update a voice prompt.
        
        Args:
            prompt_id: Prompt identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated VoicePrompt object if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"prompt_id": prompt_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return VoicePrompt(**result)
        return None
    
    async def create_flow(self, flow: ConversationFlow) -> ConversationFlow:
        """
        Create a new conversation flow.
        
        Args:
            flow: ConversationFlow object to create
            
        Returns:
            Created ConversationFlow object
        """
        flow_dict = flow.model_dump()
        await self.flows_collection.insert_one(flow_dict)
        return flow
    
    async def get_flow(self, flow_id: str) -> Optional[ConversationFlow]:
        """
        Get a conversation flow by ID.
        
        Args:
            flow_id: Flow identifier
            
        Returns:
            ConversationFlow object if found, None otherwise
        """
        flow_dict = await self.flows_collection.find_one({"flow_id": flow_id})
        if flow_dict:
            flow_dict.pop("_id", None)
            return ConversationFlow(**flow_dict)
        return None
    
    async def list_flows(self) -> List[ConversationFlow]:
        """
        Get all conversation flows.
        
        Returns:
            List of ConversationFlow objects
        """
        cursor = self.flows_collection.find({})
        flows = []
        async for flow_dict in cursor:
            flow_dict.pop("_id", None)
            flows.append(ConversationFlow(**flow_dict))
        return flows
    
    async def update_flow(
        self,
        flow_id: str,
        updates: dict
    ) -> Optional[ConversationFlow]:
        """
        Update a conversation flow.
        
        Args:
            flow_id: Flow identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated ConversationFlow object if found, None otherwise
        """
        result = await self.flows_collection.find_one_and_update(
            {"flow_id": flow_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return ConversationFlow(**result)
        return None
