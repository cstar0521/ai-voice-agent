"""
Sarvam AI Speech Adapter for Indian languages.
Provides TTS and ASR capabilities using Sarvam AI API.
"""

import os
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, AsyncIterator
from app.integrations.speech_adapter import SpeechAdapter, VoiceGender

logger = logging.getLogger(__name__)


class SarvamSpeechAdapter(SpeechAdapter):
    """
    Sarvam AI Speech adapter for Indian languages.
    
    Supports:
    - Text-to-Speech (TTS) with Indian voices
    - Automatic Speech Recognition (ASR) for Indian languages
    - Language detection
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None
    ):
        """
        Initialize Sarvam AI adapter.
        
        Args:
            api_key: Sarvam AI API key
            api_url: Sarvam AI API base URL
        """
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        self.api_url = api_url or os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/v1")
        
        if not self.api_key:
            logger.warning("Sarvam AI API key not provided. TTS/ASR will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Sarvam AI Speech adapter initialized")
        
        # Model configurations
        self.tts_model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v1")
        self.asr_model = os.getenv("SARVAM_ASR_MODEL", "saaras:v1")
        self.default_speaker = os.getenv("SARVAM_VOICE_SPEAKER", "meera")
        
        # Language mappings
        self.language_map = {
            "hinglish": "hi-IN",
            "hindi": "hi-IN",
            "english": "en-IN",
            "telugu": "te-IN",
            "hi-IN": "hi-IN",
            "en-IN": "en-IN",
            "te-IN": "te-IN"
        }
        
        # Voice mappings for different languages and genders
        self.voice_map = {
            "hi-IN": {
                VoiceGender.FEMALE: "meera",
                VoiceGender.MALE: "arjun"
            },
            "en-IN": {
                VoiceGender.FEMALE: "kavya",
                VoiceGender.MALE: "raj"
            },
            "te-IN": {
                VoiceGender.FEMALE: "lakshmi",
                VoiceGender.MALE: "ravi"
            }
        }
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Sarvam AI ASR.
        
        Args:
            audio_data: Audio bytes (WAV format preferred)
            language: Language code
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary with transcript, confidence, and language
        """
        if not self.enabled:
            raise Exception("Sarvam AI adapter not enabled - missing API key")
        
        try:
            # Map language code
            sarvam_language = self.language_map.get(language.lower(), "hi-IN")
            
            # Prepare the request
            url = f"{self.api_url}/speech-to-text"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Convert audio to base64 for API
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "model": self.asr_model,
                "language_code": sarvam_language,
                "audio": {
                    "audioContent": audio_base64
                },
                "config": {
                    "encoding": "LINEAR16",
                    "sampleRateHertz": sample_rate,
                    "languageCode": sarvam_language
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract transcript and confidence
                        transcript = result.get("transcript", "")
                        confidence = result.get("confidence", 0.0)
                        
                        logger.info(f"Sarvam ASR result: '{transcript}' (confidence: {confidence})")
                        
                        return {
                            "transcript": transcript,
                            "confidence": confidence,
                            "language": sarvam_language
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Sarvam ASR failed: {response.status} - {error_text}")
                        raise Exception(f"Sarvam ASR API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Sarvam ASR transcription failed: {str(e)}")
            raise
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Transcribe streaming audio (not supported by Sarvam AI yet).
        Falls back to batch processing.
        """
        logger.warning("Sarvam AI streaming ASR not yet supported, using batch processing")
        
        # Collect audio chunks
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)
        
        # Combine chunks
        audio_data = b''.join(audio_chunks)
        
        # Process as batch
        result = await self.transcribe_audio(audio_data, language, sample_rate)
        result["is_final"] = True
        
        yield result
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """
        Synthesize speech using Sarvam AI TTS.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice_gender: Voice gender preference
            speaking_rate: Speech rate (0.5 to 2.0)
            
        Returns:
            Audio bytes in MP3 format
        """
        if not self.enabled:
            raise Exception("Sarvam AI adapter not enabled - missing API key")
        
        try:
            # Map language code
            sarvam_language = self.language_map.get(language.lower(), "hi-IN")
            
            # Select voice based on language and gender
            voice_name = self.voice_map.get(sarvam_language, {}).get(
                voice_gender, self.default_speaker
            )
            
            # Prepare the request
            url = f"{self.api_url}/text-to-speech"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.tts_model,
                "speaker": voice_name,
                "text": text,
                "language_code": sarvam_language,
                "speed": speaking_rate,
                "pitch": 0,  # Default pitch
                "loudness": 0  # Default loudness
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Get audio URL or base64 data
                        if "audio" in result:
                            audio_base64 = result["audio"]
                            import base64
                            audio_data = base64.b64decode(audio_base64)
                            
                            logger.info(f"Sarvam TTS generated audio for: '{text[:50]}...' in {sarvam_language}")
                            return audio_data
                        
                        elif "audio_url" in result:
                            # Download audio from URL
                            audio_url = result["audio_url"]
                            async with session.get(audio_url) as audio_response:
                                if audio_response.status == 200:
                                    audio_data = await audio_response.read()
                                    logger.info(f"Sarvam TTS downloaded audio for: '{text[:50]}...'")
                                    return audio_data
                                else:
                                    raise Exception(f"Failed to download audio: {audio_response.status}")
                        
                        else:
                            raise Exception("No audio data in Sarvam TTS response")
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Sarvam TTS failed: {response.status} - {error_text}")
                        raise Exception(f"Sarvam TTS API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Sarvam TTS synthesis failed: {str(e)}")
            raise
    
    async def detect_language(
        self,
        audio_data: bytes,
        candidate_languages: Optional[list] = None
    ) -> str:
        """
        Detect language from audio (basic implementation).
        
        Args:
            audio_data: Audio bytes
            candidate_languages: List of candidate language codes
            
        Returns:
            Detected language code
        """
        if not candidate_languages:
            candidate_languages = ["hi-IN", "en-IN", "te-IN"]
        
        try:
            # Try transcribing with each candidate language
            best_language = "hi-IN"
            best_confidence = 0.0
            
            for lang in candidate_languages:
                try:
                    result = await self.transcribe_audio(audio_data, lang)
                    confidence = result.get("confidence", 0.0)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_language = lang
                        
                except Exception:
                    continue
            
            logger.info(f"Detected language: {best_language} (confidence: {best_confidence})")
            return best_language
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return "hi-IN"  # Default fallback
    
    async def test_connection(self) -> bool:
        """Test connection to Sarvam AI API."""
        if not self.enabled:
            return False
        
        try:
            # Test with a simple TTS request
            test_text = "Hello, this is a test."
            audio_data = await self.synthesize_speech(test_text, "en-IN")
            return len(audio_data) > 0
            
        except Exception as e:
            logger.error(f"Sarvam AI connection test failed: {str(e)}")
            return False
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return list(self.language_map.values())
    
    def get_supported_voices(self, language: str) -> list:
        """Get list of supported voices for a language."""
        sarvam_language = self.language_map.get(language.lower(), "hi-IN")
        return list(self.voice_map.get(sarvam_language, {}).values())


# Factory function to create the appropriate speech adapter
async def get_speech_adapter() -> SpeechAdapter:
    """Get the configured speech adapter."""
    from config import settings
    
    provider = getattr(settings, 'speech_provider', 'sarvam_ai').lower()
    
    if provider == 'sarvam_ai':
        adapter = SarvamSpeechAdapter()
        if adapter.enabled:
            logger.info("Using Sarvam AI speech adapter")
            return adapter
        else:
            logger.warning("Sarvam AI not configured, falling back to Google Cloud")
    
    # Fallback to Google Cloud
    try:
        from app.integrations.speech_adapter import GoogleCloudSpeechAdapter
        adapter = GoogleCloudSpeechAdapter()
        logger.info("Using Google Cloud speech adapter")
        return adapter
    except Exception as e:
        logger.error(f"Failed to initialize speech adapter: {e}")
        raise Exception("No speech adapter available")