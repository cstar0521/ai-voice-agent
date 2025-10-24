"""
Call Orchestrator for managing call lifecycle and coordinating components.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from app.models.call import Call
from app.models.lead import Lead
from app.repositories.call_repository import CallRepository
from app.repositories.lead_repository import LeadRepository
from app.integrations.twilio_adapter import TwilioAdapter
from app.services.conversation_state_machine import ConversationState
from app.services.conversation_context import ConversationContextManager


class CallState(str, Enum):
    """Call lifecycle states."""
    INITIATED = "initiated"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    ENDING = "ending"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    NETWORK_ERROR = "network_error"


class CallEvent(str, Enum):
    """Call events that trigger state transitions."""
    CALL_INITIATED = "call_initiated"
    CALL_RINGING = "call_ringing"
    CALL_ANSWERED = "call_answered"
    SPEECH_DETECTED = "speech_detected"
    SILENCE_TIMEOUT = "silence_timeout"
    USER_HANGUP = "user_hangup"
    AGENT_HANGUP = "agent_hangup"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"
    NETWORK_ERROR = "network_error"


class CallOrchestrator:
    """
    Orchestrates call lifecycle and coordinates between telephony, conversation, and data layers.
    
    Manages call state transitions, event processing, and integration with various services.
    """
    
    # Valid state transitions for call lifecycle
    VALID_TRANSITIONS: Dict[CallState, set] = {
        CallState.INITIATED: {CallState.DIALING, CallState.FAILED},
        CallState.DIALING: {CallState.RINGING, CallState.NO_ANSWER, CallState.BUSY, CallState.FAILED},
        CallState.RINGING: {CallState.CONNECTED, CallState.NO_ANSWER, CallState.FAILED},
        CallState.CONNECTED: {CallState.IN_PROGRESS, CallState.ENDING, CallState.FAILED},
        CallState.IN_PROGRESS: {CallState.ENDING, CallState.FAILED, CallState.NETWORK_ERROR},
        CallState.ENDING: {CallState.COMPLETED, CallState.FAILED},
        CallState.COMPLETED: set(),
        CallState.FAILED: set(),
        CallState.NO_ANSWER: set(),
        CallState.BUSY: set(),
        CallState.NETWORK_ERROR: set()
    }
    
    # Maximum retry attempts for failed calls
    MAX_RETRY_ATTEMPTS = 3
    
    # Retry intervals in hours
    RETRY_INTERVALS = [1, 6, 24]  # 1 hour, 6 hours, 24 hours
    
    def __init__(
        self,
        call_repository: CallRepository,
        lead_repository: LeadRepository,
        twilio_adapter: TwilioAdapter,
        context_manager: ConversationContextManager
    ):
        """
        Initialize call orchestrator with required dependencies.
        
        Args:
            call_repository: Repository for call data
            lead_repository: Repository for lead data
            twilio_adapter: Adapter for Twilio telephony
            context_manager: Manager for conversation contexts
        """
        self.call_repo = call_repository
        self.lead_repo = lead_repository
        self.twilio = twilio_adapter
        self.context_manager = context_manager
        
        # Track active calls
        self.active_calls: Dict[str, CallState] = {}
    
    async def initiate_outbound_call(
        self,
        phone_number: str,
        lead_data: Optional[Dict[str, Any]] = None,
        preferred_language: str = "hinglish"
    ) -> str:
        """
        Initiate an outbound call to a lead.
        
        Args:
            phone_number: Phone number to call
            lead_data: Optional lead data (creates new lead if not exists)
            preferred_language: Preferred language for conversation
        
        Returns:
            Call ID
        """
        # Create or get lead
        lead = await self.lead_repo.get_by_phone(phone_number)
        if not lead:
            lead = Lead(
                phone=phone_number,
                language=preferred_language,
                status="new",
                **(lead_data or {})
            )
            lead = await self.lead_repo.create(lead)
        
        # Create call record
        call = Call(
            lead_id=lead.lead_id,
            direction="outbound",
            status="initiated"
        )
        call = await self.call_repo.create(call)
        
        # Track call state
        self.active_calls[call.call_id] = CallState.INITIATED
        
        # Initiate call via Twilio
        try:
            call_sid = await self.twilio.make_call(
                to_number=phone_number,
                callback_url=f"/api/v1/calls/{call.call_id}/webhook"
            )
            
            # Update call with Twilio SID
            await self.call_repo.update(call.call_id, {
                "call_sid": call_sid,
                "status": "dialing",
                "start_time": datetime.utcnow()
            })
            
            # Transition to dialing state
            await self.transition_state(call.call_id, CallState.DIALING)
            
        except Exception as e:
            # Handle call initiation failure
            await self.handle_call_failure(call.call_id, str(e))
            raise
        
        return call.call_id
    
    async def handle_inbound_call(
        self,
        call_sid: str,
        from_number: str
    ) -> str:
        """
        Handle an incoming call.
        
        Args:
            call_sid: Twilio call SID
            from_number: Caller's phone number
        
        Returns:
            Call ID
        """
        # Create or get lead
        lead = await self.lead_repo.get_by_phone(from_number)
        if not lead:
            lead = Lead(
                phone=from_number,
                status="new"
            )
            lead = await self.lead_repo.create(lead)
        
        # Create call record
        call = Call(
            lead_id=lead.lead_id,
            call_sid=call_sid,
            direction="inbound",
            status="connected",
            start_time=datetime.utcnow()
        )
        call = await self.call_repo.create(call)
        
        # Track call state
        self.active_calls[call.call_id] = CallState.CONNECTED
        
        # Create conversation context (skip greeting for inbound)
        context = self.context_manager.create_context(
            call_id=call.call_id,
            lead_id=lead.lead_id,
            language=lead.language or "hinglish",
            initial_state=ConversationState.QUALIFICATION_START
        )
        
        return call.call_id
    
    async def process_call_event(
        self,
        call_id: str,
        event: CallEvent,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Process a call event and trigger appropriate actions.
        
        Args:
            call_id: Call identifier
            event: Event type
            event_data: Optional event data
        """
        current_state = self.active_calls.get(call_id)
        if not current_state:
            raise ValueError(f"Call {call_id} not found in active calls")
        
        # Handle different event types
        if event == CallEvent.CALL_RINGING:
            await self.transition_state(call_id, CallState.RINGING)
        
        elif event == CallEvent.CALL_ANSWERED:
            await self.transition_state(call_id, CallState.CONNECTED)
            await self._start_conversation(call_id)
        
        elif event == CallEvent.SPEECH_DETECTED:
            if current_state == CallState.CONNECTED:
                await self.transition_state(call_id, CallState.IN_PROGRESS)
        
        elif event == CallEvent.SILENCE_TIMEOUT:
            await self._handle_silence_timeout(call_id)
        
        elif event == CallEvent.USER_HANGUP:
            await self._handle_user_hangup(call_id)
        
        elif event == CallEvent.AGENT_HANGUP:
            await self.end_call(call_id, "agent_ended")
        
        elif event == CallEvent.CALL_COMPLETED:
            await self.transition_state(call_id, CallState.COMPLETED)
            await self._finalize_call(call_id)
        
        elif event == CallEvent.CALL_FAILED:
            error_reason = event_data.get("reason") if event_data else "unknown"
            await self.handle_call_failure(call_id, error_reason)
        
        elif event == CallEvent.NETWORK_ERROR:
            await self.transition_state(call_id, CallState.NETWORK_ERROR)
            await self._handle_network_error(call_id)
    
    async def transition_state(
        self,
        call_id: str,
        new_state: CallState
    ) -> None:
        """
        Transition call to a new state with validation.
        
        Args:
            call_id: Call identifier
            new_state: Target state
        
        Raises:
            ValueError: If transition is invalid
        """
        current_state = self.active_calls.get(call_id)
        if not current_state:
            raise ValueError(f"Call {call_id} not found")
        
        # Validate transition
        valid_targets = self.VALID_TRANSITIONS.get(current_state, set())
        if new_state not in valid_targets:
            raise ValueError(
                f"Invalid transition from {current_state} to {new_state}"
            )
        
        # Update state
        self.active_calls[call_id] = new_state
        
        # Update database
        await self.call_repo.update(call_id, {"status": new_state.value})
    
    async def end_call(
        self,
        call_id: str,
        reason: str = "normal"
    ) -> None:
        """
        End a call gracefully.
        
        Args:
            call_id: Call identifier
            reason: Reason for ending call
        """
        # Transition to ending state
        current_state = self.active_calls.get(call_id)
        if current_state and current_state not in [
            CallState.COMPLETED,
            CallState.FAILED,
            CallState.NO_ANSWER
        ]:
            await self.transition_state(call_id, CallState.ENDING)
        
        # Get call record
        call = await self.call_repo.get_by_id(call_id)
        if not call:
            return
        
        # Hangup via Twilio if call is active
        if call.call_sid:
            try:
                await self.twilio.hangup_call(call.call_sid)
            except Exception:
                pass  # Ignore hangup errors
        
        # Update call record
        end_time = datetime.utcnow()
        duration = None
        if call.start_time:
            duration = int((end_time - call.start_time).total_seconds())
        
        await self.call_repo.update(call_id, {
            "status": "completed",
            "end_time": end_time,
            "duration": duration
        })
        
        # Transition to completed
        await self.transition_state(call_id, CallState.COMPLETED)
        
        # Finalize call
        await self._finalize_call(call_id)
    
    async def handle_call_failure(
        self,
        call_id: str,
        error_reason: str
    ) -> None:
        """
        Handle call failure and determine if retry is needed.
        
        Args:
            call_id: Call identifier
            error_reason: Reason for failure
        """
        # Update call state
        if call_id in self.active_calls:
            self.active_calls[call_id] = CallState.FAILED
        
        # Get call record
        call = await self.call_repo.get_by_id(call_id)
        if not call:
            return
        
        # Update call record
        await self.call_repo.update(call_id, {
            "status": "failed",
            "error_reason": error_reason,
            "end_time": datetime.utcnow()
        })
        
        # Check if retry is eligible
        if await self.is_retry_eligible(call_id):
            await self.schedule_retry(call_id)
        else:
            # Mark lead as unreachable
            await self.lead_repo.update_status(call.lead_id, "unreachable")
        
        # Clean up
        await self._finalize_call(call_id)
    
    async def is_retry_eligible(self, call_id: str) -> bool:
        """
        Check if call is eligible for retry.
        
        Args:
            call_id: Call identifier
        
        Returns:
            True if eligible for retry, False otherwise
        """
        call = await self.call_repo.get_by_id(call_id)
        if not call:
            return False
        
        return call.retry_count < self.MAX_RETRY_ATTEMPTS
    
    async def schedule_retry(self, call_id: str) -> None:
        """
        Schedule a retry for a failed call.
        
        Args:
            call_id: Call identifier
        """
        call = await self.call_repo.get_by_id(call_id)
        if not call:
            return
        
        # Get retry interval based on attempt number
        retry_interval_hours = self.RETRY_INTERVALS[
            min(call.retry_count, len(self.RETRY_INTERVALS) - 1)
        ]
        
        # In a production system, this would schedule a background job
        # For now, we just update the retry count
        await self.call_repo.update(call_id, {
            "retry_count": call.retry_count + 1
        })
    
    async def _start_conversation(self, call_id: str) -> None:
        """Start conversation flow for connected call."""
        call = await self.call_repo.get_by_id(call_id)
        if not call:
            return
        
        # Get or create conversation context
        context = self.context_manager.get_context(call_id)
        if not context:
            lead = await self.lead_repo.get_by_id(call.lead_id)
            context = self.context_manager.create_context(
                call_id=call_id,
                lead_id=call.lead_id,
                language=lead.language if lead else "hinglish",
                initial_state=ConversationState.GREETING
            )
    
    async def _handle_silence_timeout(self, call_id: str) -> None:
        """Handle silence timeout during call."""
        # This would trigger a silence prompt in the conversation manager
        pass
    
    async def _handle_user_hangup(self, call_id: str) -> None:
        """Handle user hanging up the call."""
        await self.end_call(call_id, "user_hangup")
    
    async def _handle_network_error(self, call_id: str) -> None:
        """Handle network error during call."""
        await self.handle_call_failure(call_id, "network_error")
    
    async def _finalize_call(self, call_id: str) -> None:
        """Finalize call and clean up resources."""
        # Remove from active calls
        if call_id in self.active_calls:
            del self.active_calls[call_id]
        
        # Clean up conversation context
        self.context_manager.delete_context(call_id)
    
    def get_call_state(self, call_id: str) -> Optional[CallState]:
        """
        Get current state of a call.
        
        Args:
            call_id: Call identifier
        
        Returns:
            Current call state or None if not found
        """
        return self.active_calls.get(call_id)
    
    def get_active_calls(self) -> Dict[str, CallState]:
        """
        Get all active calls.
        
        Returns:
            Dictionary of call_id to CallState
        """
        return self.active_calls.copy()
