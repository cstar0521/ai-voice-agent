"""
Integration tests for CRM adapter.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.integrations.crm_adapter import CRMAdapter
from app.models.lead import Lead


@pytest.fixture
def crm_adapter():
    """Create CRM adapter with test credentials."""
    return CRMAdapter(
        api_url="https://api.test-crm.com",
        api_key="test_api_key"
    )


@pytest.fixture
def sample_lead():
    """Create sample lead."""
    return Lead(
        lead_id="lead_123",
        phone="+919876543210",
        name="John Doe",
        language="english",
        country="US",
        degree="masters",
        loan_amount=50000.0,
        collateral="yes",
        eligibility_category="public_secured",
        status="qualified"
    )


@pytest.fixture
def sample_lead_data():
    """Create sample lead data dictionary."""
    return {
        "phone": "+919876543210",
        "name": "John Doe",
        "language": "english",
        "country": "US",
        "degree": "masters",
        "loan_amount": 50000.0,
        "collateral": "yes"
    }


class TestLeadCreation:
    """Test lead creation in CRM."""
    
    @pytest.mark.asyncio
    async def test_create_lead_success(self, crm_adapter, sample_lead_data):
        """Test successful lead creation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"lead_id": "crm_lead_456"}
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            crm_lead_id = await crm_adapter.create_lead(sample_lead_data)
            
            assert crm_lead_id == "crm_lead_456"
            mock_client.__aenter__.return_value.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_lead_http_error(self, crm_adapter, sample_lead_data):
        """Test lead creation with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = httpx.HTTPError("Error")
            mock_client_class.return_value = mock_client
            
            crm_lead_id = await crm_adapter.create_lead(sample_lead_data)
            
            assert crm_lead_id is None
    
    @pytest.mark.asyncio
    async def test_create_lead_no_api_key(self, sample_lead_data):
        """Test lead creation without API key."""
        adapter = CRMAdapter(api_key=None)
        
        crm_lead_id = await adapter.create_lead(sample_lead_data)
        
        assert crm_lead_id is None


class TestLeadUpdate:
    """Test lead updates in CRM."""
    
    @pytest.mark.asyncio
    async def test_update_lead_success(self, crm_adapter):
        """Test successful lead update."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.__aenter__.return_value.put.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            updates = {"status": "qualified", "eligibility_category": "public_secured"}
            success = await crm_adapter.update_lead("crm_lead_456", updates)
            
            assert success is True
            mock_client.__aenter__.return_value.put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_lead_not_found(self, crm_adapter):
        """Test lead update when lead not found."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPError("Not found")
            mock_client.__aenter__.return_value.put.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            success = await crm_adapter.update_lead("crm_lead_999", {"status": "qualified"})
            
            assert success is False


class TestLeadRetrieval:
    """Test lead retrieval from CRM."""
    
    @pytest.mark.asyncio
    async def test_get_lead_success(self, crm_adapter):
        """Test successful lead retrieval."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "lead_id": "crm_lead_456",
                "phone": "+919876543210",
                "status": "qualified"
            }
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            lead_data = await crm_adapter.get_lead("crm_lead_456")
            
            assert lead_data is not None
            assert lead_data["lead_id"] == "crm_lead_456"
            assert lead_data["phone"] == "+919876543210"
    
    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, crm_adapter):
        """Test lead retrieval when not found."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.side_effect = httpx.HTTPError("Not found")
            mock_client_class.return_value = mock_client
            
            lead_data = await crm_adapter.get_lead("crm_lead_999")
            
            assert lead_data is None


class TestExpertNotification:
    """Test expert notification for handoffs."""
    
    @pytest.mark.asyncio
    async def test_notify_expert_success(self, crm_adapter):
        """Test successful expert notification."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            handoff_summary = {
                "lead_id": "lead_123",
                "priority": "high",
                "reason": "explicit_request"
            }
            
            success = await crm_adapter.notify_expert(
                lead_id="lead_123",
                expert_id="expert_789",
                handoff_summary=handoff_summary
            )
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_notify_expert_failure(self, crm_adapter):
        """Test expert notification failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = httpx.HTTPError("Error")
            mock_client_class.return_value = mock_client
            
            success = await crm_adapter.notify_expert(
                lead_id="lead_123",
                expert_id="expert_789",
                handoff_summary={}
            )
            
            assert success is False


class TestExpertAvailability:
    """Test expert availability checking."""
    
    @pytest.mark.asyncio
    async def test_check_expert_available(self, crm_adapter):
        """Test checking when expert is available."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "available": True,
                "expert_id": "expert_789",
                "phone": "+919999999999"
            }
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            expert = await crm_adapter.check_expert_availability(
                language="english",
                priority="high"
            )
            
            assert expert is not None
            assert expert["available"] is True
            assert expert["expert_id"] == "expert_789"
    
    @pytest.mark.asyncio
    async def test_check_expert_unavailable(self, crm_adapter):
        """Test checking when expert is unavailable."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"available": False}
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            expert = await crm_adapter.check_expert_availability()
            
            assert expert is None


class TestLeadSynchronization:
    """Test lead summary synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_lead_summary_success(self, crm_adapter):
        """Test successful lead summary sync."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "crm_lead_id": "crm_lead_456",
                "sync_id": "sync_789"
            }
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            lead_summary = {
                "lead_id": "lead_123",
                "phone": "+919876543210",
                "eligibility_category": "public_secured"
            }
            
            result = await crm_adapter.sync_lead_summary(
                lead_id="lead_123",
                lead_summary=lead_summary
            )
            
            assert result["success"] is True
            assert result["crm_lead_id"] == "crm_lead_456"
            assert result["should_retry"] is False
    
    @pytest.mark.asyncio
    async def test_sync_lead_summary_server_error_retry(self, crm_adapter):
        """Test lead sync with server error should retry."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await crm_adapter.sync_lead_summary(
                lead_id="lead_123",
                lead_summary={},
                retry_count=0
            )
            
            assert result["success"] is False
            assert result["should_retry"] is True
    
    @pytest.mark.asyncio
    async def test_sync_lead_summary_max_retries(self, crm_adapter):
        """Test lead sync should not retry after max attempts."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await crm_adapter.sync_lead_summary(
                lead_id="lead_123",
                lead_summary={},
                retry_count=3
            )
            
            assert result["success"] is False
            assert result["should_retry"] is False
    
    @pytest.mark.asyncio
    async def test_sync_lead_summary_network_error(self, crm_adapter):
        """Test lead sync with network error should retry."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = httpx.RequestError(
                "Connection failed"
            )
            mock_client_class.return_value = mock_client
            
            result = await crm_adapter.sync_lead_summary(
                lead_id="lead_123",
                lead_summary={},
                retry_count=0
            )
            
            assert result["success"] is False
            assert result["should_retry"] is True


class TestBatchSync:
    """Test batch lead synchronization."""
    
    @pytest.mark.asyncio
    async def test_batch_sync_success(self, crm_adapter):
        """Test successful batch sync."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success_count": 3,
                "failed_count": 0,
                "failed_leads": []
            }
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            lead_summaries = [
                {"lead_id": "lead_1"},
                {"lead_id": "lead_2"},
                {"lead_id": "lead_3"}
            ]
            
            result = await crm_adapter.batch_sync_leads(lead_summaries)
            
            assert result["success"] is True
            assert result["success_count"] == 3
            assert result["failed_count"] == 0
    
    @pytest.mark.asyncio
    async def test_batch_sync_partial_failure(self, crm_adapter):
        """Test batch sync with partial failures."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success_count": 2,
                "failed_count": 1,
                "failed_leads": ["lead_3"]
            }
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            lead_summaries = [
                {"lead_id": "lead_1"},
                {"lead_id": "lead_2"},
                {"lead_id": "lead_3"}
            ]
            
            result = await crm_adapter.batch_sync_leads(lead_summaries)
            
            assert result["success"] is True
            assert result["success_count"] == 2
            assert result["failed_count"] == 1
            assert "lead_3" in result["failed_leads"]


class TestLeadSummaryPreparation:
    """Test lead summary preparation."""
    
    def test_prepare_lead_summary_basic(self, crm_adapter, sample_lead):
        """Test basic lead summary preparation."""
        summary = crm_adapter.prepare_lead_summary(sample_lead)
        
        assert summary["lead_id"] == "lead_123"
        assert summary["phone"] == "+919876543210"
        assert summary["name"] == "John Doe"
        assert summary["eligibility_category"] == "public_secured"
    
    def test_prepare_lead_summary_with_eligibility(self, crm_adapter, sample_lead):
        """Test lead summary with eligibility data."""
        eligibility_data = {
            "category": "public_secured",
            "lenders": ["SBI", "HDFC"],
            "urgency": "high"
        }
        
        summary = crm_adapter.prepare_lead_summary(
            sample_lead,
            eligibility_data=eligibility_data
        )
        
        assert "eligibility" in summary
        assert summary["eligibility"]["category"] == "public_secured"
        assert len(summary["eligibility"]["lenders"]) == 2
    
    def test_prepare_lead_summary_with_call_data(self, crm_adapter, sample_lead):
        """Test lead summary with call data."""
        call_data = {
            "call_id": "call_456",
            "duration": 180,
            "status": "completed"
        }
        
        summary = crm_adapter.prepare_lead_summary(
            sample_lead,
            call_data=call_data
        )
        
        assert "call" in summary
        assert summary["call"]["call_id"] == "call_456"
        assert summary["call"]["duration"] == 180
    
    def test_prepare_lead_summary_complete(self, crm_adapter, sample_lead):
        """Test complete lead summary with all data."""
        eligibility_data = {"category": "public_secured"}
        call_data = {"call_id": "call_456"}
        conversation_data = {
            "turn_count": 10,
            "average_sentiment": 0.5
        }
        
        summary = crm_adapter.prepare_lead_summary(
            sample_lead,
            eligibility_data=eligibility_data,
            call_data=call_data,
            conversation_data=conversation_data
        )
        
        assert "eligibility" in summary
        assert "call" in summary
        assert "conversation" in summary
        assert summary["conversation"]["turn_count"] == 10
