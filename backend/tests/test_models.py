"""
Unit tests for data models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.lead import Lead
from app.models.call import Call
from app.models.conversation import Conversation, Turn
from app.models.configuration import VoicePrompt, ConversationFlow


class TestLeadModel:
    """Tests for Lead model validation."""
    
    def test_lead_creation_with_valid_data(self):
        """Test creating a lead with valid data."""
        lead = Lead(
            phone="+919876543210",
            language="hinglish",
            country="US",
            degree="masters",
            loan_amount=5000000.0,
            status="new"
        )
        assert lead.phone == "+919876543210"
        assert lead.language == "hinglish"
        assert lead.degree == "masters"
        assert lead.status == "new"
        assert lead.lead_id.startswith("lead_")
    
    def test_lead_invalid_language(self):
        """Test that invalid language raises validation error."""
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", language="spanish")
    
    def test_lead_invalid_degree(self):
        """Test that invalid degree raises validation error."""
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", degree="phd")
    
    def test_lead_invalid_status(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", status="invalid_status")
    
    def test_lead_invalid_sentiment_score(self):
        """Test that sentiment score outside range raises error."""
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", sentiment_score=1.5)
    
    def test_lead_negative_loan_amount(self):
        """Test that negative loan amount raises error."""
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", loan_amount=-1000)
    
    def test_lead_yes_no_validation(self):
        """Test yes/no field validation."""
        lead = Lead(phone="+919876543210", collateral="yes")
        assert lead.collateral == "yes"
        
        with pytest.raises(ValidationError):
            Lead(phone="+919876543210", collateral="maybe")


class TestCallModel:
    """Tests for Call model validation."""
    
    def test_call_creation_with_valid_data(self):
        """Test creating a call with valid data."""
        call = Call(
            lead_id="lead_abc123",
            direction="outbound",
            status="initiated"
        )
        assert call.lead_id == "lead_abc123"
        assert call.direction == "outbound"
        assert call.status == "initiated"
        assert call.call_id.startswith("call_")
        assert call.retry_count == 0
    
    def test_call_invalid_direction(self):
        """Test that invalid direction raises validation error."""
        with pytest.raises(ValidationError):
            Call(lead_id="lead_abc123", direction="sideways")
    
    def test_call_invalid_status(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError):
            Call(lead_id="lead_abc123", direction="outbound", status="unknown")
    
    def test_call_negative_duration(self):
        """Test that negative duration raises error."""
        with pytest.raises(ValidationError):
            Call(lead_id="lead_abc123", direction="outbound", duration=-10)


class TestConversationModel:
    """Tests for Conversation and Turn models."""
    
    def test_turn_creation(self):
        """Test creating a turn."""
        turn = Turn(
            turn_id=1,
            speaker="agent",
            text="Hello, how can I help you?",
            sentiment_score=0.8
        )
        assert turn.turn_id == 1
        assert turn.speaker == "agent"
        assert turn.sentiment_score == 0.8
    
    def test_turn_invalid_speaker(self):
        """Test that invalid speaker raises error."""
        with pytest.raises(ValidationError):
            Turn(turn_id=1, speaker="robot", text="Hello")
    
    def test_conversation_creation(self):
        """Test creating a conversation."""
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123",
            language="english",
            current_state="greeting"
        )
        assert conversation.call_id == "call_xyz123"
        assert conversation.language == "english"
        assert conversation.current_state == "greeting"
        assert len(conversation.turns) == 0
        assert conversation.negative_turn_count == 0
    
    def test_conversation_with_turns(self):
        """Test conversation with multiple turns."""
        turn1 = Turn(turn_id=1, speaker="agent", text="Hello")
        turn2 = Turn(turn_id=2, speaker="user", text="Hi")
        
        conversation = Conversation(
            call_id="call_xyz123",
            lead_id="lead_abc123",
            turns=[turn1, turn2]
        )
        assert len(conversation.turns) == 2
        assert conversation.turns[0].speaker == "agent"
        assert conversation.turns[1].speaker == "user"


class TestConfigurationModels:
    """Tests for configuration models."""
    
    def test_voice_prompt_creation(self):
        """Test creating a voice prompt."""
        prompt = VoicePrompt(
            prompt_id="greeting_hinglish_001",
            state="greeting",
            language="hinglish",
            text="Namaste! Main education loan team se bol rahi hoon."
        )
        assert prompt.prompt_id == "greeting_hinglish_001"
        assert prompt.state == "greeting"
        assert prompt.language == "hinglish"
    
    def test_conversation_flow_creation(self):
        """Test creating a conversation flow."""
        flow = ConversationFlow(
            flow_id="qualification_flow_v1",
            name="Standard Qualification Flow",
            states=["greeting", "qualification", "handoff"],
            transitions={"greeting": "qualification"}
        )
        assert flow.flow_id == "qualification_flow_v1"
        assert len(flow.states) == 3
        assert flow.transitions["greeting"] == "qualification"
