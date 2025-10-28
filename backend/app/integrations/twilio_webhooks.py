"""
Twilio webhook handlers for call events.

This module handles various Twilio webhook callbacks including:
- Call status updates (initiated, ringing, answered, completed)
- Recording status callbacks
- Speech recognition results
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TwilioCallStatusWebhook(BaseModel):
    """Model for Twilio call status webhook."""
    CallSid: str = Field(..., description="Unique call identifier")
    AccountSid: str = Field(..., description="Twilio account SID")
    From: str = Field(..., description="Caller phone number")
    To: str = Field(..., description="Called phone number")
    CallStatus: str = Field(..., description="Call status")
    Direction: str = Field(..., description="Call direction")
    Timestamp: Optional[str] = Field(None, description="Event timestamp")
    CallDuration: Optional[str] = Field(None, description="Call duration in seconds")
    
    # Optional fields
    CallerName: Optional[str] = None
    CallerCity: Optional[str] = None
    CallerState: Optional[str] = None
    CallerCountry: Optional[str] = None


class TwilioRecordingStatusWebhook(BaseModel):
    """Model for Twilio recording status webhook."""
    RecordingSid: str = Field(..., description="Unique recording identifier")
    RecordingUrl: str = Field(..., description="URL to access recording")
    RecordingStatus: str = Field(..., description="Recording status")
    RecordingDuration: str = Field(..., description="Recording duration in seconds")
    CallSid: str = Field(..., description="Associated call SID")
    AccountSid: str = Field(..., description="Twilio account SID")
    RecordingChannels: Optional[str] = Field(None, description="Number of channels")
    RecordingSource: Optional[str] = Field(None, description="Recording source")


class TwilioSpeechResultWebhook(BaseModel):
    """Model for Twilio speech recognition result webhook."""
    CallSid: str = Field(..., description="Unique call identifier")
    AccountSid: str = Field(..., description="Twilio account SID")
    SpeechResult: Optional[str] = Field(None, description="Transcribed speech text")
    Confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    UnstableSpeechResult: Optional[str] = Field(None, description="Partial/unstable result")
    
    # Gather-specific fields
    Digits: Optional[str] = Field(None, description="DTMF digits if any")


class TwilioWebhookHandler:
    """
    Handler for processing Twilio webhook events.
    
    Processes call status updates, recording callbacks, and speech recognition results.
    """
    
    @staticmethod
    async def handle_call_status(
        webhook_data: TwilioCallStatusWebhook,
        call_repository,
        lead_repository
    ) -> Dict[str, Any]:
        """
        Handle call status callback from Twilio.
        
        Processes status updates: initiated, ringing, answered, completed, failed, busy, no-answer
        
        Args:
            webhook_data: Parsed webhook data
            call_repository: Repository for call operations
            lead_repository: Repository for lead operations
            
        Returns:
            Processing result with status and message
        """
        try:
            call_sid = webhook_data.CallSid
            call_status = webhook_data.CallStatus.lower()
            
            logger.info(f"Processing call status webhook: {call_sid} - {call_status}")
            
            # Find call by call_sid
            call = await call_repository.get_by_call_sid(call_sid)
            
            if not call:
                logger.warning(f"Call not found for SID: {call_sid}")
                return {
                    "status": "error",
                    "message": f"Call not found: {call_sid}"
                }
            
            # Map Twilio status to our internal status
            status_mapping = {
                "initiated": "initiated",
                "ringing": "connected",  # Map ringing to connected since call is being established
                "in-progress": "in_progress",
                "answered": "connected",
                "completed": "completed",
                "failed": "failed",
                "busy": "no_answer",  # Map busy to no_answer since both mean call wasn't answered
                "no-answer": "no_answer",
                "canceled": "failed"
            }
            
            internal_status = status_mapping.get(call_status, call_status)
            
            # Update call status
            updates = {"status": internal_status}
            
            # Handle specific status transitions
            if call_status == "answered":
                updates["start_time"] = datetime.utcnow()
                logger.info(f"Call {call_sid} answered, recording start time")
                
            elif call_status == "completed":
                updates["end_time"] = datetime.utcnow()
                
                # Calculate duration if available
                if webhook_data.CallDuration:
                    try:
                        updates["duration"] = int(webhook_data.CallDuration)
                    except ValueError:
                        logger.warning(f"Invalid duration value: {webhook_data.CallDuration}")
                
                logger.info(f"Call {call_sid} completed, duration: {updates.get('duration', 'N/A')}s")
                
            elif call_status in ["failed", "busy", "no-answer"]:
                updates["error_reason"] = call_status
                logger.warning(f"Call {call_sid} failed with reason: {call_status}")
            
            # Update call in database
            await call_repository.update(call.call_id, updates)
            
            return {
                "status": "success",
                "message": f"Call status updated to {internal_status}",
                "call_id": call.call_id,
                "call_status": internal_status
            }
            
        except Exception as e:
            logger.error(f"Error handling call status webhook: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    async def handle_recording_status(
        webhook_data: TwilioRecordingStatusWebhook,
        call_repository
    ) -> Dict[str, Any]:
        """
        Handle recording status callback from Twilio.
        
        Processes recording completion and stores recording URL.
        
        Args:
            webhook_data: Parsed webhook data
            call_repository: Repository for call operations
            
        Returns:
            Processing result with status and message
        """
        try:
            call_sid = webhook_data.CallSid
            recording_sid = webhook_data.RecordingSid
            recording_status = webhook_data.RecordingStatus.lower()
            
            logger.info(
                f"Processing recording status webhook: {recording_sid} - {recording_status}"
            )
            
            # Find call by call_sid
            call = await call_repository.get_by_call_sid(call_sid)
            
            if not call:
                logger.warning(f"Call not found for recording SID: {call_sid}")
                return {
                    "status": "error",
                    "message": f"Call not found: {call_sid}"
                }
            
            # Update call with recording information
            if recording_status == "completed":
                updates = {
                    "recording_url": webhook_data.RecordingUrl,
                }
                
                await call_repository.update(call.call_id, updates)
                
                logger.info(f"Recording {recording_sid} completed and URL saved")
                
                return {
                    "status": "success",
                    "message": "Recording URL saved",
                    "call_id": call.call_id,
                    "recording_url": webhook_data.RecordingUrl
                }
            
            return {
                "status": "success",
                "message": f"Recording status: {recording_status}"
            }
            
        except Exception as e:
            logger.error(f"Error handling recording status webhook: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    async def handle_speech_result(
        webhook_data: TwilioSpeechResultWebhook,
        conversation_repository
    ) -> Dict[str, Any]:
        """
        Handle speech recognition result from Twilio.
        
        Processes transcribed speech and stores in conversation history.
        
        Args:
            webhook_data: Parsed webhook data
            conversation_repository: Repository for conversation operations
            
        Returns:
            Processing result with transcribed text and confidence
        """
        try:
            call_sid = webhook_data.CallSid
            speech_result = webhook_data.SpeechResult
            confidence = webhook_data.Confidence
            
            logger.info(
                f"Processing speech result for call {call_sid}: "
                f"'{speech_result}' (confidence: {confidence})"
            )
            
            if not speech_result:
                logger.warning(f"No speech detected for call {call_sid}")
                return {
                    "status": "no_speech",
                    "message": "No speech detected",
                    "confidence": 0.0
                }
            
            # Find conversation by call_sid
            conversation = await conversation_repository.get_by_call_sid(call_sid)
            
            if conversation:
                # Add user turn to conversation
                from app.models.conversation import Turn
                
                turn = Turn(
                    turn_id=len(conversation.turns) + 1,
                    speaker="user",
                    text=speech_result,
                    timestamp=datetime.utcnow(),
                    confidence_score=confidence
                )
                
                await conversation_repository.add_turn(
                    conversation.conversation_id,
                    turn
                )
                
                logger.info(f"Speech result added to conversation {conversation.conversation_id}")
            
            return {
                "status": "success",
                "message": "Speech processed",
                "transcript": speech_result,
                "confidence": confidence,
                "call_sid": call_sid
            }
            
        except Exception as e:
            logger.error(f"Error handling speech result webhook: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def validate_webhook_signature(
        twilio_adapter,
        url: str,
        params: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Validate Twilio webhook signature for security.
        
        Args:
            twilio_adapter: TwilioAdapter instance
            url: Full webhook URL
            params: POST parameters
            signature: X-Twilio-Signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            is_valid = twilio_adapter.validate_webhook_signature(url, params, signature)
            
            if not is_valid:
                logger.warning(f"Invalid Twilio webhook signature for URL: {url}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {str(e)}")
            return False
