"""
Unit tests for Call Orchestrator.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.call_orchestrator import (
    CallOrchestrator,
    CallState,
    CallEvent
)
from app.models.call import Call
from app.models.lead import Lead


class TestCallOrchestrator:
    """Test suite for call orchestrator."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        call_repo = AsyncMock()
        lead_repo = AsyncMock()
        return call_repo, lead_repo
    
    @pytest.fixture
    def mock_twilio(self):
        """Create mock Twilio adapter."""
        twilio = AsyncMock()
        twilio.make_call = AsyncMock(return_value="CA123456")
        twilio.hangup_call = AsyncMock()
        return twilio
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create mock conversation context manager."""
        manager = Mock()
        manager.create_context = Mock()
        manager.get_context = Mock(return_value=None)
        manager.delete_context = Mock()
        return manager
    
    @pytest.fixture
    def orchestrator(self, mock_repositories, mock_twilio, mock_context_manager):
        """Create call orchestrator instance."""
        call_repo, lead_repo = mock_repositories
        return CallOrchestrator(
            call_repository=call_repo,
            lead_repository=lead_repo,
            twilio_adapter=mock_twilio,
            context_manager=mock_context_manager
        )
    
    # Test Call Lifecycle Management
    
    @pytest.mark.asyncio
    async def test_initiate_outbound_call_new_lead(self, orchestrator, mock_repositories):
        """Test initiating outbound call with new lead."""
        call_repo, lead_repo = mock_repositories
        
        # Mock lead not found, then created
        lead_repo.get_by_phone = AsyncMock(return_value=None)
        lead_repo.create = AsyncMock(return_value=Lead(
            lead_id="lead_123",
            phone="+919876543210",
            language="hinglish"
        ))
        
        # Mock call creation
        call_repo.create = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound",
            status="initiated"
        ))
        call_repo.update = AsyncMock()
        
        # Initiate call
        call_id = await orchestrator.initiate_outbound_call("+919876543210")
        
        assert call_id == "call_123"
        assert orchestrator.get_call_state(call_id) == CallState.DIALING
        lead_repo.create.assert_called_once()
        call_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initiate_outbound_call_existing_lead(self, orchestrator, mock_repositories):
        """Test initiating outbound call with existing lead."""
        call_repo, lead_repo = mock_repositories
        
        # Mock existing lead
        lead_repo.get_by_phone = AsyncMock(return_value=Lead(
            lead_id="lead_123",
            phone="+919876543210",
            language="english"
        ))
        
        # Mock call creation
        call_repo.create = AsyncMock(return_value=Call(
            call_id="call_456",
            lead_id="lead_123",
            direction="outbound",
            status="initiated"
        ))
        call_repo.update = AsyncMock()
        
        # Initiate call
        call_id = await orchestrator.initiate_outbound_call("+919876543210")
        
        assert call_id == "call_456"
        lead_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_inbound_call(self, orchestrator, mock_repositories):
        """Test handling inbound call."""
        call_repo, lead_repo = mock_repositories
        
        # Mock lead creation
        lead_repo.get_by_phone = AsyncMock(return_value=None)
        lead_repo.create = AsyncMock(return_value=Lead(
            lead_id="lead_789",
            phone="+919876543210"
        ))
        
        # Mock call creation
        call_repo.create = AsyncMock(return_value=Call(
            call_id="call_789",
            lead_id="lead_789",
            direction="inbound",
            status="connected"
        ))
        
        # Handle inbound call
        call_id = await orchestrator.handle_inbound_call("CA123456", "+919876543210")
        
        assert call_id == "call_789"
        assert orchestrator.get_call_state(call_id) == CallState.CONNECTED
    
    # Test State Transitions
    
    @pytest.mark.asyncio
    async def test_valid_state_transition(self, orchestrator, mock_repositories):
        """Test valid state transition."""
        call_repo, _ = mock_repositories
        call_repo.update = AsyncMock()
        
        # Set up initial state
        orchestrator.active_calls["call_123"] = CallState.INITIATED
        
        # Transition to dialing
        await orchestrator.transition_state("call_123", CallState.DIALING)
        
        assert orchestrator.get_call_state("call_123") == CallState.DIALING
        call_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_state_transition(self, orchestrator):
        """Test invalid state transition raises error."""
        orchestrator.active_calls["call_123"] = CallState.INITIATED
        
        with pytest.raises(ValueError, match="Invalid transition"):
            await orchestrator.transition_state("call_123", CallState.COMPLETED)
    
    # Test Call Event Processing
    
    @pytest.mark.asyncio
    async def test_process_call_answered_event(self, orchestrator, mock_repositories):
        """Test processing call answered event."""
        call_repo, lead_repo = mock_repositories
        call_repo.update = AsyncMock()
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound"
        ))
        lead_repo.get_by_id = AsyncMock(return_value=Lead(
            lead_id="lead_123",
            phone="+919876543210",
            language="hinglish"
        ))
        
        # Set up call in ringing state
        orchestrator.active_calls["call_123"] = CallState.RINGING
        
        # Process answered event
        await orchestrator.process_call_event("call_123", CallEvent.CALL_ANSWERED)
        
        assert orchestrator.get_call_state("call_123") == CallState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_process_speech_detected_event(self, orchestrator, mock_repositories):
        """Test processing speech detected event."""
        call_repo, _ = mock_repositories
        call_repo.update = AsyncMock()
        
        # Set up call in connected state
        orchestrator.active_calls["call_123"] = CallState.CONNECTED
        
        # Process speech detected event
        await orchestrator.process_call_event("call_123", CallEvent.SPEECH_DETECTED)
        
        assert orchestrator.get_call_state("call_123") == CallState.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_process_user_hangup_event(self, orchestrator, mock_repositories, mock_twilio):
        """Test processing user hangup event."""
        call_repo, _ = mock_repositories
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            call_sid="CA123456",
            direction="outbound",
            start_time=datetime.utcnow()
        ))
        call_repo.update = AsyncMock()
        
        # Set up call in progress
        orchestrator.active_calls["call_123"] = CallState.IN_PROGRESS
        
        # Process user hangup
        await orchestrator.process_call_event("call_123", CallEvent.USER_HANGUP)
        
        # Should transition through ending to completed
        assert "call_123" not in orchestrator.active_calls
    
    # Test Call Ending
    
    @pytest.mark.asyncio
    async def test_end_call(self, orchestrator, mock_repositories, mock_twilio):
        """Test ending a call."""
        call_repo, _ = mock_repositories
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            call_sid="CA123456",
            direction="outbound",
            start_time=datetime.utcnow()
        ))
        call_repo.update = AsyncMock()
        
        # Set up active call
        orchestrator.active_calls["call_123"] = CallState.IN_PROGRESS
        
        # End call
        await orchestrator.end_call("call_123")
        
        # Verify Twilio hangup was called
        mock_twilio.hangup_call.assert_called_once_with("CA123456")
        
        # Verify call was removed from active calls
        assert "call_123" not in orchestrator.active_calls
    
    # Test Call Failure and Retry
    
    @pytest.mark.asyncio
    async def test_handle_call_failure_with_retry(self, orchestrator, mock_repositories):
        """Test handling call failure with retry eligibility."""
        call_repo, lead_repo = mock_repositories
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound",
            retry_count=0
        ))
        call_repo.update = AsyncMock()
        
        orchestrator.active_calls["call_123"] = CallState.DIALING
        
        # Handle failure
        await orchestrator.handle_call_failure("call_123", "no_answer")
        
        # Verify retry was scheduled
        assert call_repo.update.call_count >= 2  # Status update + retry count update
    
    @pytest.mark.asyncio
    async def test_handle_call_failure_max_retries(self, orchestrator, mock_repositories):
        """Test handling call failure after max retries."""
        call_repo, lead_repo = mock_repositories
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound",
            retry_count=3
        ))
        call_repo.update = AsyncMock()
        lead_repo.update_status = AsyncMock()
        
        orchestrator.active_calls["call_123"] = CallState.DIALING
        
        # Handle failure
        await orchestrator.handle_call_failure("call_123", "no_answer")
        
        # Verify lead marked as unreachable
        lead_repo.update_status.assert_called_once_with("lead_123", "unreachable")
    
    @pytest.mark.asyncio
    async def test_is_retry_eligible(self, orchestrator, mock_repositories):
        """Test retry eligibility check."""
        call_repo, _ = mock_repositories
        
        # Test eligible (retry_count < 3)
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound",
            retry_count=1
        ))
        
        eligible = await orchestrator.is_retry_eligible("call_123")
        assert eligible is True
        
        # Test not eligible (retry_count >= 3)
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_456",
            lead_id="lead_456",
            direction="outbound",
            retry_count=3
        ))
        
        eligible = await orchestrator.is_retry_eligible("call_456")
        assert eligible is False
    
    @pytest.mark.asyncio
    async def test_schedule_retry(self, orchestrator, mock_repositories):
        """Test scheduling a retry."""
        call_repo, _ = mock_repositories
        call_repo.get_by_id = AsyncMock(return_value=Call(
            call_id="call_123",
            lead_id="lead_123",
            direction="outbound",
            retry_count=1
        ))
        call_repo.update = AsyncMock()
        
        # Schedule retry
        await orchestrator.schedule_retry("call_123")
        
        # Verify retry count was incremented
        call_repo.update.assert_called_once()
        update_call = call_repo.update.call_args[0]
        assert update_call[1]["retry_count"] == 2
    
    # Test Active Call Management
    
    def test_get_call_state(self, orchestrator):
        """Test getting call state."""
        orchestrator.active_calls["call_123"] = CallState.IN_PROGRESS
        
        state = orchestrator.get_call_state("call_123")
        assert state == CallState.IN_PROGRESS
        
        state = orchestrator.get_call_state("call_999")
        assert state is None
    
    def test_get_active_calls(self, orchestrator):
        """Test getting all active calls."""
        orchestrator.active_calls["call_123"] = CallState.IN_PROGRESS
        orchestrator.active_calls["call_456"] = CallState.CONNECTED
        
        active = orchestrator.get_active_calls()
        assert len(active) == 2
        assert active["call_123"] == CallState.IN_PROGRESS
        assert active["call_456"] == CallState.CONNECTED
