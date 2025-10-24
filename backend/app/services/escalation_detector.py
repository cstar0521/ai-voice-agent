"""
Escalation Detector for identifying when to transfer calls to human experts.
"""
from typing import Dict, List, Optional
from enum import Enum

from app.services.conversation_context import ConversationContext
from app.services.nlu_engine import Intent


class EscalationReason(str, Enum):
    """Reasons for escalating a conversation."""
    EXPLICIT_REQUEST = "explicit_request"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    CLARIFICATION_THRESHOLD = "clarification_threshold"
    AGGRESSIVE_TONE = "aggressive_tone"
    COMPLEX_QUERY = "complex_query"
    SYSTEM_ERROR = "system_error"


class EscalationDetector:
    """
    Detects when a conversation should be escalated to a human expert.
    
    Monitors multiple signals including sentiment, clarification count,
    explicit requests, and aggressive tone.
    """
    
    # Thresholds for escalation
    NEGATIVE_SENTIMENT_THRESHOLD = 2  # Consecutive negative turns
    CLARIFICATION_THRESHOLD = 2  # Number of clarifications
    SENTIMENT_SCORE_THRESHOLD = -0.3  # Sentiment score below this is negative
    
    # Aggressive/rude keywords
    AGGRESSIVE_KEYWORDS = {
        "hinglish": [
            "stupid", "bewakoof", "pagal", "useless", "faltu",
            "waste", "bakwas", "nonsense", "shut up", "chup"
        ],
        "english": [
            "stupid", "idiot", "useless", "waste", "nonsense",
            "shut up", "ridiculous", "pathetic", "terrible"
        ],
        "telugu": [
            "stupid", "waste", "useless", "nonsense",
            "buddi ledu", "pani ledu"
        ]
    }
    
    def __init__(self):
        """Initialize escalation detector."""
        pass
    
    def should_escalate(
        self,
        context: ConversationContext,
        current_intent: Optional[Intent] = None,
        current_utterance: Optional[str] = None
    ) -> tuple[bool, Optional[EscalationReason], Optional[str]]:
        """
        Determine if conversation should be escalated.
        
        Args:
            context: Current conversation context
            current_intent: Most recent detected intent
            current_utterance: Most recent user utterance
        
        Returns:
            Tuple of (should_escalate, reason, explanation)
        """
        # Check for explicit handoff request
        if current_intent == Intent.REQUEST_HUMAN:
            return True, EscalationReason.EXPLICIT_REQUEST, "User requested to speak with human expert"
        
        # Check for negative sentiment threshold
        if context.should_escalate_sentiment(self.NEGATIVE_SENTIMENT_THRESHOLD):
            return True, EscalationReason.NEGATIVE_SENTIMENT, f"Negative sentiment detected for {context.negative_turn_count} consecutive turns"
        
        # Check for clarification threshold
        if context.should_escalate_clarification(self.CLARIFICATION_THRESHOLD):
            return True, EscalationReason.CLARIFICATION_THRESHOLD, f"Clarification requested {context.clarification_count} times"
        
        # Check for aggressive tone
        if current_utterance:
            is_aggressive, keywords = self._detect_aggressive_tone(
                current_utterance,
                context.language
            )
            if is_aggressive:
                return True, EscalationReason.AGGRESSIVE_TONE, f"Aggressive tone detected: {', '.join(keywords)}"
        
        return False, None, None
    
    def _detect_aggressive_tone(
        self,
        utterance: str,
        language: str
    ) -> tuple[bool, List[str]]:
        """
        Detect aggressive or rude tone in utterance.
        
        Args:
            utterance: User utterance
            language: Conversation language
        
        Returns:
            Tuple of (is_aggressive, matched_keywords)
        """
        utterance_lower = utterance.lower()
        keywords = self.AGGRESSIVE_KEYWORDS.get(language, self.AGGRESSIVE_KEYWORDS["english"])
        
        matched = [kw for kw in keywords if kw in utterance_lower]
        
        return len(matched) > 0, matched
    
    def get_escalation_priority(
        self,
        reason: EscalationReason
    ) -> str:
        """
        Get priority level for escalation.
        
        Args:
            reason: Escalation reason
        
        Returns:
            Priority level: "high", "medium", or "low"
        """
        high_priority = {
            EscalationReason.AGGRESSIVE_TONE,
            EscalationReason.SYSTEM_ERROR
        }
        
        medium_priority = {
            EscalationReason.NEGATIVE_SENTIMENT,
            EscalationReason.EXPLICIT_REQUEST
        }
        
        if reason in high_priority:
            return "high"
        elif reason in medium_priority:
            return "medium"
        else:
            return "low"
    
    def get_escalation_message(
        self,
        reason: EscalationReason,
        language: str
    ) -> str:
        """
        Get appropriate message for escalation based on reason.
        
        Args:
            reason: Escalation reason
            language: Conversation language
        
        Returns:
            Escalation message string
        """
        messages = {
            EscalationReason.EXPLICIT_REQUEST: {
                "hinglish": "Bilkul! Main aapko abhi expert se connect karti hoon.",
                "english": "Absolutely! I'll connect you with an expert right away.",
                "telugu": "Avunu! Nenu mimmalini expert tho ippude connect chestanu."
            },
            EscalationReason.NEGATIVE_SENTIMENT: {
                "hinglish": "Main samajh sakti hoon ki aap frustrated feel kar rahe hain. Chaliye main aapko expert se connect karti hoon.",
                "english": "I understand you might be feeling frustrated. Let me connect you with an expert.",
                "telugu": "Meeru frustrated ga feel avutunnaru ani naku artham aindi. Nenu mimmalini expert tho connect chestanu."
            },
            EscalationReason.CLARIFICATION_THRESHOLD: {
                "hinglish": "Main samajh sakti hoon ki yeh thoda confusing ho sakta hai. Chaliye main aapko expert se connect karti hoon jo better explain kar sakenge.",
                "english": "I understand this might be a bit confusing. Let me connect you with an expert who can explain better.",
                "telugu": "Idi konchem confusing ga undavachu ani naku artham aindi. Nenu mimmalini expert tho connect chestanu, varu better explain chestaru."
            },
            EscalationReason.AGGRESSIVE_TONE: {
                "hinglish": "Main aapki frustration samajh sakti hoon. Chaliye main aapko expert se connect karti hoon.",
                "english": "I understand your frustration. Let me connect you with an expert.",
                "telugu": "Mee frustration naku artham aindi. Nenu mimmalini expert tho connect chestanu."
            },
            EscalationReason.COMPLEX_QUERY: {
                "hinglish": "Yeh query thodi complex hai. Chaliye main aapko expert se connect karti hoon jo isme better help kar sakenge.",
                "english": "This query is a bit complex. Let me connect you with an expert who can help better.",
                "telugu": "Ee query konchem complex undi. Nenu mimmalini expert tho connect chestanu, varu better help chestaru."
            },
            EscalationReason.SYSTEM_ERROR: {
                "hinglish": "Mujhe kuch technical issue aa raha hai. Chaliye main aapko expert se connect karti hoon.",
                "english": "I'm experiencing some technical issues. Let me connect you with an expert.",
                "telugu": "Naku konni technical issues vastunnai. Nenu mimmalini expert tho connect chestanu."
            }
        }
        
        reason_messages = messages.get(reason, messages[EscalationReason.EXPLICIT_REQUEST])
        return reason_messages.get(language, reason_messages["english"])
    
    def log_escalation(
        self,
        context: ConversationContext,
        reason: EscalationReason,
        explanation: str
    ) -> None:
        """
        Log escalation event in conversation context.
        
        Args:
            context: Conversation context
            reason: Escalation reason
            explanation: Detailed explanation
        """
        if "escalations" not in context.metadata:
            context.metadata["escalations"] = []
        
        context.metadata["escalations"].append({
            "reason": reason,
            "explanation": explanation,
            "turn": len(context.turn_history),
            "negative_turn_count": context.negative_turn_count,
            "clarification_count": context.clarification_count,
            "average_sentiment": context.get_average_sentiment()
        })
    
    def get_escalation_summary(
        self,
        context: ConversationContext
    ) -> Dict:
        """
        Get summary of escalation events in conversation.
        
        Args:
            context: Conversation context
        
        Returns:
            Dictionary with escalation summary
        """
        escalations = context.metadata.get("escalations", [])
        
        return {
            "escalation_count": len(escalations),
            "escalations": escalations,
            "current_negative_turns": context.negative_turn_count,
            "current_clarifications": context.clarification_count,
            "average_sentiment": context.get_average_sentiment()
        }
