"""
Unit tests for NLU engine - intent detection and entity extraction.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.nlu_engine import (
    NLUEngine,
    Intent,
    EntityType
)


class TestNLUEngine:
    """Test suite for NLU engine."""
    
    @pytest.fixture
    def nlu_engine(self):
        """Create NLU engine instance with mocked OpenAI."""
        with patch('app.services.nlu_engine.openai'):
            engine = NLUEngine(api_key="test_key", model="gpt-3.5-turbo")
            return engine
    
    # Intent Detection Tests
    
    def test_detect_intent_affirmative_english(self, nlu_engine):
        """Test affirmative intent detection in English."""
        utterances = ["yes", "yeah", "sure", "correct", "right", "okay"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.AFFIRMATIVE
            assert confidence > 0.8
    
    def test_detect_intent_affirmative_hinglish(self, nlu_engine):
        """Test affirmative intent detection in Hinglish."""
        utterances = ["haan", "ha", "bilkul", "yes haan"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.AFFIRMATIVE
            assert confidence > 0.8
    
    def test_detect_intent_negative_english(self, nlu_engine):
        """Test negative intent detection in English."""
        utterances = ["no", "nope", "nah", "not really"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.NEGATIVE
            assert confidence > 0.8
    
    def test_detect_intent_negative_hinglish(self, nlu_engine):
        """Test negative intent detection in Hinglish."""
        utterances = ["nahi", "na", "galat"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.NEGATIVE
            assert confidence > 0.8
    
    def test_detect_intent_request_human(self, nlu_engine):
        """Test human request intent detection."""
        utterances = [
            "I want to speak with a person",
            "connect me to an agent",
            "transfer to human expert",
            "kisi se baat karni hai"
        ]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.REQUEST_HUMAN
            assert confidence > 0.8
    
    def test_detect_intent_clarification(self, nlu_engine):
        """Test clarification needed intent detection."""
        utterances = [
            "what?",
            "pardon",
            "sorry, I didn't understand",
            "can you repeat",
            "samajh nahi aaya"
        ]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.CLARIFICATION_NEEDED
            assert confidence > 0.7
    
    def test_detect_intent_greeting(self, nlu_engine):
        """Test greeting intent detection."""
        utterances = ["hello", "hi", "hey", "namaste", "namaskar"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.GREETING
            assert confidence > 0.8
    
    def test_detect_intent_farewell(self, nlu_engine):
        """Test farewell intent detection."""
        utterances = ["bye", "goodbye", "thank you", "thanks", "dhanyavaad"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.FAREWELL
            assert confidence > 0.8
    
    def test_detect_intent_language_switch(self, nlu_engine):
        """Test language switch intent detection."""
        utterances = [
            "can we speak in English",
            "switch to Hindi",
            "I want to talk in Telugu"
        ]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.LANGUAGE_SWITCH
            assert confidence > 0.8
    
    def test_detect_intent_unknown(self, nlu_engine):
        """Test unknown intent for ambiguous utterances."""
        utterance = "xyz abc random words"
        intent, confidence = nlu_engine._detect_intent_regex(utterance)
        assert intent == Intent.UNKNOWN
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_detect_intent_openai_success(self, nlu_engine):
        """Test intent detection using OpenAI API."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "affirmative|0.95"
        
        with patch('app.services.nlu_engine.openai.ChatCompletion.acreate', 
                   return_value=mock_response):
            intent, confidence = await nlu_engine._detect_intent_openai(
                "I want to apply for a loan"
            )
            
            assert intent == Intent.AFFIRMATIVE
            assert confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_detect_intent_openai_failure(self, nlu_engine):
        """Test intent detection fallback on OpenAI failure."""
        with patch('app.services.nlu_engine.openai.ChatCompletion.acreate',
                   side_effect=Exception("API Error")):
            intent, confidence = await nlu_engine._detect_intent_openai("test")
            
            assert intent == Intent.UNKNOWN
            assert confidence == 0.0
    
    # Entity Extraction Tests
    
    def test_extract_yes_no_entity(self, nlu_engine):
        """Test yes/no entity extraction."""
        # Yes cases
        yes_utterances = ["yes", "haan", "correct", "right"]
        for utterance in yes_utterances:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.YES_NO)
            assert value is True
        
        # No cases
        no_utterances = ["no", "nahi", "nope"]
        for utterance in no_utterances:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.YES_NO)
            assert value is False
    
    def test_extract_loan_amount_lakhs(self, nlu_engine):
        """Test loan amount extraction in lakhs."""
        test_cases = [
            ("I need 20 lakhs", 20.0),
            ("20 lakh loan", 20.0),
            ("around 25L", 25.0),
            ("15.5 lakhs", 15.5)
        ]
        
        for utterance, expected in test_cases:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.LOAN_AMOUNT)
            assert value == expected
    
    def test_extract_loan_amount_dollars(self, nlu_engine):
        """Test loan amount extraction in dollars."""
        test_cases = [
            ("$50000", 50000.0),
            ("$50,000", 50000.0),
            ("50k dollars", 0.5)  # Converts to lakhs
        ]
        
        for utterance, expected in test_cases:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.LOAN_AMOUNT)
            assert value is not None
    
    def test_extract_country_entity(self, nlu_engine):
        """Test country extraction."""
        test_cases = [
            ("I want to study in USA", "USA"),
            ("going to UK", "UK"),
            ("Canada is my choice", "Canada"),
            ("Australia", "Australia")
        ]
        
        for utterance, expected in test_cases:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.COUNTRY)
            assert value == expected
    
    def test_extract_degree_entity(self, nlu_engine):
        """Test degree level extraction."""
        test_cases = [
            ("I'm doing Bachelor's", "Bachelor's"),
            ("pursuing Masters", "Master's"),
            ("PhD program", "PhD"),
            ("undergraduate degree", "Bachelor's"),
            ("postgraduate studies", "Master's")
        ]
        
        for utterance, expected in test_cases:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.DEGREE)
            assert value == expected
    
    def test_extract_language_entity(self, nlu_engine):
        """Test language preference extraction."""
        test_cases = [
            ("speak in English", "english"),
            ("Hindi please", "hinglish"),
            ("Telugu mein baat karo", "telugu")
        ]
        
        for utterance, expected in test_cases:
            value = nlu_engine._extract_entity_regex(utterance, EntityType.LANGUAGE)
            assert value == expected
    
    def test_extract_entity_not_found(self, nlu_engine):
        """Test entity extraction when entity not present."""
        value = nlu_engine._extract_entity_regex(
            "random text",
            EntityType.COUNTRY
        )
        assert value is None
    
    @pytest.mark.asyncio
    async def test_extract_entities_openai_success(self, nlu_engine):
        """Test entity extraction using OpenAI API."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"country": "USA", "degree": "Master\'s"}'
        
        with patch('app.services.nlu_engine.openai.ChatCompletion.acreate',
                   return_value=mock_response):
            entities = await nlu_engine._extract_entities_openai(
                "I want to do Masters in USA",
                [EntityType.COUNTRY, EntityType.DEGREE],
                None
            )
            
            assert entities[EntityType.COUNTRY] == "USA"
            assert entities[EntityType.DEGREE] == "Master's"
    
    @pytest.mark.asyncio
    async def test_extract_entities_openai_failure(self, nlu_engine):
        """Test entity extraction fallback on OpenAI failure."""
        with patch('app.services.nlu_engine.openai.ChatCompletion.acreate',
                   side_effect=Exception("API Error")):
            entities = await nlu_engine._extract_entities_openai(
                "test",
                [EntityType.COUNTRY],
                None
            )
            
            assert entities == {}
    
    @pytest.mark.asyncio
    async def test_extract_entities_combined(self, nlu_engine):
        """Test combined regex and OpenAI entity extraction."""
        # Mock OpenAI for entities not found by regex
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"name": "John Doe"}'
        
        with patch('app.services.nlu_engine.openai.ChatCompletion.acreate',
                   return_value=mock_response):
            entities = await nlu_engine.extract_entities(
                "Yes, I'm John Doe and I want to study in USA",
                [EntityType.YES_NO, EntityType.COUNTRY, EntityType.NAME],
                None
            )
            
            # Regex should find yes/no and country
            assert entities[EntityType.YES_NO] is True
            assert entities[EntityType.COUNTRY] == "USA"
    
    # Confidence Scoring Tests
    
    def test_calculate_confidence_high(self, nlu_engine):
        """Test confidence calculation with high confidence intent."""
        confidence = nlu_engine.calculate_confidence(
            Intent.AFFIRMATIVE,
            {EntityType.COUNTRY: "USA", EntityType.DEGREE: "Master's"},
            [EntityType.COUNTRY, EntityType.DEGREE]
        )
        
        assert confidence > 0.8
    
    def test_calculate_confidence_partial_entities(self, nlu_engine):
        """Test confidence with partial entity extraction."""
        confidence = nlu_engine.calculate_confidence(
            Intent.PROVIDE_INFO,
            {EntityType.COUNTRY: "USA"},
            [EntityType.COUNTRY, EntityType.DEGREE, EntityType.LOAN_AMOUNT]
        )
        
        # Should be lower due to missing entities
        assert 0.4 < confidence < 0.7
    
    def test_calculate_confidence_unknown_intent(self, nlu_engine):
        """Test confidence with unknown intent."""
        confidence = nlu_engine.calculate_confidence(
            Intent.UNKNOWN,
            {},
            []
        )
        
        assert confidence == 0.0
    
    def test_calculate_confidence_no_expected_entities(self, nlu_engine):
        """Test confidence when no entities expected."""
        confidence = nlu_engine.calculate_confidence(
            Intent.AFFIRMATIVE,
            {},
            []
        )
        
        assert confidence == 0.9
    
    # Multilingual Tests
    
    def test_multilingual_hinglish_utterances(self, nlu_engine):
        """Test Hinglish mixed language utterances."""
        test_cases = [
            ("haan, main USA jaana chahta hoon", Intent.AFFIRMATIVE),
            ("nahi, mujhe nahi chahiye", Intent.NEGATIVE),
            ("kisi se baat karni hai", Intent.REQUEST_HUMAN)
        ]
        
        for utterance, expected_intent in test_cases:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == expected_intent
    
    def test_multilingual_entity_extraction(self, nlu_engine):
        """Test entity extraction from multilingual text."""
        # Hinglish with English entities
        utterance = "Main 20 lakh ka loan chahiye USA ke liye"
        
        amount = nlu_engine._extract_entity_regex(utterance, EntityType.LOAN_AMOUNT)
        country = nlu_engine._extract_entity_regex(utterance, EntityType.COUNTRY)
        
        assert amount == 20.0
        assert country == "USA"
    
    # Edge Cases
    
    def test_empty_utterance(self, nlu_engine):
        """Test handling of empty utterance."""
        intent, confidence = nlu_engine._detect_intent_regex("")
        assert intent == Intent.UNKNOWN
        assert confidence == 0.0
    
    def test_very_long_utterance(self, nlu_engine):
        """Test handling of very long utterance."""
        long_utterance = "yes " * 100
        intent, confidence = nlu_engine._detect_intent_regex(long_utterance)
        assert intent == Intent.AFFIRMATIVE
    
    def test_special_characters_in_utterance(self, nlu_engine):
        """Test handling of special characters."""
        utterance = "yes!!! @#$ correct???"
        intent, confidence = nlu_engine._detect_intent_regex(utterance)
        assert intent == Intent.AFFIRMATIVE
    
    def test_case_insensitive_detection(self, nlu_engine):
        """Test case-insensitive intent detection."""
        utterances = ["YES", "Yes", "yes", "YeS"]
        
        for utterance in utterances:
            intent, confidence = nlu_engine._detect_intent_regex(utterance)
            assert intent == Intent.AFFIRMATIVE
