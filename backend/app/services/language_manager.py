"""
Language Manager for handling language detection and switching.
"""
from typing import Optional, Tuple
import re

from app.services.conversation_context import ConversationContext


class LanguageManager:
    """
    Manages language detection and switching during conversations.
    
    Supports three languages: Hinglish, English, and Telugu.
    """
    
    SUPPORTED_LANGUAGES = ["hinglish", "english", "telugu"]
    DEFAULT_LANGUAGE = "hinglish"
    FALLBACK_LANGUAGE = "english"
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        "hinglish": [
            r"\b(hindi|hinglish|हिंदी|हिन्दी)\b",
            r"\b(haan|nahi|kya|aap|main|mujhe|chahiye)\b",
            r"\b(theek|achha|bilkul|samajh)\b"
        ],
        "english": [
            r"\b(english|angrezi)\b",
            r"\b(yes|no|what|you|me|need|want)\b",
            r"\b(okay|alright|understand|got it)\b"
        ],
        "telugu": [
            r"\b(telugu|తెలుగు)\b",
            r"\b(avunu|kaadu|emi|meeru|nenu|kavali)\b",
            r"\b(sare|artham|bagundi)\b"
        ]
    }
    
    # Explicit language switch requests
    SWITCH_REQUESTS = {
        "hinglish": [
            "hindi mein bolo",
            "hindi please",
            "hinglish mein",
            "can you speak in hindi",
            "hindi lo matladandi"
        ],
        "english": [
            "english mein bolo",
            "english please",
            "speak in english",
            "can you speak in english",
            "english lo matladandi"
        ],
        "telugu": [
            "telugu mein bolo",
            "telugu please",
            "telugu lo matladandi",
            "can you speak in telugu"
        ]
    }
    
    def __init__(self):
        """Initialize language manager."""
        pass
    
    def detect_language(
        self,
        utterance: str,
        current_language: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Detect language from user utterance.
        
        Args:
            utterance: User's spoken text
            current_language: Current conversation language (optional)
        
        Returns:
            Tuple of (detected_language, confidence_score)
        """
        utterance_lower = utterance.lower()
        
        # Check for explicit language switch requests first
        for lang, patterns in self.SWITCH_REQUESTS.items():
            for pattern in patterns:
                if pattern in utterance_lower:
                    return lang, 1.0
        
        # Count pattern matches for each language
        scores = {}
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, utterance_lower, re.IGNORECASE))
                score += matches
            scores[lang] = score
        
        # Get language with highest score
        if max(scores.values()) > 0:
            detected_lang = max(scores, key=scores.get)
            # Calculate confidence based on score
            total_matches = sum(scores.values())
            confidence = scores[detected_lang] / total_matches if total_matches > 0 else 0.0
            return detected_lang, confidence
        
        # If no patterns matched, return current language or default
        return current_language or self.DEFAULT_LANGUAGE, 0.5
    
    def should_switch_language(
        self,
        utterance: str,
        current_language: str,
        asr_confidence: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if language should be switched based on utterance and ASR confidence.
        
        Args:
            utterance: User's spoken text
            current_language: Current conversation language
            asr_confidence: ASR confidence score (0-1)
        
        Returns:
            Tuple of (should_switch, new_language)
        """
        # Check for explicit switch request
        detected_lang, detection_confidence = self.detect_language(utterance, current_language)
        
        # Switch if explicit request detected with high confidence
        if detection_confidence >= 0.8 and detected_lang != current_language:
            return True, detected_lang
        
        # Switch to fallback if ASR confidence is very low
        if asr_confidence < 0.6 and current_language != self.FALLBACK_LANGUAGE:
            return True, self.FALLBACK_LANGUAGE
        
        return False, None
    
    def switch_language(
        self,
        context: ConversationContext,
        new_language: str
    ) -> bool:
        """
        Switch conversation language.
        
        Args:
            context: Conversation context to update
            new_language: Target language
        
        Returns:
            True if switch was successful, False otherwise
        """
        if new_language not in self.SUPPORTED_LANGUAGES:
            return False
        
        old_language = context.language
        context.language = new_language
        
        # Add metadata about language switch
        if "language_switches" not in context.metadata:
            context.metadata["language_switches"] = []
        
        context.metadata["language_switches"].append({
            "from": old_language,
            "to": new_language,
            "turn": len(context.turn_history)
        })
        
        return True
    
    def get_language_name(self, language_code: str, in_language: str) -> str:
        """
        Get the name of a language in another language.
        
        Args:
            language_code: Language code to get name for
            in_language: Language to return the name in
        
        Returns:
            Language name string
        """
        names = {
            "hinglish": {
                "hinglish": "Hinglish",
                "english": "English",
                "telugu": "Telugu"
            },
            "english": {
                "hinglish": "Hinglish",
                "english": "English",
                "telugu": "Telugu"
            },
            "telugu": {
                "hinglish": "Hinglish",
                "english": "English",
                "telugu": "Telugu"
            }
        }
        
        return names.get(in_language, {}).get(language_code, language_code)
    
    def validate_language(self, language: str) -> bool:
        """
        Validate if language is supported.
        
        Args:
            language: Language code to validate
        
        Returns:
            True if supported, False otherwise
        """
        return language in self.SUPPORTED_LANGUAGES
    
    def get_language_stats(self, context: ConversationContext) -> dict:
        """
        Get statistics about language usage in conversation.
        
        Args:
            context: Conversation context
        
        Returns:
            Dictionary with language statistics
        """
        switches = context.metadata.get("language_switches", [])
        
        return {
            "current_language": context.language,
            "switch_count": len(switches),
            "languages_used": list(set(
                [context.language] + [s["to"] for s in switches]
            ))
        }
