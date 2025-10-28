#!/usr/bin/env python3
"""
Test script specifically for speech APIs (Sarvam AI and OpenAI).
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append('backend')

async def test_sarvam_tts():
    """Test Sarvam AI Text-to-Speech."""
    print("🗣️ Testing Sarvam AI TTS...")
    
    try:
        from app.integrations.sarvam_speech_adapter import SarvamSpeechAdapter
        
        adapter = SarvamSpeechAdapter()
        if not adapter.enabled:
            print("❌ Sarvam AI not enabled - check API key")
            return False
        
        # Test different languages
        test_cases = [
            ("Hello, this is a test in English.", "en-IN", "English"),
            ("नमस्ते, यह हिंदी में एक टेस्ट है।", "hi-IN", "Hindi"),
            ("హలో, ఇది తెలుగులో ఒక పరీక్ష.", "te-IN", "Telugu")
        ]
        
        for text, lang, lang_name in test_cases:
            try:
                print(f"  Testing {lang_name}: '{text[:30]}...'")
                audio_data = await adapter.synthesize_speech(text, lang)
                
                if audio_data and len(audio_data) > 0:
                    print(f"  ✅ {lang_name} TTS: {len(audio_data)} bytes generated")
                    
                    # Save audio file for testing
                    audio_dir = Path("test_audio")
                    audio_dir.mkdir(exist_ok=True)
                    
                    audio_file = audio_dir / f"test_{lang_name.lower()}.mp3"
                    with open(audio_file, "wb") as f:
                        f.write(audio_data)
                    print(f"  💾 Saved to: {audio_file}")
                else:
                    print(f"  ❌ {lang_name} TTS: No audio generated")
                    
            except Exception as e:
                print(f"  ❌ {lang_name} TTS failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sarvam TTS test failed: {e}")
        return False

async def test_openai_nlu():
    """Test OpenAI for Natural Language Understanding."""
    print("\n🧠 Testing OpenAI NLU...")
    
    try:
        import openai
        from config import settings
        
        if not settings.openai_api_key:
            print("❌ OpenAI API key not configured")
            return False
        
        openai.api_key = settings.openai_api_key
        
        # Test intent detection
        test_utterances = [
            "I need a loan for studying in USA",
            "मुझे अमेरिका में पढ़ाई के लिए लोन चाहिए",
            "Can you help me with education loan?",
            "I want to study masters in Canada"
        ]
        
        for utterance in test_utterances:
            try:
                print(f"  Testing: '{utterance}'")
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI that detects intent from user utterances. Respond with just the intent: 'loan_inquiry', 'greeting', 'goodbye', or 'other'."
                        },
                        {
                            "role": "user",
                            "content": utterance
                        }
                    ],
                    max_tokens=10,
                    temperature=0
                )
                
                intent = response.choices[0].message.content.strip()
                print(f"  ✅ Detected intent: {intent}")
                
            except Exception as e:
                print(f"  ❌ NLU failed for '{utterance}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI NLU test failed: {e}")
        return False

async def test_speech_integration():
    """Test the integrated speech system."""
    print("\n🎯 Testing Speech Integration...")
    
    try:
        from app.integrations.sarvam_speech_adapter import get_speech_adapter
        
        adapter = await get_speech_adapter()
        print(f"✅ Speech adapter loaded: {type(adapter).__name__}")
        
        # Test supported languages
        if hasattr(adapter, 'get_supported_languages'):
            languages = adapter.get_supported_languages()
            print(f"✅ Supported languages: {languages}")
        
        # Test supported voices
        if hasattr(adapter, 'get_supported_voices'):
            for lang in ['hi-IN', 'en-IN']:
                voices = adapter.get_supported_voices(lang)
                print(f"✅ {lang} voices: {voices}")
        
        return True
        
    except Exception as e:
        print(f"❌ Speech integration test failed: {e}")
        return False

async def main():
    """Run all speech API tests."""
    print("🎤 AI Voice Agent - Speech APIs Test")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    tests = [
        ("Sarvam AI TTS", test_sarvam_tts),
        ("OpenAI NLU", test_openai_nlu),
        ("Speech Integration", test_speech_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SPEECH TESTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Speech APIs: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All speech APIs are working!")
        print("🎤 Your AI can now speak and understand!")
    else:
        print(f"\n⚠️ {total - passed} speech tests failed.")
        print("Check your API keys and network connection.")

if __name__ == "__main__":
    asyncio.run(main())