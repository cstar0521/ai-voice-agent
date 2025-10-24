"""
Sentiment Tracker for monitoring emotion trends and triggering escalation.

Tracks sentiment history per conversation and implements escalation logic
based on negative sentiment patterns and aggressive tone detection.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentTracker:
    """
    Tracks sentiment history and manages escalation logic.
    
    Monitors sentiment trends across conversation turns and triggers
    escalation when negative patterns are detected.
    """
    
    # Escalation thresholds
    NEGATIVE_SENTIMENT_THRESHOLD = -0.3
    NEGATIVE_TURN_THRESHOLD = 2
    
    def __init__(self):
        """Initialize sentiment tracker."""
        logger.info("SentimentTracker initialized")
    
    def track_sentiment(
        self,
        conversation_data: Dict[str, Any],
        sentiment_score: float,
        text: str = "",
        aggressive_tone_detected: bool = False
    ) -> Dict[str, Any]:
        """
        Track sentiment for a conversation turn and update counters.
        
        Args:
            conversation_data: Current conversation data with sentiment history
            sentiment_score: Sentiment score for current turn
            text: User's text (for logging)
            aggressive_tone_detected: Whether aggressive/rude tone was detected
            
        Returns:
            Updated conversation data with sentiment tracking
        """
        # Initialize sentiment history if not present
        if "sentiment_history" not in conversation_data:
            conversation_data["sentiment_history"] = []
        
        # Add current sentiment to history
        conversation_data["sentiment_history"].append({
            "score": sentiment_score,
            "timestamp": datetime.utcnow().isoformat(),
            "text_preview": text[:50] if text else "",
            "aggressive_tone": aggressive_tone_detected
        })
        
        # Update negative turn counter
        if sentiment_score < self.NEGATIVE_SENTIMENT_THRESHOLD:
            conversation_data["negative_turn_count"] = conversation_data.get("negative_turn_count", 0) + 1
            logger.info(
                f"Negative sentiment detected: {sentiment_score:.2f}, "
                f"negative_turn_count={conversation_data['negative_turn_count']}"
            )
        else:
            # Reset counter on positive/neutral sentiment
            if conversation_data.get("negative_turn_count", 0) > 0:
                logger.info(
                    f"Sentiment improved: {sentiment_score:.2f}, "
                    f"resetting negative_turn_count"
                )
            conversation_data["negative_turn_count"] = 0
        
        # Track aggressive tone separately
        if aggressive_tone_detected:
            logger.warning(f"Aggressive/rude tone detected in turn")
            conversation_data["aggressive_tone_detected"] = True
        
        return conversation_data
    
    def should_escalate(
        self,
        conversation_data: Dict[str, Any],
        aggressive_tone_detected: bool = False
    ) -> bool:
        """
        Determine if conversation should be escalated to human expert.
        
        Escalation triggers:
        1. Negative turn count >= 2 (two consecutive negative sentiment turns)
        2. Aggressive or rude tone detected
        
        Args:
            conversation_data: Current conversation data
            aggressive_tone_detected: Whether aggressive tone was detected
            
        Returns:
            True if escalation should be triggered
        """
        negative_turn_count = conversation_data.get("negative_turn_count", 0)
        
        # Check if already escalated
        if conversation_data.get("escalation_triggered", False):
            logger.debug("Escalation already triggered")
            return False
        
        # Trigger on aggressive tone
        if aggressive_tone_detected:
            logger.warning("Escalation triggered: aggressive tone detected")
            return True
        
        # Trigger on negative turn threshold
        if negative_turn_count >= self.NEGATIVE_TURN_THRESHOLD:
            logger.warning(
                f"Escalation triggered: negative_turn_count={negative_turn_count} "
                f">= threshold={self.NEGATIVE_TURN_THRESHOLD}"
            )
            return True
        
        return False
    
    def mark_escalation_triggered(
        self,
        conversation_data: Dict[str, Any],
        reason: str = "negative_sentiment"
    ) -> Dict[str, Any]:
        """
        Mark escalation as triggered in conversation data.
        
        Args:
            conversation_data: Current conversation data
            reason: Reason for escalation
            
        Returns:
            Updated conversation data
        """
        conversation_data["escalation_triggered"] = True
        conversation_data["escalation_reason"] = reason
        conversation_data["escalation_timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"Escalation marked: reason={reason}")
        
        return conversation_data
    
    def get_sentiment_summary(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary of sentiment trends for the conversation.
        
        Args:
            conversation_data: Conversation data with sentiment history
            
        Returns:
            Dictionary with sentiment statistics
        """
        sentiment_history = conversation_data.get("sentiment_history", [])
        
        if not sentiment_history:
            return {
                "average_sentiment": 0.0,
                "min_sentiment": 0.0,
                "max_sentiment": 0.0,
                "total_turns": 0,
                "negative_turns": 0,
                "positive_turns": 0,
                "neutral_turns": 0
            }
        
        scores = [entry["score"] for entry in sentiment_history]
        
        average_sentiment = sum(scores) / len(scores)
        min_sentiment = min(scores)
        max_sentiment = max(scores)
        
        negative_turns = sum(1 for score in scores if score < -0.1)
        positive_turns = sum(1 for score in scores if score > 0.1)
        neutral_turns = len(scores) - negative_turns - positive_turns
        
        summary = {
            "average_sentiment": round(average_sentiment, 2),
            "min_sentiment": round(min_sentiment, 2),
            "max_sentiment": round(max_sentiment, 2),
            "total_turns": len(scores),
            "negative_turns": negative_turns,
            "positive_turns": positive_turns,
            "neutral_turns": neutral_turns,
            "current_negative_streak": conversation_data.get("negative_turn_count", 0),
            "escalation_triggered": conversation_data.get("escalation_triggered", False)
        }
        
        logger.debug(f"Sentiment summary: {summary}")
        
        return summary
    
    def get_recent_sentiment_trend(
        self,
        conversation_data: Dict[str, Any],
        last_n_turns: int = 3
    ) -> str:
        """
        Get trend of recent sentiment (improving, declining, stable).
        
        Args:
            conversation_data: Conversation data with sentiment history
            last_n_turns: Number of recent turns to analyze
            
        Returns:
            Trend label (improving, declining, stable, insufficient_data)
        """
        sentiment_history = conversation_data.get("sentiment_history", [])
        
        if len(sentiment_history) < 2:
            return "insufficient_data"
        
        # Get recent scores
        recent_scores = [
            entry["score"]
            for entry in sentiment_history[-last_n_turns:]
        ]
        
        if len(recent_scores) < 2:
            return "insufficient_data"
        
        # Calculate trend
        first_half_avg = sum(recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
        second_half_avg = sum(recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)
        
        difference = second_half_avg - first_half_avg
        
        if difference > 0.2:
            return "improving"
        elif difference < -0.2:
            return "declining"
        else:
            return "stable"
    
    def reset_negative_counter(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reset negative turn counter (e.g., after successful clarification).
        
        Args:
            conversation_data: Current conversation data
            
        Returns:
            Updated conversation data
        """
        conversation_data["negative_turn_count"] = 0
        logger.info("Negative turn counter reset")
        
        return conversation_data
