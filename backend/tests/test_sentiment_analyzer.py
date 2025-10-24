"""
Unit tests for sentiment analyzer and sentiment tracker.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.sentiment_tracker import SentimentTracker


class TestSentimentAnalyzer:
    """Test suite for sentiment analyzer."""
    
    @pytest.fixture
    def sentiment_analyzer(self):
        """Create sentiment analyzer instance."""
        with patch('app.services.sentiment_analyzer.openai'):
            analyzer = SentimentAnalyzer(api_key="test_key", model="gpt-3.5-turbo")
            return analyzer
    
    def test_positive_sentiment_english(self, sentiment_analyzer):
        """Test positive sentiment detection in English."""
        positive_texts = [
            "I'm very happy with this service",
            "This is great, thank you so much",
            "Excellent information, very helpful",
            "Perfect, exactly what I needed"
        ]
        
        for text in positive_texts:
            score = sentiment_analyzer._analyze_textblob(text)
            assert score > 0.1, f"Expected positive sentiment for: {text}"
    
    def test_negative_sentiment_english(self, sentiment_analyzer):
        """Test negative sentiment detection in English."""
        negative_texts = [
            "I'm very frustrated with this",
            "This is terrible and confusing",
            "I'm angry and upset",
            "This is a waste of time"
        ]
        
        for text in negative_texts:
            score = sentiment_analyzer._analyze_textblob(text)
            assert score < -0.1, f"Expected negative sentiment for: {text}"

    def test_neutral_sentiment_english(self, sentiment_analyzer):
        """Test neutral sentiment detection in English."""
        neutral_texts = [
            "I need information about loans",
            "What are the requirements",
            "Can you tell me more",
            "I'm looking for education loan"
        ]
        
        for text in neutral_texts:
            score = sentiment_analyzer._analyze_textblob(text)
            assert -0.2 <= score <= 0.2, f"Expected neutral sentiment for: {text}"
    
    def test_frustration_keywords_english(self, sentiment_analyzer):
        """Test frustration keyword detection in English."""
        frustration_texts = [
            "I don't understand this at all",
            "This is not clear to me",
            "I'm confused about the process",
            "This is a waste of my time"
        ]
        
        for text in frustration_texts:
            detected = sentiment_analyzer.detect_frustration_keywords(text, "english")
            assert detected, f"Expected frustration detection for: {text}"
    
    def test_frustration_keywords_hinglish(self, sentiment_analyzer):
        """Test frustration keyword detection in Hinglish."""
        frustration_texts = [
            "Samajh nahi aa raha hai",
            "Main confuse ho gaya hoon",
            "Bahut pareshan kar diya",
            "Time waste ho raha hai"
        ]
        
        for text in frustration_texts:
            detected = sentiment_analyzer.detect_frustration_keywords(text, "hinglish")
            assert detected, f"Expected frustration detection for: {text}"
    
    def test_no_frustration_keywords(self, sentiment_analyzer):
        """Test that normal text doesn't trigger frustration detection."""
        normal_texts = [
            "I want to apply for a loan",
            "Tell me about the process",
            "What documents do I need",
            "Thank you for the information"
        ]
        
        for text in normal_texts:
            detected = sentiment_analyzer.detect_frustration_keywords(text, "english")
            assert not detected, f"Unexpected frustration detection for: {text}"
    
    def test_aggressive_tone_english(self, sentiment_analyzer):
        """Test aggressive tone detection in English."""
        aggressive_texts = [
            "Shut up and listen",
            "You're an idiot",
            "Stop calling me",
            "This is harassment"
        ]
        
        for text in aggressive_texts:
            detected = sentiment_analyzer.detect_aggressive_tone(text, "english")
            assert detected, f"Expected aggressive tone detection for: {text}"
    
    def test_aggressive_tone_hinglish(self, sentiment_analyzer):
        """Test aggressive tone detection in Hinglish."""
        aggressive_texts = [
            "Chup raho",
            "Bewakoof ho kya",
            "Phone mat karo mujhe",
            "Ye fraud hai"
        ]
        
        for text in aggressive_texts:
            detected = sentiment_analyzer.detect_aggressive_tone(text, "hinglish")
            assert detected, f"Expected aggressive tone detection for: {text}"

    def test_no_aggressive_tone(self, sentiment_analyzer):
        """Test that normal text doesn't trigger aggressive detection."""
        normal_texts = [
            "I need help with my application",
            "Can you explain this again",
            "I'm not sure about this",
            "Please call me later"
        ]
        
        for text in normal_texts:
            detected = sentiment_analyzer.detect_aggressive_tone(text, "english")
            assert not detected, f"Unexpected aggressive detection for: {text}"
    
    def test_keyword_analysis_frustration(self, sentiment_analyzer):
        """Test keyword-based sentiment for frustration."""
        text = "I'm confused and frustrated"
        score = sentiment_analyzer._analyze_keywords(text, "english")
        assert score < -0.3, "Expected negative score for frustration keywords"
    
    def test_keyword_analysis_aggressive(self, sentiment_analyzer):
        """Test keyword-based sentiment for aggressive tone."""
        text = "Shut up you idiot"
        score = sentiment_analyzer._analyze_keywords(text, "english")
        assert score < -0.8, "Expected very negative score for aggressive keywords"
    
    def test_keyword_analysis_neutral(self, sentiment_analyzer):
        """Test keyword-based sentiment for neutral text."""
        text = "I want to apply for a loan"
        score = sentiment_analyzer._analyze_keywords(text, "english")
        assert score == 0.0, "Expected neutral score for normal text"
    
    def test_sentiment_labels(self, sentiment_analyzer):
        """Test sentiment label generation."""
        assert sentiment_analyzer.get_sentiment_label(-0.8) == "very_negative"
        assert sentiment_analyzer.get_sentiment_label(-0.3) == "negative"
        assert sentiment_analyzer.get_sentiment_label(0.0) == "neutral"
        assert sentiment_analyzer.get_sentiment_label(0.3) == "positive"
        assert sentiment_analyzer.get_sentiment_label(0.8) == "very_positive"
    
    def test_is_negative_sentiment(self, sentiment_analyzer):
        """Test negative sentiment threshold check."""
        assert sentiment_analyzer.is_negative_sentiment(-0.5) is True
        assert sentiment_analyzer.is_negative_sentiment(-0.3) is False
        assert sentiment_analyzer.is_negative_sentiment(-0.31) is True
        assert sentiment_analyzer.is_negative_sentiment(0.0) is False
        assert sentiment_analyzer.is_negative_sentiment(0.5) is False


class TestSentimentTracker:
    """Test suite for sentiment tracker."""
    
    @pytest.fixture
    def sentiment_tracker(self):
        """Create sentiment tracker instance."""
        return SentimentTracker()
    
    @pytest.fixture
    def conversation_data(self):
        """Create sample conversation data."""
        return {
            "conversation_id": "conv_123",
            "call_id": "call_456",
            "sentiment_history": [],
            "negative_turn_count": 0,
            "escalation_triggered": False
        }
    
    def test_track_positive_sentiment(self, sentiment_tracker, conversation_data):
        """Test tracking positive sentiment."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=0.7,
            text="This is great, thank you"
        )
        
        assert len(updated["sentiment_history"]) == 1
        assert updated["sentiment_history"][0]["score"] == 0.7
        assert updated["negative_turn_count"] == 0

    def test_track_negative_sentiment(self, sentiment_tracker, conversation_data):
        """Test tracking negative sentiment."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.5,
            text="I'm frustrated"
        )
        
        assert len(updated["sentiment_history"]) == 1
        assert updated["sentiment_history"][0]["score"] == -0.5
        assert updated["negative_turn_count"] == 1
    
    def test_track_consecutive_negative_sentiment(self, sentiment_tracker, conversation_data):
        """Test tracking consecutive negative sentiment turns."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.4,
            text="I'm confused"
        )
        assert updated["negative_turn_count"] == 1
        
        updated = sentiment_tracker.track_sentiment(
            updated,
            sentiment_score=-0.5,
            text="This is frustrating"
        )
        assert updated["negative_turn_count"] == 2
    
    def test_reset_negative_counter_on_positive(self, sentiment_tracker, conversation_data):
        """Test that negative counter resets on positive sentiment."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.4,
            text="I'm confused"
        )
        assert updated["negative_turn_count"] == 1
        
        updated = sentiment_tracker.track_sentiment(
            updated,
            sentiment_score=0.5,
            text="Oh I understand now"
        )
        assert updated["negative_turn_count"] == 0
    
    def test_track_aggressive_tone(self, sentiment_tracker, conversation_data):
        """Test tracking aggressive tone."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.8,
            text="Shut up",
            aggressive_tone_detected=True
        )
        
        assert updated["aggressive_tone_detected"] is True
        assert updated["sentiment_history"][0]["aggressive_tone"] is True
    
    def test_escalation_on_negative_threshold(self, sentiment_tracker, conversation_data):
        """Test escalation trigger on negative turn threshold."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.4,
            text="I'm confused"
        )
        assert not sentiment_tracker.should_escalate(updated)
        
        updated = sentiment_tracker.track_sentiment(
            updated,
            sentiment_score=-0.5,
            text="This is frustrating"
        )
        assert sentiment_tracker.should_escalate(updated)
    
    def test_escalation_on_aggressive_tone(self, sentiment_tracker, conversation_data):
        """Test escalation trigger on aggressive tone."""
        should_escalate = sentiment_tracker.should_escalate(
            conversation_data,
            aggressive_tone_detected=True
        )
        assert should_escalate
    
    def test_no_escalation_on_single_negative(self, sentiment_tracker, conversation_data):
        """Test no escalation on single negative turn."""
        updated = sentiment_tracker.track_sentiment(
            conversation_data,
            sentiment_score=-0.4,
            text="I'm a bit confused"
        )
        assert not sentiment_tracker.should_escalate(updated)
    
    def test_mark_escalation_triggered(self, sentiment_tracker, conversation_data):
        """Test marking escalation as triggered."""
        updated = sentiment_tracker.mark_escalation_triggered(
            conversation_data,
            reason="negative_sentiment"
        )
        
        assert updated["escalation_triggered"] is True
        assert updated["escalation_reason"] == "negative_sentiment"
        assert "escalation_timestamp" in updated
