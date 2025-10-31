"""
Call management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from app.auth import get_current_user, verify_api_key

logger = logging.getLogger(__name__)
from app.database import database
from app.models.call import Call
from app.models.lead import Lead
from app.repositories.call_repository import CallRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.conversation_repository import ConversationRepository
from app.integrations.twilio_adapter import TwilioAdapter
from app.integrations.twilio_webhooks import (
    TwilioWebhookHandler,
    TwilioCallStatusWebhook,
    TwilioRecordingStatusWebhook,
    TwilioSpeechResultWebhook
)

router = APIRouter()

# Twilio adapter will be initialized lazily
_twilio_adapter = None

def get_twilio_adapter() -> TwilioAdapter:
    """Get or create Twilio adapter instance."""
    global _twilio_adapter
    if _twilio_adapter is None:
        from config import settings
        _twilio_adapter = TwilioAdapter(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            phone_number=settings.twilio_phone_number
        )
    return _twilio_adapter


class OutboundCallRequest(BaseModel):
    """Request model for initiating outbound call."""
    phone_number: str = Field(..., description="Phone number to call")
    lead_source: Optional[str] = Field(None, description="Source of the lead")
    preferred_language: str = Field("hinglish", description="Preferred language (hinglish, english, telugu, hindi)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class OutboundCallResponse(BaseModel):
    """Response model for outbound call."""
    call_id: str
    lead_id: str
    status: str
    created_at: datetime


class TwilioWebhookRequest(BaseModel):
    """Request model for Twilio webhook."""
    CallSid: str
    From: str
    To: Optional[str] = None
    CallStatus: Optional[str] = None
    Direction: Optional[str] = None


class HangupResponse(BaseModel):
    """Response model for hangup."""
    call_id: str
    status: str
    message: str


class CallListResponse(BaseModel):
    """Response model for call list."""
    calls: List[Call]
    total: int
    page: int
    page_size: int


@router.post("/outbound", response_model=OutboundCallResponse, status_code=status.HTTP_201_CREATED)
async def initiate_outbound_call(
    request: OutboundCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Initiate an outbound call to a lead.
    
    Args:
        request: Outbound call request data
        current_user: Authenticated user
        
    Returns:
        Created call and lead information
    """
    try:
        db = database.get_database()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available. Please try again later."
        )
    
    lead_repo = LeadRepository(db)
    call_repo = CallRepository(db)
    
    # Check if lead exists by phone
    existing_lead = await lead_repo.get_by_phone(request.phone_number)
    
    if existing_lead:
        lead = existing_lead
    else:
        # Create new lead
        lead = Lead(
            phone=request.phone_number,
            language=request.preferred_language,
            lead_source=request.lead_source,
            metadata=request.metadata
        )
        lead = await lead_repo.create(lead)
    
    # Create call record
    call = Call(
        lead_id=lead.lead_id,
        direction="outbound",
        status="initiated"
    )
    call = await call_repo.create(call)
    
    # Initiate Twilio call
    try:
        twilio_adapter = get_twilio_adapter()
        
        # Prepare callback URLs
        from config import settings
        base_url = settings.base_url or "http://localhost:8000"
        status_callback_url = f"{base_url}/api/v1/calls/status/webhook"
        
        # Initiate the call
        twilio_call = await twilio_adapter.initiate_outbound_call(
            to_number=request.phone_number,
            language=request.preferred_language,
            status_callback_url=status_callback_url
        )
        
        # Update call with Twilio SID (let webhooks handle status updates)
        call.call_sid = twilio_call.sid
        await call_repo.update(call.call_id, {
            "call_sid": twilio_call.sid
        })
        
        logger.info(f"Outbound call initiated: {call.call_id}, Twilio SID: {twilio_call.sid}")
        
    except Exception as e:
        logger.error(f"Failed to initiate Twilio call: {str(e)}")
        # Update call status to failed
        call.status = "failed"
        await call_repo.update(call.call_id, {"status": "failed"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate call: {str(e)}"
        )
    
    return OutboundCallResponse(
        call_id=call.call_id,
        lead_id=lead.lead_id,
        status=call.status,
        created_at=call.created_at
    )


@router.post("/inbound/webhook")
async def handle_inbound_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    """
    Handle Twilio inbound call webhook.
    
    Args:
        request: FastAPI request object
        x_twilio_signature: Twilio signature header for validation
        
    Returns:
        TwiML response for Twilio
    """
    # Get form data from Twilio
    form_data = await request.form()
    params = dict(form_data)
    
    # Validate webhook signature
    url = str(request.url)
    if x_twilio_signature:
        is_valid = get_twilio_adapter().validate_webhook_signature(
            url, params, x_twilio_signature
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
    
    db = database.get_database()
    lead_repo = LeadRepository(db)
    call_repo = CallRepository(db)
    
    call_sid = params.get("CallSid")
    from_number = params.get("From")
    
    # Get or create lead
    existing_lead = await lead_repo.get_by_phone(from_number)
    
    if existing_lead:
        lead = existing_lead
    else:
        lead = Lead(
            phone=from_number,
            language="hinglish"
        )
        lead = await lead_repo.create(lead)
    
    # Check if call record already exists (for outbound calls)
    existing_call = await call_repo.get_by_call_sid(call_sid)
    
    if existing_call:
        # Update existing call to connected status
        call = await call_repo.update(existing_call.call_id, {
            "status": "connected",
            "start_time": datetime.utcnow()
        })
        logger.info(f"Updated existing call {call_sid} to connected status")
    else:
        # Create new call record (for direct inbound calls)
        call = Call(
            lead_id=lead.lead_id,
            call_sid=call_sid,
            direction="inbound",
            status="connected",
            start_time=datetime.utcnow()
        )
        call = await call_repo.create(call)
        logger.info(f"Created new call record for {call_sid}")
    
    # Generate TwiML response with Sarvam AI
    greeting = "नमस्ते! मैं एजुकेशन लोन एडवाइजर हूँ। क्या आप विदेश में पढ़ाई के लिए लोन के बारे में जानना चाहते हैं?"
    gather_url = f"{request.base_url}api/v1/calls/speech/webhook"
    
    logger.info(f"Generating TwiML for call {call_sid} with Sarvam AI")
    
    try:
        # Try Sarvam AI first
        twiml = await get_twilio_adapter().answer_call(
            call_sid=call_sid,
            greeting_text=greeting,
            gather_url=gather_url,
            language="hi-IN",
            use_sarvam_ai=True  # Enable Sarvam AI
        )
        
        logger.info(f"✅ Generated Sarvam AI TwiML for call {call_sid}")
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Sarvam AI failed for call {call_sid}: {e}")
        
        # Fallback to working Twilio voice
        fallback_twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">नमस्ते! मैं एजुकेशन लोन एडवाइजर हूँ। क्या आप विदेश में पढ़ाई के लिए लोन के बारे में जानना चाहते हैं?</Say>
    <Pause length="2"/>
    <Gather input="speech" timeout="10" language="hi-IN">
        <Say voice="Polly.Aditi" language="hi-IN">कृपया अपना जवाब दें।</Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">धन्यवाद! अलविदा।</Say>
</Response>'''
        
        logger.info(f"🔄 Using Twilio fallback for call {call_sid}")
        return Response(content=fallback_twiml, media_type="application/xml")


@router.post("/status/webhook")
async def handle_call_status_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    """
    Handle Twilio call status callback webhook.
    
    Processes status updates: initiated, ringing, answered, completed, failed, busy, no-answer
    
    Args:
        request: FastAPI request object
        x_twilio_signature: Twilio signature header for validation
        
    Returns:
        Processing result
    """
    # Get form data from Twilio
    form_data = await request.form()
    params = dict(form_data)
    
    # Validate webhook signature
    url = str(request.url)
    if x_twilio_signature:
        is_valid = get_twilio_adapter().validate_webhook_signature(
            url, params, x_twilio_signature
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
    
    # Parse webhook data
    webhook_data = TwilioCallStatusWebhook(**params)
    
    db = database.get_database()
    call_repo = CallRepository(db)
    lead_repo = LeadRepository(db)
    
    # Process call status
    result = await TwilioWebhookHandler.handle_call_status(
        webhook_data, call_repo, lead_repo
    )
    
    return result


@router.post("/recording/webhook")
async def handle_recording_status_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    """
    Handle Twilio recording status callback webhook.
    
    Processes recording completion and stores recording URL.
    
    Args:
        request: FastAPI request object
        x_twilio_signature: Twilio signature header for validation
        
    Returns:
        Processing result
    """
    # Get form data from Twilio
    form_data = await request.form()
    params = dict(form_data)
    
    # Validate webhook signature
    url = str(request.url)
    if x_twilio_signature:
        is_valid = get_twilio_adapter().validate_webhook_signature(
            url, params, x_twilio_signature
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
    
    # Parse webhook data
    webhook_data = TwilioRecordingStatusWebhook(**params)
    
    db = database.get_database()
    call_repo = CallRepository(db)
    
    # Process recording status
    result = await TwilioWebhookHandler.handle_recording_status(
        webhook_data, call_repo
    )
    
    return result


@router.post("/speech/webhook")
async def handle_speech_result_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    """
    Handle Twilio speech recognition result webhook.
    
    Processes transcribed speech from user.
    
    Args:
        request: FastAPI request object
        x_twilio_signature: Twilio signature header for validation
        
    Returns:
        TwiML response with next action
    """
    # Get form data from Twilio
    form_data = await request.form()
    params = dict(form_data)
    
    # Validate webhook signature
    url = str(request.url)
    if x_twilio_signature:
        is_valid = get_twilio_adapter().validate_webhook_signature(
            url, params, x_twilio_signature
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
    
    # Parse webhook data
    webhook_data = TwilioSpeechResultWebhook(**params)
    
    db = database.get_database()
    conversation_repo = ConversationRepository(db)
    
    # Process speech result
    result = await TwilioWebhookHandler.handle_speech_result(
        webhook_data, conversation_repo
    )
    
    # Generate TwiML response (placeholder - will be enhanced with conversation manager)
    from twilio.twiml.voice_response import VoiceResponse
    
    response = VoiceResponse()
    response.say("Thank you for your response. We are processing your information.")
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/{call_id}/hangup", response_model=HangupResponse)
async def hangup_call(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    End an active call.
    
    Args:
        call_id: Call identifier
        current_user: Authenticated user
        
    Returns:
        Hangup confirmation
        
    Raises:
        HTTPException: If call not found
    """
    db = database.get_database()
    call_repo = CallRepository(db)
    
    # Get call
    call = await call_repo.get_by_id(call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )
    
    # Hangup call via Twilio
    if call.call_sid:
        try:
            await get_twilio_adapter().hangup_call(call.call_sid)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to hangup call: {str(e)}"
            )
    
    # Update call status
    call = await call_repo.update_status(call_id, "completed")
    
    return HangupResponse(
        call_id=call_id,
        status="completed",
        message="Call ended successfully"
    )


@router.get("/{call_id}", response_model=Call)
async def get_call(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get call details by ID.
    
    Args:
        call_id: Call identifier
        current_user: Authenticated user
        
    Returns:
        Call details
        
    Raises:
        HTTPException: If call not found
    """
    db = database.get_database()
    call_repo = CallRepository(db)
    
    call = await call_repo.get_by_id(call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )
    
    return call


@router.get("", response_model=CallListResponse)
async def list_calls(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    direction: Optional[str] = Query(None, description="Filter by direction"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    List calls with pagination and filters.
    
    Args:
        status_filter: Filter by call status
        direction: Filter by call direction
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        
    Returns:
        Paginated list of calls
    """
    db = database.get_database()
    call_repo = CallRepository(db)
    
    skip = (page - 1) * page_size
    
    calls = await call_repo.list(
        status=status_filter,
        direction=direction,
        skip=skip,
        limit=page_size
    )
    
    # Get total count
    total = await call_repo.collection.count_documents({})
    
    return CallListResponse(
        calls=calls,
        total=total,
        page=page,
        page_size=page_size
    )
