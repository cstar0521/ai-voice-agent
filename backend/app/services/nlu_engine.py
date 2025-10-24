"""
Natural Language Understanding (NLU) Engine for intent and entity extraction.

Uses OpenAI API for intent classification and entity extraction with
multilingual support (Hinglish, English, Telugu).
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import openai

logger = logging.getLogger(__name__)


class Intent(Enum):
    """User intent types for loan qualification conversation."""
    AFFIRMATIVE = "affirmative"  # Yes, correct, right, haan
    NEGATIVE = "negative"  # No, nahi, wrong
    PROVIDE_INFO = "provide_info"  # Providing requested information
    REQUEST_HUMAN = "request_human"  # Want to speak with person
    CLARIFICATION_NEEDED = "clarification_needed"  # Didn't understand
    GREETING = "greeting"  # Hello, hi, namaste
    FAREWELL = "farewell"  # Bye, goodbye, thank you
    LANGUAGE_SWITCH = "language_switch"  # Want to change language
    UNKNOWN = "unknown"  # Cannot determine intent


class EntityType(Enum):
    """Entity types to extract from user utterances."""
    COUNTRY = "country"  # US, UK, Canada, Australia, etc.
    DEGREE = "degree"  # Bachelor's, Master's, PhD
    LOAN_AMOUNT = "loan_amount"  # Numeric amount in lakhs/dollars
    YES_NO = "yes_no"  # Boolean response
    COLLATERAL = "collateral"  # Property, land, house
    ITR_STATUS = "itr_status"  # ITR availability
    VISA_TIMELINE = "visa_timeline"  # Date or duration
    LANGUAGE = "language"  # Hinglish, English, Telugu
    NAME = "name"  # User's name


class NLUEngine:
    """
    Natural Language Understanding engine for intent and entity extraction.
    
    Uses OpenAI GPT models for multilingual understanding with
    regex-based fallbacks for simple patterns.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize NLU engine.
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        openai.api_key = self.api_key
        
        logger.info(f"NLUEngine initialized with model: {model}")
    
    async def detect_intent(
        self,
        utterance: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Intent, float]:
        """
        Detect user intent from utterance.
        
        Args:
            utterance: User's spoken text
            context: Optional conversation context
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        try:
            # Try regex-based detection first for simple patterns
            regex_intent, confidence = self._detect_intent_regex(utterance)
            if confidence > 0.8:
                logger.info(f"Intent detected via regex: {regex_intent.value} ({confidence})")
                return regex_intent, confidence
            
            # Use OpenAI for complex intent detection
            intent, confidence = await self._detect_intent_openai(utterance, context)
            logger.info(f"Intent detected via OpenAI: {intent.value} ({confidence})")
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return Intent.UNKNOWN, 0.0
    
    def _detect_intent_regex(self, utterance: str) -> Tuple[Intent, float]:
        """
        Detect intent using regex patterns (fast fallback).
        
        Args:
            utterance: User's text
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        utterance_lower = utterance.lower().strip()
        
        # Affirmative patterns
        affirmative_patterns = [
            r'\b(yes|yeah|yep|sure|correct|right|okay|ok|haan|ha|bilkul)\b',
            r'^(y|yes)$'
        ]
        for pattern in affirmative_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.AFFIRMATIVE, 0.9
        
        # Negative patterns
        negative_patterns = [
            r'\b(no|nope|nah|not|nahi|na|galat)\b',
            r'^(n|no)$'
        ]
        for pattern in negative_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.NEGATIVE, 0.9
        
        # Request human patterns
        human_patterns = [
            r'\b(speak|talk|connect|transfer).*(person|human|agent|expert|counselor)\b',
            r'\b(person|human|agent|expert|counselor).*(speak|talk)\b',
            r'\bkisi se baat\b'
        ]
        for pattern in human_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.REQUEST_HUMAN, 0.85
        
        # Clarification patterns
        clarification_patterns = [
            r'\b(what|pardon|sorry|repeat|again|samajh nahi aaya)\b',
            r'\bkya\b.*\?',
            r'\bdobara\b'
        ]
        for pattern in clarification_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.CLARIFICATION_NEEDED, 0.8
        
        # Greeting patterns
        greeting_patterns = [
            r'\b(hello|hi|hey|namaste|namaskar)\b'
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.GREETING, 0.85
        
        # Farewell patterns
        farewell_patterns = [
            r'\b(bye|goodbye|thank you|thanks|dhanyavaad|shukriya)\b'
        ]
        for pattern in farewell_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.FAREWELL, 0.85
        
        # Language switch patterns
        language_patterns = [
            r'\b(english|hindi|telugu|hinglish).*(speak|talk|switch|change)\b',
            r'\b(speak|talk|switch|change).*(english|hindi|telugu|hinglish)\b'
        ]
        for pattern in language_patterns:
            if re.search(pattern, utterance_lower):
                return Intent.LANGUAGE_SWITCH, 0.85
        
        return Intent.UNKNOWN, 0.0
    
    async def _detect_intent_openai(
        self,
        utterance: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Intent, float]:
        """
        Detect intent using OpenAI API.
        
        Args:
            utterance: User's text
            context: Conversation context
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        try:
            # Build context string
            context_str = ""
            if context:
                current_state = context.get("current_state", "")
                context_str = f"Current conversation state: {current_state}\n"
            
            # Create prompt for intent classification
            prompt = f"""{context_str}
User utterance: "{utterance}"

Classify the user's intent into one of these categories:
- affirmative: User agrees or confirms (yes, haan, correct, right)
- negative: User disagrees or denies (no, nahi, wrong)
- provide_info: User is providing requested information
- request_human: User wants to speak with a human agent
- clarification_needed: User didn't understand or needs clarification
- greeting: User is greeting (hello, hi, namaste)
- farewell: User is ending conversation (bye, thank you)
- language_switch: User wants to change language
- unknown: Cannot determine intent

Respond with ONLY the intent category and confidence (0.0-1.0) in format: "intent|confidence"
Example: "affirmative|0.95"
"""
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at understanding user intent in multilingual conversations (English, Hindi, Hinglish, Telugu)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse response
            parts = result.split("|")
            if len(parts) == 2:
                intent_str, confidence_str = parts
                intent = Intent(intent_str.strip().lower())
                confidence = float(confidence_str.strip())
                return intent, confidence
            
            return Intent.UNKNOWN, 0.0
            
        except Exception as e:
            logger.error(f"OpenAI intent detection failed: {str(e)}")
            return Intent.UNKNOWN, 0.0
    
    async def extract_entities(
        self,
        utterance: str,
        expected_entities: List[EntityType],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[EntityType, Any]:
        """
        Extract entities from user utterance.
        
        Args:
            utterance: User's text
            expected_entities: List of entity types to extract
            context: Conversation context
            
        Returns:
            Dictionary mapping entity types to extracted values
        """
        try:
            entities = {}
            
            # Try regex-based extraction first
            for entity_type in expected_entities:
                value = self._extract_entity_regex(utterance, entity_type)
                if value is not None:
                    entities[entity_type] = value
            
            # Use OpenAI for remaining entities
            if len(entities) < len(expected_entities):
                openai_entities = await self._extract_entities_openai(
                    utterance, expected_entities, context
                )
                entities.update(openai_entities)
            
            logger.info(f"Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return {}
    
    def _extract_entity_regex(
        self,
        utterance: str,
        entity_type: EntityType
    ) -> Optional[Any]:
        """
        Extract entity using regex patterns.
        
        Args:
            utterance: User's text
            entity_type: Type of entity to extract
            
        Returns:
            Extracted value or None
        """
        utterance_lower = utterance.lower()
        
        if entity_type == EntityType.YES_NO:
            # Check for yes/no patterns
            if re.search(r'\b(yes|yeah|haan|ha|correct|right)\b', utterance_lower):
                return True
            elif re.search(r'\b(no|nahi|na|nope)\b', utterance_lower):
                return False
        
        elif entity_type == EntityType.LOAN_AMOUNT:
            # Extract numeric amounts
            # Pattern: "20 lakhs", "20 lakh", "20L", "$50000", "50k"
            patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|l)\b',
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*k\b'
            ]
            for pattern in patterns:
                match = re.search(pattern, utterance_lower)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    # Convert to lakhs if in thousands
                    if 'k' in utterance_lower:
                        amount = amount / 100  # Convert thousands to lakhs
                    return amount
        
        elif entity_type == EntityType.COUNTRY:
            # Extract country names
            countries = [
                'usa', 'us', 'united states', 'america',
                'uk', 'united kingdom', 'britain', 'england',
                'canada',
                'australia',
                'germany',
                'ireland',
                'new zealand',
                'singapore',
                'france',
                'netherlands'
            ]
            for country in countries:
                if country in utterance_lower:
                    # Normalize country name
                    if country in ['usa', 'us', 'united states', 'america']:
                        return 'USA'
                    elif country in ['uk', 'united kingdom', 'britain', 'england']:
                        return 'UK'
                    elif country == 'canada':
                        return 'Canada'
                    elif country == 'australia':
                        return 'Australia'
                    elif country == 'germany':
                        return 'Germany'
                    else:
                        return country.title()
        
        elif entity_type == EntityType.DEGREE:
            # Extract degree level
            if re.search(r'\b(bachelor|bachelors|undergraduate|ug|btech|bsc|ba)\b', utterance_lower):
                return "Bachelor's"
            elif re.search(r'\b(master|masters|postgraduate|pg|mtech|msc|ma|mba)\b', utterance_lower):
                return "Master's"
            elif re.search(r'\b(phd|doctorate|doctoral)\b', utterance_lower):
                return "PhD"
        
        elif entity_type == EntityType.LANGUAGE:
            # Extract language preference
            if re.search(r'\b(hindi|hinglish)\b', utterance_lower):
                return "hinglish"
            elif re.search(r'\benglish\b', utterance_lower):
                return "english"
            elif re.search(r'\btelugu\b', utterance_lower):
                return "telugu"
        
        return None
    
    async def _extract_entities_openai(
        self,
        utterance: str,
        expected_entities: List[EntityType],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[EntityType, Any]:
        """
        Extract entities using OpenAI API.
        
        Args:
            utterance: User's text
            expected_entities: Entity types to extract
            context: Conversation context
            
        Returns:
            Dictionary of extracted entities
        """
        try:
            entity_descriptions = {
                EntityType.COUNTRY: "Country of study (e.g., USA, UK, Canada, Australia)",
                EntityType.DEGREE: "Degree level (Bachelor's, Master's, PhD)",
                EntityType.LOAN_AMOUNT: "Loan amount in lakhs or dollars",
                EntityType.YES_NO: "Boolean yes/no response",
                EntityType.COLLATERAL: "Collateral availability or type",
                EntityType.ITR_STATUS: "ITR (Income Tax Return) availability",
                EntityType.VISA_TIMELINE: "Visa deadline or timeline",
                EntityType.LANGUAGE: "Language preference (hinglish, english, telugu)",
                EntityType.NAME: "Person's name"
            }
            
            entities_str = "\n".join([
                f"- {et.value}: {entity_descriptions.get(et, '')}"
                for et in expected_entities
            ])
            
            prompt = f"""User utterance: "{utterance}"

Extract the following entities from the user's response:
{entities_str}

Respond in JSON format with entity names as keys and extracted values as values.
If an entity is not found, omit it from the response.
Example: {{"country": "USA", "degree": "Master's"}}
"""
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from multilingual text (English, Hindi, Hinglish, Telugu)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            entities_dict = json.loads(result)
            
            # Convert to EntityType keys
            entities = {}
            for entity_type in expected_entities:
                if entity_type.value in entities_dict:
                    entities[entity_type] = entities_dict[entity_type.value]
            
            return entities
            
        except Exception as e:
            logger.error(f"OpenAI entity extraction failed: {str(e)}")
            return {}
    
    def calculate_confidence(
        self,
        intent: Intent,
        entities: Dict[EntityType, Any],
        expected_entities: List[EntityType]
    ) -> float:
        """
        Calculate overall confidence score for NLU results.
        
        Args:
            intent: Detected intent
            entities: Extracted entities
            expected_entities: Expected entity types
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from intent
        if intent == Intent.UNKNOWN:
            base_confidence = 0.0
        elif intent in [Intent.AFFIRMATIVE, Intent.NEGATIVE]:
            base_confidence = 0.9
        else:
            base_confidence = 0.7
        
        # Adjust based on entity extraction success
        if expected_entities:
            entity_score = len(entities) / len(expected_entities)
            confidence = (base_confidence * 0.6) + (entity_score * 0.4)
        else:
            confidence = base_confidence
        
        return min(confidence, 1.0)
