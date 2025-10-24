"""
Callback data model.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class Callback(BaseModel):
    """
    Model for callback scheduling.
    
    Represents a scheduled callback request when expert is unavailable.
    """
    callback_id: str = Field(default_factory=lambda: f"callback_{uuid.uuid4().hex[:12]}")
    lead_id: str
    call_id: str
    phone: str
    language: str = "english"
    preferred_time: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    status: str = "pending"  # pending, scheduled, completed, cancelled
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "callback_id": "callback_abc123",
                "lead_id": "lead_xyz789",
                "call_id": "call_def456",
                "phone": "+919876543210",
                "language": "hinglish",
                "preferred_time": "2025-10-25T14:00:00Z",
                "scheduled_time": "2025-10-25T14:00:00Z",
                "status": "scheduled",
                "reason": "expert_unavailable",
                "notes": "User requested callback for loan consultation"
            }
        }
