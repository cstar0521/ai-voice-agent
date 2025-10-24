"""
GDPR compliance API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import json

from app.auth import get_current_user, require_admin
from app.database import database
from app.services.data_retention_service import DataRetentionService

router = APIRouter()


class DataDeletionRequest(BaseModel):
    """Request model for data deletion."""
    lead_id: str
    reason: str = "gdpr_request"
    confirm: bool = False


@router.get("/export/{lead_id}")
async def export_lead_data(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Export all data for a lead (GDPR data portability - Article 20).
    
    Args:
        lead_id: Lead identifier
        current_user: Authenticated user
        
    Returns:
        JSON file with all lead data
    """
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    try:
        export_data = await retention_service.export_lead_data(lead_id)
        
        # Return as downloadable JSON file
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=lead_{lead_id}_export.json"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


@router.post("/delete")
async def delete_lead_data(
    request: DataDeletionRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Delete all data for a lead (GDPR right to erasure - Article 17).
    Requires admin privileges and confirmation.
    
    Args:
        request: Deletion request data
        current_user: Authenticated admin user
        
    Returns:
        Deletion statistics
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion must be confirmed by setting confirm=true"
        )
    
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    try:
        stats = await retention_service.delete_lead_data(
            lead_id=request.lead_id,
            reason=request.reason
        )
        
        return {
            "message": "Lead data deleted successfully",
            "lead_id": request.lead_id,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data: {str(e)}"
        )


@router.post("/anonymize/{lead_id}")
async def anonymize_lead_data(
    lead_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Anonymize lead data (alternative to deletion).
    
    Args:
        lead_id: Lead identifier
        current_user: Authenticated admin user
        
    Returns:
        Success message
    """
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    success = await retention_service.anonymize_lead_data(lead_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to anonymize data"
        )
    
    return {
        "message": "Lead data anonymized successfully",
        "lead_id": lead_id
    }


@router.get("/retention/statistics")
async def get_retention_statistics(
    current_user: dict = Depends(require_admin)
):
    """
    Get data retention statistics (admin only).
    
    Args:
        current_user: Authenticated admin user
        
    Returns:
        Retention statistics
    """
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    stats = await retention_service.get_retention_statistics()
    
    return stats


@router.post("/retention/cleanup")
async def run_retention_cleanup(
    current_user: dict = Depends(require_admin)
):
    """
    Manually trigger retention cleanup job (admin only).
    Deletes recordings older than retention period.
    
    Args:
        current_user: Authenticated admin user
        
    Returns:
        Cleanup statistics
    """
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    result = await retention_service.schedule_retention_cleanup()
    
    return result


@router.delete("/recordings/old")
async def delete_old_recordings(
    days: int = 90,
    current_user: dict = Depends(require_admin)
):
    """
    Delete recordings older than specified days (admin only).
    
    Args:
        days: Number of days to retain recordings
        current_user: Authenticated admin user
        
    Returns:
        Deletion statistics
    """
    db = database.get_database()
    retention_service = DataRetentionService(db)
    
    result = await retention_service.delete_old_recordings(days)
    
    return result
