#!/usr/bin/env python3
"""
Minimal Sarvam AI test - no external dependencies except requests.
"""

import json
import requests

# Get API key from environment
import os
API_KEY = os.getenv("SARVAM_API_KEY", "your_sarvam_api_key_here")
API_URL = "https://api.sarvam.ai"

def test_sarvam_tts():
    """Test Sarvam AI Text-to-Speech."""
    
    print(f"🔑 Testing API Key: {API_KEY[:15]}...")
    
    url = f"{API_URL}/text-to-speech"
    
    headers = {
        "api-subscription-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": ["Hello, this is a test"],
        "target_language_code": "hi-IN", 
        "speaker": "anushka",
        "model": "bulbul:v2"
    }
    
    print(f"\n🧪 Testing TTS")
    print(f"📡 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! TTS works!")
            print(f"📄 Response keys: {list(result.keys())}")
            
            if "audios" in result and result["audios"]:
                audio_data = result["audios"][0]
                print(f"🎵 Audio data: {len(audio_data)} chars")
                
                # Try to save audio
                try:
                    import base64
                    audio_bytes = base64.b64decode(audio_data)
                    with open("sarvam_test.wav", "wb") as f:
                        f.write(audio_bytes)
                    print(f"💾 Audio saved to sarvam_test.wav ({len(audio_bytes)} bytes)")
                except Exception as e:
                    print(f"⚠️ Could not save audio: {e}")
            
            return True
            
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_sarvam_translate():
    """Test Sarvam AI Translation."""
    
    url = f"{API_URL}/translate"
    
    headers = {
        "api-subscription-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": "Hello world",
        "source_language_code": "en-IN",
        "target_language_code": "hi-IN"
    }
    
    print(f"\n🧪 Testing Translation")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Translation works!")
            print(f"📄 Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run tests."""
    
    print("🚀 Minimal Sarvam AI Test")
    print("=" * 40)
    
    # Test TTS
    tts_ok = test_sarvam_tts()
    
    # Test Translation  
    translate_ok = test_sarvam_translate()
    
    print("\n" + "=" * 40)
    print("📊 Results:")
    print(f"   TTS: {'✅ PASS' if tts_ok else '❌ FAIL'}")
    print(f"   Translation: {'✅ PASS' if translate_ok else '❌ FAIL'}")
    
    if tts_ok or translate_ok:
        print("\n🎉 Your Sarvam API key works!")
    else:
        print("\n❌ API key issues - check subscription")
    
    print("=" * 40)

if __name__ == "__main__":
    main()