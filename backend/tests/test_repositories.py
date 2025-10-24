"""
Unit tests for repository layer.
"""
import pytest
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from app.models.lead import Lead
from app.models.call import Call
from app.models.conversation import Conversation, Turn
from app.models.configuration import VoicePrompt, ConversationFlow
from app.repositories.lead_repository import LeadRepository
from app.repositories.call_repository import CallRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.configuration_repository import ConfigurationRepository


@pytest.fixture
async def test_db():
    """Create a test database connection."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_voice_agent
    yield db
    # Cleanup
    await client.drop_database("test_voice_agent")
    client.close()


@pytest.fixture
def lead_repo(test_db):
    """Create a LeadRepository instance."""
    return LeadRepository(test_db)


@pytest.fixture
def call_repo(test_db):
    """Create a CallRepository instance."""
    return CallRepository(test_db)


@pytest.fixture
def conversation_repo(test_db):
    """Create a ConversationRepository instance."""
    return ConversationRepository(test_db)


@pytest.fixture
def config_repo(test_db):
    """Create a ConfigurationRepository instance."""
    return ConfigurationRepository(test_db)


class TestLeadRepository:
    """Tests for LeadRepository."""
    
    @pytest.mark.asyncio
    async def test_create_lead(self, lead_repo):
        """Test creating a lead."""
        lead = Lead(phone="+919876543210", language="hinglish")
        created_lead = await lead_repo.create(lead)
        
        assert created_lead.lead_id == lead.lead_id
        assert created_lead.phone == "+919876543210"
    
    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, lead_repo):
        """Test retrieving a lead by ID."""
        lead = Lead(phone="+919876543210", language="english")
        await lead_repo.create(lead)
        
        retrieved_lead = await lead_repo.get_by_id(lead.lead_id)
        assert retrieved_lead is not None
        assert retrieved_lead.lead_id == lead.lead_id
        assert retrieved_lead.phone == "+919876543210"
    
    @pytest.mark.asyncio
    async def test_get_lead_by_phone(self, lead_repo):
        """Test retrieving a lead by phone number."""
        lead = Lead(phone="+919876543210", language="hinglish")
        await lead_repo.create(lead)
        
        retrieved_lead = await lead_repo.get_by_phone("+919876543210")
        assert retrieved_lead is not None
        assert retrieved_lead.phone == "+919876543210"
    
    @pytest.mark.asyncio
    async def test_update_lead(self, lead_repo):
        """Test updating a lead."""
        lead = Lead(phone="+919876543210", status="new")
        await lead_repo.create(lead)
        
        updated_lead = await lead_repo.update(lead.lead_id, {"status": "qualified"})
        assert updated_lead is not None
        assert updated_lead.status == "qualified"
    
    @pytest.mark.asyncio
    async def test_delete_lead(self, lead_repo):
        """Test deleting a lead."""
        lead = Lead(phone="+919876543210")
        await lead_repo.create(lead)
        
        deleted = await lead_repo.delete(lead.lead_id)
        assert deleted is True
        
        retrieved_lead = await lead_repo.get_by_id(lead.lead_id)
        assert retrieved_lead is None
    
    @pytest.mark.asyncio
    async def test_list_leads(self, lead_repo):
        """Test listing leads."""
        lead1 = Lead(phone="+919876543210", status="new")
        lead2 = Lead(phone="+919876543211", status="qualified")
        await lead_repo.create(lead1)
        await lead_repo.create(lead2)
        
        leads = await lead_repo.list()
        assert len(leads) == 2
        
        qualified_leads = await lead_repo.list(status="qualified")
        assert len(qualified_leads) == 1
        assert qualified_leads[0].status == "qualified"


class TestCallRepository:
    """Tests for CallRepository."""
    
    @pytest.mark.asyncio
    async def test_create_call(self, call_repo):
        """Test creating a call."""
        call = Call(lead_id="lead_abc123", direction="outbound")
        created_call = await call_repo.create(call)
        
        assert created_call.call_id == call.call_id
        assert created_call.direction == "outbound"
    
    @pytest.mark.asyncio
    async def test_get_call_by_id(self, call_repo):
        """Test retrieving a call by ID."""
        call = Call(lead_id="lead_abc123", direction="outbound")
        await call_repo.create(call)
        
        retrieved_call = await call_repo.get_by_id(call.call_id)
        assert retrieved_call is not None
        assert retrieved_call.call_id == call.call_id
    
    @pytest.mark.asyncio
    async def test_get_calls_by_lead_id(self, call_repo):
        """Test retrieving calls for a lead."""
        call1 = Call(lead_id="lead_abc123", direction="outbound")
        call2 = Call(lead_id="lead_abc123", direction="inbound")
        await call_repo.create(call1)
        await call_repo.create(call2)
        
        calls = await call_repo.get_by_lead_id("lead_abc123")
        assert len(calls) == 2
    
    @pytest.mark.asyncio
    async def test_update_call_status(self, call_repo):
        """Test updating call status."""
        call = Call(lead_id="lead_abc123", direction="outbound", status="initiated")
        await call_repo.create(call)
        
        updated_call = await call_repo.update_status(call.call_id, "completed")
        assert updated_call is not None
        assert updated_call.status == "completed"
    
    @pytest.mark.asyncio
    async def test_increment_retry_count(self, call_repo):
        """Test incrementing retry count."""
        call = Call(lead_id="lead_abc123", direction="outbound", retry_count=0)
        await call_repo.create(call)
        
        updated_call = await call_repo.increment_retry_count(call.call_id)
        assert updated_call is not None
        assert updated_call.retry_count == 1


class TestConversationRepository:
    """Tests for ConversationRepository."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, conversation_repo):
        """Test creating a conversation."""
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123",
            language="hinglish"
        )
        created_conv = await conversation_repo.create(conversation)
        
        assert created_conv.conversation_id == conversation.conversation_id
        assert created_conv.call_id == "call_xyz123"
    
    @pytest.mark.asyncio
    async def test_append_turn(self, conversation_repo):
        """Test appending a turn to conversation."""
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123"
        )
        await conversation_repo.create(conversation)
        
        turn = Turn(turn_id=1, speaker="agent", text="Hello")
        updated_conv = await conversation_repo.append_turn(
            conversation.conversation_id,
            turn
        )
        
        assert updated_conv is not None
        assert len(updated_conv.turns) == 1
        assert updated_conv.turns[0].text == "Hello"
    
    @pytest.mark.asyncio
    async def test_update_state(self, conversation_repo):
        """Test updating conversation state."""
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123",
            current_state="greeting"
        )
        await conversation_repo.create(conversation)
        
        updated_conv = await conversation_repo.update_state(
            conversation.conversation_id,
            "qualification"
        )
        
        assert updated_conv is not None
        assert updated_conv.current_state == "qualification"
    
    @pytest.mark.asyncio
    async def test_increment_negative_turn_count(self, conversation_repo):
        """Test incrementing negative turn count."""
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123",
            negative_turn_count=0
        )
        await conversation_repo.create(conversation)
        
        updated_conv = await conversation_repo.increment_negative_turn_count(
            conversation.conversation_id
        )
        
        assert updated_conv is not None
        assert updated_conv.negative_turn_count == 1


class TestConfigurationRepository:
    """Tests for ConfigurationRepository."""
    
    @pytest.mark.asyncio
    async def test_create_and_get_prompt(self, config_repo):
        """Test creating and retrieving a prompt."""
        prompt = VoicePrompt(
            prompt_id="greeting_hinglish_001",
            state="greeting",
            language="hinglish",
            text="Namaste!"
        )
        await config_repo.create_prompt(prompt)
        
        retrieved_prompt = await config_repo.get_prompt("greeting", "hinglish")
        assert retrieved_prompt is not None
        assert retrieved_prompt.text == "Namaste!"
    
    @pytest.mark.asyncio
    async def test_create_and_get_flow(self, config_repo):
        """Test creating and retrieving a flow."""
        flow = ConversationFlow(
            flow_id="qualification_flow_v1",
            name="Standard Flow",
            states=["greeting", "qualification"]
        )
        await config_repo.create_flow(flow)
        
        retrieved_flow = await config_repo.get_flow("qualification_flow_v1")
        assert retrieved_flow is not None
        assert retrieved_flow.name == "Standard Flow"
        assert len(retrieved_flow.states) == 2
