"""
Data retention and GDPR compliance service.
Handles data deletion, export, and retention policies.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

from app.logging_config import get_logger
from app.repositories.call_repository import CallRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.conversation_repository import ConversationRepository

logger = get_logger('security')


class DataRetentionService:
    """Service for managing data retention and GDPR compliance."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.call_repo = CallRepository(db)
        self.lead_repo = LeadRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.retention_days = 90  # Default retention period
    
    async def delete_old_recordings(self, days: int = 90) -> Dict:
        """
        Delete recordings older than specified days.
        
        Args:
            days: Number of days to retain recordings
            
        Returns:
            Dictionary with deletion statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logger.info(f"Starting deletion of recordings older than {days} days")
        
        # Find calls with recordings older than cutoff date
        old_calls = await self.call_repo.collection.find({
            "created_at": {"$lt": cutoff_date},
            "recording_url": {"$ne": None}
        }).to_list(None)
        
        deleted_count = 0
        failed_count = 0
        
        for call in old_calls:
            try:
                # Delete recording from storage (Twilio/S3/GCS)
                recording_url = call.get("recording_url")
                if recording_url:
                    await self._delete_recording_file(recording_url)
                
                # Update call record to remove recording URL
                await self.call_repo.update_call(
                    call["call_id"],
                    {
                        "recording_url": None,
                        "recording_deleted": True,
                        "recording_deleted_at": datetime.utcnow(),
                        "deletion_reason": f"retention_policy_{days}_days"
                    }
                )
                
                deleted_count += 1
                
            except Exception as e:
                logger.error(
                    f"Failed to delete recording for call {call['call_id']}: {e}",
                    exc_info=True
                )
                failed_count += 1
        
        logger.info(
            f"Recording deletion complete",
            extra={
                "deleted": deleted_count,
                "failed": failed_count,
                "retention_days": days
            }
        )
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def _delete_recording_file(self, recording_url: str) -> bool:
        """
        Delete recording file from storage.
        
        Args:
            recording_url: URL of the recording to delete
            
        Returns:
            True if deleted successfully
        """
        # Implementation depends on storage provider
        # For Twilio, use Twilio API
        # For S3/GCS, use respective SDKs
        
        logger.info(f"Deleting recording file: {recording_url}")
        
        # Placeholder - implement based on your storage provider
        # Example for Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # client.recordings(recording_sid).delete()
        
        return True
    
    async def export_lead_data(self, lead_id: str) -> Dict:
        """
        Export all data for a lead (GDPR data portability).
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Dictionary with all lead data
        """
        logger.info(f"Exporting data for lead {lead_id}")
        
        # Get lead data
        lead = await self.lead_repo.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Get all calls for the lead
        calls = await self.call_repo.collection.find({"lead_id": lead_id}).to_list(None)
        
        # Get all conversations for the lead
        conversations = await self.conversation_repo.collection.find({"lead_id": lead_id}).to_list(None)
        
        # Get consent records
        consent_records = await self.db["consent_records"].find({"lead_id": lead_id}).to_list(None)
        
        # Clean up MongoDB _id fields
        for item in calls + conversations + consent_records:
            item.pop("_id", None)
        
        export_data = {
            "lead": lead.model_dump() if lead else None,
            "calls": calls,
            "conversations": conversations,
            "consent_records": consent_records,
            "export_date": datetime.utcnow().isoformat(),
            "export_format": "JSON"
        }
        
        logger.info(
            f"Data export complete for lead {lead_id}",
            extra={
                "calls_count": len(calls),
                "conversations_count": len(conversations)
            }
        )
        
        return export_data
    
    async def delete_lead_data(self, lead_id: str, reason: str = "gdpr_request") -> Dict:
        """
        Delete all data for a lead (GDPR right to erasure).
        
        Args:
            lead_id: Lead identifier
            reason: Reason for deletion
            
        Returns:
            Dictionary with deletion statistics
        """
        logger.info(
            f"Starting data deletion for lead {lead_id}",
            extra={"reason": reason}
        )
        
        stats = {
            "lead_deleted": False,
            "calls_deleted": 0,
            "conversations_deleted": 0,
            "consent_records_deleted": 0,
            "recordings_deleted": 0
        }
        
        try:
            # Delete recordings first
            calls = await self.call_repo.collection.find({"lead_id": lead_id}).to_list(None)
            for call in calls:
                if call.get("recording_url"):
                    try:
                        await self._delete_recording_file(call["recording_url"])
                        stats["recordings_deleted"] += 1
                    except Exception as e:
                        logger.error(f"Failed to delete recording: {e}")
            
            # Delete calls
            result = await self.call_repo.collection.delete_many({"lead_id": lead_id})
            stats["calls_deleted"] = result.deleted_count
            
            # Delete conversations
            result = await self.conversation_repo.collection.delete_many({"lead_id": lead_id})
            stats["conversations_deleted"] = result.deleted_count
            
            # Delete consent records
            result = await self.db["consent_records"].delete_many({"lead_id": lead_id})
            stats["consent_records_deleted"] = result.deleted_count
            
            # Delete lead (or anonymize)
            await self.lead_repo.delete_lead(lead_id)
            stats["lead_deleted"] = True
            
            # Log deletion
            await self.db["data_deletions"].insert_one({
                "lead_id": lead_id,
                "deleted_at": datetime.utcnow(),
                "reason": reason,
                "statistics": stats
            })
            
            logger.info(
                f"Data deletion complete for lead {lead_id}",
                extra=stats
            )
            
        except Exception as e:
            logger.error(f"Failed to delete lead data: {e}", exc_info=True)
            raise
        
        return stats
    
    async def anonymize_lead_data(self, lead_id: str) -> bool:
        """
        Anonymize lead data instead of deleting (alternative to deletion).
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            True if anonymized successfully
        """
        logger.info(f"Anonymizing data for lead {lead_id}")
        
        try:
            # Anonymize lead
            await self.lead_repo.update_lead(lead_id, {
                "name": "ANONYMIZED",
                "phone": "ANONYMIZED",
                "email": "ANONYMIZED",
                "anonymized": True,
                "anonymized_at": datetime.utcnow()
            })
            
            # Anonymize conversations (remove PII from turns)
            await self.conversation_repo.collection.update_many(
                {"lead_id": lead_id},
                {
                    "$set": {
                        "anonymized": True,
                        "anonymized_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Data anonymized for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to anonymize lead data: {e}", exc_info=True)
            return False
    
    async def get_retention_statistics(self) -> Dict:
        """
        Get statistics about data retention.
        
        Returns:
            Dictionary with retention statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Count recordings older than retention period
        old_recordings_count = await self.call_repo.collection.count_documents({
            "created_at": {"$lt": cutoff_date},
            "recording_url": {"$ne": None},
            "recording_deleted": {"$ne": True}
        })
        
        # Count total recordings
        total_recordings = await self.call_repo.collection.count_documents({
            "recording_url": {"$ne": None}
        })
        
        # Count deleted recordings
        deleted_recordings = await self.call_repo.collection.count_documents({
            "recording_deleted": True
        })
        
        # Count GDPR deletions
        gdpr_deletions = await self.db["data_deletions"].count_documents({
            "reason": {"$regex": "gdpr"}
        })
        
        return {
            "retention_days": self.retention_days,
            "old_recordings_pending_deletion": old_recordings_count,
            "total_recordings": total_recordings,
            "deleted_recordings": deleted_recordings,
            "gdpr_deletions": gdpr_deletions,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def schedule_retention_cleanup(self) -> Dict:
        """
        Run scheduled retention cleanup job.
        Should be called by a background scheduler (e.g., daily).
        
        Returns:
            Cleanup statistics
        """
        logger.info("Starting scheduled retention cleanup")
        
        # Delete old recordings
        deletion_stats = await self.delete_old_recordings(self.retention_days)
        
        # Get updated statistics
        retention_stats = await self.get_retention_statistics()
        
        return {
            "cleanup_date": datetime.utcnow().isoformat(),
            "deletion_stats": deletion_stats,
            "retention_stats": retention_stats
        }
