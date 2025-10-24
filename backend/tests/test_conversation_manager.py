"""
Unit tests for Conversation Manager components.
"""
import pytest
from datetime import datetime, timedelta

from app.services.conversation_state_machine import (
    ConversationState,
    ConversationStateMachine,
    StateTransitionError
)
from app.services.conversation_context import (
    ConversationContext,
    ConversationContextManager,
    Turn
)
from app.services.prompt_generator import PromptGenerator
from app.services.language_manager import LanguageManager
from app.services.escalation_detector import (
    EscalationDetector,
    EscalationReason
)


class TestConversationStateMachine:
    """Test suite for conversation state machine."""
    
    @pytest.fixture
    def state_machine(self):
        """Create state machine instance."""
        return ConversationStateMachine()
    
    def test_initial_state(self, state_machine):
        """Test state machine starts in INITIATED state."""
        assert state_machine.current_state == ConversationState.INITIATED
        assert len(state_machine.state_history) == 1
    
    def test_valid_transition(self, state_machine):
        """Test valid state transition."""
        state_machine.transition_to(ConversationState.GREETING, "test")
        assert state_machine.current_state == ConversationState.GREETING
        assert len(state_machine.state_history) == 2
    
    def test_invalid_transition(self, state_machine):
        """Test invalid state transition raises error."""
        with pytest.raises(StateTransitionError):
            state_machine.transition_to(ConversationState.COMPLETED, "invalid")
    
    def test_can_transition_to(self, state_machine):
        """Test checking if transition is valid."""
        assert state_machine.can_transition_to(ConversationState.GREETING)
        assert not state_machine.can_transition_to(ConversationState.COMPLETED)
    
    def test_is_terminal(self, state_machine):
        """Test terminal state detection."""
        assert not state_machine.is_terminal()
        state_machine.transition_to(ConversationState.GREETING)
        state_machine.transition_to(ConversationState.USER_HANGUP)
        assert state_machine.is_terminal()
    
    def test_is_data_collection(self, state_machine):
        """Test data collection state detection."""
        assert not state_machine.is_data_collection()
        state_machine.transition_to(ConversationState.GREETING)
        state_machine.transition_to(ConversationState.LANGUAGE_DETECTION)
        state_machine.transition_to(ConversationState.QUALIFICATION_START)
        state_machine.transition_to(ConversationState.COLLECT_DEGREE)
        assert state_machine.is_data_collection()
    
    def test_get_next_collection_state(self, state_machine):
        """Test getting next collection state in sequence."""
        state_machine.transition_to(ConversationState.GREETING)
        state_machine.transition_to(ConversationState.LANGUAGE_DETECTION)
        state_machine.transition_to(ConversationState.QUALIFICATION_START)
        state_machine.transition_to(ConversationState.COLLECT_DEGREE)
        
        next_state = state_machine.get_next_collection_state()
        assert next_state == ConversationState.COLLECT_COUNTRY
    
    def test_state_history(self, state_machine):
        """Test state history tracking."""
        state_machine.transition_to(ConversationState.GREETING, "greeting")
        state_machine.transition_to(ConversationState.LANGUAGE_DETECTION, "detect")
        
        history = state_machine.get_state_history()
        assert len(history) == 3
        assert history[1]["to_state"] == ConversationState.GREETING
        assert history[1]["reason"] == "greeting"


class TestConversationContext:
    """Test suite for conversation context."""
    
    @pytest.fixture
    def context(self):
        """Create conversation context instance."""
        return ConversationContext(
            call_id="test_call_123",
            lead_id="test_lead_456",
            language="hinglish"
        )
    
    def test_initial_context(self, context):
        """Test initial context state."""
        assert context.call_id == "test_call_123"
        assert context.lead_id == "test_lead_456"
        assert context.language == "hinglish"
        assert context.current_state == ConversationState.INITIATED
        assert len(context.turn_history) == 0
    
    def test_add_turn(self, context):
        """Test adding turns to conversation."""
        turn = context.add_turn(
            speaker="user",
            transcript="Hello",
            sentiment_score=0.5
        )
        
        assert turn.speaker == "user"
        assert turn.transcript == "Hello"
        assert turn.sentiment_score == 0.5
        assert len(context.turn_history) == 1
        assert len(context.sentiment_history) == 1
    
    def test_negative_turn_counter(self, context):
        """Test negative turn counter increments."""
        context.add_turn("user", "I'm frustrated", sentiment_score=-0.5)
        assert context.negative_turn_count == 1
        
        context.add_turn("user", "This is terrible", sentiment_score=-0.6)
        assert context.negative_turn_count == 2
        
        # Positive turn resets counter
        context.add_turn("user", "Okay thanks", sentiment_score=0.3)
        assert context.negative_turn_count == 0
    
    def test_update_collected_data(self, context):
        """Test updating collected data."""
        context.update_collected_data("degree", "masters")
        assert context.get_collected_data("degree") == "masters"
        assert context.has_collected_data("degree")
    
    def test_clarification_count(self, context):
        """Test clarification counter."""
        assert context.clarification_count == 0
        context.increment_clarification_count()
        assert context.clarification_count == 1
        context.reset_clarification_count()
        assert context.clarification_count == 0
    
    def test_get_recent_turns(self, context):
        """Test getting recent turns."""
        for i in range(10):
            context.add_turn("user", f"Turn {i}")
        
        recent = context.get_recent_turns(3)
        assert len(recent) == 3
        assert recent[-1].transcript == "Turn 9"
    
    def test_get_average_sentiment(self, context):
        """Test average sentiment calculation."""
        context.add_turn("user", "Good", sentiment_score=0.5)
        context.add_turn("user", "Bad", sentiment_score=-0.5)
        context.add_turn("user", "Okay", sentiment_score=0.0)
        
        avg = context.get_average_sentiment()
        assert avg == 0.0
    
    def test_should_escalate_sentiment(self, context):
        """Test sentiment escalation detection."""
        assert not context.should_escalate_sentiment()
        
        context.add_turn("user", "Bad", sentiment_score=-0.5)
        context.add_turn("user", "Worse", sentiment_score=-0.6)
        
        assert context.should_escalate_sentiment(threshold=2)
    
    def test_should_escalate_clarification(self, context):
        """Test clarification escalation detection."""
        assert not context.should_escalate_clarification()
        
        context.increment_clarification_count()
        context.increment_clarification_count()
        context.increment_clarification_count()
        
        assert context.should_escalate_clarification(threshold=2)
    
    def test_to_summary(self, context):
        """Test conversation summary generation."""
        context.add_turn("user", "Hello", sentiment_score=0.5)
        context.update_collected_data("degree", "masters")
        
        summary = context.to_summary()
        assert summary["call_id"] == "test_call_123"
        assert summary["turn_count"] == 1
        assert summary["collected_data"]["degree"] == "masters"


class TestConversationContextManager:
    """Test suite for conversation context manager."""
    
    @pytest.fixture
    def manager(self):
        """Create context manager instance."""
        return ConversationContextManager()
    
    def test_create_context(self, manager):
        """Test creating new context."""
        context = manager.create_context("call_1", "lead_1", "english")
        assert context.call_id == "call_1"
        assert context.language == "english"
    
    def test_get_context(self, manager):
        """Test retrieving context."""
        manager.create_context("call_1", "lead_1")
        context = manager.get_context("call_1")
        assert context is not None
        assert context.call_id == "call_1"
    
    def test_delete_context(self, manager):
        """Test deleting context."""
        manager.create_context("call_1", "lead_1")
        assert manager.delete_context("call_1")
        assert manager.get_context("call_1") is None
    
    def test_list_active_contexts(self, manager):
        """Test listing active contexts."""
        manager.create_context("call_1", "lead_1")
        manager.create_context("call_2", "lead_2")
        
        active = manager.list_active_contexts()
        assert len(active) == 2
        assert "call_1" in active
        assert "call_2" in active


class TestPromptGenerator:
    """Test suite for prompt generator."""
    
    @pytest.fixture
    def generator(self):
        """Create prompt generator instance."""
        return PromptGenerator()
    
    def test_generate_greeting_prompt(self, generator):
        """Test generating greeting prompt."""
        prompt = generator.generate_prompt(
            ConversationState.GREETING,
            "hinglish"
        )
        assert "Namaste" in prompt
        assert "EduLoan" in prompt
    
    def test_generate_prompt_all_languages(self, generator):
        """Test prompt generation for all languages."""
        for lang in ["hinglish", "english", "telugu"]:
            prompt = generator.generate_prompt(
                ConversationState.GREETING,
                lang
            )
            assert len(prompt) > 0
    
    def test_generate_clarification_prompt(self, generator):
        """Test clarification prompt generation."""
        prompt = generator.generate_clarification_prompt("english")
        assert "sorry" in prompt.lower()
        assert "understand" in prompt.lower()
    
    def test_generate_silence_prompt(self, generator):
        """Test silence prompt generation."""
        prompt = generator.generate_silence_prompt("hinglish")
        assert len(prompt) > 0
    
    def test_generate_negative_sentiment_prompt(self, generator):
        """Test negative sentiment prompt generation."""
        prompt = generator.generate_negative_sentiment_prompt("english")
        assert "frustrated" in prompt.lower()
    
    def test_generate_language_switch_confirmation(self, generator):
        """Test language switch confirmation."""
        prompt = generator.generate_language_switch_confirmation(
            "english",
            "hinglish"
        )
        assert len(prompt) > 0
    
    def test_generate_data_confirmation(self, generator):
        """Test data confirmation prompt."""
        prompt = generator.generate_data_confirmation(
            "degree",
            "masters",
            "english"
        )
        assert "masters" in prompt.lower()


class TestLanguageManager:
    """Test suite for language manager."""
    
    @pytest.fixture
    def manager(self):
        """Create language manager instance."""
        return LanguageManager()
    
    def test_detect_language_hinglish(self, manager):
        """Test Hinglish language detection."""
        lang, conf = manager.detect_language("haan main chahta hoon")
        assert lang == "hinglish"
        assert conf > 0.0
    
    def test_detect_language_english(self, manager):
        """Test English language detection."""
        lang, conf = manager.detect_language("yes I want to know")
        assert lang == "english"
        assert conf > 0.0
    
    def test_detect_explicit_switch_request(self, manager):
        """Test explicit language switch request."""
        lang, conf = manager.detect_language("english please")
        assert lang == "english"
        assert conf == 1.0
    
    def test_should_switch_language(self, manager):
        """Test language switch detection."""
        should_switch, new_lang = manager.should_switch_language(
            "english mein bolo",
            "hinglish",
            0.9
        )
        assert should_switch
        assert new_lang == "english"
    
    def test_switch_language(self, manager):
        """Test switching language in context."""
        context = ConversationContext(
            call_id="test",
            lead_id="test",
            language="hinglish"
        )
        
        success = manager.switch_language(context, "english")
        assert success
        assert context.language == "english"
        assert len(context.metadata.get("language_switches", [])) == 1
    
    def test_validate_language(self, manager):
        """Test language validation."""
        assert manager.validate_language("hinglish")
        assert manager.validate_language("english")
        assert manager.validate_language("telugu")
        assert not manager.validate_language("french")


class TestEscalationDetector:
    """Test suite for escalation detector."""
    
    @pytest.fixture
    def detector(self):
        """Create escalation detector instance."""
        return EscalationDetector()
    
    @pytest.fixture
    def context(self):
        """Create conversation context for testing."""
        return ConversationContext(
            call_id="test",
            lead_id="test",
            language="english"
        )
    
    def test_no_escalation_needed(self, detector, context):
        """Test no escalation when conditions not met."""
        should_escalate, reason, explanation = detector.should_escalate(context)
        assert not should_escalate
        assert reason is None
    
    def test_escalate_negative_sentiment(self, detector, context):
        """Test escalation due to negative sentiment."""
        context.add_turn("user", "Bad", sentiment_score=-0.5)
        context.add_turn("user", "Worse", sentiment_score=-0.6)
        
        should_escalate, reason, explanation = detector.should_escalate(context)
        assert should_escalate
        assert reason == EscalationReason.NEGATIVE_SENTIMENT
    
    def test_escalate_clarification_threshold(self, detector, context):
        """Test escalation due to clarification threshold."""
        context.increment_clarification_count()
        context.increment_clarification_count()
        context.increment_clarification_count()
        
        should_escalate, reason, explanation = detector.should_escalate(context)
        assert should_escalate
        assert reason == EscalationReason.CLARIFICATION_THRESHOLD
    
    def test_escalate_aggressive_tone(self, detector, context):
        """Test escalation due to aggressive tone."""
        should_escalate, reason, explanation = detector.should_escalate(
            context,
            current_utterance="This is stupid and useless"
        )
        assert should_escalate
        assert reason == EscalationReason.AGGRESSIVE_TONE
    
    def test_get_escalation_priority(self, detector):
        """Test escalation priority levels."""
        assert detector.get_escalation_priority(
            EscalationReason.AGGRESSIVE_TONE
        ) == "high"
        assert detector.get_escalation_priority(
            EscalationReason.NEGATIVE_SENTIMENT
        ) == "medium"
    
    def test_get_escalation_message(self, detector):
        """Test escalation message generation."""
        message = detector.get_escalation_message(
            EscalationReason.EXPLICIT_REQUEST,
            "english"
        )
        assert len(message) > 0
        assert "expert" in message.lower()
    
    def test_log_escalation(self, detector, context):
        """Test logging escalation event."""
        detector.log_escalation(
            context,
            EscalationReason.NEGATIVE_SENTIMENT,
            "Test escalation"
        )
        
        assert "escalations" in context.metadata
        assert len(context.metadata["escalations"]) == 1
