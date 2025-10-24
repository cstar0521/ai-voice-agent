"""
Conversation model for tracking dialogue history and context.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid


class Turn(BaseModel):
    """
    Turn model representing a single exchange in the conversation.
    
    Attributes:
        turn_id: Sequential turn number
        speaker: Who spoke (agent, user)
        text: Transcript of what was said
        audio_url: URL to audio recording of this turn
        timestamp: When this turn occurred
        intent: Detected intent from NLU
        entities: Extracted entities as key-value pairs
        sentiment_score: Sentiment score for this turn
        confidence_score: Confidence score for ASR/NLU
    """
    
    turn_id: int
    speaker: str
    text: str
    audio_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    intent: Optional[str] = None
    entities: dict = Field(default_factory=dict)
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    @field_validator("speaker")
    @classmethod
    def validate_speaker(cls, v: str) -> str:
        """Validate speaker is agent or user."""
        allowed = ["agent", "user"]
        if v.lower() not in allowed:
            raise ValueError(f"Speaker must be one of {allowed}")
        return v.lower()
    
    @field_validator("sentiment_score")
    @classmethod
    def validate_sentiment(cls, v: Optional[float]) -> Optional[float]:
        """Validate sentiment score is between -1 and 1."""
        if v is not None and (v < -1.0 or v > 1.0):
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        return v
    
    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Validate confidence score is between 0 and 1."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class Conversation(BaseModel):
    """
    Conversation model representing the full dialogue context.
    
    Attributes:
        conversation_id: Unique identifier for the conversation
        call_id: Associated call identifier
        lead_id: Associated lead identifier
        language: Language used in conversation
        current_state: Current state in conversation flow
        turns: List of conversation turns
        collected_data: Data collected during conversation
        negative_turn_count: Count of consecutive negative sentiment turns
        clarification_count: Count of clarification requests
        escalation_triggered: Whether escalation was triggered
        created_at: Timestamp when conversation started
        updated_at: Timestamp when conversation was last updated
    """
    
    conversation_id: str = Field(default_factory=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    call_id: str
    lead_id: str
    language: str = "hinglish"
    current_state: str = "greeting"
    turns: list[Turn] = Field(default_factory=list)
    collected_data: dict = Field(default_factory=dict)
    negative_turn_count: int = 0
    clarification_count: int = 0
    escalation_triggered: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is one of supported languages."""
        allowed = ["hinglish", "english", "telugu"]
        if v.lower() not in allowed:
            raise ValueError(f"Language must be one of {allowed}")
        return v.lower()
    
    @field_validator("negative_turn_count", "clarification_count")
    @classmethod
    def validate_counts(cls, v: int) -> int:
        """Validate counts are non-negative."""
        if v < 0:
            raise ValueError("Count must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_def456789012",
                "call_id": "call_xyz987654321",
                "lead_id": "lead_abc123456789",
                "language": "hinglish",
                "current_state": "qualification",
                "turns": [
                    {
                        "turn_id": 1,
                        "speaker": "agent",
                        "text": "Hello! I'm calling from the education loan team.",
                        "timestamp": "2025-10-24T10:30:00Z",
                        "sentiment_score": 0.8
                    },
                    {
                        "turn_id": 2,
                        "speaker": "user",
                        "text": "Yes, I need information about loans.",
                        "timestamp": "2025-10-24T10:30:05Z",
                        "intent": "loan_interest",
                        "sentiment_score": 0.6
                    }
                ],
                "collected_data": {
                    "country": "US",
                    "degree": "masters"
                },
                "negative_turn_count": 0,
                "clarification_count": 0,
                "escalation_triggered": False
            }
        }
