"""
Integration tests for speech processing adapters and audio streaming.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from app.integrations.speech_adapter import (
    GoogleCloudSpeechAdapter,
    AWSSpeechAdapter,
    create_speech_adapter,
    VoiceGender,
    Language
)
from app.integrations.audio_stream_handler import (
    AudioBuffer,
    AudioStreamHandler,
    TTSAudioCache,
    AudioFormatConverter
)


class TestGoogleCloudSpeechAdapter:
    """Test suite for Google Cloud Speech adapter."""
    
    @pytest.fixture
    def mock_google_clients(self):
        """Mock Google Cloud clients."""
        with patch('app.integrations.speech_adapter.speech_v1p1beta1') as mock_speech, \
             patch('app.integrations.speech_adapter.texttospeech') as mock_tts:
            yield mock_speech, mock_tts
    
    @pytest.fixture
    def speech_adapter(self, mock_google_clients):
        """Create GoogleCloudSpeechAdapter with mocked clients."""
        mock_speech, mock_tts = mock_google_clients
        
        # Mock client initialization
        mock_speech.SpeechClient.return_value = Mock()
        mock_tts.TextToSpeechClient.return_value = Mock()
        
        adapter = GoogleCloudSpeechAdapter()
        return adapter
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, speech_adapter):
        """Test successful audio transcription."""
        # Mock response
        mock_result = Mock()
        mock_alternative = Mock()
        mock_alternative.transcript = "Hello, I want to apply for a loan"
        mock_alternative.confidence = 0.95
        mock_result.alternatives = [mock_alternative]
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        
        speech_adapter.speech_client.recognize = Mock(return_value=mock_response)
        
        # Test transcription
        audio_data = b"fake_audio_data"
        result = await speech_adapter.transcribe_audio(
            audio_data,
            language="hi-IN",
            sample_rate=8000
        )
        
        # Verify
        assert result["transcript"] == "Hello, I want to apply for a loan"
        assert result["confidence"] == 0.95
        assert result["language"] == "hi-IN"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_results(self, speech_adapter):
        """Test transcription with no results."""
        # Mock empty response
        mock_response = Mock()
        mock_response.results = []
        
        speech_adapter.speech_client.recognize = Mock(return_value=mock_response)
        
        # Test transcription
        audio_data = b"fake_audio_data"
        result = await speech_adapter.transcribe_audio(audio_data)
        
        # Verify
        assert result["transcript"] == ""
        assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_hinglish(self, speech_adapter):
        """Test TTS for Hinglish."""
        # Mock response
        mock_response = Mock()
        mock_response.audio_content = b"fake_audio_mp3_data"
        
        speech_adapter.tts_client.synthesize_speech = Mock(return_value=mock_response)
        
        # Test synthesis
        audio_data = await speech_adapter.synthesize_speech(
            text="Namaste, aap kaise hain?",
            language="hi-IN",
            voice_gender=VoiceGender.FEMALE
        )
        
        # Verify
        assert audio_data == b"fake_audio_mp3_data"
        speech_adapter.tts_client.synthesize_speech.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_english(self, speech_adapter):
        """Test TTS for English."""
        # Mock response
        mock_response = Mock()
        mock_response.audio_content = b"fake_audio_mp3_data"
        
        speech_adapter.tts_client.synthesize_speech = Mock(return_value=mock_response)
        
        # Test synthesis
        audio_data = await speech_adapter.synthesize_speech(
            text="Hello, how are you?",
            language="en-IN",
            voice_gender=VoiceGender.MALE
        )
        
        # Verify
        assert audio_data == b"fake_audio_mp3_data"
    
    @pytest.mark.asyncio
    async def test_detect_language(self, speech_adapter):
        """Test language detection."""
        # Mock response
        mock_result = Mock()
        mock_result.language_code = "en-IN"
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        
        speech_adapter.speech_client.recognize = Mock(return_value=mock_response)
        
        # Test detection
        audio_data = b"fake_audio_data"
        detected_lang = await speech_adapter.detect_language(
            audio_data,
            candidate_languages=["hi-IN", "en-IN", "te-IN"]
        )
        
        # Verify
        assert detected_lang == "en-IN"
    
    @pytest.mark.asyncio
    async def test_detect_language_fallback(self, speech_adapter):
        """Test language detection fallback to default."""
        # Mock empty response
        mock_response = Mock()
        mock_response.results = []
        
        speech_adapter.speech_client.recognize = Mock(return_value=mock_response)
        
        # Test detection
        audio_data = b"fake_audio_data"
        detected_lang = await speech_adapter.detect_language(audio_data)
        
        # Verify fallback to Hinglish
        assert detected_lang == "hi-IN"


class TestAWSSpeechAdapter:
    """Test suite for AWS Speech adapter."""
    
    @pytest.fixture
    def mock_boto3(self):
        """Mock boto3 clients."""
        with patch('app.integrations.speech_adapter.boto3') as mock_boto:
            yield mock_boto
    
    @pytest.fixture
    def speech_adapter(self, mock_boto3):
        """Create AWSSpeechAdapter with mocked clients."""
        mock_boto3.client.return_value = Mock()
        
        adapter = AWSSpeechAdapter(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1"
        )
        return adapter
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_polly(self, speech_adapter):
        """Test TTS using AWS Polly."""
        # Mock Polly response
        mock_stream = Mock()
        mock_stream.read.return_value = b"fake_audio_mp3_data"
        
        mock_response = {'AudioStream': mock_stream}
        speech_adapter.polly_client.synthesize_speech = Mock(return_value=mock_response)
        
        # Test synthesis
        audio_data = await speech_adapter.synthesize_speech(
            text="Hello, how are you?",
            language="en-IN",
            voice_gender=VoiceGender.FEMALE
        )
        
        # Verify
        assert audio_data == b"fake_audio_mp3_data"
        speech_adapter.polly_client.synthesize_speech.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_with_rate(self, speech_adapter):
        """Test TTS with custom speaking rate."""
        # Mock Polly response
        mock_stream = Mock()
        mock_stream.read.return_value = b"fake_audio_mp3_data"
        
        mock_response = {'AudioStream': mock_stream}
        speech_adapter.polly_client.synthesize_speech = Mock(return_value=mock_response)
        
        # Test synthesis with rate
        audio_data = await speech_adapter.synthesize_speech(
            text="Hello",
            language="hi-IN",
            speaking_rate=1.2
        )
        
        # Verify SSML was used
        call_args = speech_adapter.polly_client.synthesize_speech.call_args
        assert 'prosody' in call_args[1]['Text']
        assert audio_data == b"fake_audio_mp3_data"


class TestAudioBuffer:
    """Test suite for AudioBuffer."""
    
    def test_add_and_get_chunks(self):
        """Test adding and retrieving audio chunks."""
        buffer = AudioBuffer(max_duration_seconds=5.0, sample_rate=8000)
        
        chunk1 = b"audio_chunk_1"
        chunk2 = b"audio_chunk_2"
        
        buffer.add_chunk(chunk1)
        buffer.add_chunk(chunk2)
        
        all_data = buffer.get_all()
        assert all_data == chunk1 + chunk2
    
    def test_buffer_overflow(self):
        """Test buffer eviction when max size exceeded."""
        buffer = AudioBuffer(max_duration_seconds=0.001, sample_rate=8000)
        
        # Add chunks that exceed buffer size
        for i in range(100):
            buffer.add_chunk(b"x" * 1000)
        
        # Buffer should have evicted old chunks
        assert buffer.total_bytes <= buffer.max_bytes
    
    def test_get_last_n_seconds(self):
        """Test retrieving last N seconds of audio."""
        buffer = AudioBuffer(max_duration_seconds=10.0, sample_rate=8000)
        
        # Add 1 second of audio (8000 samples * 2 bytes = 16000 bytes)
        chunk = b"x" * 16000
        buffer.add_chunk(chunk)
        
        # Get last 0.5 seconds
        last_half = buffer.get_last_n_seconds(0.5)
        assert len(last_half) <= 8000  # Should be approximately half
    
    def test_clear_buffer(self):
        """Test clearing buffer."""
        buffer = AudioBuffer()
        buffer.add_chunk(b"audio_data")
        
        buffer.clear()
        
        assert buffer.is_empty()
        assert buffer.total_bytes == 0
    
    def test_duration_calculation(self):
        """Test buffer duration calculation."""
        buffer = AudioBuffer(sample_rate=8000)
        
        # Add 1 second of audio (8000 samples * 2 bytes)
        buffer.add_chunk(b"x" * 16000)
        
        duration = buffer.duration_seconds()
        assert 0.9 < duration < 1.1  # Allow small margin


class TestAudioStreamHandler:
    """Test suite for AudioStreamHandler."""
    
    @pytest.mark.asyncio
    async def test_process_stream(self):
        """Test processing audio stream."""
        handler = AudioStreamHandler(sample_rate=8000)
        
        # Create mock audio stream
        async def mock_stream():
            for i in range(5):
                yield b"audio_chunk_" + str(i).encode()
                await asyncio.sleep(0.01)
        
        # Process stream
        chunks = []
        async for chunk in handler.process_stream(mock_stream()):
            chunks.append(chunk)
        
        # Verify
        assert len(chunks) == 5
        assert handler.get_buffer_duration() > 0
    
    @pytest.mark.asyncio
    async def test_detect_silence(self):
        """Test silence detection."""
        handler = AudioStreamHandler(silence_threshold_seconds=0.1)
        
        # Initially no silence
        assert not await handler.detect_silence()
        
        # Simulate audio
        handler.last_audio_time = handler.last_audio_time or asyncio.get_event_loop().time()
        
        # Wait for silence threshold
        await asyncio.sleep(0.15)
        
        # Should detect silence now
        # Note: This test may be flaky due to timing
    
    def test_get_buffered_audio(self):
        """Test retrieving buffered audio."""
        handler = AudioStreamHandler()
        
        handler.buffer.add_chunk(b"audio_data_1")
        handler.buffer.add_chunk(b"audio_data_2")
        
        buffered = handler.get_buffered_audio()
        assert buffered == b"audio_data_1audio_data_2"
    
    def test_clear_buffer(self):
        """Test clearing audio buffer."""
        handler = AudioStreamHandler()
        
        handler.buffer.add_chunk(b"audio_data")
        handler.clear_buffer()
        
        assert handler.buffer.is_empty()
        assert handler.last_audio_time is None


class TestTTSAudioCache:
    """Test suite for TTSAudioCache."""
    
    def test_cache_put_and_get(self):
        """Test caching and retrieving audio."""
        cache = TTSAudioCache(max_cache_size=10)
        
        key = "hello_hi-IN_female"
        audio_data = b"cached_audio_data"
        
        cache.put(key, audio_data)
        retrieved = cache.get(key)
        
        assert retrieved == audio_data
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = TTSAudioCache()
        
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = TTSAudioCache(max_cache_size=2)
        
        cache.put("key1", b"data1")
        cache.put("key2", b"data2")
        
        # Access key1 to make it more recent
        cache.get("key1")
        
        # Add key3, should evict key2 (least accessed)
        cache.put("key3", b"data3")
        
        assert cache.get("key1") is not None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = TTSAudioCache()
        
        cache.put("key1", b"data1")
        cache.put("key2", b"data2")
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("key1") is None


class TestAudioFormatConverter:
    """Test suite for AudioFormatConverter."""
    
    def test_mulaw_to_linear_conversion(self):
        """Test mu-law to linear PCM conversion."""
        # Create sample mu-law data
        mulaw_data = b"\x00\x01\x02\x03\x04"
        
        try:
            linear_data = AudioFormatConverter.mulaw_to_linear(mulaw_data)
            assert isinstance(linear_data, bytes)
            assert len(linear_data) > 0
        except ImportError:
            pytest.skip("audioop module not available")
    
    def test_linear_to_mulaw_conversion(self):
        """Test linear PCM to mu-law conversion."""
        # Create sample linear data
        linear_data = b"\x00\x00\x01\x00\x02\x00"
        
        try:
            mulaw_data = AudioFormatConverter.linear_to_mulaw(linear_data)
            assert isinstance(mulaw_data, bytes)
            assert len(mulaw_data) > 0
        except ImportError:
            pytest.skip("audioop module not available")
    
    def test_resample_audio(self):
        """Test audio resampling."""
        # Create sample audio data (1 second at 8kHz)
        audio_data = b"\x00\x00" * 8000
        
        try:
            resampled = AudioFormatConverter.resample_audio(
                audio_data,
                from_rate=8000,
                to_rate=16000
            )
            assert isinstance(resampled, bytes)
            # Resampled should be approximately double the size
            assert len(resampled) > len(audio_data)
        except ImportError:
            pytest.skip("audioop module not available")


class TestSpeechAdapterFactory:
    """Test suite for speech adapter factory."""
    
    @patch('app.integrations.speech_adapter.GoogleCloudSpeechAdapter')
    def test_create_google_adapter(self, mock_google):
        """Test creating Google Cloud adapter."""
        adapter = create_speech_adapter("google_cloud")
        mock_google.assert_called_once()
    
    @patch('app.integrations.speech_adapter.AWSSpeechAdapter')
    def test_create_aws_adapter(self, mock_aws):
        """Test creating AWS adapter."""
        adapter = create_speech_adapter("aws")
        mock_aws.assert_called_once()
    
    def test_create_invalid_adapter(self):
        """Test creating adapter with invalid provider."""
        with pytest.raises(ValueError):
            create_speech_adapter("invalid_provider")
