"""
Lead management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List

from app.auth import get_current_user
from app.database import database
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository

router = APIRouter()


class LeadUpdateRequest(BaseModel):
    """Request model for updating lead."""
    name: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    degree: Optional[str] = None
    loan_amount: Optional[float] = None
    offer_letter: Optional[str] = None
    coapplicant_itr: Optional[str] = None
    collateral: Optional[str] = None
    visa_timeline: Optional[str] = None
    eligibility_category: Optional[str] = None
    sentiment_score: Optional[float] = None
    urgency: Optional[str] = None
    status: Optional[str] = None


class LeadListResponse(BaseModel):
    """Response model for lead list."""
    leads: List[Lead]
    total: int
    page: int
    page_size: int


class HandoffResponse(BaseModel):
    """Response model for handoff trigger."""
    lead_id: str
    status: str
    message: str
    handoff_triggered: bool


@router.get("", response_model=LeadListResponse)
async def list_leads(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    List leads with filters and pagination.
    
    Args:
        status_filter: Filter by lead status
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        
    Returns:
        Paginated list of leads
    """
    db = database.get_database()
    lead_repo = LeadRepository(db)
    
    skip = (page - 1) * page_size
    
    leads = await lead_repo.list(
        status=status_filter,
        skip=skip,
        limit=page_size
    )
    
    total = await lead_repo.count(status=status_filter)
    
    return LeadListResponse(
        leads=leads,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get lead details by ID.
    
    Args:
        lead_id: Lead identifier
        current_user: Authenticated user
        
    Returns:
        Lead details
        
    Raises:
        HTTPException: If lead not found
    """
    db = database.get_database()
    lead_repo = LeadRepository(db)
    
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )
    
    return lead


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str,
    request: LeadUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update lead information.
    
    Args:
        lead_id: Lead identifier
        request: Lead update data
        current_user: Authenticated user
        
    Returns:
        Updated lead
        
    Raises:
        HTTPException: If lead not found
    """
    db = database.get_database()
    lead_repo = LeadRepository(db)
    
    # Check if lead exists
    existing_lead = await lead_repo.get_by_id(lead_id)
    if not existing_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )
    
    # Prepare updates (only include non-None values)
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        return existing_lead
    
    # Update lead
    updated_lead = await lead_repo.update(lead_id, updates)
    
    return updated_lead


@router.post("/{lead_id}/handoff", response_model=HandoffResponse)
async def trigger_handoff(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger human expert handoff for a lead.
    
    Args:
        lead_id: Lead identifier
        current_user: Authenticated user
        
    Returns:
        Handoff confirmation
        
    Raises:
        HTTPException: If lead not found
    """
    db = database.get_database()
    lead_repo = LeadRepository(db)
    
    # Check if lead exists
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )
    
    # Update lead status to handoff
    updated_lead = await lead_repo.update_status(lead_id, "handoff")
    
    # TODO: Integrate with CRM to notify expert
    # TODO: Send notification to lead via WhatsApp/SMS
    
    return HandoffResponse(
        lead_id=lead_id,
        status=updated_lead.status,
        message="Handoff triggered successfully",
        handoff_triggered=True
    )
