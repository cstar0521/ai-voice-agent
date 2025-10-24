"""
Configuration models for voice prompts and conversation flows.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class VoicePrompt(BaseModel):
    """
    Voice prompt model for storing conversation prompts.
    
    Attributes:
        prompt_id: Unique identifier for the prompt
        state: Conversation state this prompt is for
        language: Language of the prompt
        text: Text content of the prompt
        audio_url: URL to pre-generated TTS audio
        version: Version number for A/B testing and rollback
        is_active: Whether this prompt version is currently active
    """
    
    prompt_id: str
    state: str
    language: str
    text: str
    audio_url: Optional[str] = None
    version: int = 1
    is_active: bool = True
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is one of supported languages."""
        allowed = ["hinglish", "english", "hindi", "telugu", "tamil"]
        if v.lower() not in allowed:
            raise ValueError(f"Language must be one of {allowed}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_id": "greeting_hinglish_001",
                "state": "greeting",
                "language": "hinglish",
                "text": "Namaste! Main education loan team se bol rahi hoon.",
                "audio_url": "https://storage.example.com/prompts/greeting_hinglish.mp3"
            }
        }


class ConversationFlow(BaseModel):
    """
    Conversation flow model defining state transitions.
    
    Attributes:
        flow_id: Unique identifier for the flow
        name: Name of the conversation flow
        states: List of states in the flow
        transitions: State transition mapping
        prompts: State to prompt_id mapping
    """
    
    flow_id: str
    name: str
    states: list[str] = Field(default_factory=list)
    transitions: dict = Field(default_factory=dict)
    prompts: dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "flow_id": "qualification_flow_v1",
                "name": "Standard Qualification Flow",
                "states": [
                    "greeting",
                    "language_detection",
                    "degree_question",
                    "country_question",
                    "qualification",
                    "eligibility_mapping",
                    "handoff_offer"
                ],
                "transitions": {
                    "greeting": "language_detection",
                    "language_detection": "degree_question",
                    "degree_question": "country_question",
                    "country_question": "qualification"
                },
                "prompts": {
                    "greeting": "greeting_hinglish_001",
                    "degree_question": "degree_question_hinglish_001"
                }
            }
        }
