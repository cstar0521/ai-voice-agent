"""
TTS Audio Caching Service for pre-generating and storing voice prompts.
Supports Google Cloud TTS and AWS Polly with cloud storage (S3/GCS).
"""

import asyncio
import hashlib
import logging
from typing import Optional, Dict
from pathlib import Path
import aiofiles
import boto3
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import storage as gcs_storage

from config import settings
from app.repositories.prompt_repository import PromptRepository
from app.models.configuration import VoicePrompt

logger = logging.getLogger(__name__)


class TTSCacheService:
    """Service for generating and caching TTS audio files."""
    
    def __init__(self, prompt_repo: PromptRepository):
        self.prompt_repo = prompt_repo
        self.use_google = bool(settings.google_cloud_project)
        self.use_aws = bool(settings.aws_access_key_id)
        
        # Initialize clients
        if self.use_google:
            self.tts_client = texttospeech.TextToSpeechClient()
            self.gcs_client = gcs_storage.Client(project=settings.google_cloud_project)
            self.bucket_name = f"{settings.google_cloud_project}-voice-prompts"
        
        if self.use_aws:
            self.polly_client = boto3.client(
                'polly',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.s3_bucket = "voice-agent-prompts"
    
    def _get_voice_config(self, language: str) -> Dict:
        """Get voice configuration for a language."""
        voice_configs = {
            "hinglish": {
                "google": {"language_code": "hi-IN", "name": "hi-IN-Wavenet-D"},
                "aws": {"voice_id": "Aditi", "language_code": "hi-IN"}
            },
            "english": {
                "google": {"language_code": "en-US", "name": "en-US-Wavenet-F"},
                "aws": {"voice_id": "Joanna", "language_code": "en-US"}
            },
            "telugu": {
                "google": {"language_code": "te-IN", "name": "te-IN-Standard-A"},
                "aws": {"voice_id": "Aditi", "language_code": "hi-IN"}  # Fallback to Hindi
            }
        }
        return voice_configs.get(language, voice_configs["english"])
    
    async def generate_audio_google(self, text: str, language: str) -> bytes:
        """
        Generate audio using Google Cloud TTS.
        
        Args:
            text: Text to convert to speech
            language: Language code
            
        Returns:
            Audio content as bytes
        """
        voice_config = self._get_voice_config(language)["google"]
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
        )
        
        return response.audio_content
    
    async def generate_audio_aws(self, text: str, language: str) -> bytes:
        """
        Generate audio using AWS Polly.
        
        Args:
            text: Text to convert to speech
            language: Language code
            
        Returns:
            Audio content as bytes
        """
        voice_config = self._get_voice_config(language)["aws"]
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_config["voice_id"],
                LanguageCode=voice_config["language_code"],
                Engine='neural'
            )
        )
        
        audio_stream = response['AudioStream']
        return audio_stream.read()
    
    async def upload_to_gcs(self, audio_content: bytes, file_path: str) -> str:
        """
        Upload audio to Google Cloud Storage.
        
        Args:
            audio_content: Audio bytes
            file_path: Path in bucket
            
        Returns:
            Public URL of uploaded file
        """
        bucket = self.gcs_client.bucket(self.bucket_name)
        blob = bucket.blob(file_path)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: blob.upload_from_string(
                audio_content,
                content_type='audio/mpeg'
            )
        )
        
        # Make public
        await loop.run_in_executor(None, blob.make_public)
        
        return blob.public_url
    
    async def upload_to_s3(self, audio_content: bytes, file_path: str) -> str:
        """
        Upload audio to AWS S3.
        
        Args:
            audio_content: Audio bytes
            file_path: Path in bucket
            
        Returns:
            Public URL of uploaded file
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=file_path,
                Body=audio_content,
                ContentType='audio/mpeg',
                ACL='public-read'
            )
        )
        
        url = f"https://{self.s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{file_path}"
        return url
    
    def _generate_file_path(self, prompt_id: str, text: str) -> str:
        """Generate a unique file path for the audio file."""
        # Create hash of text for versioning
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"prompts/{prompt_id}_{text_hash}.mp3"
    
    async def cache_prompt_audio(self, prompt: VoicePrompt) -> Optional[str]:
        """
        Generate and cache audio for a prompt.
        
        Args:
            prompt: VoicePrompt object
            
        Returns:
            URL of cached audio file, or None if failed
        """
        try:
            logger.info(f"Generating audio for prompt: {prompt.prompt_id}")
            
            # Generate audio
            if self.use_google:
                audio_content = await self.generate_audio_google(prompt.text, prompt.language)
                file_path = self._generate_file_path(prompt.prompt_id, prompt.text)
                audio_url = await self.upload_to_gcs(audio_content, file_path)
            elif self.use_aws:
                audio_content = await self.generate_audio_aws(prompt.text, prompt.language)
                file_path = self._generate_file_path(prompt.prompt_id, prompt.text)
                audio_url = await self.upload_to_s3(audio_content, file_path)
            else:
                logger.warning("No TTS provider configured, skipping audio generation")
                return None
            
            # Update prompt with audio URL
            await self.prompt_repo.update_audio_url(prompt.prompt_id, audio_url)
            
            logger.info(f"Successfully cached audio for {prompt.prompt_id}: {audio_url}")
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to cache audio for {prompt.prompt_id}: {e}")
            return None
    
    async def cache_all_prompts(self, language: Optional[str] = None) -> Dict[str, int]:
        """
        Generate and cache audio for all prompts.
        
        Args:
            language: Optional language filter
            
        Returns:
            Dictionary with success and failure counts
        """
        prompts = await self.prompt_repo.get_all_prompts(language)
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for prompt in prompts:
            # Skip if already has audio URL
            if prompt.audio_url:
                logger.info(f"Skipping {prompt.prompt_id} - already has audio URL")
                results["skipped"] += 1
                continue
            
            audio_url = await self.cache_prompt_audio(prompt)
            
            if audio_url:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        logger.info(f"Audio caching complete: {results}")
        return results
    
    async def regenerate_prompt_audio(self, prompt_id: str) -> Optional[str]:
        """
        Regenerate audio for a specific prompt.
        
        Args:
            prompt_id: ID of the prompt
            
        Returns:
            URL of new audio file, or None if failed
        """
        # Get prompt from database
        prompts = await self.prompt_repo.get_all_prompts()
        prompt = next((p for p in prompts if p.prompt_id == prompt_id), None)
        
        if not prompt:
            logger.error(f"Prompt not found: {prompt_id}")
            return None
        
        return await self.cache_prompt_audio(prompt)
    
    async def get_audio_url_with_fallback(
        self,
        state: str,
        language: str,
        text: str
    ) -> Optional[str]:
        """
        Get audio URL for a prompt with real-time TTS fallback.
        
        Args:
            state: Conversation state
            language: Language code
            text: Prompt text (for fallback generation)
            
        Returns:
            Audio URL or None
        """
        # Try to get cached audio
        prompt = await self.prompt_repo.get_prompt(state, language)
        
        if prompt and prompt.audio_url:
            return prompt.audio_url
        
        # Fallback: generate audio on-the-fly
        logger.warning(f"No cached audio for {state}/{language}, generating on-the-fly")
        
        try:
            if self.use_google:
                audio_content = await self.generate_audio_google(text, language)
            elif self.use_aws:
                audio_content = await self.generate_audio_aws(text, language)
            else:
                return None
            
            # Save to temporary location or return base64
            # For now, we'll just log that we generated it
            logger.info(f"Generated real-time audio for {state}/{language}")
            return None  # Would return temporary URL in production
            
        except Exception as e:
            logger.error(f"Failed to generate fallback audio: {e}")
            return None
