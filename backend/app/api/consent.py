"""
Consent management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.auth import get_current_user, require_admin
from app.database import database
from app.services.consent_service import ConsentService

router = APIRouter()


class ConsentRequest(BaseModel):
    """Request model for recording consent."""
    call_id: str
    lead_id: str
    consent_given: bool
    consent_text: Optional[str] = None
    audio_url: Optional[str] = None


class ConsentRevocationRequest(BaseModel):
    """Request model for revoking consent."""
    lead_id: str
    call_id: Optional[str] = None


@router.post("/consent/record")
async def record_consent(
    request: ConsentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Record consent decision for a call.
    
    Args:
        request: Consent recording data
        current_user: Authenticated user
        
    Returns:
        Consent record
    """
    db = database.get_database()
    consent_service = ConsentService(db)
    
    consent_record = await consent_service.record_consent(
        call_id=request.call_id,
        lead_id=request.lead_id,
        consent_given=request.consent_given,
        consent_text=request.consent_text,
        audio_url=request.audio_url
    )
    
    # Enable or disable recording based on consent
    if request.consent_given:
        await consent_service.enable_recording(request.call_id)
    else:
        await consent_service.disable_recording(request.call_id)
    
    return consent_record


@router.get("/consent/{call_id}")
async def get_consent_status(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get consent status for a call.
    
    Args:
        call_id: Call identifier
        current_user: Authenticated user
        
    Returns:
        Consent status
    """
    db = database.get_database()
    consent_service = ConsentService(db)
    
    consent_given = await consent_service.get_consent_status(call_id)
    
    if consent_given is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent status not found for this call"
        )
    
    return {
        "call_id": call_id,
        "consent_given": consent_given
    }


@router.get("/consent/lead/{lead_id}/history")
async def get_consent_history(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get consent history for a lead.
    
    Args:
        lead_id: Lead identifier
        current_user: Authenticated user
        
    Returns:
        List of consent records
    """
    db = database.get_database()
    consent_service = ConsentService(db)
    
    history = await consent_service.get_consent_history(lead_id)
    
    return {"lead_id": lead_id, "consent_history": history}


@router.post("/consent/revoke")
async def revoke_consent(
    request: ConsentRevocationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke consent for a lead (GDPR compliance).
    
    Args:
        request: Revocation request data
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    db = database.get_database()
    consent_service = ConsentService(db)
    
    success = await consent_service.revoke_consent(
        lead_id=request.lead_id,
        call_id=request.call_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke consent"
        )
    
    return {
        "message": "Consent revoked successfully",
        "lead_id": request.lead_id,
        "call_id": request.call_id
    }


@router.get("/consent/statistics")
async def get_consent_statistics(
    current_user: dict = Depends(require_admin)
):
    """
    Get consent statistics (admin only).
    
    Args:
        current_user: Authenticated admin user
        
    Returns:
        Consent statistics
    """
    db = database.get_database()
    consent_service = ConsentService(db)
    
    stats = await consent_service.get_consent_statistics()
    
    return stats
