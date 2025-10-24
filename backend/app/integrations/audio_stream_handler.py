"""
Audio streaming and buffering utilities for real-time speech processing.

Handles audio stream management, buffering, and format conversions for
integration with Twilio and speech processing services.
"""

import asyncio
import logging
from typing import AsyncIterator, Optional, List
from collections import deque
from datetime import datetime, timedelta
import io

logger = logging.getLogger(__name__)


class AudioBuffer:
    """
    Circular buffer for audio data with time-based windowing.
    
    Maintains a sliding window of audio chunks for processing.
    """
    
    def __init__(self, max_duration_seconds: float = 10.0, sample_rate: int = 8000):
        """
        Initialize audio buffer.
        
        Args:
            max_duration_seconds: Maximum duration to buffer
            sample_rate: Audio sample rate in Hz
        """
        self.max_duration = max_duration_seconds
        self.sample_rate = sample_rate
        self.buffer: deque = deque()
        self.total_bytes = 0
        self.max_bytes = int(max_duration_seconds * sample_rate * 2)  # 16-bit audio
        
        logger.debug(f"AudioBuffer initialized: {max_duration_seconds}s, {sample_rate}Hz")
    
    def add_chunk(self, chunk: bytes) -> None:
        """
        Add audio chunk to buffer.
        
        Args:
            chunk: Audio data bytes
        """
        self.buffer.append(chunk)
        self.total_bytes += len(chunk)
        
        # Remove old chunks if buffer exceeds max size
        while self.total_bytes > self.max_bytes and self.buffer:
            old_chunk = self.buffer.popleft()
            self.total_bytes -= len(old_chunk)
    
    def get_all(self) -> bytes:
        """
        Get all buffered audio data.
        
        Returns:
            Concatenated audio bytes
        """
        return b''.join(self.buffer)
    
    def get_last_n_seconds(self, seconds: float) -> bytes:
        """
        Get last N seconds of audio.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Audio bytes for specified duration
        """
        target_bytes = int(seconds * self.sample_rate * 2)
        
        if target_bytes >= self.total_bytes:
            return self.get_all()
        
        # Get chunks from the end
        result = []
        bytes_collected = 0
        
        for chunk in reversed(self.buffer):
            result.insert(0, chunk)
            bytes_collected += len(chunk)
            if bytes_collected >= target_bytes:
                break
        
        return b''.join(result)
    
    def clear(self) -> None:
        """Clear all buffered data."""
        self.buffer.clear()
        self.total_bytes = 0
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0
    
    def duration_seconds(self) -> float:
        """Get current buffer duration in seconds."""
        return self.total_bytes / (self.sample_rate * 2)


class AudioStreamHandler:
    """
    Handler for real-time audio streaming with ASR integration.
    
    Manages audio stream from Twilio, buffers chunks, and feeds to speech recognition.
    """
    
    def __init__(
        self,
        sample_rate: int = 8000,
        chunk_duration_ms: int = 100,
        silence_threshold_seconds: float = 2.0
    ):
        """
        Initialize audio stream handler.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_duration_ms: Duration of each audio chunk in milliseconds
            silence_threshold_seconds: Silence duration to trigger processing
        """
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.silence_threshold = silence_threshold_seconds
        
        self.buffer = AudioBuffer(max_duration_seconds=30.0, sample_rate=sample_rate)
        self.is_streaming = False
        self.last_audio_time: Optional[datetime] = None
        
        logger.info(
            f"AudioStreamHandler initialized: {sample_rate}Hz, "
            f"{chunk_duration_ms}ms chunks, {silence_threshold_seconds}s silence threshold"
        )
    
    async def process_stream(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[bytes]:
        """
        Process incoming audio stream and yield chunks for ASR.
        
        Args:
            audio_stream: Async iterator of audio chunks from Twilio
            
        Yields:
            Processed audio chunks ready for speech recognition
        """
        try:
            self.is_streaming = True
            self.last_audio_time = datetime.utcnow()
            
            async for chunk in audio_stream:
                if not chunk:
                    continue
                
                # Add to buffer
                self.buffer.add_chunk(chunk)
                self.last_audio_time = datetime.utcnow()
                
                # Yield chunk for real-time processing
                yield chunk
                
                # Check for silence
                await asyncio.sleep(0.01)  # Small delay to prevent tight loop
                
        except Exception as e:
            logger.error(f"Error processing audio stream: {str(e)}")
            raise
        finally:
            self.is_streaming = False
    
    async def detect_silence(self) -> bool:
        """
        Detect if silence threshold has been exceeded.
        
        Returns:
            True if silence detected, False otherwise
        """
        if self.last_audio_time is None:
            return False
        
        silence_duration = (datetime.utcnow() - self.last_audio_time).total_seconds()
        return silence_duration >= self.silence_threshold
    
    def get_buffered_audio(self, duration_seconds: Optional[float] = None) -> bytes:
        """
        Get buffered audio data.
        
        Args:
            duration_seconds: Optional duration to retrieve (None for all)
            
        Returns:
            Audio bytes
        """
        if duration_seconds is None:
            return self.buffer.get_all()
        return self.buffer.get_last_n_seconds(duration_seconds)
    
    def clear_buffer(self) -> None:
        """Clear audio buffer."""
        self.buffer.clear()
        self.last_audio_time = None
    
    def get_buffer_duration(self) -> float:
        """Get current buffer duration in seconds."""
        return self.buffer.duration_seconds()


class TTSAudioCache:
    """
    Cache for pre-generated TTS audio to reduce latency.
    
    Stores frequently used prompts as pre-generated audio files.
    """
    
    def __init__(self, max_cache_size: int = 100):
        """
        Initialize TTS audio cache.
        
        Args:
            max_cache_size: Maximum number of cached audio files
        """
        self.cache: dict = {}
        self.max_size = max_cache_size
        self.access_count: dict = {}
        
        logger.info(f"TTSAudioCache initialized with max size: {max_cache_size}")
    
    def get(self, key: str) -> Optional[bytes]:
        """
        Get cached audio by key.
        
        Args:
            key: Cache key (typically text + language + voice)
            
        Returns:
            Cached audio bytes or None if not found
        """
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            logger.debug(f"TTS cache hit: {key}")
            return self.cache[key]
        
        logger.debug(f"TTS cache miss: {key}")
        return None
    
    def put(self, key: str, audio_data: bytes) -> None:
        """
        Store audio in cache.
        
        Args:
            key: Cache key
            audio_data: Audio bytes to cache
        """
        # Evict least accessed item if cache is full
        if len(self.cache) >= self.max_size:
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_accessed]
            del self.access_count[least_accessed]
            logger.debug(f"Evicted from TTS cache: {least_accessed}")
        
        self.cache[key] = audio_data
        self.access_count[key] = 0
        logger.debug(f"Added to TTS cache: {key}")
    
    def clear(self) -> None:
        """Clear all cached audio."""
        self.cache.clear()
        self.access_count.clear()
        logger.info("TTS cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class AudioFormatConverter:
    """
    Utility for converting audio between different formats.
    
    Handles conversions needed for Twilio (mulaw) and speech services (linear PCM).
    """
    
    @staticmethod
    def mulaw_to_linear(mulaw_data: bytes) -> bytes:
        """
        Convert mu-law encoded audio to linear PCM.
        
        Args:
            mulaw_data: Mu-law encoded audio bytes
            
        Returns:
            Linear PCM audio bytes
        """
        try:
            import audioop
            return audioop.ulaw2lin(mulaw_data, 2)  # 2 bytes per sample (16-bit)
        except Exception as e:
            logger.error(f"Mu-law to linear conversion failed: {str(e)}")
            raise
    
    @staticmethod
    def linear_to_mulaw(linear_data: bytes) -> bytes:
        """
        Convert linear PCM audio to mu-law encoding.
        
        Args:
            linear_data: Linear PCM audio bytes
            
        Returns:
            Mu-law encoded audio bytes
        """
        try:
            import audioop
            return audioop.lin2ulaw(linear_data, 2)  # 2 bytes per sample (16-bit)
        except Exception as e:
            logger.error(f"Linear to mu-law conversion failed: {str(e)}")
            raise
    
    @staticmethod
    def resample_audio(
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
        sample_width: int = 2
    ) -> bytes:
        """
        Resample audio to different sample rate.
        
        Args:
            audio_data: Input audio bytes
            from_rate: Source sample rate
            to_rate: Target sample rate
            sample_width: Bytes per sample (2 for 16-bit)
            
        Returns:
            Resampled audio bytes
        """
        try:
            import audioop
            return audioop.ratecv(
                audio_data,
                sample_width,
                1,  # mono
                from_rate,
                to_rate,
                None
            )[0]
        except Exception as e:
            logger.error(f"Audio resampling failed: {str(e)}")
            raise
    
    @staticmethod
    def convert_to_wav(
        audio_data: bytes,
        sample_rate: int = 8000,
        channels: int = 1,
        sample_width: int = 2
    ) -> bytes:
        """
        Convert raw PCM audio to WAV format.
        
        Args:
            audio_data: Raw PCM audio bytes
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            sample_width: Bytes per sample
            
        Returns:
            WAV formatted audio bytes
        """
        try:
            import wave
            
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"WAV conversion failed: {str(e)}")
            raise


# Global TTS cache instance
tts_cache = TTSAudioCache(max_cache_size=100)
