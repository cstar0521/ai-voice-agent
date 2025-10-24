"""
Audit log API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List

from app.auth import get_current_user, require_admin
from app.database import database
from app.services.audit_service import AuditService, AuditAction

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(require_admin)
):
    """
    Get audit logs with filters (admin only).
    
    Args:
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        user_id: Filter by user ID
        action: Filter by action type
        days: Number of days to look back
        limit: Maximum number of results
        current_user: Authenticated admin user
        
    Returns:
        List of audit log entries
    """
    db = database.get_database()
    audit_service = AuditService(db)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Convert action string to enum if provided
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass
    
    logs = await audit_service.get_audit_logs(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action=action_enum,
        start_date=start_date,
        limit=limit
    )
    
    return {"logs": logs, "count": len(logs)}


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, le=500),
    current_user: dict = Depends(require_admin)
):
    """
    Get complete audit history for a specific resource (admin only).
    
    Args:
        resource_type: Type of resource
        resource_id: ID of resource
        limit: Maximum number of results
        current_user: Authenticated admin user
        
    Returns:
        List of audit log entries
    """
    db = database.get_database()
    audit_service = AuditService(db)
    
    history = await audit_service.get_resource_history(
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit
    )
    
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "history": history,
        "count": len(history)
    }


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(require_admin)
):
    """
    Get all activity for a specific user (admin only).
    
    Args:
        user_id: User ID
        days: Number of days to look back
        limit: Maximum number of results
        current_user: Authenticated admin user
        
    Returns:
        List of audit log entries
    """
    db = database.get_database()
    audit_service = AuditService(db)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    activity = await audit_service.get_user_activity(
        user_id=user_id,
        start_date=start_date,
        limit=limit
    )
    
    return {
        "user_id": user_id,
        "activity": activity,
        "count": len(activity)
    }


@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(require_admin)
):
    """
    Get audit log statistics (admin only).
    
    Args:
        days: Number of days to analyze
        current_user: Authenticated admin user
        
    Returns:
        Audit statistics
    """
    db = database.get_database()
    audit_service = AuditService(db)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    stats = await audit_service.get_audit_statistics(
        start_date=start_date
    )
    
    return stats
