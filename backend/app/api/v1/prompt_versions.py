"""
API endpoints for prompt versioning and A/B testing.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.prompt_versioning import (
    PromptVersioningService,
    get_prompt_versioning_service,
    PromptVersion,
    ABTest,
    PromptStatus,
    ABTestStatus
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/prompt-versions", tags=["Prompt Versioning"])


# Request/Response Models
class CreateVersionRequest(BaseModel):
    prompt_id: str
    state: str
    language: str
    text: str
    voice: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateABTestRequest(BaseModel):
    name: str
    description: str
    prompt_id: str
    state: str
    language: str
    version_a: str
    version_b: str
    traffic_split: float = 0.5
    target_sample_size: int = 1000
    confidence_level: float = 0.95


class VersionResponse(BaseModel):
    version_id: str
    prompt_id: str
    state: str
    language: str
    text: str
    voice: Optional[str]
    version_number: str
    status: str
    created_at: str
    created_by: str
    notes: Optional[str]
    usage_count: int
    success_rate: float


class ABTestResponse(BaseModel):
    test_id: str
    name: str
    description: str
    status: str
    version_a: str
    version_b: str
    traffic_split: float
    current_sample_size: int
    target_sample_size: int
    start_date: Optional[str]
    end_date: Optional[str]
    winner: Optional[str]


@router.post("/versions", response_model=VersionResponse)
async def create_version(
    request: CreateVersionRequest,
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Create a new prompt version."""
    try:
        version = await versioning_service.create_version(
            prompt_id=request.prompt_id,
            state=request.state,
            language=request.language,
            text=request.text,
            created_by=current_user.get("username", "unknown"),
            voice=request.voice,
            notes=request.notes,
            metadata=request.metadata
        )
        
        return VersionResponse(
            version_id=version.version_id,
            prompt_id=version.prompt_id,
            state=version.state,
            language=version.language,
            text=version.text,
            voice=version.voice,
            version_number=version.version_number,
            status=version.status.value,
            created_at=version.created_at.isoformat(),
            created_by=version.created_by,
            notes=version.notes,
            usage_count=version.usage_count,
            success_rate=version.success_rate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: str,
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Get a specific prompt version."""
    version = await versioning_service.get_version(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return VersionResponse(
        version_id=version.version_id,
        prompt_id=version.prompt_id,
        state=version.state,
        language=version.language,
        text=version.text,
        voice=version.voice,
        version_number=version.version_number,
        status=version.status.value,
        created_at=version.created_at.isoformat(),
        created_by=version.created_by,
        notes=version.notes,
        usage_count=version.usage_count,
        success_rate=version.success_rate
    )


@router.get("/versions", response_model=List[VersionResponse])
async def list_versions(
    prompt_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """List prompt versions with optional filters."""
    try:
        status_enum = None
        if status:
            try:
                status_enum = PromptStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        versions = await versioning_service.list_versions(
            prompt_id=prompt_id,
            state=state,
            language=language,
            status=status_enum,
            limit=limit
        )
        
        return [
            VersionResponse(
                version_id=v.version_id,
                prompt_id=v.prompt_id,
                state=v.state,
                language=v.language,
                text=v.text,
                voice=v.voice,
                version_number=v.version_number,
                status=v.status.value,
                created_at=v.created_at.isoformat(),
                created_by=v.created_by,
                notes=v.notes,
                usage_count=v.usage_count,
                success_rate=v.success_rate
            )
            for v in versions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.post("/versions/{version_id}/activate")
async def activate_version(
    version_id: str,
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Activate a specific prompt version."""
    success = await versioning_service.activate_version(version_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to activate version")
    
    return {"message": f"Version {version_id} activated successfully"}


@router.post("/versions/{version_id}/rollback")
async def rollback_to_version(
    version_id: str,
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Rollback to a previous version."""
    success = await versioning_service.rollback_to_version(version_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to rollback to version")
    
    return {"message": f"Successfully rolled back to version {version_id}"}


@router.get("/active/{prompt_id}/{state}/{language}", response_model=VersionResponse)
async def get_active_version(
    prompt_id: str,
    state: str,
    language: str,
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Get the currently active version of a prompt."""
    version = await versioning_service.get_active_version(prompt_id, state, language)
    
    if not version:
        raise HTTPException(status_code=404, detail="No active version found")
    
    return VersionResponse(
        version_id=version.version_id,
        prompt_id=version.prompt_id,
        state=version.state,
        language=version.language,
        text=version.text,
        voice=version.voice,
        version_number=version.version_number,
        status=version.status.value,
        created_at=version.created_at.isoformat(),
        created_by=version.created_by,
        notes=version.notes,
        usage_count=version.usage_count,
        success_rate=version.success_rate
    )


# A/B Testing Endpoints

@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    request: CreateABTestRequest,
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Create a new A/B test."""
    try:
        ab_test = await versioning_service.create_ab_test(
            name=request.name,
            description=request.description,
            prompt_id=request.prompt_id,
            state=request.state,
            language=request.language,
            version_a=request.version_a,
            version_b=request.version_b,
            created_by=current_user.get("username", "unknown"),
            traffic_split=request.traffic_split,
            target_sample_size=request.target_sample_size,
            confidence_level=request.confidence_level
        )
        
        return ABTestResponse(
            test_id=ab_test.test_id,
            name=ab_test.name,
            description=ab_test.description,
            status=ab_test.status.value,
            version_a=ab_test.version_a,
            version_b=ab_test.version_b,
            traffic_split=ab_test.traffic_split,
            current_sample_size=ab_test.current_sample_size,
            target_sample_size=ab_test.target_sample_size,
            start_date=ab_test.start_date.isoformat() if ab_test.start_date else None,
            end_date=ab_test.end_date.isoformat() if ab_test.end_date else None,
            winner=ab_test.winner
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create A/B test: {str(e)}")


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Start an A/B test."""
    success = await versioning_service.start_ab_test(test_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start A/B test")
    
    return {"message": f"A/B test {test_id} started successfully"}


@router.post("/ab-tests/{test_id}/stop")
async def stop_ab_test(
    test_id: str,
    winner: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Stop an A/B test and optionally declare a winner."""
    success = await versioning_service.stop_ab_test(test_id, winner)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop A/B test")
    
    return {"message": f"A/B test {test_id} stopped successfully", "winner": winner}


@router.get("/ab-tests/{test_id}/results")
async def get_ab_test_results(
    test_id: str,
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Get A/B test results and analysis."""
    results = await versioning_service.get_ab_test_results(test_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    return results


@router.get("/ab-tests")
async def list_ab_tests(
    prompt_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """List A/B tests with optional filters."""
    try:
        # This would need to be implemented in the service
        # For now, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list A/B tests: {str(e)}")


# Utility endpoints

@router.get("/prompt/{prompt_id}/{state}/{language}/for-user/{user_id}", response_model=VersionResponse)
async def get_version_for_user(
    prompt_id: str,
    state: str,
    language: str,
    user_id: str,
    versioning_service: PromptVersioningService = Depends(get_prompt_versioning_service)
):
    """Get prompt version for a specific user (considering A/B tests)."""
    version = await versioning_service.get_version_for_ab_test(prompt_id, state, language, user_id)
    
    if not version:
        raise HTTPException(status_code=404, detail="No version found for user")
    
    return VersionResponse(
        version_id=version.version_id,
        prompt_id=version.prompt_id,
        state=version.state,
        language=version.language,
        text=version.text,
        voice=version.voice,
        version_number=version.version_number,
        status=version.status.value,
        created_at=version.created_at.isoformat(),
        created_by=version.created_by,
        notes=version.notes,
        usage_count=version.usage_count,
        success_rate=version.success_rate
    )