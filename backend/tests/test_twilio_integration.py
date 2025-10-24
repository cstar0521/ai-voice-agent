"""
Integration tests for Twilio adapter and webhook handlers.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.integrations.twilio_adapter import TwilioAdapter
from app.integrations.twilio_webhooks import (
    TwilioWebhookHandler,
    TwilioCallStatusWebhook,
    TwilioRecordingStatusWebhook,
    TwilioSpeechResultWebhook
)
from app.models.call import Call
from app.models.conversation import Conversation, Turn


class TestTwilioAdapter:
    """Test suite for TwilioAdapter class."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock Twilio client."""
        with patch('app.integrations.twilio_adapter.Client') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def twilio_adapter(self, mock_twilio_client):
        """Create TwilioAdapter instance with mocked client."""
        adapter = TwilioAdapter(
            account_sid="test_account_sid",
            auth_token="test_auth_token",
            phone_number="+15555555555"
        )
        return adapter
    
    @pytest.mark.asyncio
    async def test_make_call_success(self, twilio_adapter, mock_twilio_client):
        """Test successful outbound call initiation."""
        # Mock call creation
        mock_call = Mock()
        mock_call.sid = "CA1234567890abcdef"
        mock_twilio_client.return_value.calls.create.return_value = mock_call
        
        # Make call
        call_sid = await twilio_adapter.make_call(
            to_number="+919876543210",
            callback_url="https://example.com/callback",
            status_callback_url="https://example.com/status"
        )
        
        # Verify
        assert call_sid == "CA1234567890abcdef"
        mock_twilio_client.return_value.calls.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_call_failure(self, twilio_adapter, mock_twilio_client):
        """Test failed outbound call initiation."""
        # Mock call creation failure
        mock_twilio_client.return_value.calls.create.side_effect = Exception("API Error")
        
        # Make call should raise exception
        with pytest.raises(Exception) as exc_info:
            await twilio_adapter.make_call(
                to_number="+919876543210",
                callback_url="https://example.com/callback"
            )
        
        assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_answer_call(self, twilio_adapter):
        """Test answering inbound call with TwiML generation."""
        twiml = await twilio_adapter.answer_call(
            call_sid="CA1234567890abcdef",
            greeting_text="Hello, welcome!",
            gather_url="https://example.com/gather",
            language="en-IN"
        )
        
        # Verify TwiML contains expected elements
        assert "Hello, welcome!" in twiml
        assert "Gather" in twiml
        assert "https://example.com/gather" in twiml
    
    @pytest.mark.asyncio
    async def test_transfer_call_success(self, twilio_adapter, mock_twilio_client):
        """Test successful call transfer."""
        # Mock call update
        mock_call = Mock()
        mock_twilio_client.return_value.calls.return_value.update.return_value = mock_call
        
        # Transfer call
        result = await twilio_adapter.transfer_call(
            call_sid="CA1234567890abcdef",
            to_number="+919876543210",
            transfer_message="Transferring you now"
        )
        
        # Verify
        assert result is True
        mock_twilio_client.return_value.calls.return_value.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hangup_call_success(self, twilio_adapter, mock_twilio_client):
        """Test successful call hangup."""
        # Mock call update
        mock_call = Mock()
        mock_twilio_client.return_value.calls.return_value.update.return_value = mock_call
        
        # Hangup call
        result = await twilio_adapter.hangup_call("CA1234567890abcdef")
        
        # Verify
        assert result is True
        mock_twilio_client.return_value.calls.return_value.update.assert_called_once_with(
            status="completed"
        )
    
    @pytest.mark.asyncio
    async def test_start_recording_success(self, twilio_adapter, mock_twilio_client):
        """Test starting call recording."""
        # Mock recording creation
        mock_recording = Mock()
        mock_recording.sid = "RE1234567890abcdef"
        mock_twilio_client.return_value.calls.return_value.recordings.create.return_value = mock_recording
        
        # Start recording
        recording_sid = await twilio_adapter.start_recording(
            call_sid="CA1234567890abcdef",
            recording_status_callback="https://example.com/recording"
        )
        
        # Verify
        assert recording_sid == "RE1234567890abcdef"
        mock_twilio_client.return_value.calls.return_value.recordings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_recording_success(self, twilio_adapter, mock_twilio_client):
        """Test stopping call recording."""
        # Mock recording update
        mock_recording = Mock()
        mock_twilio_client.return_value.calls.return_value.recordings.return_value.update.return_value = mock_recording
        
        # Stop recording
        result = await twilio_adapter.stop_recording(
            call_sid="CA1234567890abcdef",
            recording_sid="RE1234567890abcdef"
        )
        
        # Verify
        assert result is True
        mock_twilio_client.return_value.calls.return_value.recordings.return_value.update.assert_called_once_with(
            status="stopped"
        )
    
    def test_validate_webhook_signature_valid(self, twilio_adapter):
        """Test webhook signature validation with valid signature."""
        # Mock validator
        with patch.object(twilio_adapter.validator, 'validate', return_value=True):
            result = twilio_adapter.validate_webhook_signature(
                url="https://example.com/webhook",
                params={"CallSid": "CA123"},
                signature="valid_signature"
            )
            
            assert result is True
    
    def test_validate_webhook_signature_invalid(self, twilio_adapter):
        """Test webhook signature validation with invalid signature."""
        # Mock validator
        with patch.object(twilio_adapter.validator, 'validate', return_value=False):
            result = twilio_adapter.validate_webhook_signature(
                url="https://example.com/webhook",
                params={"CallSid": "CA123"},
                signature="invalid_signature"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_call_details(self, twilio_adapter, mock_twilio_client):
        """Test retrieving call details from Twilio."""
        # Mock call fetch
        mock_call = Mock()
        mock_call.sid = "CA1234567890abcdef"
        mock_call.status = "completed"
        mock_call.direction = "outbound"
        mock_call.from_ = "+15555555555"
        mock_call.to = "+919876543210"
        mock_call.duration = "120"
        mock_call.start_time = datetime.utcnow()
        mock_call.end_time = datetime.utcnow()
        mock_call.price = "-0.02"
        mock_call.price_unit = "USD"
        
        mock_twilio_client.return_value.calls.return_value.fetch.return_value = mock_call
        
        # Get call details
        details = await twilio_adapter.get_call_details("CA1234567890abcdef")
        
        # Verify
        assert details["call_sid"] == "CA1234567890abcdef"
        assert details["status"] == "completed"
        assert details["direction"] == "outbound"


class TestTwilioWebhookHandler:
    """Test suite for TwilioWebhookHandler class."""
    
    @pytest.fixture
    def mock_call_repo(self):
        """Create mock call repository."""
        repo = Mock()
        repo.get_by_call_sid = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_lead_repo(self):
        """Create mock lead repository."""
        repo = Mock()
        return repo
    
    @pytest.fixture
    def mock_conversation_repo(self):
        """Create mock conversation repository."""
        repo = Mock()
        repo.get_by_call_sid = AsyncMock()
        repo.add_turn = AsyncMock()
        return repo
    
    @pytest.fixture
    def sample_call(self):
        """Create sample call object."""
        return Call(
            call_id="call_123",
            lead_id="lead_456",
            call_sid="CA1234567890abcdef",
            direction="outbound",
            status="initiated"
        )
    
    @pytest.mark.asyncio
    async def test_handle_call_status_answered(
        self, mock_call_repo, mock_lead_repo, sample_call
    ):
        """Test handling call status webhook for answered call."""
        # Setup
        mock_call_repo.get_by_call_sid.return_value = sample_call
        mock_call_repo.update.return_value = sample_call
        
        webhook_data = TwilioCallStatusWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            From="+919876543210",
            To="+15555555555",
            CallStatus="answered",
            Direction="outbound"
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_call_status(
            webhook_data, mock_call_repo, mock_lead_repo
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["call_status"] == "connected"
        mock_call_repo.update.assert_called_once()
        
        # Check that start_time was set
        call_args = mock_call_repo.update.call_args[0]
        assert "start_time" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_handle_call_status_completed(
        self, mock_call_repo, mock_lead_repo, sample_call
    ):
        """Test handling call status webhook for completed call."""
        # Setup
        mock_call_repo.get_by_call_sid.return_value = sample_call
        mock_call_repo.update.return_value = sample_call
        
        webhook_data = TwilioCallStatusWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            From="+919876543210",
            To="+15555555555",
            CallStatus="completed",
            Direction="outbound",
            CallDuration="120"
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_call_status(
            webhook_data, mock_call_repo, mock_lead_repo
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["call_status"] == "completed"
        
        # Check that end_time and duration were set
        call_args = mock_call_repo.update.call_args[0]
        assert "end_time" in call_args[1]
        assert call_args[1]["duration"] == 120
    
    @pytest.mark.asyncio
    async def test_handle_call_status_failed(
        self, mock_call_repo, mock_lead_repo, sample_call
    ):
        """Test handling call status webhook for failed call."""
        # Setup
        mock_call_repo.get_by_call_sid.return_value = sample_call
        mock_call_repo.update.return_value = sample_call
        
        webhook_data = TwilioCallStatusWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            From="+919876543210",
            To="+15555555555",
            CallStatus="failed",
            Direction="outbound"
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_call_status(
            webhook_data, mock_call_repo, mock_lead_repo
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["call_status"] == "failed"
        
        # Check that error_reason was set
        call_args = mock_call_repo.update.call_args[0]
        assert call_args[1]["error_reason"] == "failed"
    
    @pytest.mark.asyncio
    async def test_handle_call_status_not_found(
        self, mock_call_repo, mock_lead_repo
    ):
        """Test handling call status webhook when call not found."""
        # Setup
        mock_call_repo.get_by_call_sid.return_value = None
        
        webhook_data = TwilioCallStatusWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            From="+919876543210",
            To="+15555555555",
            CallStatus="answered",
            Direction="outbound"
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_call_status(
            webhook_data, mock_call_repo, mock_lead_repo
        )
        
        # Verify
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_recording_status_completed(
        self, mock_call_repo, sample_call
    ):
        """Test handling recording status webhook for completed recording."""
        # Setup
        mock_call_repo.get_by_call_sid.return_value = sample_call
        mock_call_repo.update.return_value = sample_call
        
        webhook_data = TwilioRecordingStatusWebhook(
            RecordingSid="RE1234567890abcdef",
            RecordingUrl="https://api.twilio.com/recordings/RE123",
            RecordingStatus="completed",
            RecordingDuration="120",
            CallSid="CA1234567890abcdef",
            AccountSid="AC123"
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_recording_status(
            webhook_data, mock_call_repo
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["recording_url"] == "https://api.twilio.com/recordings/RE123"
        
        # Check that recording_url was saved
        call_args = mock_call_repo.update.call_args[0]
        assert call_args[1]["recording_url"] == "https://api.twilio.com/recordings/RE123"
    
    @pytest.mark.asyncio
    async def test_handle_speech_result_success(
        self, mock_conversation_repo
    ):
        """Test handling speech recognition result."""
        # Setup
        mock_conversation = Mock()
        mock_conversation.conversation_id = "conv_123"
        mock_conversation.turns = []
        mock_conversation_repo.get_by_call_sid.return_value = mock_conversation
        mock_conversation_repo.add_turn.return_value = mock_conversation
        
        webhook_data = TwilioSpeechResultWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            SpeechResult="I want to apply for a loan",
            Confidence=0.95
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_speech_result(
            webhook_data, mock_conversation_repo
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["transcript"] == "I want to apply for a loan"
        assert result["confidence"] == 0.95
        mock_conversation_repo.add_turn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_speech_result_no_speech(
        self, mock_conversation_repo
    ):
        """Test handling speech recognition result with no speech detected."""
        # Setup
        webhook_data = TwilioSpeechResultWebhook(
            CallSid="CA1234567890abcdef",
            AccountSid="AC123",
            SpeechResult=None,
            Confidence=None
        )
        
        # Execute
        result = await TwilioWebhookHandler.handle_speech_result(
            webhook_data, mock_conversation_repo
        )
        
        # Verify
        assert result["status"] == "no_speech"
        assert result["confidence"] == 0.0
