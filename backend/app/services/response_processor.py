"""
Response Processor for handling user utterances and extracting information.
"""
from typing import Dict, Optional, Any, Tuple
import re

from app.services.conversation_state_machine import ConversationState
from app.services.conversation_context import ConversationContext
from app.services.nlu_engine import NLUEngine, Intent, EntityType


class ResponseProcessor:
    """
    Processes user responses and extracts relevant information based on conversation state.
    """
    
    def __init__(self, nlu_engine: NLUEngine):
        """
        Initialize response processor with NLU engine.
        
        Args:
            nlu_engine: NLU engine for intent and entity extraction
        """
        self.nlu_engine = nlu_engine
    
    async def process_response(
        self,
        utterance: str,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        Process user utterance based on current conversation state.
        
        Args:
            utterance: User's spoken text
            context: Current conversation context
        
        Returns:
            Dictionary containing:
                - intent: Detected intent
                - entities: Extracted entities
                - confidence: Confidence score
                - next_state: Recommended next state
                - needs_clarification: Whether clarification is needed
        """
        current_state = context.current_state
        
        # Detect intent
        intent, intent_confidence = await self.nlu_engine.detect_intent(
            utterance,
            context.language
        )
        
        # Check for handoff request
        if intent == Intent.REQUEST_HUMAN:
            return {
                "intent": intent,
                "entities": {},
                "confidence": intent_confidence,
                "next_state": ConversationState.HANDOFF_OFFER,
                "needs_clarification": False
            }
        
        # Process based on current state
        if current_state in [
            ConversationState.GREETING,
            ConversationState.QUALIFICATION_START
        ]:
            return await self._process_affirmative_negative(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.LANGUAGE_DETECTION:
            return await self._process_language_selection(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.COLLECT_DEGREE:
            return await self._process_degree(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.COLLECT_COUNTRY:
            return await self._process_country(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.COLLECT_OFFER_LETTER:
            return await self._process_yes_no(
                utterance, intent, intent_confidence, context, "offer_letter"
            )
        
        elif current_state == ConversationState.COLLECT_LOAN_AMOUNT:
            return await self._process_loan_amount(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.COLLECT_ITR:
            return await self._process_yes_no(
                utterance, intent, intent_confidence, context, "coapplicant_itr"
            )
        
        elif current_state == ConversationState.COLLECT_COLLATERAL:
            return await self._process_yes_no(
                utterance, intent, intent_confidence, context, "collateral"
            )
        
        elif current_state == ConversationState.COLLECT_VISA_TIMELINE:
            return await self._process_visa_timeline(
                utterance, intent, intent_confidence, context
            )
        
        elif current_state == ConversationState.HANDOFF_OFFER:
            return await self._process_handoff_response(
                utterance, intent, intent_confidence, context
            )
        
        # Default: unclear state
        return {
            "intent": intent,
            "entities": {},
            "confidence": 0.0,
            "next_state": current_state,
            "needs_clarification": True
        }
    
    async def _process_affirmative_negative(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process affirmative/negative responses."""
        if intent == Intent.AFFIRMATIVE and confidence > 0.6:
            next_state = ConversationState.COLLECT_DEGREE
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": next_state,
                "needs_clarification": False
            }
        elif intent == Intent.NEGATIVE and confidence > 0.6:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": ConversationState.ENDING,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_language_selection(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process language selection."""
        # Extract language from utterance
        language = self._detect_language_preference(utterance)
        
        if language:
            return {
                "intent": Intent.PROVIDE_INFO,
                "entities": {"language": language},
                "confidence": 0.9,
                "next_state": ConversationState.QUALIFICATION_START,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": {},
                "confidence": 0.0,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_degree(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process degree information."""
        entities = await self.nlu_engine.extract_entities(
            utterance,
            [EntityType.DEGREE],
            context.language
        )
        
        degree = entities.get(EntityType.DEGREE)
        
        if degree and degree.lower() in ["bachelors", "masters", "mba"]:
            return {
                "intent": Intent.PROVIDE_INFO,
                "entities": {"degree": degree.lower()},
                "confidence": 0.9,
                "next_state": ConversationState.COLLECT_COUNTRY,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": entities,
                "confidence": 0.0,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_country(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process country information."""
        entities = await self.nlu_engine.extract_entities(
            utterance,
            [EntityType.COUNTRY],
            context.language
        )
        
        country = entities.get(EntityType.COUNTRY)
        
        if country:
            return {
                "intent": Intent.PROVIDE_INFO,
                "entities": {"country": country.upper()},
                "confidence": 0.9,
                "next_state": ConversationState.COLLECT_OFFER_LETTER,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": entities,
                "confidence": 0.0,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_yes_no(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext,
        field_name: str
    ) -> Dict[str, Any]:
        """Process yes/no responses."""
        if intent == Intent.AFFIRMATIVE and confidence > 0.6:
            value = "yes"
        elif intent == Intent.NEGATIVE and confidence > 0.6:
            value = "no"
        else:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": context.current_state,
                "needs_clarification": True
            }
        
        # Determine next state based on field
        state_map = {
            "offer_letter": ConversationState.COLLECT_LOAN_AMOUNT,
            "coapplicant_itr": ConversationState.COLLECT_COLLATERAL,
            "collateral": ConversationState.COLLECT_VISA_TIMELINE
        }
        
        next_state = state_map.get(field_name, context.current_state)
        
        return {
            "intent": intent,
            "entities": {field_name: value},
            "confidence": confidence,
            "next_state": next_state,
            "needs_clarification": False
        }
    
    async def _process_loan_amount(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process loan amount information."""
        entities = await self.nlu_engine.extract_entities(
            utterance,
            [EntityType.LOAN_AMOUNT],
            context.language
        )
        
        loan_amount = entities.get(EntityType.LOAN_AMOUNT)
        
        if loan_amount and isinstance(loan_amount, (int, float)) and loan_amount > 0:
            return {
                "intent": Intent.PROVIDE_INFO,
                "entities": {"loan_amount": float(loan_amount)},
                "confidence": 0.9,
                "next_state": ConversationState.COLLECT_ITR,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": entities,
                "confidence": 0.0,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_visa_timeline(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process visa timeline information."""
        entities = await self.nlu_engine.extract_entities(
            utterance,
            [EntityType.VISA_TIMELINE],
            context.language
        )
        
        visa_timeline = entities.get(EntityType.VISA_TIMELINE)
        
        if visa_timeline:
            return {
                "intent": Intent.PROVIDE_INFO,
                "entities": {"visa_timeline": visa_timeline},
                "confidence": 0.9,
                "next_state": ConversationState.ELIGIBILITY_MAPPING,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": entities,
                "confidence": 0.0,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    async def _process_handoff_response(
        self,
        utterance: str,
        intent: Intent,
        confidence: float,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process handoff offer response."""
        if intent == Intent.AFFIRMATIVE and confidence > 0.6:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": ConversationState.HANDOFF_ACCEPTED,
                "needs_clarification": False
            }
        elif intent == Intent.NEGATIVE and confidence > 0.6:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": ConversationState.HANDOFF_DECLINED,
                "needs_clarification": False
            }
        else:
            return {
                "intent": intent,
                "entities": {},
                "confidence": confidence,
                "next_state": context.current_state,
                "needs_clarification": True
            }
    
    def _detect_language_preference(self, utterance: str) -> Optional[str]:
        """
        Detect language preference from utterance.
        
        Args:
            utterance: User utterance
        
        Returns:
            Language code or None
        """
        utterance_lower = utterance.lower()
        
        # Hinglish patterns
        if any(word in utterance_lower for word in ["hindi", "hinglish", "हिंदी"]):
            return "hinglish"
        
        # English patterns
        if any(word in utterance_lower for word in ["english", "angrezi"]):
            return "english"
        
        # Telugu patterns
        if any(word in utterance_lower for word in ["telugu", "తెలుగు"]):
            return "telugu"
        
        return None
    
    def validate_entity(
        self,
        entity_type: str,
        value: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate extracted entity value.
        
        Args:
            entity_type: Type of entity
            value: Entity value to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if entity_type == "degree":
            if value.lower() in ["bachelors", "masters", "mba"]:
                return True, None
            return False, "Degree must be Bachelors, Masters, or MBA"
        
        elif entity_type == "country":
            if value and len(value) >= 2:
                return True, None
            return False, "Please provide a valid country name"
        
        elif entity_type == "loan_amount":
            if isinstance(value, (int, float)) and value > 0:
                return True, None
            return False, "Loan amount must be a positive number"
        
        elif entity_type in ["offer_letter", "coapplicant_itr", "collateral"]:
            if value.lower() in ["yes", "no"]:
                return True, None
            return False, "Please answer yes or no"
        
        elif entity_type == "visa_timeline":
            if value and len(value) > 0:
                return True, None
            return False, "Please provide a valid timeline"
        
        return True, None
