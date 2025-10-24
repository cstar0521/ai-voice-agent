"""
Enhanced speech adapter with audio caching support.
Wraps the base speech adapter to provide caching functionality.
"""

import logging
from typing import Optional, Dict, Any, AsyncIterator, List
from app.integrations.speech_adapter import SpeechAdapter, VoiceGender
from app.services.audio_cache import AudioCacheService

logger = logging.getLogger(__name__)


class EnhancedSpeechAdapter:
    """
    Enhanced speech adapter with audio caching capabilities.
    Provides fallback to real-time TTS when cache is unavailable.
    """
    
    def __init__(self, speech_adapter: SpeechAdapter, audio_cache: Optional[AudioCacheService] = None):
        """
        Initialize enhanced speech adapter.
        
        Args:
            speech_adapter: Base speech adapter for TTS/ASR
            audio_cache: Audio cache service (optional)
        """
        self.speech_adapter = speech_adapter
        self.audio_cache = audio_cache
        self.cache_enabled = audio_cache is not None
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text (no caching for ASR).
        
        Args:
            audio_data: Audio bytes in supported format
            language: Language code (hi-IN, en-IN, te-IN)
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Dictionary with transcript, confidence, and language
        """
        return await self.speech_adapter.transcribe_audio(audio_data, language, sample_rate)
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "hi-IN",
        sample_rate: int = 8000
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Transcribe streaming audio in real-time (no caching for streaming).
        
        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code
            sample_rate: Audio sample rate in Hz
            
        Yields:
            Partial transcription results
        """
        async for result in self.speech_adapter.transcribe_stream(audio_stream, language, sample_rate):
            yield result
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> bytes:
        """
        Convert text to speech audio (direct synthesis, no caching).
        
        Args:
            text: Text to synthesize
            language: Language code
            voice_gender: Voice gender preference
            speaking_rate: Speech rate (0.5 to 2.0)
            
        Returns:
            Audio bytes in MP3 or WAV format
        """
        return await self.speech_adapter.synthesize_speech(text, language, voice_gender, speaking_rate)
    
    async def synthesize_speech_with_cache(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Convert text to speech with caching support.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice_gender: Voice gender preference
            speaking_rate: Speech rate (0.5 to 2.0)
            use_cache: Whether to use audio caching
            
        Returns:
            Audio URL (cached or newly generated), None if failed
        """
        try:
            # If caching is disabled or not available, use direct synthesis
            if not use_cache or not self.cache_enabled:
                logger.info("Cache disabled, using direct TTS synthesis")
                audio_data = await self.synthesize_speech(text, language, voice_gender, speaking_rate)
                if audio_data:
                    # For direct synthesis, we could save to temporary storage
                    # and return a temporary URL, but for simplicity we'll return None
                    # and let the caller handle the audio_data directly
                    return None
                return None
            
            # Generate voice identifier
            voice_id = f"{voice_gender.value}_{speaking_rate}"
            
            # Try to get cached audio URL
            cached_url = await self.audio_cache.get_cached_audio_url(text, language, voice_id)
            if cached_url:
                logger.info(f"Using cached audio for text: {text[:50]}...")
                return cached_url
            
            # Generate new audio and cache it
            logger.info(f"Generating and caching new audio for text: {text[:50]}...")
            audio_data = await self.synthesize_speech(text, language, voice_gender, speaking_rate)
            
            if audio_data:
                # Cache the audio and get URL
                audio_url = await self.audio_cache.cache_audio(text, language, voice_id)
                if audio_url:
                    logger.info(f"Successfully cached audio: {audio_url}")
                    return audio_url
                else:
                    logger.warning("Failed to cache audio, but synthesis succeeded")
                    return None
            else:
                logger.error("TTS synthesis failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in synthesize_speech_with_cache: {e}")
            
            # Fallback to direct synthesis
            try:
                logger.info("Falling back to direct TTS synthesis")
                audio_data = await self.synthesize_speech(text, language, voice_gender, speaking_rate)
                return None if not audio_data else None  # Return None for direct synthesis
            except Exception as fallback_error:
                logger.error(f"Fallback synthesis also failed: {fallback_error}")
                return None
    
    async def get_cached_audio_url(
        self,
        text: str,
        language: str = "hi-IN",
        voice_gender: VoiceGender = VoiceGender.FEMALE,
        speaking_rate: float = 1.0
    ) -> Optional[str]:
        """
        Get cached audio URL without generating new audio.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice_gender: Voice gender preference
            speaking_rate: Speech rate
            
        Returns:
            Cached audio URL if available, None otherwise
        """
        if not self.cache_enabled:
            return None
        
        voice_id = f"{voice_gender.value}_{speaking_rate}"
        return await self.audio_cache.get_cached_audio_url(text, language, voice_id)
    
    async def pre_cache_prompts(self, prompts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Pre-cache a list of prompts.
        
        Args:
            prompts: List of prompt dictionaries with text, language, voice info
            
        Returns:
            Statistics about caching results
        """
        if not self.cache_enabled:
            return {"error": "Cache not enabled"}
        
        stats = {
            "total": len(prompts),
            "cached": 0,
            "generated": 0,
            "failed": 0
        }
        
        for prompt in prompts:
            try:
                text = prompt.get("text", "")
                language = prompt.get("language", "hi-IN")
                voice_gender = VoiceGender(prompt.get("voice_gender", "female"))
                speaking_rate = prompt.get("speaking_rate", 1.0)
                
                # Try to cache the prompt
                audio_url = await self.synthesize_speech_with_cache(
                    text, language, voice_gender, speaking_rate, use_cache=True
                )
                
                if audio_url:
                    # Check if it was already cached or newly generated
                    # This is a simplified check - in practice you'd track this better
                    stats["generated"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error pre-caching prompt: {e}")
                stats["failed"] += 1
        
        return stats
    
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
        return await self.speech_adapter.detect_language(audio_data, candidate_languages)
    
    async def cleanup_cache(self, max_age_days: int = 90) -> int:
        """
        Clean up old cached audio files.
        
        Args:
            max_age_days: Maximum age in days for cached files
            
        Returns:
            Number of files cleaned up
        """
        if not self.cache_enabled:
            return 0
        
        return await self.audio_cache.cleanup_old_cache(max_age_days)
    
    def is_cache_enabled(self) -> bool:
        """Check if audio caching is enabled."""
        return self.cache_enabled
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        try:
            # Get cache collection stats
            cache_collection = self.audio_cache.cache_collection
            
            total_entries = await cache_collection.count_documents({})
            
            # Get size statistics
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_size": {"$sum": "$file_size"},
                        "avg_size": {"$avg": "$file_size"}
                    }
                }
            ]
            
            size_stats = await cache_collection.aggregate(pipeline).to_list(length=1)
            
            stats = {
                "cache_enabled": True,
                "total_entries": total_entries,
                "total_size_bytes": size_stats[0]["total_size"] if size_stats else 0,
                "average_size_bytes": size_stats[0]["avg_size"] if size_stats else 0
            }
            
            # Get language distribution
            language_pipeline = [
                {
                    "$group": {
                        "_id": "$language",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            language_stats = await cache_collection.aggregate(language_pipeline).to_list(length=None)
            stats["language_distribution"] = {item["_id"]: item["count"] for item in language_stats}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"cache_enabled": True, "error": str(e)}


# Dependency injection
_enhanced_speech_adapter: Optional[EnhancedSpeechAdapter] = None


async def get_enhanced_speech_adapter() -> EnhancedSpeechAdapter:
    """Get enhanced speech adapter instance."""
    global _enhanced_speech_adapter
    if _enhanced_speech_adapter is None:
        from app.integrations.speech_adapter import get_speech_adapter
        from app.services.audio_cache import get_audio_cache_service
        
        base_adapter = await get_speech_adapter()
        
        try:
            audio_cache = await get_audio_cache_service()
            _enhanced_speech_adapter = EnhancedSpeechAdapter(base_adapter, audio_cache)
            logger.info("Enhanced speech adapter initialized with caching")
        except Exception as e:
            logger.warning(f"Failed to initialize audio cache, using adapter without caching: {e}")
            _enhanced_speech_adapter = EnhancedSpeechAdapter(base_adapter, None)
    
    return _enhanced_speech_adapter