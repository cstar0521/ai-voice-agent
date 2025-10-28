"""
Lead model for storing student/professional information.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid


class Lead(BaseModel):
    """
    Lead model representing a potential customer seeking education loan.
    
    Attributes:
        lead_id: Unique identifier for the lead
        name: Full name of the lead
        phone: Contact phone number
        language: Preferred language (hinglish, english, telugu)
        country: Country of study
        degree: Degree level (bachelors, masters, mba)
        loan_amount: Requested loan amount
        offer_letter: Whether lead has offer letter (yes, no)
        coapplicant_itr: Whether co-applicant has ITR (yes, no)
        collateral: Whether collateral is available (yes, no)
        visa_timeline: Timeline for visa (e.g., "30 days", "2 months")
        eligibility_category: Loan category (public_secured, private_unsecured, intl_usd, escalate)
        sentiment_score: Overall sentiment score from conversation
        urgency: Urgency level (high, medium, low)
        status: Lead status (new, qualified, handoff, callback, unreachable, converted)
        lead_source: Source of the lead (e.g., facebook_ad, website)
        created_at: Timestamp when lead was created
        updated_at: Timestamp when lead was last updated
        metadata: Additional metadata as key-value pairs
    """
    
    lead_id: str = Field(default_factory=lambda: f"lead_{uuid.uuid4().hex[:12]}")
    name: Optional[str] = None
    phone: str
    language: str = "hinglish"
    country: Optional[str] = None
    degree: Optional[str] = None
    loan_amount: Optional[float] = None
    offer_letter: Optional[str] = None
    coapplicant_itr: Optional[str] = None
    collateral: Optional[str] = None
    visa_timeline: Optional[str] = None
    eligibility_category: Optional[str] = None
    sentiment_score: Optional[float] = None
    urgency: Optional[str] = None
    status: str = "new"
    lead_source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is one of supported languages."""
        # Map common language variations
        language_map = {
            "hindi": "hinglish",
            "hinglish": "hinglish", 
            "english": "english",
            "telugu": "telugu",
            "hi": "hinglish",
            "en": "english",
            "te": "telugu",
            "hi-in": "hinglish",
            "en-in": "english", 
            "te-in": "telugu"
        }
        
        normalized = v.lower().replace("-", "").replace("_", "")
        mapped_language = language_map.get(normalized)
        
        if mapped_language:
            return mapped_language
        
        allowed = ["hinglish", "english", "telugu"]
        raise ValueError(f"Language must be one of {allowed} (got: {v})")
    
    @field_validator("degree")
    @classmethod
    def validate_degree(cls, v: Optional[str]) -> Optional[str]:
        """Validate degree is one of supported types."""
        if v is None:
            return v
        allowed = ["bachelors", "masters", "mba"]
        if v.lower() not in allowed:
            raise ValueError(f"Degree must be one of {allowed}")
        return v.lower()
    
    @field_validator("offer_letter", "coapplicant_itr", "collateral")
    @classmethod
    def validate_yes_no(cls, v: Optional[str]) -> Optional[str]:
        """Validate yes/no fields."""
        if v is None:
            return v
        allowed = ["yes", "no"]
        if v.lower() not in allowed:
            raise ValueError(f"Value must be 'yes' or 'no'")
        return v.lower()
    
    @field_validator("eligibility_category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate eligibility category."""
        if v is None:
            return v
        allowed = ["public_secured", "private_unsecured", "intl_usd", "escalate"]
        if v.lower() not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v.lower()
    
    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: Optional[str]) -> Optional[str]:
        """Validate urgency level."""
        if v is None:
            return v
        allowed = ["high", "medium", "low"]
        if v.lower() not in allowed:
            raise ValueError(f"Urgency must be one of {allowed}")
        return v.lower()
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate lead status."""
        allowed = ["new", "qualified", "handoff", "callback", "unreachable", "converted"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.lower()
    
    @field_validator("sentiment_score")
    @classmethod
    def validate_sentiment(cls, v: Optional[float]) -> Optional[float]:
        """Validate sentiment score is between -1 and 1."""
        if v is not None and (v < -1.0 or v > 1.0):
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        return v
    
    @field_validator("loan_amount")
    @classmethod
    def validate_loan_amount(cls, v: Optional[float]) -> Optional[float]:
        """Validate loan amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Loan amount must be positive")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "lead_abc123456789",
                "name": "John Doe",
                "phone": "+919876543210",
                "language": "hinglish",
                "country": "US",
                "degree": "masters",
                "loan_amount": 5000000.0,
                "offer_letter": "yes",
                "coapplicant_itr": "yes",
                "collateral": "no",
                "visa_timeline": "45 days",
                "eligibility_category": "private_unsecured",
                "sentiment_score": 0.7,
                "urgency": "medium",
                "status": "qualified",
                "lead_source": "facebook_ad"
            }
        }
