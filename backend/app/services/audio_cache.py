"""
Audio caching service for pre-generated TTS audio files.
Manages cloud storage of audio files and provides fallback to real-time TTS.
"""

import asyncio
import hashlib
import logging
from typing import Dict, Optional, List
from pathlib import Path
import aiofiles
import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.services.speech_adapter import SpeechAdapter
from app.models.conversation import VoicePrompt

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioCacheService:
    """Service for managing pre-generated TTS audio caching."""
    
    def __init__(self, database: AsyncIOMotorDatabase, speech_adapter: SpeechAdapter):
        self.db = database
        self.speech_adapter = speech_adapter
        self.cache_collection = database.audio_cache
        self.base_url = settings.AUDIO_CACHE_BASE_URL or "https://storage.googleapis.com/voice-agent-audio"
        
    async def get_cached_audio_url(
        self, 
        text: str, 
        language: str, 
        voice: str = "default"
    ) -> Optional[str]:
        """
        Get cached audio URL for given text and language.
        
        Args:
            text: Text to synthesize
            language: Language code (hinglish, english, telugu)
            voice: Voice identifier
            
        Returns:
            Audio URL if cached, None if not found
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(text, language, voice)
            
            # Check database for cached entry
            cached_entry = await self.cache_collection.find_one({"cache_key": cache_key})
            
            if cached_entry and cached_entry.get("audio_url"):
                # Verify audio file exists
                if await self._verify_audio_exists(cached_entry["audio_url"]):
                    logger.info(f"Cache hit for audio: {cache_key}")
                    return cached_entry["audio_url"]
                else:
                    # Remove invalid cache entry
                    await self.cache_collection.delete_one({"cache_key": cache_key})
                    logger.warning(f"Removed invalid cache entry: {cache_key}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached audio: {e}")
            return None
    
    async def cache_audio(
        self, 
        text: str, 
        language: str, 
        voice: str = "default",
        force_regenerate: bool = False
    ) -> Optional[str]:
        """
        Generate and cache audio for given text.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice: Voice identifier
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Audio URL if successful, None if failed
        """
        try:
            cache_key = self._generate_cache_key(text, language, voice)
            
            # Check if already cached and not forcing regeneration
            if not force_regenerate:
                existing_url = await self.get_cached_audio_url(text, language, voice)
                if existing_url:
                    return existing_url
            
            # Generate TTS audio
            logger.info(f"Generating TTS audio for: {cache_key}")
            audio_data = await self.speech_adapter.synthesize_speech(text, language, voice)
            
            if not audio_data:
                logger.error(f"Failed to generate TTS audio for: {cache_key}")
                return None
            
            # Upload to cloud storage
            audio_url = await self._upload_audio(cache_key, audio_data)
            
            if audio_url:
                # Store in database
                await self.cache_collection.update_one(
                    {"cache_key": cache_key},
                    {
                        "$set": {
                            "cache_key": cache_key,
                            "text": text,
                            "language": language,
                            "voice": voice,
                            "audio_url": audio_url,
                            "created_at": asyncio.get_event_loop().time(),
                            "file_size": len(audio_data)
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"Cached audio successfully: {cache_key} -> {audio_url}")
                return audio_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error caching audio: {e}")
            return None
    
    async def get_or_generate_audio(
        self, 
        text: str, 
        language: str, 
        voice: str = "default"
    ) -> Optional[str]:
        """
        Get cached audio URL or generate if not cached.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice: Voice identifier
            
        Returns:
            Audio URL (cached or newly generated)
        """
        # Try to get from cache first
        cached_url = await self.get_cached_audio_url(text, language, voice)
        if cached_url:
            return cached_url
        
        # Generate and cache if not found
        return await self.cache_audio(text, language, voice)
    
    async def pre_generate_common_prompts(self) -> Dict[str, int]:
        """
        Pre-generate TTS audio for all common prompts.
        
        Returns:
            Dictionary with generation statistics
        """
        stats = {
            "total_prompts": 0,
            "generated": 0,
            "cached": 0,
            "failed": 0
        }
        
        try:
            # Get all prompts from database
            prompts_cursor = self.db.voice_prompts.find({})
            prompts = await prompts_cursor.to_list(length=None)
            
            stats["total_prompts"] = len(prompts)
            
            # Process each prompt
            for prompt_doc in prompts:
                try:
                    prompt = VoicePrompt(**prompt_doc)
                    
                    # Check if already cached
                    cached_url = await self.get_cached_audio_url(
                        prompt.text, 
                        prompt.language, 
                        prompt.voice or "default"
                    )
                    
                    if cached_url:
                        stats["cached"] += 1
                        continue
                    
                    # Generate and cache
                    audio_url = await self.cache_audio(
                        prompt.text, 
                        prompt.language, 
                        prompt.voice or "default"
                    )
                    
                    if audio_url:
                        stats["generated"] += 1
                        
                        # Update prompt with audio URL
                        await self.db.voice_prompts.update_one(
                            {"_id": prompt_doc["_id"]},
                            {"$set": {"audio_url": audio_url}}
                        )
                    else:
                        stats["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing prompt {prompt_doc.get('prompt_id')}: {e}")
                    stats["failed"] += 1
            
            logger.info(f"Pre-generation complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in pre-generation: {e}")
            return stats
    
    async def cleanup_old_cache(self, max_age_days: int = 90) -> int:
        """
        Clean up old cached audio files.
        
        Args:
            max_age_days: Maximum age in days for cached files
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_time = asyncio.get_event_loop().time() - (max_age_days * 24 * 60 * 60)
            
            # Find old cache entries
            old_entries = await self.cache_collection.find(
                {"created_at": {"$lt": cutoff_time}}
            ).to_list(length=None)
            
            cleaned_count = 0
            
            for entry in old_entries:
                try:
                    # Delete from cloud storage
                    if await self._delete_audio_file(entry["audio_url"]):
                        # Delete from database
                        await self.cache_collection.delete_one({"_id": entry["_id"]})
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Error cleaning cache entry {entry['cache_key']}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old cache entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error in cache cleanup: {e}")
            return 0
    
    def _generate_cache_key(self, text: str, language: str, voice: str) -> str:
        """Generate unique cache key for text, language, and voice combination."""
        content = f"{text}|{language}|{voice}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _verify_audio_exists(self, audio_url: str) -> bool:
        """Verify that audio file exists at the given URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(audio_url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _upload_audio(self, cache_key: str, audio_data: bytes) -> Optional[str]:
        """
        Upload audio data to cloud storage.
        
        Args:
            cache_key: Unique cache key
            audio_data: Audio file bytes
            
        Returns:
            Public URL of uploaded file
        """
        try:
            # For Google Cloud Storage
            if settings.CLOUD_PROVIDER == "gcp":
                return await self._upload_to_gcs(cache_key, audio_data)
            
            # For AWS S3
            elif settings.CLOUD_PROVIDER == "aws":
                return await self._upload_to_s3(cache_key, audio_data)
            
            # For local storage (development)
            else:
                return await self._upload_to_local(cache_key, audio_data)
                
        except Exception as e:
            logger.error(f"Error uploading audio: {e}")
            return None
    
    async def _upload_to_gcs(self, cache_key: str, audio_data: bytes) -> Optional[str]:
        """Upload to Google Cloud Storage."""
        try:
            from google.cloud import storage
            
            client = storage.Client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            
            blob_name = f"audio/{cache_key}.mp3"
            blob = bucket.blob(blob_name)
            
            # Upload with proper content type
            blob.upload_from_string(
                audio_data,
                content_type="audio/mpeg"
            )
            
            # Make publicly readable
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return None
    
    async def _upload_to_s3(self, cache_key: str, audio_data: bytes) -> Optional[str]:
        """Upload to AWS S3."""
        try:
            import boto3
            
            s3_client = boto3.client('s3')
            
            key = f"audio/{cache_key}.mp3"
            
            s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                Body=audio_data,
                ContentType="audio/mpeg",
                ACL="public-read"
            )
            
            return f"https://{settings.S3_BUCKET_NAME}.s3.amazonaws.com/{key}"
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return None
    
    async def _upload_to_local(self, cache_key: str, audio_data: bytes) -> Optional[str]:
        """Upload to local storage (development only)."""
        try:
            # Create audio directory if it doesn't exist
            audio_dir = Path("static/audio")
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = audio_dir / f"{cache_key}.mp3"
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(audio_data)
            
            return f"{settings.BASE_URL}/static/audio/{cache_key}.mp3"
            
        except Exception as e:
            logger.error(f"Error uploading to local storage: {e}")
            return None
    
    async def _delete_audio_file(self, audio_url: str) -> bool:
        """Delete audio file from cloud storage."""
        try:
            if settings.CLOUD_PROVIDER == "gcp":
                return await self._delete_from_gcs(audio_url)
            elif settings.CLOUD_PROVIDER == "aws":
                return await self._delete_from_s3(audio_url)
            else:
                return await self._delete_from_local(audio_url)
                
        except Exception as e:
            logger.error(f"Error deleting audio file: {e}")
            return False
    
    async def _delete_from_gcs(self, audio_url: str) -> bool:
        """Delete from Google Cloud Storage."""
        try:
            from google.cloud import storage
            
            # Extract blob name from URL
            blob_name = audio_url.split(f"{settings.GCS_BUCKET_NAME}/")[-1]
            
            client = storage.Client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_name)
            
            blob.delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from GCS: {e}")
            return False
    
    async def _delete_from_s3(self, audio_url: str) -> bool:
        """Delete from AWS S3."""
        try:
            import boto3
            
            # Extract key from URL
            key = audio_url.split(f"{settings.S3_BUCKET_NAME}.s3.amazonaws.com/")[-1]
            
            s3_client = boto3.client('s3')
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            return False
    
    async def _delete_from_local(self, audio_url: str) -> bool:
        """Delete from local storage."""
        try:
            # Extract filename from URL
            filename = audio_url.split("/")[-1]
            file_path = Path("static/audio") / filename
            
            if file_path.exists():
                file_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from local storage: {e}")
            return False


class AudioCacheManager:
    """Manager for audio cache operations and background tasks."""
    
    def __init__(self, audio_cache_service: AudioCacheService):
        self.cache_service = audio_cache_service
        self._background_tasks = set()
    
    async def start_background_tasks(self):
        """Start background tasks for cache management."""
        # Pre-generate common prompts on startup
        task1 = asyncio.create_task(self._pre_generate_prompts_task())
        self._background_tasks.add(task1)
        task1.add_done_callback(self._background_tasks.discard)
        
        # Schedule daily cleanup
        task2 = asyncio.create_task(self._daily_cleanup_task())
        self._background_tasks.add(task2)
        task2.add_done_callback(self._background_tasks.discard)
    
    async def _pre_generate_prompts_task(self):
        """Background task to pre-generate common prompts."""
        try:
            await asyncio.sleep(60)  # Wait 1 minute after startup
            stats = await self.cache_service.pre_generate_common_prompts()
            logger.info(f"Pre-generation task completed: {stats}")
        except Exception as e:
            logger.error(f"Error in pre-generation task: {e}")
    
    async def _daily_cleanup_task(self):
        """Background task for daily cache cleanup."""
        while True:
            try:
                # Wait 24 hours
                await asyncio.sleep(24 * 60 * 60)
                
                # Perform cleanup
                cleaned_count = await self.cache_service.cleanup_old_cache()
                logger.info(f"Daily cleanup completed: {cleaned_count} files removed")
                
            except Exception as e:
                logger.error(f"Error in daily cleanup task: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(60 * 60)


# Dependency injection
_audio_cache_service: Optional[AudioCacheService] = None
_audio_cache_manager: Optional[AudioCacheManager] = None


async def get_audio_cache_service() -> AudioCacheService:
    """Get audio cache service instance."""
    global _audio_cache_service
    if _audio_cache_service is None:
        from app.database import get_database
        from app.services.speech_adapter import get_speech_adapter
        
        database = await get_database()
        speech_adapter = await get_speech_adapter()
        _audio_cache_service = AudioCacheService(database, speech_adapter)
    
    return _audio_cache_service


async def get_audio_cache_manager() -> AudioCacheManager:
    """Get audio cache manager instance."""
    global _audio_cache_manager
    if _audio_cache_manager is None:
        cache_service = await get_audio_cache_service()
        _audio_cache_manager = AudioCacheManager(cache_service)
    
    return _audio_cache_manager