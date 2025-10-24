"""
Consent management service for call recording compliance.
Handles consent requests, storage, and recording control.
"""

import logging
from datetime import datetime
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.logging_config import get_logger
from app.repositories.call_repository import CallRepository

logger = get_logger('business')


class ConsentService:
    """Service for managing call recording consent."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.call_repo = CallRepository(db)
        self.consent_collection = db["consent_records"]
    
    async def request_consent(
        self,
        call_id: str,
        lead_id: str,
        language: str = "english"
    ) -> str:
        """
        Generate consent request prompt for the specified language.
        
        Args:
            call_id: Call identifier
            lead_id: Lead identifier
            language: Language for consent prompt
            
        Returns:
            Consent request text
        """
        consent_prompts = {
            "hinglish": "Is call ko recording ke liye aapki permission chahiye. Kya aap allow karte hain?",
            "english": "I need your permission to record this call. Do you consent to recording?",
            "telugu": "Ee call ni record cheyadaniki mee permission kavali. Meeru allow chestara?"
        }
        
        prompt = consent_prompts.get(language, consent_prompts["english"])
        
        logger.info(
            f"Requesting consent for call",
            extra={
                "call_id": call_id,
                "lead_id": lead_id,
                "language": language
            }
        )
        
        return prompt
    
    async def record_consent(
        self,
        call_id: str,
        lead_id: str,
        consent_given: bool,
        consent_text: Optional[str] = None,
        audio_url: Optional[str] = None
    ) -> Dict:
        """
        Record consent decision in database.
        
        Args:
            call_id: Call identifier
            lead_id: Lead identifier
            consent_given: Whether consent was given
            consent_text: Transcript of consent response
            audio_url: URL to consent audio recording
            
        Returns:
            Consent record
        """
        consent_record = {
            "call_id": call_id,
            "lead_id": lead_id,
            "consent_given": consent_given,
            "consent_text": consent_text,
            "audio_url": audio_url,
            "timestamp": datetime.utcnow(),
            "ip_address": None,  # Can be added if available
            "user_agent": None   # Can be added if available
        }
        
        # Store consent record
        await self.consent_collection.insert_one(consent_record)
        
        # Update call record
        await self.call_repo.update_call(call_id, {
            "consent_given": consent_given,
            "consent_timestamp": datetime.utcnow()
        })
        
        logger.info(
            f"Consent recorded",
            extra={
                "call_id": call_id,
                "lead_id": lead_id,
                "consent_given": consent_given
            }
        )
        
        return consent_record
    
    async def get_consent_status(self, call_id: str) -> Optional[bool]:
        """
        Get consent status for a call.
        
        Args:
            call_id: Call identifier
            
        Returns:
            True if consent given, False if declined, None if not recorded
        """
        call = await self.call_repo.get_call(call_id)
        if call:
            return call.consent_given
        return None
    
    async def enable_recording(self, call_id: str) -> bool:
        """
        Enable recording for a call (after consent is given).
        
        Args:
            call_id: Call identifier
            
        Returns:
            True if recording enabled successfully
        """
        try:
            # Update call record to enable recording
            await self.call_repo.update_call(call_id, {
                "recording_enabled": True,
                "recording_started_at": datetime.utcnow()
            })
            
            logger.info(f"Recording enabled for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable recording: {e}", exc_info=True)
            return False
    
    async def disable_recording(self, call_id: str, reason: str = "consent_declined") -> bool:
        """
        Disable recording for a call (if consent is declined).
        
        Args:
            call_id: Call identifier
            reason: Reason for disabling recording
            
        Returns:
            True if recording disabled successfully
        """
        try:
            # Update call record to disable recording
            await self.call_repo.update_call(call_id, {
                "recording_enabled": False,
                "recording_disabled_reason": reason,
                "recording_disabled_at": datetime.utcnow()
            })
            
            logger.info(
                f"Recording disabled for call",
                extra={
                    "call_id": call_id,
                    "reason": reason
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable recording: {e}", exc_info=True)
            return False
    
    async def get_consent_history(self, lead_id: str) -> list:
        """
        Get consent history for a lead across all calls.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            List of consent records
        """
        cursor = self.consent_collection.find({"lead_id": lead_id}).sort("timestamp", -1)
        
        records = []
        async for record in cursor:
            record.pop("_id", None)
            records.append(record)
        
        return records
    
    async def revoke_consent(self, lead_id: str, call_id: Optional[str] = None) -> bool:
        """
        Revoke consent for a lead (GDPR right to withdraw consent).
        
        Args:
            lead_id: Lead identifier
            call_id: Optional specific call ID, or all calls if None
            
        Returns:
            True if consent revoked successfully
        """
        try:
            # Create revocation record
            revocation_record = {
                "lead_id": lead_id,
                "call_id": call_id,
                "revoked_at": datetime.utcnow(),
                "revocation_type": "specific" if call_id else "all"
            }
            
            await self.consent_collection.insert_one(revocation_record)
            
            # Update call records
            if call_id:
                await self.call_repo.update_call(call_id, {
                    "consent_revoked": True,
                    "consent_revoked_at": datetime.utcnow()
                })
            else:
                # Revoke for all calls
                await self.call_repo.collection.update_many(
                    {"lead_id": lead_id},
                    {
                        "$set": {
                            "consent_revoked": True,
                            "consent_revoked_at": datetime.utcnow()
                        }
                    }
                )
            
            logger.info(
                f"Consent revoked",
                extra={
                    "lead_id": lead_id,
                    "call_id": call_id,
                    "type": "specific" if call_id else "all"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke consent: {e}", exc_info=True)
            return False
    
    async def check_consent_required(self, lead_id: str) -> bool:
        """
        Check if consent needs to be requested for a lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            True if consent is required, False if already given
        """
        # Check if lead has any active consent
        recent_consent = await self.consent_collection.find_one({
            "lead_id": lead_id,
            "consent_given": True,
            "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
        })
        
        # Consent is required if no recent consent found
        return recent_consent is None
    
    async def get_consent_statistics(self) -> Dict:
        """
        Get consent statistics for reporting.
        
        Returns:
            Dictionary with consent statistics
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$consent_given",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.consent_collection.aggregate(pipeline).to_list(None)
        
        stats = {
            "total_requests": 0,
            "consents_given": 0,
            "consents_declined": 0,
            "consent_rate": 0.0
        }
        
        for result in results:
            count = result["count"]
            stats["total_requests"] += count
            
            if result["_id"] is True:
                stats["consents_given"] = count
            elif result["_id"] is False:
                stats["consents_declined"] = count
        
        if stats["total_requests"] > 0:
            stats["consent_rate"] = stats["consents_given"] / stats["total_requests"]
        
        return stats
