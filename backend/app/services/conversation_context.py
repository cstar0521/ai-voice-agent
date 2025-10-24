"""
Conversation Context Management for maintaining dialogue state and history.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.services.conversation_state_machine import ConversationState


class Turn(BaseModel):
    """
    Represents a single turn in the conversation.
    """
    turn_id: int
    timestamp: datetime
    speaker: str  # "user" or "agent"
    transcript: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    sentiment_score: Optional[float] = None
    confidence: Optional[float] = None


class ConversationContext(BaseModel):
    """
    Maintains the complete context of a conversation.
    
    This includes the current state, collected data, turn history,
    sentiment tracking, and other metadata needed for conversation management.
    """
    call_id: str
    lead_id: str
    current_state: ConversationState = ConversationState.INITIATED
    language: str = "hinglish"  # hinglish, english, telugu
    
    # Collected lead data
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Conversation history (last 3 minutes)
    turn_history: List[Turn] = Field(default_factory=list)
    
    # Sentiment tracking
    sentiment_history: List[float] = Field(default_factory=list)
    negative_turn_count: int = 0
    
    # Clarification tracking
    clarification_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ConversationState: lambda v: v.value
        }
    
    def add_turn(
        self,
        speaker: str,
        transcript: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        sentiment_score: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> Turn:
        """
        Add a new turn to the conversation history.
        
        Args:
            speaker: "user" or "agent"
            transcript: Text of the utterance
            intent: Detected intent (optional)
            entities: Extracted entities (optional)
            sentiment_score: Sentiment score between -1 and 1 (optional)
            confidence: Confidence score between 0 and 1 (optional)
        
        Returns:
            The created Turn object
        """
        turn = Turn(
            turn_id=len(self.turn_history) + 1,
            timestamp=datetime.utcnow(),
            speaker=speaker,
            transcript=transcript,
            intent=intent,
            entities=entities or {},
            sentiment_score=sentiment_score,
            confidence=confidence
        )
        
        self.turn_history.append(turn)
        self.last_activity = datetime.utcnow()
        
        # Track sentiment if provided
        if sentiment_score is not None:
            self.sentiment_history.append(sentiment_score)
            
            # Update negative turn counter
            if sentiment_score < -0.3:
                self.negative_turn_count += 1
            else:
                # Reset counter on positive/neutral turn
                self.negative_turn_count = 0
        
        # Prune old turns (keep only last 3 minutes)
        self._prune_old_turns()
        
        return turn
    
    def _prune_old_turns(self, window_minutes: int = 3) -> None:
        """
        Remove turns older than the specified window.
        
        Args:
            window_minutes: Number of minutes to keep in history
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        self.turn_history = [
            turn for turn in self.turn_history
            if turn.timestamp >= cutoff_time
        ]
    
    def update_collected_data(self, field: str, value: Any) -> None:
        """
        Update a field in the collected data.
        
        Args:
            field: Field name to update
            value: Value to set
        """
        self.collected_data[field] = value
        self.last_activity = datetime.utcnow()
    
    def get_collected_data(self, field: str) -> Optional[Any]:
        """
        Get a field from collected data.
        
        Args:
            field: Field name to retrieve
        
        Returns:
            Field value if exists, None otherwise
        """
        return self.collected_data.get(field)
    
    def has_collected_data(self, field: str) -> bool:
        """
        Check if a field has been collected.
        
        Args:
            field: Field name to check
        
        Returns:
            True if field exists and is not None, False otherwise
        """
        return field in self.collected_data and self.collected_data[field] is not None
    
    def increment_clarification_count(self) -> int:
        """
        Increment the clarification counter.
        
        Returns:
            Updated clarification count
        """
        self.clarification_count += 1
        self.last_activity = datetime.utcnow()
        return self.clarification_count
    
    def reset_clarification_count(self) -> None:
        """Reset the clarification counter to zero."""
        self.clarification_count = 0
        self.last_activity = datetime.utcnow()
    
    def get_recent_turns(self, count: int = 5) -> List[Turn]:
        """
        Get the most recent N turns.
        
        Args:
            count: Number of recent turns to retrieve
        
        Returns:
            List of recent turns
        """
        return self.turn_history[-count:] if self.turn_history else []
    
    def get_user_turns(self) -> List[Turn]:
        """
        Get all user turns from history.
        
        Returns:
            List of user turns
        """
        return [turn for turn in self.turn_history if turn.speaker == "user"]
    
    def get_agent_turns(self) -> List[Turn]:
        """
        Get all agent turns from history.
        
        Returns:
            List of agent turns
        """
        return [turn for turn in self.turn_history if turn.speaker == "agent"]
    
    def get_average_sentiment(self) -> Optional[float]:
        """
        Calculate average sentiment score from history.
        
        Returns:
            Average sentiment score, or None if no sentiment data
        """
        if not self.sentiment_history:
            return None
        return sum(self.sentiment_history) / len(self.sentiment_history)
    
    def get_recent_sentiment(self, count: int = 3) -> Optional[float]:
        """
        Calculate average sentiment from recent turns.
        
        Args:
            count: Number of recent turns to consider
        
        Returns:
            Average recent sentiment, or None if insufficient data
        """
        if not self.sentiment_history:
            return None
        recent = self.sentiment_history[-count:]
        return sum(recent) / len(recent) if recent else None
    
    def should_escalate_sentiment(self, threshold: int = 2) -> bool:
        """
        Check if conversation should be escalated based on negative sentiment.
        
        Args:
            threshold: Number of consecutive negative turns to trigger escalation
        
        Returns:
            True if escalation is recommended, False otherwise
        """
        return self.negative_turn_count >= threshold
    
    def should_escalate_clarification(self, threshold: int = 2) -> bool:
        """
        Check if conversation should be escalated based on clarification count.
        
        Args:
            threshold: Number of clarifications to trigger escalation
        
        Returns:
            True if escalation is recommended, False otherwise
        """
        return self.clarification_count > threshold
    
    def is_stale(self, timeout_minutes: int = 5) -> bool:
        """
        Check if conversation has been inactive for too long.
        
        Args:
            timeout_minutes: Minutes of inactivity to consider stale
        
        Returns:
            True if conversation is stale, False otherwise
        """
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_activity > timeout
    
    def get_conversation_duration(self) -> timedelta:
        """
        Get the total duration of the conversation.
        
        Returns:
            Duration as timedelta
        """
        return datetime.utcnow() - self.created_at
    
    def to_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the conversation for handoff or logging.
        
        Returns:
            Dictionary containing conversation summary
        """
        return {
            "call_id": self.call_id,
            "lead_id": self.lead_id,
            "language": self.language,
            "current_state": self.current_state,
            "collected_data": self.collected_data,
            "turn_count": len(self.turn_history),
            "average_sentiment": self.get_average_sentiment(),
            "negative_turn_count": self.negative_turn_count,
            "clarification_count": self.clarification_count,
            "duration_seconds": self.get_conversation_duration().total_seconds(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }


class ConversationContextManager:
    """
    Manager for loading, saving, and managing conversation contexts.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self._contexts: Dict[str, ConversationContext] = {}
    
    def create_context(
        self,
        call_id: str,
        lead_id: str,
        language: str = "hinglish",
        initial_state: ConversationState = ConversationState.INITIATED
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            call_id: Unique call identifier
            lead_id: Unique lead identifier
            language: Initial language preference
            initial_state: Initial conversation state
        
        Returns:
            Created ConversationContext
        """
        context = ConversationContext(
            call_id=call_id,
            lead_id=lead_id,
            language=language,
            current_state=initial_state
        )
        self._contexts[call_id] = context
        return context
    
    def get_context(self, call_id: str) -> Optional[ConversationContext]:
        """
        Get an existing conversation context.
        
        Args:
            call_id: Call identifier
        
        Returns:
            ConversationContext if exists, None otherwise
        """
        return self._contexts.get(call_id)
    
    def update_context(self, call_id: str, context: ConversationContext) -> None:
        """
        Update a conversation context.
        
        Args:
            call_id: Call identifier
            context: Updated context
        """
        self._contexts[call_id] = context
    
    def delete_context(self, call_id: str) -> bool:
        """
        Delete a conversation context.
        
        Args:
            call_id: Call identifier
        
        Returns:
            True if deleted, False if not found
        """
        if call_id in self._contexts:
            del self._contexts[call_id]
            return True
        return False
    
    def list_active_contexts(self) -> List[str]:
        """
        List all active conversation context IDs.
        
        Returns:
            List of call IDs
        """
        return list(self._contexts.keys())
    
    def cleanup_stale_contexts(self, timeout_minutes: int = 10) -> int:
        """
        Remove stale conversation contexts.
        
        Args:
            timeout_minutes: Minutes of inactivity to consider stale
        
        Returns:
            Number of contexts removed
        """
        stale_ids = [
            call_id for call_id, context in self._contexts.items()
            if context.is_stale(timeout_minutes)
        ]
        
        for call_id in stale_ids:
            del self._contexts[call_id]
        
        return len(stale_ids)
