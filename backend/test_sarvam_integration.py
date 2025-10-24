"""
Test script for Sarvam AI speech adapter integration.

This script tests the basic functionality of the Sarvam AI adapter:
- Configuration loading
- Adapter initialization
- API connectivity
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.speech_adapter import create_speech_adapter, SpeechProvider
from config import settings


async def test_sarvam_adapter():
    """Test Sarvam AI adapter initialization and basic functionality."""
    
    print("=" * 60)
    print("Sarvam AI Integration Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking Configuration...")
    print(f"   Speech Provider: {settings.speech_provider}")
    print(f"   Sarvam API URL: {settings.sarvam_api_url}")
    print(f"   Sarvam API Key: {'*' * 20}{settings.sarvam_api_key[-10:] if settings.sarvam_api_key else 'NOT SET'}")
    
    if not settings.sarvam_api_key:
        print("\n   ❌ ERROR: SARVAM_API_KEY not configured in .env file")
        return False
    
    print("   ✓ Configuration loaded successfully")
    
    # Initialize adapter
    print("\n2. Initializing Sarvam AI Adapter...")
    try:
        adapter = create_speech_adapter("sarvam_ai")
        print("   ✓ Adapter initialized successfully")
    except Exception as e:
        print(f"   ❌ ERROR: Failed to initialize adapter: {str(e)}")
        return False
    
    # Test TTS (Text-to-Speech)
    print("\n3. Testing Text-to-Speech...")
    test_text = "नमस्ते, मैं आपकी शिक्षा ऋण में मदद करने के लिए यहाँ हूँ।"
    print(f"   Input text: {test_text}")
    
    try:
        audio_data = await adapter.synthesize_speech(
            text=test_text,
            language="hi-IN"
        )
        print(f"   ✓ TTS successful - Generated {len(audio_data)} bytes of audio")
    except Exception as e:
        print(f"   ❌ ERROR: TTS failed: {str(e)}")
        print(f"   Details: {type(e).__name__}")
        return False
    
    # Test language conversion
    print("\n4. Testing Language Code Conversion...")
    try:
        lang_code = adapter._convert_language_code("hi-IN")
        print(f"   hi-IN -> {lang_code}")
        print("   ✓ Language conversion working")
    except Exception as e:
        print(f"   ❌ ERROR: Language conversion failed: {str(e)}")
        return False
    
    # Cleanup
    print("\n5. Cleaning up...")
    try:
        await adapter.close()
        print("   ✓ Adapter closed successfully")
    except Exception as e:
        print(f"   ⚠ Warning: Cleanup issue: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)
    return True


async def main():
    """Main test runner."""
    try:
        success = await test_sarvam_adapter()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
