"""
Repository for managing voice prompts in the database.
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.configuration import VoicePrompt


class PromptRepository:
    """Repository for voice prompt operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["voice_prompts"]
    
    async def get_prompt(self, state: str, language: str) -> Optional[VoicePrompt]:
        """
        Get an active prompt for a specific state and language.
        
        Args:
            state: Conversation state
            language: Language code (hinglish, english, telugu)
            
        Returns:
            VoicePrompt if found, None otherwise
        """
        prompt_data = await self.collection.find_one({
            "state": state,
            "language": language.lower(),
            "is_active": True
        })
        
        if prompt_data:
            return VoicePrompt(**prompt_data)
        return None
    
    async def get_all_prompts(self, language: Optional[str] = None) -> List[VoicePrompt]:
        """
        Get all active prompts, optionally filtered by language.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of VoicePrompt objects
        """
        query = {"is_active": True}
        if language:
            query["language"] = language.lower()
        
        cursor = self.collection.find(query)
        prompts = []
        async for prompt_data in cursor:
            prompts.append(VoicePrompt(**prompt_data))
        
        return prompts
    
    async def create_prompt(self, prompt: VoicePrompt) -> VoicePrompt:
        """
        Create a new prompt.
        
        Args:
            prompt: VoicePrompt object to create
            
        Returns:
            Created VoicePrompt
        """
        await self.collection.insert_one(prompt.model_dump())
        return prompt
    
    async def update_prompt(self, prompt_id: str, updates: dict) -> Optional[VoicePrompt]:
        """
        Update a prompt.
        
        Args:
            prompt_id: ID of the prompt to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated VoicePrompt if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"prompt_id": prompt_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return VoicePrompt(**result)
        return None
    
    async def create_new_version(
        self,
        state: str,
        language: str,
        new_text: str
    ) -> VoicePrompt:
        """
        Create a new version of a prompt for A/B testing.
        Deactivates the old version and creates a new active version.
        
        Args:
            state: Conversation state
            language: Language code
            new_text: New prompt text
            
        Returns:
            New VoicePrompt version
        """
        # Get current active prompt
        current = await self.get_prompt(state, language)
        
        if not current:
            # No existing prompt, create version 1
            new_version = 1
        else:
            # Deactivate current version
            await self.collection.update_one(
                {"prompt_id": current.prompt_id},
                {"$set": {"is_active": False}}
            )
            new_version = current.version + 1
        
        # Create new version
        new_prompt = VoicePrompt(
            prompt_id=f"{language}_{state}_v{new_version}",
            state=state,
            language=language,
            text=new_text,
            version=new_version,
            is_active=True
        )
        
        await self.create_prompt(new_prompt)
        return new_prompt
    
    async def rollback_to_version(
        self,
        state: str,
        language: str,
        version: int
    ) -> Optional[VoicePrompt]:
        """
        Rollback to a previous prompt version.
        
        Args:
            state: Conversation state
            language: Language code
            version: Version number to rollback to
            
        Returns:
            Activated VoicePrompt if found, None otherwise
        """
        # Deactivate all versions for this state/language
        await self.collection.update_many(
            {"state": state, "language": language},
            {"$set": {"is_active": False}}
        )
        
        # Activate the target version
        result = await self.collection.find_one_and_update(
            {"state": state, "language": language, "version": version},
            {"$set": {"is_active": True}},
            return_document=True
        )
        
        if result:
            return VoicePrompt(**result)
        return None
    
    async def get_prompt_versions(
        self,
        state: str,
        language: str
    ) -> List[VoicePrompt]:
        """
        Get all versions of a prompt for a specific state and language.
        
        Args:
            state: Conversation state
            language: Language code
            
        Returns:
            List of VoicePrompt versions, sorted by version number
        """
        cursor = self.collection.find({
            "state": state,
            "language": language
        }).sort("version", -1)
        
        versions = []
        async for prompt_data in cursor:
            versions.append(VoicePrompt(**prompt_data))
        
        return versions
    
    async def update_audio_url(self, prompt_id: str, audio_url: str) -> Optional[VoicePrompt]:
        """
        Update the audio URL for a prompt (used after TTS generation).
        
        Args:
            prompt_id: ID of the prompt
            audio_url: URL to the generated audio file
            
        Returns:
            Updated VoicePrompt if found, None otherwise
        """
        return await self.update_prompt(prompt_id, {"audio_url": audio_url})
