"""
Handoff Service for managing human expert handoff logic.

This module handles the detection of handoff triggers, call transfers,
callback scheduling, and CRM integration for expert handoffs.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.escalation_detector import EscalationDetector, EscalationReason
from app.services.conversation_context import ConversationContext
from app.services.nlu_engine import Intent
from app.repositories.lead_repository import LeadRepository
from app.repositories.call_repository import CallRepository
from app.repositories.callback_repository import CallbackRepository
from app.integrations.twilio_adapter import TwilioAdapter
from app.integrations.crm_adapter import CRMAdapter
from app.integrations.notification_adapter import NotificationAdapter
from app.models.callback import Callback

logger = logging.getLogger(__name__)


class HandoffStatus(str, Enum):
    """Status of handoff process."""
    PENDING = "pending"
    EXPERT_AVAILABLE = "expert_available"
    EXPERT_UNAVAILABLE = "expert_unavailable"
    TRANSFERRED = "transferred"
    CALLBACK_SCHEDULED = "callback_scheduled"
    FAILED = "failed"


class HandoffService:
    """
    Service for managing human expert handoff.
    
    Responsibilities:
    - Detect handoff triggers
    - Update lead and call status
    - Coordinate with call orchestrator for transfer
    - Schedule callbacks when experts unavailable
    """
    
    def __init__(
        self,
        lead_repository: LeadRepository,
        call_repository: CallRepository,
        callback_repository: Optional[CallbackRepository] = None,
        twilio_adapter: Optional[TwilioAdapter] = None,
        crm_adapter: Optional[CRMAdapter] = None,
        notification_adapter: Optional[NotificationAdapter] = None,
        escalation_detector: Optional[EscalationDetector] = None
    ):
        """
        Initialize handoff service.
        
        Args:
            lead_repository: Repository for lead operations
            call_repository: Repository for call operations
            callback_repository: Repository for callback operations
            twilio_adapter: Adapter for Twilio telephony operations
            crm_adapter: Adapter for CRM integration
            notification_adapter: Adapter for notifications (WhatsApp/SMS)
            escalation_detector: Detector for escalation conditions
        """
        self.lead_repo = lead_repository
        self.call_repo = call_repository
        self.callback_repo = callback_repository
        self.twilio_adapter = twilio_adapter
        self.crm_adapter = crm_adapter
        self.notification_adapter = notification_adapter
        self.escalation_detector = escalation_detector or EscalationDetector()
        
        logger.info("HandoffService initialized")
    
    async def check_handoff_trigger(
        self,
        context: ConversationContext,
        current_intent: Optional[Intent] = None,
        current_utterance: Optional[str] = None
    ) -> Tuple[bool, Optional[EscalationReason], Optional[str]]:
        """
        Check if handoff should be triggered.
        
        Args:
            context: Current conversation context
            current_intent: Most recent detected intent
            current_utterance: Most recent user utterance
        
        Returns:
            Tuple of (should_handoff, reason, explanation)
        """
        logger.info(f"Checking handoff trigger for call {context.call_id}")
        
        # Use escalation detector to check conditions
        should_escalate, reason, explanation = self.escalation_detector.should_escalate(
            context=context,
            current_intent=current_intent,
            current_utterance=current_utterance
        )
        
        if should_escalate:
            logger.info(
                f"Handoff triggered for call {context.call_id}. "
                f"Reason: {reason}, Explanation: {explanation}"
            )
            
            # Log escalation in context
            self.escalation_detector.log_escalation(context, reason, explanation)
        
        return should_escalate, reason, explanation
    
    async def initiate_handoff(
        self,
        call_id: str,
        lead_id: str,
        reason: EscalationReason,
        explanation: str,
        context: Optional[ConversationContext] = None
    ) -> Dict[str, Any]:
        """
        Initiate handoff process by updating lead and call status.
        
        Args:
            call_id: Call identifier
            lead_id: Lead identifier
            reason: Escalation reason
            explanation: Detailed explanation
            context: Optional conversation context
        
        Returns:
            Dictionary with handoff details
        """
        logger.info(f"Initiating handoff for lead {lead_id}, call {call_id}")
        
        try:
            # Update lead status to "handoff"
            lead = await self.lead_repo.update(
                lead_id=lead_id,
                updates={
                    "status": "handoff",
                    "metadata.handoff_reason": reason,
                    "metadata.handoff_explanation": explanation,
                    "metadata.handoff_initiated_at": datetime.utcnow().isoformat()
                }
            )
            
            if not lead:
                logger.error(f"Failed to update lead {lead_id} - lead not found")
                return {
                    "success": False,
                    "error": "Lead not found"
                }
            
            # Update call metadata
            call = await self.call_repo.update(
                call_id=call_id,
                updates={
                    "metadata.handoff_reason": reason,
                    "metadata.handoff_explanation": explanation,
                    "metadata.handoff_initiated_at": datetime.utcnow().isoformat()
                }
            )
            
            if not call:
                logger.warning(f"Call {call_id} not found, but lead updated")
            
            # Get escalation priority
            priority = self.escalation_detector.get_escalation_priority(reason)
            
            # Prepare handoff summary
            handoff_summary = self._prepare_handoff_summary(
                lead=lead,
                call=call,
                reason=reason,
                explanation=explanation,
                priority=priority,
                context=context
            )
            
            logger.info(f"Handoff initiated successfully for lead {lead_id}")
            
            return {
                "success": True,
                "handoff_status": HandoffStatus.PENDING,
                "lead_id": lead_id,
                "call_id": call_id,
                "reason": reason,
                "priority": priority,
                "summary": handoff_summary
            }
            
        except Exception as e:
            logger.error(f"Error initiating handoff: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_handoff_summary(
        self,
        lead: Any,
        call: Optional[Any],
        reason: EscalationReason,
        explanation: str,
        priority: str,
        context: Optional[ConversationContext] = None
    ) -> Dict[str, Any]:
        """
        Prepare summary for handoff to expert.
        
        Args:
            lead: Lead object
            call: Call object
            reason: Escalation reason
            explanation: Detailed explanation
            priority: Priority level
            context: Optional conversation context
        
        Returns:
            Dictionary with handoff summary
        """
        summary = {
            "lead_id": lead.lead_id,
            "name": lead.name,
            "phone": lead.phone,
            "language": lead.language,
            "handoff_reason": reason,
            "handoff_explanation": explanation,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Lead data
            "country": lead.country,
            "degree": lead.degree,
            "loan_amount": lead.loan_amount,
            "offer_letter": lead.offer_letter,
            "coapplicant_itr": lead.coapplicant_itr,
            "collateral": lead.collateral,
            "visa_timeline": lead.visa_timeline,
            "eligibility_category": lead.eligibility_category,
            "urgency": lead.urgency,
            
            # Call data
            "call_id": call.call_id if call else None,
            "call_duration": call.duration if call else None,
            "call_status": call.status if call else None,
        }
        
        # Add context data if available
        if context:
            summary.update({
                "sentiment_score": context.get_average_sentiment(),
                "negative_turn_count": context.negative_turn_count,
                "clarification_count": context.clarification_count,
                "conversation_state": context.current_state,
                "collected_data": context.collected_data
            })
        
        return summary
    
    def get_handoff_message(
        self,
        reason: EscalationReason,
        language: str
    ) -> str:
        """
        Get appropriate handoff message based on reason and language.
        
        Args:
            reason: Escalation reason
            language: Conversation language
        
        Returns:
            Handoff message string
        """
        return self.escalation_detector.get_escalation_message(reason, language)
    
    async def update_handoff_status(
        self,
        lead_id: str,
        call_id: str,
        status: HandoffStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update handoff status in lead and call records.
        
        Args:
            lead_id: Lead identifier
            call_id: Call identifier
            status: New handoff status
            details: Optional additional details
        
        Returns:
            True if update successful
        """
        try:
            updates = {
                "metadata.handoff_status": status,
                "metadata.handoff_updated_at": datetime.utcnow().isoformat()
            }
            
            if details:
                for key, value in details.items():
                    updates[f"metadata.handoff_{key}"] = value
            
            # Update lead
            await self.lead_repo.update(lead_id, updates)
            
            # Update call
            await self.call_repo.update(call_id, updates)
            
            logger.info(f"Updated handoff status to {status} for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating handoff status: {str(e)}")
            return False
    
    async def transfer_call_to_expert(
        self,
        call_id: str,
        lead_id: str,
        call_sid: str,
        handoff_summary: Dict[str, Any],
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Transfer active call to human expert.
        
        Args:
            call_id: Call identifier
            lead_id: Lead identifier
            call_sid: Twilio call SID
            handoff_summary: Summary of lead and handoff details
            language: Conversation language
        
        Returns:
            Dictionary with transfer result
        """
        logger.info(f"Attempting to transfer call {call_id} to expert")
        
        try:
            # Check expert availability via CRM
            expert = None
            if self.crm_adapter:
                expert = await self.crm_adapter.check_expert_availability(
                    language=language,
                    priority=handoff_summary.get("priority")
                )
            
            if not expert or not expert.get("available"):
                logger.info(f"No expert available for call {call_id}")
                return {
                    "success": False,
                    "status": HandoffStatus.EXPERT_UNAVAILABLE,
                    "message": "No expert currently available"
                }
            
            expert_phone = expert.get("phone")
            expert_id = expert.get("expert_id")
            
            if not expert_phone:
                logger.error("Expert phone number not provided")
                return {
                    "success": False,
                    "status": HandoffStatus.FAILED,
                    "message": "Expert contact information unavailable"
                }
            
            # Send lead summary to CRM before transfer
            if self.crm_adapter:
                await self.crm_adapter.notify_expert(
                    lead_id=lead_id,
                    expert_id=expert_id,
                    handoff_summary=handoff_summary
                )
            
            # Generate transfer message
            transfer_messages = {
                "hinglish": "Main aapko abhi expert se connect kar rahi hoon. Kripya line par rahein.",
                "english": "I'm connecting you with an expert now. Please stay on the line.",
                "telugu": "Nenu mimmalini expert tho connect chestunnanu. Dayachesi line lo undandi."
            }
            transfer_message = transfer_messages.get(language, transfer_messages["english"])
            
            # Transfer call via Twilio
            if not self.twilio_adapter:
                logger.error("Twilio adapter not configured")
                return {
                    "success": False,
                    "status": HandoffStatus.FAILED,
                    "message": "Telephony service not configured"
                }
            
            transfer_success = await self.twilio_adapter.transfer_call(
                call_sid=call_sid,
                to_number=expert_phone,
                transfer_message=transfer_message
            )
            
            if not transfer_success:
                logger.error(f"Failed to transfer call {call_id}")
                return {
                    "success": False,
                    "status": HandoffStatus.FAILED,
                    "message": "Call transfer failed"
                }
            
            # Update call status to "transferred"
            await self.call_repo.update(
                call_id=call_id,
                updates={
                    "status": "transferred",
                    "metadata.transferred_to_expert": expert_id,
                    "metadata.transferred_at": datetime.utcnow().isoformat()
                }
            )
            
            # Update handoff status
            await self.update_handoff_status(
                lead_id=lead_id,
                call_id=call_id,
                status=HandoffStatus.TRANSFERRED,
                details={
                    "expert_id": expert_id,
                    "expert_phone": expert_phone,
                    "transferred_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Call {call_id} transferred successfully to expert {expert_id}")
            
            return {
                "success": True,
                "status": HandoffStatus.TRANSFERRED,
                "expert_id": expert_id,
                "message": "Call transferred successfully"
            }
            
        except Exception as e:
            logger.error(f"Error transferring call: {str(e)}")
            return {
                "success": False,
                "status": HandoffStatus.FAILED,
                "error": str(e)
            }
    
    async def schedule_callback(
        self,
        call_id: str,
        lead_id: str,
        phone: str,
        language: str,
        preferred_time: Optional[datetime] = None,
        reason: str = "expert_unavailable"
    ) -> Dict[str, Any]:
        """
        Schedule callback when expert is unavailable.
        
        Args:
            call_id: Call identifier
            lead_id: Lead identifier
            phone: Phone number for callback
            language: Conversation language
            preferred_time: User's preferred callback time
            reason: Reason for callback
        
        Returns:
            Dictionary with callback details
        """
        logger.info(f"Scheduling callback for lead {lead_id}")
        
        try:
            if not self.callback_repo:
                logger.error("Callback repository not configured")
                return {
                    "success": False,
                    "error": "Callback service not available"
                }
            
            # If no preferred time, schedule for 1 hour from now
            if not preferred_time:
                preferred_time = datetime.utcnow() + timedelta(hours=1)
            
            scheduled_time = preferred_time
            
            # Create callback record
            callback = Callback(
                lead_id=lead_id,
                call_id=call_id,
                phone=phone,
                language=language,
                preferred_time=preferred_time,
                scheduled_time=scheduled_time,
                status="scheduled",
                reason=reason,
                notes=f"Callback scheduled due to {reason}"
            )
            
            callback = await self.callback_repo.create(callback)
            
            # Update lead status
            await self.lead_repo.update(
                lead_id=lead_id,
                updates={
                    "status": "callback",
                    "metadata.callback_id": callback.callback_id,
                    "metadata.callback_scheduled_at": scheduled_time.isoformat()
                }
            )
            
            # Update call metadata
            await self.call_repo.update(
                call_id=call_id,
                updates={
                    "metadata.callback_id": callback.callback_id,
                    "metadata.callback_scheduled": True
                }
            )
            
            # Update handoff status
            await self.update_handoff_status(
                lead_id=lead_id,
                call_id=call_id,
                status=HandoffStatus.CALLBACK_SCHEDULED,
                details={
                    "callback_id": callback.callback_id,
                    "scheduled_time": scheduled_time.isoformat()
                }
            )
            
            # Send confirmation via WhatsApp/SMS
            if self.notification_adapter:
                lead = await self.lead_repo.get_by_id(lead_id)
                callback_time_str = scheduled_time.strftime("%B %d, %Y at %I:%M %p")
                
                await self.notification_adapter.send_callback_confirmation(
                    phone=phone,
                    language=language,
                    callback_time=callback_time_str,
                    lead_name=lead.name if lead else None
                )
            
            logger.info(f"Callback scheduled successfully: {callback.callback_id}")
            
            return {
                "success": True,
                "callback_id": callback.callback_id,
                "scheduled_time": scheduled_time.isoformat(),
                "message": "Callback scheduled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error scheduling callback: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def offer_callback(
        self,
        language: str
    ) -> str:
        """
        Get callback offer message in appropriate language.
        
        Args:
            language: Conversation language
        
        Returns:
            Callback offer message
        """
        messages = {
            "hinglish": "Abhi koi expert available nahi hai. Kya aap chahenge ki hum aapko baad mein call karein? Aap apna preferred time bata sakte hain.",
            "english": "No expert is currently available. Would you like us to call you back? You can tell me your preferred time.",
            "telugu": "Ippudu expert available ledu. Memu meeku taruvata call cheyyamani korukuntunnara? Meeru mee preferred time cheppandi."
        }
        
        return messages.get(language, messages["english"])
    
    def parse_callback_time(
        self,
        time_utterance: str,
        language: str
    ) -> Optional[datetime]:
        """
        Parse user's preferred callback time from utterance.
        
        Args:
            time_utterance: User's time preference
            language: Conversation language
        
        Returns:
            Parsed datetime or None
        """
        # Simple parsing - in production, use more sophisticated NLP
        time_utterance_lower = time_utterance.lower()
        
        now = datetime.utcnow()
        
        # Check for relative times
        if any(word in time_utterance_lower for word in ["hour", "ghante", "ganta"]):
            # Extract number of hours
            try:
                hours = 1
                for word in time_utterance_lower.split():
                    if word.isdigit():
                        hours = int(word)
                        break
                return now + timedelta(hours=hours)
            except:
                pass
        
        if any(word in time_utterance_lower for word in ["tomorrow", "kal", "repu"]):
            return now + timedelta(days=1)
        
        if any(word in time_utterance_lower for word in ["evening", "shaam", "sayantram"]):
            # Schedule for 6 PM today or tomorrow
            target = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target
        
        if any(word in time_utterance_lower for word in ["morning", "subah", "udayam"]):
            # Schedule for 10 AM tomorrow
            target = now.replace(hour=10, minute=0, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target
        
        # Default: 1 hour from now
        return now + timedelta(hours=1)
