"""
Call model for tracking call metadata and status.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid


class Call(BaseModel):
    """
    Call model representing a phone call session.
    
    Attributes:
        call_id: Unique identifier for the call
        lead_id: Associated lead identifier
        call_sid: Twilio call SID
        direction: Call direction (inbound, outbound)
        status: Call status (initiated, connected, in_progress, completed, failed, no_answer)
        start_time: When the call started
        end_time: When the call ended
        duration: Call duration in seconds
        recording_url: URL to call recording
        transcript_url: URL to call transcript
        consent_given: Whether user gave recording consent
        retry_count: Number of retry attempts
        error_reason: Reason for call failure
        created_at: Timestamp when call record was created
    """
    
    call_id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    lead_id: str
    call_sid: Optional[str] = None
    direction: str
    status: str = "initiated"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcript_url: Optional[str] = None
    consent_given: bool = False
    retry_count: int = 0
    error_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate call direction."""
        allowed = ["inbound", "outbound"]
        if v.lower() not in allowed:
            raise ValueError(f"Direction must be one of {allowed}")
        return v.lower()
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate call status."""
        allowed = ["initiated", "connected", "in_progress", "completed", "failed", "no_answer", "ringing"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.lower()
    
    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate duration is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Duration must be non-negative")
        return v
    
    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v: int) -> int:
        """Validate retry count is non-negative."""
        if v < 0:
            raise ValueError("Retry count must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call_xyz987654321",
                "lead_id": "lead_abc123456789",
                "call_sid": "CA1234567890abcdef",
                "direction": "outbound",
                "status": "completed",
                "start_time": "2025-10-24T10:30:00Z",
                "end_time": "2025-10-24T10:33:45Z",
                "duration": 225,
                "recording_url": "https://api.twilio.com/recordings/RE123",
                "consent_given": True,
                "retry_count": 0
            }
        }
