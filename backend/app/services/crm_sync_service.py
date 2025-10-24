"""
CRM Sync Service for managing lead synchronization with retry queue.

This module handles asynchronous lead synchronization to CRM with
retry logic for failed attempts.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.integrations.crm_adapter import CRMAdapter
from app.repositories.lead_repository import LeadRepository

logger = logging.getLogger(__name__)


class CRMSyncService:
    """
    Service for managing CRM synchronization with retry queue.
    
    Handles:
    - Lead summary synchronization
    - Retry queue management
    - Failed sync tracking
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        crm_adapter: CRMAdapter,
        lead_repository: LeadRepository
    ):
        """
        Initialize CRM sync service.
        
        Args:
            db: MongoDB database instance
            crm_adapter: CRM adapter for API calls
            lead_repository: Repository for lead operations
        """
        self.db = db
        self.sync_queue = db.crm_sync_queue
        self.crm_adapter = crm_adapter
        self.lead_repo = lead_repository
        
        logger.info("CRMSyncService initialized")
    
    async def queue_lead_sync(
        self,
        lead_id: str,
        lead_summary: Dict[str, Any],
        priority: str = "normal"
    ) -> str:
        """
        Add lead to sync queue.
        
        Args:
            lead_id: Lead identifier
            lead_summary: Lead summary data
            priority: Priority level (high, normal, low)
        
        Returns:
            Queue item ID
        """
        logger.info(f"Queueing lead {lead_id} for CRM sync")
        
        queue_item = {
            "lead_id": lead_id,
            "lead_summary": lead_summary,
            "priority": priority,
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "created_at": datetime.utcnow(),
            "next_retry_at": datetime.utcnow(),
            "last_error": None
        }
        
        result = await self.sync_queue.insert_one(queue_item)
        queue_id = str(result.inserted_id)
        
        logger.info(f"Lead {lead_id} queued with ID: {queue_id}")
        return queue_id
    
    async def sync_lead(
        self,
        lead_id: str,
        lead_summary: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Synchronize lead to CRM with retry logic.
        
        Args:
            lead_id: Lead identifier
            lead_summary: Lead summary data
            retry_count: Current retry attempt
        
        Returns:
            Sync result dictionary
        """
        logger.info(f"Syncing lead {lead_id} to CRM")
        
        # Attempt sync
        result = await self.crm_adapter.sync_lead_summary(
            lead_id=lead_id,
            lead_summary=lead_summary,
            retry_count=retry_count
        )
        
        if result["success"]:
            # Update lead metadata with CRM sync info
            await self.lead_repo.update(
                lead_id=lead_id,
                updates={
                    "metadata.crm_synced": True,
                    "metadata.crm_sync_at": datetime.utcnow().isoformat(),
                    "metadata.crm_lead_id": result.get("crm_lead_id")
                }
            )
            
            logger.info(f"Lead {lead_id} synced successfully")
        else:
            logger.warning(f"Lead {lead_id} sync failed: {result.get('error')}")
            
            # Queue for retry if needed
            if result.get("should_retry"):
                await self.queue_lead_sync(
                    lead_id=lead_id,
                    lead_summary=lead_summary,
                    priority="high" if retry_count > 0 else "normal"
                )
        
        return result
    
    async def process_sync_queue(
        self,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process pending items in sync queue.
        
        Args:
            batch_size: Number of items to process in batch
        
        Returns:
            Processing results
        """
        logger.info(f"Processing sync queue (batch size: {batch_size})")
        
        # Get pending items ready for retry
        now = datetime.utcnow()
        cursor = self.sync_queue.find({
            "status": "pending",
            "next_retry_at": {"$lte": now},
            "retry_count": {"$lt": 3}
        }).sort("priority", -1).limit(batch_size)
        
        success_count = 0
        failed_count = 0
        retry_count = 0
        
        async for item in cursor:
            lead_id = item["lead_id"]
            lead_summary = item["lead_summary"]
            current_retry = item["retry_count"]
            
            # Attempt sync
            result = await self.crm_adapter.sync_lead_summary(
                lead_id=lead_id,
                lead_summary=lead_summary,
                retry_count=current_retry
            )
            
            if result["success"]:
                # Mark as completed
                await self.sync_queue.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": datetime.utcnow(),
                            "crm_lead_id": result.get("crm_lead_id")
                        }
                    }
                )
                
                # Update lead metadata
                await self.lead_repo.update(
                    lead_id=lead_id,
                    updates={
                        "metadata.crm_synced": True,
                        "metadata.crm_sync_at": datetime.utcnow().isoformat(),
                        "metadata.crm_lead_id": result.get("crm_lead_id")
                    }
                )
                
                success_count += 1
                
            elif result.get("should_retry"):
                # Update retry info
                next_retry = now + timedelta(minutes=5 * (2 ** current_retry))  # Exponential backoff
                
                await self.sync_queue.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "retry_count": current_retry + 1,
                            "next_retry_at": next_retry,
                            "last_error": result.get("error"),
                            "last_attempt_at": datetime.utcnow()
                        }
                    }
                )
                
                retry_count += 1
                
            else:
                # Mark as failed
                await self.sync_queue.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "status": "failed",
                            "failed_at": datetime.utcnow(),
                            "last_error": result.get("error")
                        }
                    }
                )
                
                failed_count += 1
        
        logger.info(
            f"Sync queue processed: {success_count} succeeded, "
            f"{retry_count} queued for retry, {failed_count} failed"
        )
        
        return {
            "success_count": success_count,
            "retry_count": retry_count,
            "failed_count": failed_count
        }
    
    async def get_failed_syncs(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get list of failed sync attempts.
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of failed sync items
        """
        cursor = self.sync_queue.find({
            "status": "failed"
        }).sort("failed_at", -1).limit(limit)
        
        failed_syncs = []
        async for item in cursor:
            item["_id"] = str(item["_id"])
            failed_syncs.append(item)
        
        return failed_syncs
    
    async def retry_failed_sync(
        self,
        queue_id: str
    ) -> bool:
        """
        Manually retry a failed sync.
        
        Args:
            queue_id: Queue item ID
        
        Returns:
            True if retry queued successfully
        """
        from bson import ObjectId
        
        try:
            result = await self.sync_queue.update_one(
                {"_id": ObjectId(queue_id)},
                {
                    "$set": {
                        "status": "pending",
                        "retry_count": 0,
                        "next_retry_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error retrying failed sync: {str(e)}")
            return False
    
    async def clear_old_completed_syncs(
        self,
        days: int = 30
    ) -> int:
        """
        Clear completed sync records older than specified days.
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.sync_queue.delete_many({
            "status": "completed",
            "completed_at": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        logger.info(f"Cleared {deleted_count} old completed sync records")
        
        return deleted_count
