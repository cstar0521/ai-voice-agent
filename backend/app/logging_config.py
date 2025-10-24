"""
Structured logging configuration with JSON formatting.
Includes context tracking for call_id and lead_id.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

# Context variables for tracking call and lead IDs across async operations
call_id_context: ContextVar[Optional[str]] = ContextVar('call_id', default=None)
lead_id_context: ContextVar[Optional[str]] = ContextVar('lead_id', default=None)


class ContextualJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that includes contextual information.
    Adds call_id, lead_id, and component information to all log records.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name (component)
        log_record['component'] = record.name
        
        # Add contextual information
        call_id = call_id_context.get()
        if call_id:
            log_record['call_id'] = call_id
        
        lead_id = lead_id_context.get()
        if lead_id:
            log_record['lead_id'] = lead_id
        
        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging to file
    """
    # Create formatter
    formatter = ContextualJsonFormatter(
        '%(timestamp)s %(level)s %(component)s %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure component-specific loggers
    setup_component_loggers(log_level)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    
    root_logger.info("Structured logging configured", extra={
        "log_level": log_level,
        "log_file": log_file
    })


def setup_component_loggers(log_level: str) -> None:
    """
    Set up loggers for different components.
    
    Components:
    - api: API endpoints and request handling
    - telephony: Twilio/Bolna integration
    - speech: ASR/TTS operations
    - business: Business logic and conversation management
    - database: Database operations
    - security: Authentication and encryption
    """
    components = [
        'api',
        'telephony',
        'speech',
        'business',
        'database',
        'security'
    ]
    
    for component in components:
        logger = logging.getLogger(component)
        logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(component: str) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        component: Component name (api, telephony, speech, business, database, security)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(component)


def set_call_context(call_id: str, lead_id: Optional[str] = None) -> None:
    """
    Set the call context for logging.
    This should be called at the start of call processing.
    
    Args:
        call_id: Call identifier
        lead_id: Optional lead identifier
    """
    call_id_context.set(call_id)
    if lead_id:
        lead_id_context.set(lead_id)


def clear_call_context() -> None:
    """Clear the call context after call processing is complete."""
    call_id_context.set(None)
    lead_id_context.set(None)


def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None
) -> None:
    """
    Log an API request with structured data.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user identifier
    """
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "event_type": "api_request",
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id
        }
    )


def log_call_event(
    logger: logging.Logger,
    event_type: str,
    call_id: str,
    lead_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log a call-related event.
    
    Args:
        logger: Logger instance
        event_type: Type of event (initiated, connected, completed, failed, etc.)
        call_id: Call identifier
        lead_id: Optional lead identifier
        **kwargs: Additional event data
    """
    extra_data = {
        "event_type": f"call_{event_type}",
        "call_id": call_id,
        **kwargs
    }
    
    if lead_id:
        extra_data["lead_id"] = lead_id
    
    logger.info(f"Call {event_type}", extra=extra_data)


def log_speech_event(
    logger: logging.Logger,
    event_type: str,
    duration_ms: Optional[float] = None,
    confidence: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log a speech processing event (ASR/TTS).
    
    Args:
        logger: Logger instance
        event_type: Type of event (asr_start, asr_complete, tts_start, tts_complete)
        duration_ms: Processing duration in milliseconds
        confidence: Confidence score (for ASR)
        **kwargs: Additional event data
    """
    extra_data = {
        "event_type": f"speech_{event_type}",
        **kwargs
    }
    
    if duration_ms is not None:
        extra_data["duration_ms"] = duration_ms
    
    if confidence is not None:
        extra_data["confidence"] = confidence
    
    logger.info(f"Speech {event_type}", extra=extra_data)


def log_business_event(
    logger: logging.Logger,
    event_type: str,
    **kwargs
) -> None:
    """
    Log a business logic event.
    
    Args:
        logger: Logger instance
        event_type: Type of event (qualification, handoff, escalation, etc.)
        **kwargs: Additional event data
    """
    logger.info(
        f"Business event: {event_type}",
        extra={
            "event_type": f"business_{event_type}",
            **kwargs
        }
    )


def log_error(
    logger: logging.Logger,
    error_type: str,
    error_message: str,
    exception: Optional[Exception] = None,
    **kwargs
) -> None:
    """
    Log an error with structured data.
    
    Args:
        logger: Logger instance
        error_type: Type of error
        error_message: Error message
        exception: Optional exception object
        **kwargs: Additional error context
    """
    extra_data = {
        "event_type": "error",
        "error_type": error_type,
        "error_message": error_message,
        **kwargs
    }
    
    if exception:
        logger.error(error_message, exc_info=exception, extra=extra_data)
    else:
        logger.error(error_message, extra=extra_data)


# Example usage in different components:
"""
# API Component
api_logger = get_logger('api')
log_api_request(api_logger, 'POST', '/api/v1/calls/outbound', 201, 145.3, user_id='user_123')

# Telephony Component
telephony_logger = get_logger('telephony')
set_call_context('call_abc123', 'lead_xyz789')
log_call_event(telephony_logger, 'initiated', 'call_abc123', 'lead_xyz789', direction='outbound')

# Speech Component
speech_logger = get_logger('speech')
log_speech_event(speech_logger, 'asr_complete', duration_ms=234.5, confidence=0.92, text='Hello')

# Business Component
business_logger = get_logger('business')
log_business_event(business_logger, 'qualification', category='public_secured', loan_amount=5000000)

# Error Logging
try:
    # Some operation
    pass
except Exception as e:
    log_error(api_logger, 'database_error', 'Failed to save lead', exception=e, lead_id='lead_123')
"""
