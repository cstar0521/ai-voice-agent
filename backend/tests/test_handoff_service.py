"""
Integration tests for handoff service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.handoff_service import HandoffService, HandoffStatus
from app.services.escalation_detector import EscalationReason
from app.services.conversation_context import ConversationContext
from app.services.nlu_engine import Intent
from app.models.lead import Lead
from app.models.call import Call
from app.models.callback import Callback
from app.repositories.lead_repository import LeadRepository
from app.repositories.call_repository import CallRepository
from app.repositories.callback_repository import CallbackRepository


@pytest.fixture
def mock_lead_repo():
    """Create mock lead repository."""
    repo = AsyncMock(spec=LeadRepository)
    return repo


@pytest.fixture
def mock_call_repo():
    """Create mock call repository."""
    repo = AsyncMock(spec=CallRepository)
    return repo


@pytest.fixture
def mock_callback_repo():
    """Create mock callback repository."""
    repo = AsyncMock(spec=CallbackRepository)
    return repo


@pytest.fixture
def mock_twilio_adapter():
    """Create mock Twilio adapter."""
    adapter = AsyncMock()
    adapter.transfer_call = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def mock_crm_adapter():
    """Create mock CRM adapter."""
    adapter = AsyncMock()
    adapter.check_expert_availability = AsyncMock(return_value={
        "available": True,
        "expert_id": "expert_123",
        "phone": "+919999999999"
    })
    adapter.notify_expert = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def mock_notification_adapter():
    """Create mock notification adapter."""
    adapter = AsyncMock()
    adapter.send_callback_confirmation = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def handoff_service(
    mock_lead_repo,
    mock_call_repo,
    mock_callback_repo,
    mock_twilio_adapter,
    mock_crm_adapter,
    mock_notification_adapter
):
    """Create handoff service with mocked dependencies."""
    return HandoffService(
        lead_repository=mock_lead_repo,
        call_repository=mock_call_repo,
        callback_repository=mock_callback_repo,
        twilio_adapter=mock_twilio_adapter,
        crm_adapter=mock_crm_adapter,
        notification_adapter=mock_notification_adapter
    )


@pytest.fixture
def sample_context():
    """Create sample conversation context."""
    context = ConversationContext(
        call_id="call_123",
        lead_id="lead_456",
        language="english"
    )
    context.negative_turn_count = 2
    context.clarification_count = 1
    return context


@pytest.fixture
def sample_lead():
    """Create sample lead."""
    return Lead(
        lead_id="lead_456",
        phone="+919876543210",
        language="english",
        country="US",
        degree="masters",
        loan_amount=50000.0,
        collateral="yes",
        eligibility_category="public_secured",
        status="qualified"
    )


@pytest.fixture
def sample_call():
    """Create sample call."""
    return Call(
        call_id="call_123",
        lead_id="lead_456",
        call_sid="CA123456",
        direction="outbound",
        status="in_progress"
    )


class TestHandoffTriggerLogic:
    """Test handoff trigger detection."""
    
    @pytest.mark.asyncio
    async def test_explicit_handoff_request(self, handoff_service, sample_context):
        """Test handoff triggered by explicit user request."""
        should_handoff, reason, explanation = await handoff_service.check_handoff_trigger(
            context=sample_context,
            current_intent=Intent.REQUEST_HUMAN
        )
        
        assert should_handoff is True
        assert reason == EscalationReason.EXPLICIT_REQUEST
        assert "requested" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_negative_sentiment_threshold(self, handoff_service, sample_context):
        """Test handoff triggered by negative sentiment."""
        sample_context.negative_turn_count = 2
        
        should_handoff, reason, explanation = await handoff_service.check_handoff_trigger(
            context=sample_context
        )
        
        assert should_handoff is True
        assert reason == EscalationReason.NEGATIVE_SENTIMENT
        assert "negative sentiment" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_clarification_threshold(self, handoff_service, sample_context):
        """Test handoff triggered by clarification threshold."""
        sample_context.clarification_count = 3
        sample_context.negative_turn_count = 0
        
        should_handoff, reason, explanation = await handoff_service.check_handoff_trigger(
            context=sample_context
        )
        
        assert should_handoff is True
        assert reason == EscalationReason.CLARIFICATION_THRESHOLD
        assert "clarification" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_aggressive_tone_detection(self, handoff_service, sample_context):
        """Test handoff triggered by aggressive tone."""
        should_handoff, reason, explanation = await handoff_service.check_handoff_trigger(
            context=sample_context,
            current_utterance="You are stupid and useless"
        )
        
        assert should_handoff is True
        assert reason == EscalationReason.AGGRESSIVE_TONE
        assert "aggressive" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_no_handoff_trigger(self, handoff_service, sample_context):
        """Test no handoff when conditions not met."""
        sample_context.negative_turn_count = 0
        sample_context.clarification_count = 0
        
        should_handoff, reason, explanation = await handoff_service.check_handoff_trigger(
            context=sample_context
        )
        
        assert should_handoff is False
        assert reason is None


class TestHandoffInitiation:
    """Test handoff initiation and status updates."""
    
    @pytest.mark.asyncio
    async def test_initiate_handoff_success(
        self,
        handoff_service,
        mock_lead_repo,
        mock_call_repo,
        sample_lead,
        sample_call
    ):
        """Test successful handoff initiation."""
        mock_lead_repo.update.return_value = sample_lead
        mock_call_repo.update.return_value = sample_call
        
        result = await handoff_service.initiate_handoff(
            call_id="call_123",
            lead_id="lead_456",
            reason=EscalationReason.EXPLICIT_REQUEST,
            explanation="User requested human expert"
        )
        
        assert result["success"] is True
        assert result["handoff_status"] == HandoffStatus.PENDING
        assert result["lead_id"] == "lead_456"
        assert result["call_id"] == "call_123"
        
        # Verify lead status updated
        mock_lead_repo.update.assert_called_once()
        call_args = mock_lead_repo.update.call_args
        assert call_args[1]["updates"]["status"] == "handoff"
    
    @pytest.mark.asyncio
    async def test_initiate_handoff_lead_not_found(
        self,
        handoff_service,
        mock_lead_repo
    ):
        """Test handoff initiation when lead not found."""
        mock_lead_repo.update.return_value = None
        
        result = await handoff_service.initiate_handoff(
            call_id="call_123",
            lead_id="lead_456",
            reason=EscalationReason.EXPLICIT_REQUEST,
            explanation="User requested human expert"
        )
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestCallTransfer:
    """Test call transfer to expert."""
    
    @pytest.mark.asyncio
    async def test_transfer_call_expert_available(
        self,
        handoff_service,
        mock_crm_adapter,
        mock_twilio_adapter,
        mock_call_repo,
        sample_call
    ):
        """Test successful call transfer when expert available."""
        mock_call_repo.update.return_value = sample_call
        
        handoff_summary = {
            "lead_id": "lead_456",
            "priority": "medium"
        }
        
        result = await handoff_service.transfer_call_to_expert(
            call_id="call_123",
            lead_id="lead_456",
            call_sid="CA123456",
            handoff_summary=handoff_summary,
            language="english"
        )
        
        assert result["success"] is True
        assert result["status"] == HandoffStatus.TRANSFERRED
        assert "expert_id" in result
        
        # Verify expert availability checked
        mock_crm_adapter.check_expert_availability.assert_called_once()
        
        # Verify expert notified
        mock_crm_adapter.notify_expert.assert_called_once()
        
        # Verify call transferred
        mock_twilio_adapter.transfer_call.assert_called_once()
        
        # Verify call status updated
        mock_call_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_transfer_call_expert_unavailable(
        self,
        handoff_service,
        mock_crm_adapter
    ):
        """Test call transfer when expert unavailable."""
        mock_crm_adapter.check_expert_availability.return_value = {
            "available": False
        }
        
        handoff_summary = {
            "lead_id": "lead_456",
            "priority": "medium"
        }
        
        result = await handoff_service.transfer_call_to_expert(
            call_id="call_123",
            lead_id="lead_456",
            call_sid="CA123456",
            handoff_summary=handoff_summary
        )
        
        assert result["success"] is False
        assert result["status"] == HandoffStatus.EXPERT_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_transfer_call_twilio_failure(
        self,
        handoff_service,
        mock_twilio_adapter
    ):
        """Test call transfer when Twilio transfer fails."""
        mock_twilio_adapter.transfer_call.return_value = False
        
        handoff_summary = {
            "lead_id": "lead_456",
            "priority": "medium"
        }
        
        result = await handoff_service.transfer_call_to_expert(
            call_id="call_123",
            lead_id="lead_456",
            call_sid="CA123456",
            handoff_summary=handoff_summary
        )
        
        assert result["success"] is False
        assert result["status"] == HandoffStatus.FAILED


class TestCallbackScheduling:
    """Test callback scheduling functionality."""
    
    @pytest.mark.asyncio
    async def test_schedule_callback_success(
        self,
        handoff_service,
        mock_callback_repo,
        mock_lead_repo,
        mock_call_repo,
        mock_notification_adapter,
        sample_lead
    ):
        """Test successful callback scheduling."""
        callback = Callback(
            callback_id="callback_789",
            lead_id="lead_456",
            call_id="call_123",
            phone="+919876543210",
            language="english"
        )
        mock_callback_repo.create.return_value = callback
        mock_lead_repo.get_by_id.return_value = sample_lead
        
        result = await handoff_service.schedule_callback(
            call_id="call_123",
            lead_id="lead_456",
            phone="+919876543210",
            language="english"
        )
        
        assert result["success"] is True
        assert "callback_id" in result
        assert "scheduled_time" in result
        
        # Verify callback created
        mock_callback_repo.create.assert_called_once()
        
        # Verify lead status updated
        mock_lead_repo.update.assert_called()
        
        # Verify notification sent
        mock_notification_adapter.send_callback_confirmation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_callback_with_preferred_time(
        self,
        handoff_service,
        mock_callback_repo,
        mock_lead_repo,
        mock_call_repo
    ):
        """Test callback scheduling with user's preferred time."""
        preferred_time = datetime.utcnow() + timedelta(hours=3)
        
        callback = Callback(
            callback_id="callback_789",
            lead_id="lead_456",
            call_id="call_123",
            phone="+919876543210",
            language="english",
            preferred_time=preferred_time
        )
        mock_callback_repo.create.return_value = callback
        
        result = await handoff_service.schedule_callback(
            call_id="call_123",
            lead_id="lead_456",
            phone="+919876543210",
            language="english",
            preferred_time=preferred_time
        )
        
        assert result["success"] is True
        
        # Verify callback created with preferred time
        call_args = mock_callback_repo.create.call_args
        created_callback = call_args[0][0]
        assert created_callback.preferred_time == preferred_time
    
    @pytest.mark.asyncio
    async def test_offer_callback_message(self, handoff_service):
        """Test callback offer message in different languages."""
        english_msg = await handoff_service.offer_callback("english")
        assert "available" in english_msg.lower()
        assert "call you back" in english_msg.lower()
        
        hinglish_msg = await handoff_service.offer_callback("hinglish")
        assert "expert" in hinglish_msg.lower()
        
        telugu_msg = await handoff_service.offer_callback("telugu")
        assert "expert" in telugu_msg.lower()
    
    def test_parse_callback_time(self, handoff_service):
        """Test parsing callback time from user utterance."""
        # Test relative time
        result = handoff_service.parse_callback_time("in 2 hours", "english")
        assert result is not None
        assert result > datetime.utcnow()
        
        # Test tomorrow
        result = handoff_service.parse_callback_time("tomorrow morning", "english")
        assert result is not None
        assert result > datetime.utcnow()
        
        # Test evening
        result = handoff_service.parse_callback_time("this evening", "english")
        assert result is not None


class TestHandoffMessages:
    """Test handoff message generation."""
    
    def test_get_handoff_message_english(self, handoff_service):
        """Test handoff message in English."""
        message = handoff_service.get_handoff_message(
            EscalationReason.EXPLICIT_REQUEST,
            "english"
        )
        
        assert message is not None
        assert len(message) > 0
        assert "expert" in message.lower()
    
    def test_get_handoff_message_hinglish(self, handoff_service):
        """Test handoff message in Hinglish."""
        message = handoff_service.get_handoff_message(
            EscalationReason.NEGATIVE_SENTIMENT,
            "hinglish"
        )
        
        assert message is not None
        assert len(message) > 0
    
    def test_get_handoff_message_telugu(self, handoff_service):
        """Test handoff message in Telugu."""
        message = handoff_service.get_handoff_message(
            EscalationReason.CLARIFICATION_THRESHOLD,
            "telugu"
        )
        
        assert message is not None
        assert len(message) > 0
