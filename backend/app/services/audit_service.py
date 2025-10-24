"""
Audit logging service for tracking all data access and modifications.
Creates an immutable audit trail for compliance and security.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum

from app.logging_config import get_logger

logger = get_logger('security')


class AuditAction(str, Enum):
    """Enumeration of audit actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    CONSENT_GIVEN = "consent_given"
    CONSENT_REVOKED = "consent_revoked"
    DATA_DELETED = "data_deleted"
    RECORDING_ENABLED = "recording_enabled"
    RECORDING_DISABLED = "recording_disabled"


class AuditService:
    """Service for creating and querying audit logs."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["audit_logs"]
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure audit log indexes exist."""
        # Note: In production, create these indexes manually or via migration
        # self.collection.create_index([("timestamp", -1)])
        # self.collection.create_index([("user_id", 1)])
        # self.collection.create_index([("resource_type", 1)])
        # self.collection.create_index([("action", 1)])
        pass
    
    async def log_action(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log an audit event.
        
        Args:
            action: Type of action performed
            resource_type: Type of resource (lead, call, conversation, etc.)
            resource_id: ID of the resource
            user_id: ID of user performing action
            user_ip: IP address of user
            changes: Dictionary of changes made (for updates)
            metadata: Additional context
            success: Whether action succeeded
            error_message: Error message if action failed
            
        Returns:
            Audit log ID
        """
        audit_log = {
            "timestamp": datetime.utcnow(),
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_ip": user_ip,
            "changes": changes or {},
            "metadata": metadata or {},
            "success": success,
            "error_message": error_message
        }
        
        result = await self.collection.insert_one(audit_log)
        audit_id = str(result.inserted_id)
        
        logger.info(
            f"Audit log created",
            extra={
                "audit_id": audit_id,
                "action": action.value,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_id
            }
        )
        
        return audit_id
    
    async def log_data_access(
        self,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        fields_accessed: Optional[List[str]] = None
    ) -> str:
        """
        Log data access event.
        
        Args:
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            user_id: ID of user accessing data
            user_ip: IP address
            fields_accessed: List of fields accessed
            
        Returns:
            Audit log ID
        """
        return await self.log_action(
            action=AuditAction.READ,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_ip=user_ip,
            metadata={"fields_accessed": fields_accessed or []}
        )
    
    async def log_data_modification(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None
    ) -> str:
        """
        Log data modification event.
        
        Args:
            action: CREATE, UPDATE, or DELETE
            resource_type: Type of resource modified
            resource_id: ID of resource modified
            user_id: ID of user making modification
            user_ip: IP address
            old_values: Previous values (for updates/deletes)
            new_values: New values (for creates/updates)
            
        Returns:
            Audit log ID
        """
        changes = {}
        if old_values:
            changes["old"] = old_values
        if new_values:
            changes["new"] = new_values
        
        return await self.log_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_ip=user_ip,
            changes=changes
        )
    
    async def log_authentication(
        self,
        action: AuditAction,
        user_id: str,
        user_ip: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log authentication event.
        
        Args:
            action: LOGIN or LOGOUT
            user_id: ID of user
            user_ip: IP address
            success: Whether authentication succeeded
            error_message: Error message if failed
            
        Returns:
            Audit log ID
        """
        return await self.log_action(
            action=action,
            resource_type="user",
            resource_id=user_id,
            user_id=user_id,
            user_ip=user_ip,
            success=success,
            error_message=error_message
        )
    
    async def log_consent_action(
        self,
        action: AuditAction,
        call_id: str,
        lead_id: str,
        user_id: Optional[str] = None,
        consent_given: Optional[bool] = None
    ) -> str:
        """
        Log consent-related action.
        
        Args:
            action: CONSENT_GIVEN or CONSENT_REVOKED
            call_id: Call ID
            lead_id: Lead ID
            user_id: User ID (if applicable)
            consent_given: Whether consent was given
            
        Returns:
            Audit log ID
        """
        return await self.log_action(
            action=action,
            resource_type="consent",
            resource_id=call_id,
            user_id=user_id,
            metadata={
                "lead_id": lead_id,
                "consent_given": consent_given
            }
        )
    
    async def log_gdpr_action(
        self,
        action: AuditAction,
        lead_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        data_exported: Optional[bool] = None
    ) -> str:
        """
        Log GDPR-related action.
        
        Args:
            action: EXPORT or DATA_DELETED
            lead_id: Lead ID
            user_id: User ID performing action
            reason: Reason for action
            data_exported: Whether data was exported
            
        Returns:
            Audit log ID
        """
        return await self.log_action(
            action=action,
            resource_type="lead",
            resource_id=lead_id,
            user_id=user_id,
            metadata={
                "reason": reason,
                "data_exported": data_exported
            }
        )
    
    async def get_audit_logs(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query audit logs with filters.
        
        Args:
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            user_id: Filter by user ID
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        query = {}
        
        if resource_type:
            query["resource_type"] = resource_type
        if resource_id:
            query["resource_id"] = resource_id
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action.value
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        
        logs = []
        async for log in cursor:
            log.pop("_id", None)
            logs.append(log)
        
        return logs
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get complete audit history for a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of resource
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        return await self.get_audit_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
    
    async def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all activity for a specific user.
        
        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        return await self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get audit log statistics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary with statistics
        """
        match_stage = {}
        if start_date or end_date:
            match_stage["timestamp"] = {}
            if start_date:
                match_stage["timestamp"]["$gte"] = start_date
            if end_date:
                match_stage["timestamp"]["$lte"] = end_date
        
        pipeline = [
            {"$match": match_stage} if match_stage else {"$match": {}},
            {
                "$group": {
                    "_id": "$action",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        
        stats = {
            "total_events": 0,
            "by_action": {}
        }
        
        for result in results:
            action = result["_id"]
            count = result["count"]
            stats["by_action"][action] = count
            stats["total_events"] += count
        
        return stats
