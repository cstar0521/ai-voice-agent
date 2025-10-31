"""
Twilio Adapter for telephony integration.

This module provides an adapter class for interacting with Twilio's Voice API,
handling outbound/inbound calls, call transfers, recording, and hangup operations.
"""

import os
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
import logging

logger = logging.getLogger(__name__)


class TwilioAdapter:
    """
    Adapter class for Twilio Voice API integration.
    
    Handles:
    - Outbound call initiation
    - Inbound call answering
    - Call transfers to human experts
    - Call hangup
    - Recording start/stop
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        phone_number: Optional[str] = None
    ):
        """
        Initialize Twilio adapter with credentials.
        
        Args:
            account_sid: Twilio account SID (defaults to env var)
            auth_token: Twilio auth token (defaults to env var)
            phone_number: Twilio phone number (defaults to env var)
        """
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = phone_number or os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning(
                "Twilio credentials not provided. Set TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables. "
                "Twilio functionality will be disabled."
            )
            self.client = None
            self.validator = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            self.validator = RequestValidator(self.auth_token)
        
        logger.info(f"TwilioAdapter initialized with phone number: {self.phone_number}")
    
    async def make_call(
        self,
        to_number: str,
        callback_url: str,
        status_callback_url: Optional[str] = None,
        timeout: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Initiate an outbound call.
        
        Args:
            to_number: Phone number to call (E.164 format)
            callback_url: URL for Twilio to request when call is answered
            status_callback_url: URL for call status updates
            timeout: Ring timeout in seconds
            metadata: Additional metadata to pass with the call
            
        Returns:
            call_sid: Twilio call SID
            
        Raises:
            Exception: If call initiation fails
        """
        try:
            logger.info(f"Initiating outbound call to {to_number}")
            
            # Build status callback events
            status_callback_events = [
                "initiated", "ringing", "answered", "completed"
            ]
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=callback_url,
                status_callback=status_callback_url,
                status_callback_event=status_callback_events,
                status_callback_method="POST",
                timeout=timeout,
                record=False  # Recording will be started explicitly after consent
            )
            
            logger.info(f"Call initiated successfully. SID: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Failed to initiate call to {to_number}: {str(e)}")
            raise
    
    async def initiate_outbound_call(
        self,
        to_number: str,
        language: str = "hinglish",
        status_callback_url: Optional[str] = None
    ):
        """
        Initiate an outbound call with conversation flow.
        
        Args:
            to_number: Phone number to call (E.164 format)
            language: Preferred language for the call
            status_callback_url: URL for call status updates
            
        Returns:
            Twilio call object
            
        Raises:
            Exception: If call initiation fails
        """
        try:
            logger.info(f"Initiating outbound call to {to_number} in {language}")
            
            # Build status callback events
            status_callback_events = [
                "initiated", "ringing", "answered", "completed"
            ]
            
            # For now, we'll use a simple TwiML that says a greeting
            # In production, this should point to your webhook that handles the conversation
            from config import settings
            base_url = settings.base_url if hasattr(settings, 'base_url') else "http://localhost:8000"
            callback_url = f"{base_url}/api/v1/calls/inbound/webhook"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=callback_url,
                status_callback=status_callback_url,
                status_callback_event=status_callback_events,
                status_callback_method="POST",
                timeout=60,
                record=False  # Recording will be started explicitly after consent
            )
            
            logger.info(f"Call initiated successfully. SID: {call.sid}")
            return call
            
        except Exception as e:
            logger.error(f"Failed to initiate call to {to_number}: {str(e)}")
            raise
    
    async def answer_call(
        self,
        call_sid: str,
        greeting_text: Optional[str] = None,
        gather_url: Optional[str] = None,
        language: str = "en-IN",
        use_sarvam_ai: bool = True
    ) -> str:
        """
        Answer an inbound call and generate TwiML response.
        
        Args:
            call_sid: Twilio call SID
            greeting_text: Optional greeting message to speak
            gather_url: URL to send user speech input
            language: Language code for speech recognition
            use_sarvam_ai: Whether to use Sarvam AI for TTS
            
        Returns:
            twiml: TwiML XML string for call handling
        """
        try:
            logger.info(f"Answering inbound call: {call_sid}")
            
            response = VoiceResponse()
            
            # Add greeting if provided
            if greeting_text:
                if use_sarvam_ai:
                    # Use Sarvam AI for natural Indian voice
                    audio_url = await self._generate_sarvam_audio(greeting_text, language)
                    if audio_url:
                        response.play(audio_url)
                        logger.info(f"Using Sarvam AI audio for call {call_sid}")
                    else:
                        # Fallback to Twilio voice
                        response.say(greeting_text, voice="Polly.Aditi", language=language)
                        logger.warning(f"Sarvam AI failed, using Twilio voice for call {call_sid}")
                else:
                    # Use Twilio's built-in voice
                    response.say(greeting_text, voice="Polly.Aditi", language=language)
            
            # Gather user input if URL provided
            if gather_url:
                gather = Gather(
                    input="speech",
                    action=gather_url,
                    method="POST",
                    language=language,
                    speech_timeout="auto",
                    timeout=8
                )
                response.append(gather)
            
            twiml = str(response)
            logger.info(f"Generated TwiML for call {call_sid}")
            return twiml
            
        except Exception as e:
            logger.error(f"Failed to answer call {call_sid}: {str(e)}")
            raise
    
    async def _generate_sarvam_audio(self, text: str, language: str = "hi-IN") -> Optional[str]:
        """
        Generate audio using Sarvam AI and return URL for Twilio to play.
        
        Args:
            text: Text to convert to speech
            language: Language code
            
        Returns:
            URL to audio file or None if failed
        """
        try:
            # Import Sarvam adapter
            from app.integrations.sarvam_speech_adapter import SarvamSpeechAdapter
            from app.integrations.speech_adapter import VoiceGender
            
            # Initialize Sarvam adapter with API key from environment
            api_key = os.getenv("SARVAM_API_KEY")
            api_url = "https://api.sarvam.ai"
            sarvam_adapter = SarvamSpeechAdapter(api_key=api_key, api_url=api_url)
            
            if not sarvam_adapter.enabled:
                logger.warning("Sarvam AI not enabled, cannot generate audio")
                return None
            
            # Generate audio with Sarvam AI
            audio_data = await sarvam_adapter.synthesize_speech(
                text=text,
                language=language,
                voice_gender=VoiceGender.FEMALE,  # Anushka voice
                speaking_rate=1.0
            )
            
            if not audio_data:
                logger.error("Sarvam AI returned empty audio data")
                return None
            
            # Save audio file and return URL
            audio_url = await self._save_and_serve_audio(audio_data, text)
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to generate Sarvam AI audio: {str(e)}")
            return None
    
    async def _save_and_serve_audio(self, audio_data: bytes, text: str) -> str:
        """
        Save audio data to file and return URL for Twilio to access.
        
        Args:
            audio_data: Audio bytes from Sarvam AI
            text: Original text (for filename)
            
        Returns:
            URL to audio file
        """
        try:
            import hashlib
            import os
            from config import settings
            
            # Create audio directory if it doesn't exist
            audio_dir = "static/audio"
            os.makedirs(audio_dir, exist_ok=True)
            
            # Generate filename based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"sarvam_{text_hash}.wav"
            filepath = os.path.join(audio_dir, filename)
            
            # Save audio file
            with open(filepath, "wb") as f:
                f.write(audio_data)
            
            # Return URL for Twilio to access
            base_url = settings.base_url or "http://localhost:8000"
            audio_url = f"{base_url}/static/audio/{filename}"
            
            logger.info(f"Saved Sarvam AI audio: {audio_url}")
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {str(e)}")
            raise
    
    async def transfer_call(
        self,
        call_sid: str,
        to_number: str,
        transfer_message: Optional[str] = None
    ) -> bool:
        """
        Transfer an active call to a human expert.
        
        Args:
            call_sid: Twilio call SID to transfer
            to_number: Expert phone number (E.164 format)
            transfer_message: Optional message before transfer
            
        Returns:
            success: True if transfer initiated successfully
            
        Raises:
            Exception: If transfer fails
        """
        try:
            logger.info(f"Transferring call {call_sid} to {to_number}")
            
            # Generate TwiML for transfer
            response = VoiceResponse()
            
            if transfer_message:
                response.say(transfer_message, voice="Polly.Aditi")
            
            # Dial the expert number
            response.dial(to_number, timeout=30)
            
            # Update the call with new TwiML
            call = self.client.calls(call_sid).update(
                twiml=str(response)
            )
            
            logger.info(f"Call {call_sid} transferred successfully to {to_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer call {call_sid}: {str(e)}")
            raise
    
    async def hangup_call(self, call_sid: str) -> bool:
        """
        Terminate an active call.
        
        Args:
            call_sid: Twilio call SID to hangup
            
        Returns:
            success: True if hangup successful
            
        Raises:
            Exception: If hangup fails
        """
        try:
            logger.info(f"Hanging up call: {call_sid}")
            
            call = self.client.calls(call_sid).update(status="completed")
            
            logger.info(f"Call {call_sid} hung up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to hangup call {call_sid}: {str(e)}")
            raise
    
    async def start_recording(
        self,
        call_sid: str,
        recording_status_callback: Optional[str] = None
    ) -> str:
        """
        Start recording an active call.
        
        Args:
            call_sid: Twilio call SID to record
            recording_status_callback: URL for recording status updates
            
        Returns:
            recording_sid: Twilio recording SID
            
        Raises:
            Exception: If recording start fails
        """
        try:
            logger.info(f"Starting recording for call: {call_sid}")
            
            recording = self.client.calls(call_sid).recordings.create(
                recording_status_callback=recording_status_callback,
                recording_status_callback_method="POST"
            )
            
            logger.info(f"Recording started. SID: {recording.sid}")
            return recording.sid
            
        except Exception as e:
            logger.error(f"Failed to start recording for call {call_sid}: {str(e)}")
            raise
    
    async def stop_recording(self, call_sid: str, recording_sid: str) -> bool:
        """
        Stop an active recording.
        
        Args:
            call_sid: Twilio call SID
            recording_sid: Twilio recording SID to stop
            
        Returns:
            success: True if recording stopped successfully
            
        Raises:
            Exception: If recording stop fails
        """
        try:
            logger.info(f"Stopping recording {recording_sid} for call {call_sid}")
            
            recording = self.client.calls(call_sid).recordings(recording_sid).update(
                status="stopped"
            )
            
            logger.info(f"Recording {recording_sid} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording {recording_sid}: {str(e)}")
            raise
    
    def validate_webhook_signature(
        self,
        url: str,
        params: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Validate Twilio webhook signature for security.
        
        Args:
            url: Full URL of the webhook endpoint
            params: POST parameters from Twilio
            signature: X-Twilio-Signature header value
            
        Returns:
            valid: True if signature is valid
        """
        try:
            is_valid = self.validator.validate(url, params, signature)
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature for URL: {url}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {str(e)}")
            return False
    
    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Retrieve call details from Twilio.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            call_details: Dictionary with call information
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch call details for {call_sid}: {str(e)}")
            raise
