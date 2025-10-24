"""
Metrics models for tracking system performance and business KPIs.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class CallMetrics(BaseModel):
    """Metrics for a single call."""
    call_id: str
    lead_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str  # completed, failed, no_answer, etc.
    direction: str  # inbound, outbound
    language: str
    
    # Performance metrics
    asr_latency_ms: Optional[float] = None
    tts_latency_ms: Optional[float] = None
    total_turns: int = 0
    
    # Business metrics
    qualification_completed: bool = False
    handoff_triggered: bool = False
    sentiment_score: Optional[float] = None
    
    # Error tracking
    error_count: int = 0
    error_types: list[str] = Field(default_factory=list)


class DailyMetrics(BaseModel):
    """Aggregated metrics for a single day."""
    date: str  # YYYY-MM-DD
    
    # Call volume
    total_calls: int = 0
    inbound_calls: int = 0
    outbound_calls: int = 0
    
    # Call outcomes
    completed_calls: int = 0
    failed_calls: int = 0
    no_answer_calls: int = 0
    
    # Performance
    avg_call_duration_seconds: float = 0.0
    avg_qualification_time_seconds: float = 0.0
    avg_asr_latency_ms: float = 0.0
    avg_tts_latency_ms: float = 0.0
    
    # Business KPIs
    qualification_rate: float = 0.0  # % of calls that completed qualification
    handoff_rate: float = 0.0  # % of qualified calls that triggered handoff
    
    # Sentiment
    avg_sentiment_score: float = 0.0
    positive_sentiment_count: int = 0
    neutral_sentiment_count: int = 0
    negative_sentiment_count: int = 0
    
    # Language distribution
    language_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Error tracking
    total_errors: int = 0
    error_rate: float = 0.0  # errors per call
    error_types: Dict[str, int] = Field(default_factory=dict)


class SystemMetrics(BaseModel):
    """Real-time system metrics."""
    timestamp: datetime
    
    # Active resources
    active_calls: int = 0
    active_connections: int = 0
    
    # API performance
    api_requests_per_minute: float = 0.0
    avg_api_latency_ms: float = 0.0
    api_error_rate: float = 0.0
    
    # External service latency
    twilio_latency_ms: Optional[float] = None
    openai_latency_ms: Optional[float] = None
    google_speech_latency_ms: Optional[float] = None
    
    # Database performance
    db_query_latency_ms: float = 0.0
    db_connection_pool_size: int = 0
    
    # Memory and CPU (optional)
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class AlertMetrics(BaseModel):
    """Metrics that trigger alerts."""
    timestamp: datetime
    metric_type: str  # error_rate, api_latency, call_failure_rate
    current_value: float
    threshold_value: float
    severity: str  # warning, critical
    message: str
    metadata: Dict = Field(default_factory=dict)
