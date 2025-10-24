"""
Integration tests for notification adapter.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.integrations.notification_adapter import NotificationAdapter


@pytest.fixture
def notification_adapter():
    """Create notification adapter with test credentials."""
    return NotificationAdapter(
        api_url="https://api.test.com",
        api_key="test_api_key",
        provider="gupshup"
    )


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message_id": "msg_123", "status": "sent"}
    mock_client.post.return_value = mock_response
    return mock_client


class TestWhatsAppMessaging:
    """Test WhatsApp message sending."""
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_success(self, notification_adapter):
        """Test successful WhatsApp message sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message_id": "msg_123"}
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await notification_adapter.send_whatsapp(
                phone="+919876543210",
                message="Test message"
            )
            
            assert result["success"] is True
            assert "message_id" in result
            assert result["channel"] == "whatsapp"
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_with_template(self, notification_adapter):
        """Test WhatsApp message with template."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message_id": "msg_456"}
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await notification_adapter.send_whatsapp(
                phone="+919876543210",
                message="",
                template_id="callback_confirmation",
                template_params={"name": "John", "time": "2PM"}
            )
            
            assert result["success"] is True
            assert result["message_id"] == "msg_456"
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_http_error(self, notification_adapter):
        """Test WhatsApp sending with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad request",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await notification_adapter.send_whatsapp(
                phone="+919876543210",
                message="Test message"
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_no_api_key(self):
        """Test WhatsApp sending without API key."""
        adapter = NotificationAdapter(api_key=None)
        
        result = await adapter.send_whatsapp(
            phone="+919876543210",
            message="Test message"
        )
        
        assert result["success"] is False
        assert "not configured" in result["error"]


class TestSMSMessaging:
    """Test SMS message sending."""
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, notification_adapter):
        """Test successful SMS sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message_id": "sms_789"}
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await notification_adapter.send_sms(
                phone="+919876543210",
                message="Test SMS"
            )
            
            assert result["success"] is True
            assert result["message_id"] == "sms_789"
            assert result["channel"] == "sms"
    
    @pytest.mark.asyncio
    async def test_send_sms_network_error(self, notification_adapter):
        """Test SMS sending with network error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = httpx.RequestError(
                "Connection failed"
            )
            mock_client_class.return_value = mock_client
            
            result = await notification_adapter.send_sms(
                phone="+919876543210",
                message="Test SMS"
            )
            
            assert result["success"] is False
            assert "error" in result


class TestCallbackConfirmation:
    """Test callback confirmation messages."""
    
    @pytest.mark.asyncio
    async def test_send_callback_confirmation_english(self, notification_adapter):
        """Test callback confirmation in English."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_123"}
            
            result = await notification_adapter.send_callback_confirmation(
                phone="+919876543210",
                language="english",
                callback_time="October 25, 2025 at 2:00 PM",
                lead_name="John"
            )
            
            assert result is True
            mock_whatsapp.assert_called_once()
            call_args = mock_whatsapp.call_args
            assert "John" in call_args[1]["message"]
            assert "2:00 PM" in call_args[1]["message"]
    
    @pytest.mark.asyncio
    async def test_send_callback_confirmation_hinglish(self, notification_adapter):
        """Test callback confirmation in Hinglish."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_456"}
            
            result = await notification_adapter.send_callback_confirmation(
                phone="+919876543210",
                language="hinglish",
                callback_time="October 25, 2025 at 2:00 PM"
            )
            
            assert result is True
            mock_whatsapp.assert_called_once()
            call_args = mock_whatsapp.call_args
            assert "callback" in call_args[1]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_send_callback_confirmation_fallback_to_sms(self, notification_adapter):
        """Test callback confirmation falls back to SMS when WhatsApp fails."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp, \
             patch.object(notification_adapter, "send_sms") as mock_sms:
            mock_whatsapp.return_value = {"success": False, "error": "Failed"}
            mock_sms.return_value = {"success": True, "message_id": "sms_789"}
            
            result = await notification_adapter.send_callback_confirmation(
                phone="+919876543210",
                language="english",
                callback_time="October 25, 2025 at 2:00 PM"
            )
            
            assert result is True
            mock_whatsapp.assert_called_once()
            mock_sms.assert_called_once()


class TestPostCallSummary:
    """Test post-call summary messages."""
    
    @pytest.mark.asyncio
    async def test_send_post_call_summary_with_eligibility(self, notification_adapter):
        """Test post-call summary with eligibility information."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_123"}
            
            result = await notification_adapter.send_post_call_summary(
                phone="+919876543210",
                language="english",
                lead_name="John",
                eligibility_category="public_secured",
                loan_amount=50000.0,
                next_steps="Submit documents within 7 days"
            )
            
            assert result["success"] is True
            mock_whatsapp.assert_called_once()
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "John" in message
            assert "eligible" in message.lower()
            assert "50,000" in message
    
    @pytest.mark.asyncio
    async def test_send_post_call_summary_with_callback(self, notification_adapter):
        """Test post-call summary with callback information."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_456"}
            
            result = await notification_adapter.send_post_call_summary(
                phone="+919876543210",
                language="hinglish",
                lead_name="Raj",
                eligibility_category="private_unsecured",
                loan_amount=30000.0,
                next_steps="Expert will call you",
                callback_scheduled=True,
                callback_time="Tomorrow at 3 PM"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "Raj" in message
            assert "3 PM" in message


class TestNoAnswerFollowup:
    """Test no-answer follow-up messages."""
    
    @pytest.mark.asyncio
    async def test_send_no_answer_followup_with_link(self, notification_adapter):
        """Test no-answer follow-up with callback link."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_123"}
            
            result = await notification_adapter.send_no_answer_followup(
                phone="+919876543210",
                language="english",
                lead_name="John",
                callback_link="https://example.com/callback",
                retry_schedule="in 1 hour"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "unavailable" in message.lower()
            assert "https://example.com/callback" in message
            assert "1 hour" in message
    
    @pytest.mark.asyncio
    async def test_send_retry_notification_first_attempt(self, notification_adapter):
        """Test retry notification for first attempt."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_456"}
            
            result = await notification_adapter.send_retry_notification(
                phone="+919876543210",
                language="english",
                lead_name="John",
                retry_count=1,
                next_retry_time="6 hours"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "earlier" in message.lower() or "pehle" in message.lower()
    
    @pytest.mark.asyncio
    async def test_send_retry_notification_final_attempt(self, notification_adapter):
        """Test retry notification for final attempt."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_789"}
            
            result = await notification_adapter.send_retry_notification(
                phone="+919876543210",
                language="english",
                lead_name="John",
                retry_count=3
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "final" in message.lower() or "aakhri" in message.lower()
    
    @pytest.mark.asyncio
    async def test_send_unreachable_notification(self, notification_adapter):
        """Test unreachable notification."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_999"}
            
            result = await notification_adapter.send_unreachable_notification(
                phone="+919876543210",
                language="english",
                lead_name="John",
                callback_link="https://example.com/callback"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "multiple times" in message.lower() or "kai baar" in message.lower()
            assert "https://example.com/callback" in message


class TestEligibilitySummary:
    """Test eligibility summary messages."""
    
    @pytest.mark.asyncio
    async def test_send_eligibility_summary_high_urgency(self, notification_adapter):
        """Test eligibility summary with high urgency."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_123"}
            
            result = await notification_adapter.send_eligibility_summary(
                phone="+919876543210",
                language="english",
                lead_name="John",
                eligibility_category="public_secured",
                lenders=["SBI", "HDFC", "ICICI", "Axis"],
                urgency="high"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "High Priority" in message
            assert "SBI" in message
            assert "HDFC" in message
            assert "ICICI" in message
    
    @pytest.mark.asyncio
    async def test_send_eligibility_summary_telugu(self, notification_adapter):
        """Test eligibility summary in Telugu."""
        with patch.object(notification_adapter, "send_whatsapp") as mock_whatsapp:
            mock_whatsapp.return_value = {"success": True, "message_id": "msg_456"}
            
            result = await notification_adapter.send_eligibility_summary(
                phone="+919876543210",
                language="telugu",
                lead_name="Ravi",
                eligibility_category="intl_usd",
                lenders=["Prodigy Finance", "MPower"],
                urgency="medium"
            )
            
            assert result["success"] is True
            call_args = mock_whatsapp.call_args
            message = call_args[1]["message"]
            assert "Ravi" in message
            assert "Prodigy Finance" in message
