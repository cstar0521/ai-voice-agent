"""
Configuration management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List

from app.auth import get_current_user, require_admin
from app.database import database
from app.models.configuration import VoicePrompt, ConversationFlow
from app.repositories.configuration_repository import ConfigurationRepository

router = APIRouter()


class PromptUpdateRequest(BaseModel):
    """Request model for updating prompt."""
    text: Optional[str] = None
    audio_url: Optional[str] = None


class PromptCreateRequest(BaseModel):
    """Request model for creating prompt."""
    prompt_id: str
    state: str
    language: str
    text: str
    audio_url: Optional[str] = None


class FlowCreateRequest(BaseModel):
    """Request model for creating flow."""
    flow_id: str
    name: str
    states: List[str]
    transitions: dict
    prompts: dict


@router.get("/prompts", response_model=List[VoicePrompt])
async def get_prompts(
    language: Optional[str] = Query(None, description="Filter by language"),
    state: Optional[str] = Query(None, description="Filter by state"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get voice prompts by language and/or state.
    
    Args:
        language: Filter by language
        state: Filter by state
        current_user: Authenticated user
        
    Returns:
        List of voice prompts
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    if language and state:
        # Get specific prompt
        prompt = await config_repo.get_prompt(state, language)
        return [prompt] if prompt else []
    elif language:
        # Get all prompts for language
        prompts = await config_repo.get_prompts_by_language(language)
        return prompts
    else:
        # Get all prompts
        cursor = config_repo.collection.find({})
        prompts = []
        async for prompt_dict in cursor:
            prompt_dict.pop("_id", None)
            prompts.append(VoicePrompt(**prompt_dict))
        return prompts


@router.post("/prompts", response_model=VoicePrompt, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new voice prompt (admin only).
    
    Args:
        request: Prompt creation data
        current_user: Authenticated admin user
        
    Returns:
        Created prompt
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    prompt = VoicePrompt(**request.model_dump())
    created_prompt = await config_repo.create_prompt(prompt)
    
    return created_prompt


@router.put("/prompts/{prompt_id}", response_model=VoicePrompt)
async def update_prompt(
    prompt_id: str,
    request: PromptUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Update a voice prompt (admin only).
    
    Args:
        prompt_id: Prompt identifier
        request: Prompt update data
        current_user: Authenticated admin user
        
    Returns:
        Updated prompt
        
    Raises:
        HTTPException: If prompt not found
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    # Prepare updates
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )
    
    updated_prompt = await config_repo.update_prompt(prompt_id, updates)
    
    if not updated_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt {prompt_id} not found"
        )
    
    return updated_prompt


@router.get("/flows", response_model=List[ConversationFlow])
async def get_flows(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all conversation flows.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of conversation flows
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    flows = await config_repo.list_flows()
    return flows


@router.get("/flows/{flow_id}", response_model=ConversationFlow)
async def get_flow(
    flow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific conversation flow.
    
    Args:
        flow_id: Flow identifier
        current_user: Authenticated user
        
    Returns:
        Conversation flow
        
    Raises:
        HTTPException: If flow not found
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    flow = await config_repo.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow {flow_id} not found"
        )
    
    return flow


@router.post("/flows", response_model=ConversationFlow, status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: FlowCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new conversation flow (admin only).
    
    Args:
        request: Flow creation data
        current_user: Authenticated admin user
        
    Returns:
        Created flow
    """
    db = database.get_database()
    config_repo = ConfigurationRepository(db)
    
    flow = ConversationFlow(**request.model_dump())
    created_flow = await config_repo.create_flow(flow)
    
    return created_flow


# Prompt Versioning Endpoints

class PromptVersionRequest(BaseModel):
    """Request model for creating a new prompt version."""
    text: str


@router.post("/prompts/{state}/{language}/versions", response_model=VoicePrompt)
async def create_prompt_version(
    state: str,
    language: str,
    request: PromptVersionRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new version of a prompt for A/B testing.
    Deactivates the current version and creates a new active version.
    
    Args:
        state: Conversation state
        language: Language code
        request: New prompt text
        current_user: Authenticated admin user
        
    Returns:
        New prompt version
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    prompt_repo = PromptRepository(db)
    
    new_version = await prompt_repo.create_new_version(state, language, request.text)
    return new_version


@router.get("/prompts/{state}/{language}/versions", response_model=List[VoicePrompt])
async def get_prompt_versions(
    state: str,
    language: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all versions of a prompt for a specific state and language.
    
    Args:
        state: Conversation state
        language: Language code
        current_user: Authenticated user
        
    Returns:
        List of prompt versions, sorted by version number (descending)
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    prompt_repo = PromptRepository(db)
    
    versions = await prompt_repo.get_prompt_versions(state, language)
    return versions


@router.post("/prompts/{state}/{language}/rollback/{version}", response_model=VoicePrompt)
async def rollback_prompt_version(
    state: str,
    language: str,
    version: int,
    current_user: dict = Depends(require_admin)
):
    """
    Rollback to a previous prompt version.
    Deactivates the current version and activates the specified version.
    
    Args:
        state: Conversation state
        language: Language code
        version: Version number to rollback to
        current_user: Authenticated admin user
        
    Returns:
        Activated prompt version
        
    Raises:
        HTTPException: If version not found
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    prompt_repo = PromptRepository(db)
    
    activated_prompt = await prompt_repo.rollback_to_version(state, language, version)
    
    if not activated_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for {state}/{language}"
        )
    
    return activated_prompt


@router.get("/prompts/{state}/{language}/active", response_model=VoicePrompt)
async def get_active_prompt(
    state: str,
    language: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the currently active prompt for a state and language.
    
    Args:
        state: Conversation state
        language: Language code
        current_user: Authenticated user
        
    Returns:
        Active prompt
        
    Raises:
        HTTPException: If no active prompt found
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    prompt_repo = PromptRepository(db)
    
    prompt = await prompt_repo.get_prompt(state, language)
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active prompt found for {state}/{language}"
        )
    
    return prompt


# TTS Cache Management Endpoints

@router.post("/prompts/{prompt_id}/regenerate-audio")
async def regenerate_prompt_audio(
    prompt_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Regenerate TTS audio for a specific prompt.
    
    Args:
        prompt_id: Prompt identifier
        current_user: Authenticated admin user
        
    Returns:
        Success message with audio URL
        
    Raises:
        HTTPException: If regeneration fails
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    from app.services.tts_cache_service import TTSCacheService
    
    prompt_repo = PromptRepository(db)
    tts_service = TTSCacheService(prompt_repo)
    
    audio_url = await tts_service.regenerate_prompt_audio(prompt_id)
    
    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate audio for {prompt_id}"
        )
    
    return {
        "message": "Audio regenerated successfully",
        "prompt_id": prompt_id,
        "audio_url": audio_url
    }


@router.post("/prompts/cache-all")
async def cache_all_prompts(
    language: Optional[str] = Query(None, description="Filter by language"),
    current_user: dict = Depends(require_admin)
):
    """
    Generate and cache TTS audio for all prompts.
    
    Args:
        language: Optional language filter
        current_user: Authenticated admin user
        
    Returns:
        Summary of caching results
    """
    db = database.get_database()
    from app.repositories.prompt_repository import PromptRepository
    from app.services.tts_cache_service import TTSCacheService
    
    prompt_repo = PromptRepository(db)
    tts_service = TTSCacheService(prompt_repo)
    
    results = await tts_service.cache_all_prompts(language)
    
    return {
        "message": "Audio caching complete",
        "results": results
    }
