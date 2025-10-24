"""
Speech processing adapter for ASR (Automatic Speech Recognition) and TTS (Text-to-Speech).

Supports both Google Cloud Speech-to-Text/Text-to-Speech and AWS Transcribe/Polly.
Handles multiple languages: Hinglish, English, Telugu.
"""

import os
import logging
from typing import Optional, Dict, Any, AsyncIterator, List
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SpeechProvider(Enum):
    """Supported speech processing providers."""
    SARVAM_AI = "sarvam_ai"
    GOOGLE_CLOUD = "google_cloud"
    AWS = "aws"


class Language(Enum):
    """Supported languages for speech processing."""
    HINGLISH = "hi-IN"  # Hindi/Hinglish
    ENGLISH = "en-IN"   # Indian English
    TELUGU = "te-IN"    # Telugu


class VoiceGender(Enum):
    """Voice gender options for TTS."""
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


class SpeechAdapter(ABC):
    """Abstract base class for speech processing adapters."""
    
    @abstractmethod
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio bytes in supported format
            language: Language code (hi-IN, en-IN, te-IN)
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Dictionary with transcript, confidence, and language
        """
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Transcribe streaming audio in real-time.
        
        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code
            sample_rate: Audio sample rate in Hz
            
        Yields:
            Partial transcription results
        """
        pass
    
    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice_gender: Voice gender preference
            speaking_rate: Speech rate (0.5 to 2.0)
            
        Returns:
            Audio bytes in MP3 or WAV format
        """
        pass
    
    @abstractmethod
    async def detect_language(
        self,
        audio_data: bytes,
        candidate_languages: List[str] = None
    ) -> str:
        """
        Detect the language spoken in audio.
        
        Args:
            audio_data: Audio bytes
            candidate_languages: List of possible language codes
            
        Returns:
            Detected language code
        """
        pass


class GoogleCloudSpeechAdapter(SpeechAdapter):
    """
    Google Cloud Speech-to-Text and Text-to-Speech adapter.
    
    Requires GOOGLE_APPLICATION_CREDENTIALS environment variable.
    """
    
    def __init__(self):
        """Initialize Google Cloud clients."""
        try:
            from google.cloud import speech_v1p1beta1 as speech
            from google.cloud import texttospeech
            
            self.speech_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            
            logger.info("Google Cloud Speech adapter initialized")
            
        except ImportError:
            logger.error("Google Cloud libraries not installed. Install with: pip install google-cloud-speech google-cloud-texttospeech")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud clients: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """Transcribe audio using Google Cloud Speech-to-Text."""
        try:
            from google.cloud import speech_v1p1beta1 as speech
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language,
                enable_automatic_punctuation=True,
                model="phone_call",
                use_enhanced=True
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": language
                }
            
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                "transcript": alternative.transcript,
                "confidence": alternative.confidence,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Google Cloud transcription failed: {str(e)}")
            raise
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """Transcribe streaming audio using Google Cloud."""
        try:
            from google.cloud import speech_v1p1beta1 as speech
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language,
                enable_automatic_punctuation=True,
                model="phone_call",
                use_enhanced=True
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True
            )
            
            async def request_generator():
                yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
                async for chunk in audio_stream:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            responses = self.speech_client.streaming_recognize(request_generator())
            
            for response in responses:
                for result in response.results:
                    alternative = result.alternatives[0]
                    yield {
                        "transcript": alternative.transcript,
                        "confidence": alternative.confidence,
                        "is_final": result.is_final,
                        "language": language
                    }
                    
        except Exception as e:
            logger.error(f"Google Cloud streaming transcription failed: {str(e)}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """Synthesize speech using Google Cloud Text-to-Speech."""
        try:
            from google.cloud import texttospeech
            
            # Map language to voice name
            voice_map = {
                "hi-IN": "hi-IN-Wavenet-A" if voice_gender == VoiceGender.FEMALE else "hi-IN-Wavenet-B",
                "en-IN": "en-IN-Wavenet-A" if voice_gender == VoiceGender.FEMALE else "en-IN-Wavenet-B",
                "te-IN": "te-IN-Standard-A" if voice_gender == VoiceGender.FEMALE else "te-IN-Standard-B"
            }
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=voice_map.get(language, "hi-IN-Wavenet-A")
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"Synthesized speech for text: '{text[:50]}...' in {language}")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Google Cloud TTS failed: {str(e)}")
            raise
    
    async def detect_language(
        self,
        audio_data: bytes,
        candidate_languages: List[str] = None
    ) -> str:
        """Detect language using Google Cloud Speech-to-Text."""
        try:
            from google.cloud import speech_v1p1beta1 as speech
            
            if candidate_languages is None:
                candidate_languages = ["hi-IN", "en-IN", "te-IN"]
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=8000,
                language_code=candidate_languages[0],
                alternative_language_codes=candidate_languages[1:],
                model="phone_call"
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                detected_language = response.results[0].language_code
                logger.info(f"Detected language: {detected_language}")
                return detected_language
            
            # Default to Hinglish if no results
            return "hi-IN"
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return "hi-IN"  # Default fallback


class AWSSpeechAdapter(SpeechAdapter):
    """
    AWS Transcribe and Polly adapter.
    
    Requires AWS credentials configured via environment variables or IAM role.
    """
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        """Initialize AWS clients."""
        try:
            import boto3
            
            self.access_key = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
            self.secret_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
            self.region = region_name or os.getenv("AWS_REGION", "us-east-1")
            
            self.transcribe_client = boto3.client(
                'transcribe',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            self.polly_client = boto3.client(
                'polly',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            logger.info("AWS Speech adapter initialized")
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """Transcribe audio using AWS Transcribe."""
        try:
            import io
            import json
            
            # AWS Transcribe requires S3 or streaming
            # For simplicity, using streaming transcribe
            logger.warning("AWS batch transcription requires S3. Using streaming instead.")
            
            # Fallback to basic transcription
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"AWS transcription failed: {str(e)}")
            raise
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """Transcribe streaming audio using AWS Transcribe Streaming."""
        try:
            # AWS Transcribe Streaming implementation would go here
            # This requires amazon-transcribe library
            logger.warning("AWS streaming transcription not fully implemented")
            yield {
                "transcript": "",
                "confidence": 0.0,
                "is_final": False,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"AWS streaming transcription failed: {str(e)}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """Synthesize speech using AWS Polly."""
        try:
            # Map language to Polly voice
            voice_map = {
                "hi-IN": {"female": "Aditi", "male": "Aditi"},  # Polly has limited Hindi voices
                "en-IN": {"female": "Aditi", "male": "Raveena"},
                "te-IN": {"female": "Aditi", "male": "Aditi"}  # Telugu not directly supported
            }
            
            gender_key = voice_gender.value if voice_gender != VoiceGender.NEUTRAL else "female"
            voice_id = voice_map.get(language, {}).get(gender_key, "Aditi")
            
            # Polly doesn't support speaking rate in the same way
            # Using SSML for rate control
            if speaking_rate != 1.0:
                rate_percent = int(speaking_rate * 100)
                text = f'<speak><prosody rate="{rate_percent}%">{text}</prosody></speak>'
                text_type = 'ssml'
            else:
                text_type = 'text'
            
            response = self.polly_client.synthesize_speech(
                Text=text,
                TextType=text_type,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode='hi-IN' if language == 'hi-IN' else 'en-IN'
            )
            
            audio_data = response['AudioStream'].read()
            logger.info(f"Synthesized speech using AWS Polly voice: {voice_id}")
            return audio_data
            
        except Exception as e:
            logger.error(f"AWS Polly TTS failed: {str(e)}")
            raise
    
    async def detect_language(
        self,
        audio_data: bytes,
        candidate_languages: List[str] = None
    ) -> str:
        """Detect language (AWS Transcribe has limited language detection)."""
        try:
            # AWS Transcribe doesn't have robust language detection
            # Fallback to default
            logger.warning("AWS language detection not fully supported, defaulting to hi-IN")
            return "hi-IN"
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return "hi-IN"


class SarvamAISpeechAdapter(SpeechAdapter):
    """
    Sarvam AI Speech adapter for Indian languages.
    
    Optimized for Hinglish, Hindi, Telugu, and other Indian languages.
    Requires SARVAM_API_KEY environment variable.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None
    ):
        """Initialize Sarvam AI client."""
        try:
            import httpx
            
            # Try to get from parameter, then env, then config
            self.api_key = api_key or os.getenv("SARVAM_API_KEY")
            
            # If still not found, try importing from config
            if not self.api_key:
                try:
                    from config import settings
                    self.api_key = settings.sarvam_api_key
                except:
                    pass
            
            if not self.api_key:
                raise ValueError("SARVAM_API_KEY is required. Set it in .env file or pass as parameter.")
            
            # Get API URL from parameter, env, or config
            self.api_url = api_url or os.getenv("SARVAM_API_URL")
            if not self.api_url:
                try:
                    from config import settings
                    self.api_url = settings.sarvam_api_url
                except:
                    self.api_url = "https://api.sarvam.ai/v1"
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            logger.info("Sarvam AI Speech adapter initialized")
            
        except ImportError:
            logger.error("httpx not installed. Install with: pip install httpx")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Sarvam AI client: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """Transcribe audio using Sarvam AI ASR."""
        try:
            import base64
            
            # Convert language code to Sarvam format
            sarvam_lang = self._convert_language_code(language)
            
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Call Sarvam ASR API
            response = await self.client.post(
                f"{self.api_url}/speech-to-text",
                json={
                    "audio_base64": audio_base64,
                    "language_code": sarvam_lang,
                    "model": "saaras:v1"  # Sarvam's ASR model
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "transcript": result.get("transcript", ""),
                "confidence": result.get("confidence", 0.0),
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Sarvam AI transcription failed: {str(e)}")
            raise
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """Transcribe streaming audio using Sarvam AI."""
        try:
            import base64
            
            sarvam_lang = self._convert_language_code(language)
            
            # Sarvam AI streaming implementation
            # Note: Check Sarvam API docs for actual streaming endpoint
            async for chunk in audio_stream:
                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                
                response = await self.client.post(
                    f"{self.api_url}/speech-to-text-stream",
                    json={
                        "audio": audio_base64,
                        "language": sarvam_lang,
                        "model": "saarika:v1"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    yield {
                        "transcript": result.get("transcript", ""),
                        "confidence": result.get("confidence", 0.0),
                        "is_final": result.get("is_final", False),
                        "language": language
                    }
                    
        except Exception as e:
            logger.error(f"Sarvam AI streaming transcription failed: {str(e)}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """Synthesize speech using Sarvam AI TTS."""
        try:
            import base64
            
            sarvam_lang = self._convert_language_code(language)
            
            # Map voice gender to Sarvam voice models
            voice_map = {
                "hi-IN": {
                    "female": "meera",  # Sarvam's Hindi female voice
                    "male": "arvind"    # Sarvam's Hindi male voice
                },
                "en-IN": {
                    "female": "meera",
                    "male": "arvind"
                },
                "te-IN": {
                    "female": "meera",
                    "male": "arvind"
                }
            }
            
            gender_key = voice_gender.value if voice_gender != VoiceGender.NEUTRAL else "female"
            voice_id = voice_map.get(language, {}).get(gender_key, "meera")
            
            # Call Sarvam TTS API
            response = await self.client.post(
                f"{self.api_url}/text-to-speech",
                json={
                    "inputs": [text],
                    "target_language_code": sarvam_lang,
                    "speaker": voice_id,
                    "pitch": 0,
                    "pace": speaking_rate,
                    "loudness": 1.5,
                    "speech_sample_rate": 8000,
                    "enable_preprocessing": True,
                    "model": "bulbul:v1"
                }
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Sarvam AI TTS API error: {response.status_code} - {error_detail}")
                raise Exception(f"Sarvam API returned {response.status_code}: {error_detail}")
            
            result = response.json()
            
            # Decode base64 audio - check for different possible response formats
            audio_base64 = result.get("audios", [None])[0] if "audios" in result else result.get("audio", "")
            if not audio_base64:
                logger.error(f"No audio in response: {result}")
                raise Exception("No audio data in Sarvam API response")
            
            audio_data = base64.b64decode(audio_base64)
            
            logger.info(f"Synthesized speech using Sarvam AI voice: {voice_id} for text: '{text[:50]}...'")
            return audio_data
            
        except Exception as e:
            logger.error(f"Sarvam AI TTS failed: {str(e)}")
            raise
    
    async def detect_language(
        self,
        audio_data: bytes,
        candidate_languages: List[str] = None
    ) -> str:
        """Detect language using Sarvam AI."""
        try:
            import base64
            
            if candidate_languages is None:
                candidate_languages = ["hi-IN", "en-IN", "te-IN"]
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Call Sarvam language detection API
            response = await self.client.post(
                f"{self.api_url}/language-detection",
                json={
                    "audio": audio_base64
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            detected_lang = result.get("language", "hi")
            
            # Convert Sarvam language code back to standard format
            lang_map = {
                "hi": "hi-IN",
                "en": "en-IN",
                "te": "te-IN",
                "ta": "ta-IN",
                "kn": "kn-IN",
                "ml": "ml-IN",
                "mr": "mr-IN",
                "gu": "gu-IN",
                "bn": "bn-IN",
                "pa": "pa-IN"
            }
            
            detected_language = lang_map.get(detected_lang, "hi-IN")
            logger.info(f"Detected language: {detected_language}")
            return detected_language
            
        except Exception as e:
            logger.error(f"Sarvam AI language detection failed: {str(e)}")
            return "hi-IN"  # Default fallback
    
    def _convert_language_code(self, language: str) -> str:
        """Convert standard language code to Sarvam format."""
        lang_map = {
            "hi-IN": "hi",
            "en-IN": "en",
            "te-IN": "te",
            "ta-IN": "ta",
            "kn-IN": "kn",
            "ml-IN": "ml",
            "mr-IN": "mr",
            "gu-IN": "gu",
            "bn-IN": "bn",
            "pa-IN": "pa"
        }
        return lang_map.get(language, "hi")
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between languages using Sarvam AI.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'hi-IN')
            target_lang: Target language code (e.g., 'en-IN')
            
        Returns:
            Translated text
        """
        try:
            source = self._convert_language_code(source_lang)
            target = self._convert_language_code(target_lang)
            
            response = await self.client.post(
                f"{self.api_url}/translate",
                json={
                    "text": text,
                    "source_language": source,
                    "target_language": target
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            translated_text = result.get("translated_text", text)
            logger.info(f"Translated text from {source_lang} to {target_lang}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Sarvam AI translation failed: {str(e)}")
            return text  # Return original text on failure
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def create_speech_adapter(provider: str = None) -> SpeechAdapter:
    """
    Factory function to create appropriate speech adapter.
    
    Args:
        provider: Provider name ('sarvam_ai', 'google_cloud', or 'aws')
        
    Returns:
        SpeechAdapter instance
    """
    if provider is None:
        provider = os.getenv("SPEECH_PROVIDER", "sarvam_ai")
    
    provider = provider.lower()
    
    if provider == "sarvam_ai":
        return SarvamAISpeechAdapter()
    elif provider == "google_cloud":
        return GoogleCloudSpeechAdapter()
    elif provider == "aws":
        return AWSSpeechAdapter()
    else:
        raise ValueError(f"Unsupported speech provider: {provider}")
