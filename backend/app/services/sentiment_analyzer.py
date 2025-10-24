"""
Sentiment Analyzer for real-time emotion detection in voice conversations.

Implements multiple approaches:
1. TextBlob-based sentiment for English
2. OpenAI-based sentiment for Hinglish/Telugu
3. Keyword-based frustration detection
4. Combined scoring: 70% ML + 30% keywords
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from textblob import TextBlob
import openai
import re

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Multi-approach sentiment analyzer for multilingual conversations.
    
    Combines ML-based sentiment analysis with keyword-based frustration
    detection to provide robust emotion tracking across languages.
    """
    
    # Frustration keywords by language
    FRUSTRATION_KEYWORDS = {
        "english": [
            "frustrated", "annoyed", "irritated", "angry", "upset",
            "confused", "don't understand", "not clear", "unclear",
            "waste of time", "useless", "stupid", "ridiculous",
            "fed up", "enough", "stop", "leave me alone"
        ],
        "hinglish": [
            "samajh nahi aa raha", "confuse ho gaya", "pareshan",
            "gussa", "thak gaya", "bore ho gaya", "time waste",
            "kya bakwas", "band karo", "chodo", "nahi chahiye"
        ],
        "telugu": [
            "artham kavatledu", "confused", "badha", "kopam",
            "bore", "waste", "aapandi", "vaddu"
        ]
    }
    
    # Aggressive/rude tone keywords
    AGGRESSIVE_KEYWORDS = {
        "english": [
            "shut up", "idiot", "stupid", "dumb", "moron",
            "get lost", "go away", "leave me", "don't call",
            "harassment", "spam", "scam"
        ],
        "hinglish": [
            "chup", "bewakoof", "pagal", "bhag jao",
            "phone mat karo", "pareshan mat karo", "fraud"
        ],
        "telugu": [
            "moham muyyi", "buddhi leni", "vellipo",
            "phone cheyaku", "fraud"
        ]
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize sentiment analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model: OpenAI model to use for non-English sentiment
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided, will use TextBlob only")
        else:
            openai.api_key = self.api_key
        
        logger.info("SentimentAnalyzer initialized")
    
    async def analyze_sentiment(
        self,
        text: str,
        language: str = "english"
    ) -> float:
        """
        Analyze sentiment of text with combined approach.
        
        Combines ML-based sentiment (70%) with keyword-based detection (30%)
        for robust emotion tracking.
        
        Args:
            text: User's utterance
            language: Language of the text (english, hinglish, telugu)
            
        Returns:
            Sentiment score from -1.0 (very negative) to +1.0 (very positive)
        """
        try:
            # Get ML-based sentiment
            if language == "english":
                ml_score = self._analyze_textblob(text)
            else:
                ml_score = await self._analyze_openai(text, language)
            
            # Get keyword-based sentiment
            keyword_score = self._analyze_keywords(text, language)
            
            # Combine scores: 70% ML + 30% keywords
            combined_score = (ml_score * 0.7) + (keyword_score * 0.3)
            
            # Clamp to [-1.0, 1.0]
            combined_score = max(-1.0, min(1.0, combined_score))
            
            logger.info(
                f"Sentiment analysis: ML={ml_score:.2f}, "
                f"Keywords={keyword_score:.2f}, "
                f"Combined={combined_score:.2f}"
            )
            
            return combined_score
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return 0.0  # Neutral on error
    
    def _analyze_textblob(self, text: str) -> float:
        """
        Analyze sentiment using TextBlob (for English).
        
        Args:
            text: English text
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        try:
            blob = TextBlob(text)
            # TextBlob polarity is already in [-1, 1] range
            polarity = blob.sentiment.polarity
            
            logger.debug(f"TextBlob sentiment: {polarity:.2f}")
            return polarity
            
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {str(e)}")
            return 0.0
    
    async def _analyze_openai(self, text: str, language: str) -> float:
        """
        Analyze sentiment using OpenAI API (for Hinglish/Telugu).
        
        Args:
            text: User's text
            language: Language of the text
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        if not self.api_key:
            logger.warning("OpenAI API key not available, returning neutral sentiment")
            return 0.0
        
        try:
            prompt = f"""Analyze the sentiment of the following {language} text.

Text: "{text}"

Respond with ONLY a sentiment score from -1.0 (very negative) to +1.0 (very positive).
Consider:
- -1.0 to -0.5: Very negative (angry, frustrated, upset)
- -0.5 to -0.1: Slightly negative (disappointed, confused)
- -0.1 to +0.1: Neutral
- +0.1 to +0.5: Slightly positive (satisfied, calm)
- +0.5 to +1.0: Very positive (happy, excited, grateful)

Respond with only the number, nothing else.
Example: -0.7
"""
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing sentiment in multilingual text, especially Hinglish (Hindi-English mix) and Telugu."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the score
            score = float(result)
            
            # Clamp to valid range
            score = max(-1.0, min(1.0, score))
            
            logger.debug(f"OpenAI sentiment: {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"OpenAI sentiment analysis failed: {str(e)}")
            return 0.0
    
    def _analyze_keywords(self, text: str, language: str) -> float:
        """
        Analyze sentiment using keyword matching.
        
        Args:
            text: User's text
            language: Language of the text
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        text_lower = text.lower()
        
        # Check for frustration keywords
        frustration_keywords = self.FRUSTRATION_KEYWORDS.get(language, [])
        frustration_count = sum(
            1 for keyword in frustration_keywords
            if keyword in text_lower
        )
        
        # Check for aggressive keywords
        aggressive_keywords = self.AGGRESSIVE_KEYWORDS.get(language, [])
        aggressive_count = sum(
            1 for keyword in aggressive_keywords
            if keyword in text_lower
        )
        
        # Calculate keyword-based score
        if aggressive_count > 0:
            # Aggressive tone is very negative
            score = -0.9
        elif frustration_count >= 2:
            # Multiple frustration keywords
            score = -0.7
        elif frustration_count == 1:
            # Single frustration keyword
            score = -0.4
        else:
            # No negative keywords, assume neutral
            score = 0.0
        
        logger.debug(
            f"Keyword analysis: frustration={frustration_count}, "
            f"aggressive={aggressive_count}, score={score:.2f}"
        )
        
        return score
    
    def is_negative_sentiment(self, score: float) -> bool:
        """
        Check if sentiment score indicates negative emotion.
        
        Args:
            score: Sentiment score
            
        Returns:
            True if sentiment is negative (< -0.3)
        """
        return score < -0.3
    
    def detect_frustration_keywords(
        self,
        text: str,
        language: str = "english"
    ) -> bool:
        """
        Detect if text contains frustration keywords.
        
        Args:
            text: User's text
            language: Language of the text
            
        Returns:
            True if frustration keywords detected
        """
        text_lower = text.lower()
        
        frustration_keywords = self.FRUSTRATION_KEYWORDS.get(language, [])
        
        for keyword in frustration_keywords:
            if keyword in text_lower:
                logger.info(f"Frustration keyword detected: {keyword}")
                return True
        
        return False
    
    def detect_aggressive_tone(
        self,
        text: str,
        language: str = "english"
    ) -> bool:
        """
        Detect if text contains aggressive or rude tone.
        
        Args:
            text: User's text
            language: Language of the text
            
        Returns:
            True if aggressive tone detected
        """
        text_lower = text.lower()
        
        aggressive_keywords = self.AGGRESSIVE_KEYWORDS.get(language, [])
        
        for keyword in aggressive_keywords:
            if keyword in text_lower:
                logger.warning(f"Aggressive keyword detected: {keyword}")
                return True
        
        return False
    
    def get_sentiment_label(self, score: float) -> str:
        """
        Get human-readable label for sentiment score.
        
        Args:
            score: Sentiment score
            
        Returns:
            Label (very_negative, negative, neutral, positive, very_positive)
        """
        if score <= -0.5:
            return "very_negative"
        elif score <= -0.1:
            return "negative"
        elif score <= 0.1:
            return "neutral"
        elif score <= 0.5:
            return "positive"
        else:
            return "very_positive"
