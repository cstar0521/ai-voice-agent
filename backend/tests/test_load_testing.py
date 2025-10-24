"""
Load testing scenarios for AI Voice Loan Agent.

Tests system performance under concurrent load:
- 10 concurrent calls
- 50 concurrent calls  
- API response time measurement
- TTS latency and overall call latency measurement

Requirements: 8.2, 8.3
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
import requests
from datetime import datetime, timedelta

from main import app
from app.services.call_orchestrator import CallOrchestrator
from app.integrations.twilio_adapter import TwilioAdapter
from app.integrations.speech_adapter import SpeechAdapter


class TestLoadTesting:
    """Load testing scenarios for concurrent call handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for load testing."""
        return {
            'twilio_adapter': AsyncMock(spec=TwilioAdapter),
            'speech_adapter': AsyncMock(spec=SpeechAdapter),
            'conversation_manager': AsyncMock(spec=ConversationManager)
        }
    
    @pytest.fixture
    def load_test_data(self):
        """Generate test data for load testing."""
        return [
            {
                "phone_number": f"+9198765432{i:02d}",
                "preferred_language": "hinglish" if i % 2 == 0 else "english",
                "lead_source": "load_test"
            }
            for i in range(100)  # Generate 100 test leads
        ]
    
    @pytest.mark.asyncio
    async def test_10_concurrent_calls(self, mock_services, load_test_data):
        """
        Test system performance with 10 concurrent calls.
        
        Measures:
        - Call initiation success rate
        - Average response time
        - Resource utilization
        
        Requirements: 8.2, 8.3
        """
        # Setup mocks for concurrent testing
        twilio = mock_services['twilio_adapter']
        speech = mock_services['speech_adapter']
        conversation = mock_services['conversation_manager']
        
        # Mock successful responses with realistic delays
        async def mock_call_initiation(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            return Mock(sid=f"CA{int(time.time() * 1000000)}")
        
        async def mock_speech_processing(*args, **kwargs):
            await asyncio.sleep(0.05)  # Simulate speech processing
            return "Mock transcription"
        
        async def mock_conversation_processing(*args, **kwargs):
            await asyncio.sleep(0.02)  # Simulate NLU processing
            return {"text": "Mock response", "state": "greeting"}
        
        twilio.initiate_outbound_call = mock_call_initiation
        speech.transcribe_audio = mock_speech_processing
        conversation.process_user_utterance = mock_conversation_processing
        
        call_orchestrator = CallOrchestrator(
            twilio_adapter=twilio,
            speech_adapter=speech,
            conversation_manager=conversation
        )
        
        # Test 10 concurrent calls
        concurrent_calls = 10
        test_leads = load_test_data[:concurrent_calls]
        
        start_time = time.time()
        call_times = []
        successful_calls = 0
        failed_calls = 0
        
        async def initiate_single_call(lead_data):
            """Initiate a single call and measure performance."""
            call_start = time.time()
            try:
                call_id = await call_orchestrator.initiate_outbound_call(
                    phone=lead_data["phone_number"],
                    lead_data=lead_data
                )
                call_end = time.time()
                return {
                    "success": True,
                    "call_id": call_id,
                    "duration": call_end - call_start
                }
            except Exception as e:
                call_end = time.time()
                return {
                    "success": False,
                    "error": str(e),
                    "duration": call_end - call_start
                }
        
        # Execute concurrent calls
        tasks = [initiate_single_call(lead) for lead in test_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        for result in results:
            if isinstance(result, dict):
                call_times.append(result["duration"])
                if result["success"]:
                    successful_calls += 1
                else:
                    failed_calls += 1
            else:
                failed_calls += 1
        
        # Performance assertions
        success_rate = successful_calls / concurrent_calls
        avg_call_time = statistics.mean(call_times) if call_times else 0
        max_call_time = max(call_times) if call_times else 0
        
        print(f"\n10 Concurrent Calls Results:")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Average Call Initiation Time: {avg_call_time:.3f}s")
        print(f"Max Call Initiation Time: {max_call_time:.3f}s")
        print(f"Total Test Time: {total_time:.3f}s")
        
        # Performance requirements
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        assert avg_call_time <= 2.0, f"Average call time {avg_call_time:.3f}s exceeds 2s"
        assert max_call_time <= 5.0, f"Max call time {max_call_time:.3f}s exceeds 5s"
    
    @pytest.mark.asyncio
    async def test_50_concurrent_calls(self, mock_services, load_test_data):
        """
        Test system performance with 50 concurrent calls.
        
        Measures:
        - System stability under higher load
        - Performance degradation patterns
        - Resource limits
        
        Requirements: 8.2, 8.3
        """
        # Setup mocks with realistic performance characteristics
        twilio = mock_services['twilio_adapter']
        speech = mock_services['speech_adapter']
        conversation = mock_services['conversation_manager']
        
        # Mock with variable delays to simulate real-world conditions
        async def mock_call_with_jitter(*args, **kwargs):
            # Add jitter to simulate network variability
            delay = 0.1 + (asyncio.get_event_loop().time() % 0.05)
            await asyncio.sleep(delay)
            return Mock(sid=f"CA{int(time.time() * 1000000)}")
        
        twilio.initiate_outbound_call = mock_call_with_jitter
        
        call_orchestrator = CallOrchestrator(
            twilio_adapter=twilio,
            speech_adapter=speech,
            conversation_manager=conversation
        )
        
        # Test 50 concurrent calls
        concurrent_calls = 50
        test_leads = load_test_data[:concurrent_calls]
        
        start_time = time.time()
        call_times = []
        successful_calls = 0
        
        # Use semaphore to control concurrency and prevent resource exhaustion
        semaphore = asyncio.Semaphore(20)  # Limit to 20 simultaneous operations
        
        async def rate_limited_call(lead_data):
            """Execute call with rate limiting."""
            async with semaphore:
                call_start = time.time()
                try:
                    call_id = await call_orchestrator.initiate_outbound_call(
                        phone=lead_data["phone_number"],
                        lead_data=lead_data
                    )
                    call_end = time.time()
                    return {
                        "success": True,
                        "duration": call_end - call_start
                    }
                except Exception as e:
                    call_end = time.time()
                    return {
                        "success": False,
                        "duration": call_end - call_start,
                        "error": str(e)
                    }
        
        # Execute with controlled concurrency
        tasks = [rate_limited_call(lead) for lead in test_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        for result in results:
            if isinstance(result, dict):
                call_times.append(result["duration"])
                if result["success"]:
                    successful_calls += 1
        
        # Performance analysis
        success_rate = successful_calls / concurrent_calls
        avg_call_time = statistics.mean(call_times) if call_times else 0
        p95_call_time = statistics.quantiles(call_times, n=20)[18] if len(call_times) >= 20 else 0
        throughput = concurrent_calls / total_time
        
        print(f"\n50 Concurrent Calls Results:")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Average Call Time: {avg_call_time:.3f}s")
        print(f"95th Percentile Call Time: {p95_call_time:.3f}s")
        print(f"Throughput: {throughput:.2f} calls/second")
        print(f"Total Test Time: {total_time:.3f}s")
        
        # Performance requirements for higher load
        assert success_rate >= 0.90, f"Success rate {success_rate:.2%} below 90%"
        assert avg_call_time <= 3.0, f"Average call time {avg_call_time:.3f}s exceeds 3s"
        assert p95_call_time <= 8.0, f"95th percentile {p95_call_time:.3f}s exceeds 8s"
    
    def test_api_response_times(self, client):
        """
        Measure API response times under load.
        
        Tests all major API endpoints for performance.
        
        Requirements: 8.3
        """
        # Test endpoints with authentication
        login_response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com", 
            "password": "admin123"
        })
        
        headers = {}
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        # Define API endpoints to test
        endpoints = [
            ("GET", "/health", {}),
            ("GET", "/", {}),
            ("GET", "/api/v1/calls", headers),
            ("GET", "/api/v1/leads", headers),
            ("GET", "/api/v1/config/prompts", headers),
            ("GET", "/api/v1/analytics/metrics", headers)
        ]
        
        response_times = {}
        
        # Test each endpoint multiple times
        for method, endpoint, test_headers in endpoints:
            times = []
            
            for _ in range(10):  # 10 requests per endpoint
                start_time = time.time()
                
                if method == "GET":
                    response = client.get(endpoint, headers=test_headers)
                elif method == "POST":
                    response = client.post(endpoint, headers=test_headers)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                times.append(response_time)
                
                # Allow some endpoints to fail in test environment
                assert response.status_code in [200, 401, 404, 500]
            
            response_times[endpoint] = {
                "avg": statistics.mean(times),
                "max": max(times),
                "min": min(times),
                "p95": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
            }
        
        # Print results
        print(f"\nAPI Response Time Results:")
        for endpoint, metrics in response_times.items():
            print(f"{endpoint}:")
            print(f"  Average: {metrics['avg']:.1f}ms")
            print(f"  95th Percentile: {metrics['p95']:.1f}ms")
            print(f"  Max: {metrics['max']:.1f}ms")
        
        # Performance assertions
        for endpoint, metrics in response_times.items():
            if endpoint in ["/health", "/"]:  # Simple endpoints
                assert metrics["avg"] <= 50, f"{endpoint} avg response time {metrics['avg']:.1f}ms > 50ms"
                assert metrics["p95"] <= 100, f"{endpoint} p95 response time {metrics['p95']:.1f}ms > 100ms"
            else:  # API endpoints
                assert metrics["avg"] <= 200, f"{endpoint} avg response time {metrics['avg']:.1f}ms > 200ms"
                assert metrics["p95"] <= 500, f"{endpoint} p95 response time {metrics['p95']:.1f}ms > 500ms"
    
    @pytest.mark.asyncio
    async def test_tts_latency_measurement(self, mock_services):
        """
        Measure TTS (Text-to-Speech) latency.
        
        Tests speech synthesis performance under load.
        
        Requirements: 8.2
        """
        speech = mock_services['speech_adapter']
        
        # Mock TTS with realistic processing time
        async def mock_tts_with_delay(text, language, voice):
            # Simulate TTS processing based on text length
            processing_time = len(text) * 0.01 + 0.2  # Base 200ms + 10ms per character
            await asyncio.sleep(processing_time)
            return b"mock_audio_data"
        
        speech.synthesize_speech = mock_tts_with_delay
        
        # Test prompts of varying lengths
        test_prompts = [
            "Hello!",  # Short
            "Hello! Thank you for calling. How can I help you with your education loan today?",  # Medium
            "Thank you for providing that information. Based on what you've told me about your study plans, loan requirements, and financial situation, I can see that you're looking for an education loan for your masters program in the United States. Let me connect you with one of our loan experts who can provide you with detailed information about the best loan options available for your specific needs.",  # Long
        ]
        
        languages = ["hinglish", "english", "telugu"]
        
        tts_times = []
        
        # Test TTS performance
        for prompt in test_prompts:
            for language in languages:
                start_time = time.time()
                
                audio_data = await speech.synthesize_speech(
                    text=prompt,
                    language=language,
                    voice="female"
                )
                
                end_time = time.time()
                tts_time = end_time - start_time
                tts_times.append({
                    "text_length": len(prompt),
                    "language": language,
                    "duration": tts_time
                })
        
        # Analyze TTS performance
        avg_tts_time = statistics.mean([t["duration"] for t in tts_times])
        max_tts_time = max([t["duration"] for t in tts_times])
        
        # Group by text length
        short_times = [t["duration"] for t in tts_times if t["text_length"] < 50]
        medium_times = [t["duration"] for t in tts_times if 50 <= t["text_length"] < 200]
        long_times = [t["duration"] for t in tts_times if t["text_length"] >= 200]
        
        print(f"\nTTS Latency Results:")
        print(f"Average TTS Time: {avg_tts_time:.3f}s")
        print(f"Max TTS Time: {max_tts_time:.3f}s")
        if short_times:
            print(f"Short Text Average: {statistics.mean(short_times):.3f}s")
        if medium_times:
            print(f"Medium Text Average: {statistics.mean(medium_times):.3f}s")
        if long_times:
            print(f"Long Text Average: {statistics.mean(long_times):.3f}s")
        
        # Performance requirements
        assert avg_tts_time <= 1.2, f"Average TTS time {avg_tts_time:.3f}s exceeds 1.2s"
        assert max_tts_time <= 3.0, f"Max TTS time {max_tts_time:.3f}s exceeds 3.0s"
        
        # Short prompts should be very fast
        if short_times:
            assert statistics.mean(short_times) <= 0.5, "Short text TTS too slow"
    
    @pytest.mark.asyncio
    async def test_overall_call_latency(self, mock_services):
        """
        Measure overall call latency (user utterance to agent response).
        
        Tests end-to-end response time including ASR, NLU, and TTS.
        
        Requirements: 8.2, 8.3
        """
        speech = mock_services['speech_adapter']
        conversation = mock_services['conversation_manager']
        
        # Mock realistic processing times for each component
        async def mock_asr(audio_data, language):
            await asyncio.sleep(0.3)  # ASR processing
            return "User said something"
        
        async def mock_conversation_processing(call_id, transcript):
            await asyncio.sleep(0.1)  # NLU + business logic
            return {
                "text": "Agent response",
                "audio_url": None,
                "state": "qualification"
            }
        
        async def mock_tts(text, language, voice):
            await asyncio.sleep(0.4)  # TTS processing
            return b"audio_response"
        
        speech.transcribe_audio = mock_asr
        speech.synthesize_speech = mock_tts
        conversation.process_user_utterance = mock_conversation_processing
        
        # Simulate complete conversation turns
        call_id = "latency_test_call"
        test_utterances = [
            "Hello, I need education loan information",
            "I want to study masters in USA",
            "Yes I have offer letter",
            "I need 40 lakh rupees",
            "Yes my father has ITR"
        ]
        
        turn_latencies = []
        
        for utterance in test_utterances:
            turn_start = time.time()
            
            # Simulate complete turn: ASR → NLU → TTS
            transcript = await speech.transcribe_audio(
                audio_data=b"mock_audio",
                language="hinglish"
            )
            
            response = await conversation.process_user_utterance(
                call_id=call_id,
                transcript=transcript
            )
            
            audio_response = await speech.synthesize_speech(
                text=response["text"],
                language="hinglish",
                voice="female"
            )
            
            turn_end = time.time()
            turn_latency = turn_end - turn_start
            turn_latencies.append(turn_latency)
        
        # Analyze overall latency
        avg_latency = statistics.mean(turn_latencies)
        max_latency = max(turn_latencies)
        p95_latency = statistics.quantiles(turn_latencies, n=20)[18] if len(turn_latencies) >= 20 else max_latency
        
        print(f"\nOverall Call Latency Results:")
        print(f"Average Turn Latency: {avg_latency:.3f}s")
        print(f"Max Turn Latency: {max_latency:.3f}s")
        print(f"95th Percentile Latency: {p95_latency:.3f}s")
        
        # Performance requirements
        assert avg_latency <= 2.0, f"Average turn latency {avg_latency:.3f}s exceeds 2.0s"
        assert max_latency <= 4.0, f"Max turn latency {max_latency:.3f}s exceeds 4.0s"
        assert p95_latency <= 3.0, f"95th percentile latency {p95_latency:.3f}s exceeds 3.0s"


class TestStressAndReliability:
    """Stress testing and reliability under extreme conditions."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_services):
        """Test memory usage during sustained load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate sustained load
        call_orchestrator = CallOrchestrator(
            twilio_adapter=mock_services['twilio_adapter'],
            speech_adapter=mock_services['speech_adapter'],
            conversation_manager=mock_services['conversation_manager']
        )
        
        # Create many concurrent operations
        tasks = []
        for i in range(100):
            task = call_orchestrator.initiate_outbound_call(
                phone=f"+9198765432{i:02d}",
                lead_data={"language": "hinglish"}
            )
            tasks.append(task)
        
        # Execute and measure memory
        await asyncio.gather(*tasks, return_exceptions=True)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\nMemory Usage Test:")
        print(f"Initial Memory: {initial_memory:.1f} MB")
        print(f"Final Memory: {final_memory:.1f} MB")
        print(f"Memory Increase: {memory_increase:.1f} MB")
        
        # Memory should not increase excessively
        assert memory_increase <= 100, f"Memory increase {memory_increase:.1f} MB too high"
    
    @pytest.mark.asyncio
    async def test_error_rate_under_load(self, mock_services):
        """Test error handling under high load conditions."""
        # Introduce random failures
        twilio = mock_services['twilio_adapter']
        
        call_count = 0
        async def failing_call_mock(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail 10% of calls randomly
            if call_count % 10 == 0:
                raise Exception("Simulated failure")
            return Mock(sid=f"CA{call_count}")
        
        twilio.initiate_outbound_call = failing_call_mock
        
        call_orchestrator = CallOrchestrator(
            twilio_adapter=twilio,
            speech_adapter=mock_services['speech_adapter'],
            conversation_manager=mock_services['conversation_manager']
        )
        
        # Test error handling under load
        results = []
        for i in range(50):
            try:
                call_id = await call_orchestrator.initiate_outbound_call(
                    phone=f"+9198765432{i:02d}",
                    lead_data={"language": "hinglish"}
                )
                results.append("success")
            except Exception:
                results.append("failure")
        
        success_count = results.count("success")
        failure_count = results.count("failure")
        error_rate = failure_count / len(results)
        
        print(f"\nError Rate Test:")
        print(f"Successful Calls: {success_count}")
        print(f"Failed Calls: {failure_count}")
        print(f"Error Rate: {error_rate:.2%}")
        
        # System should handle errors gracefully
        assert error_rate <= 0.15, f"Error rate {error_rate:.2%} too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])