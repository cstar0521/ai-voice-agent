#!/usr/bin/env python3
"""
Complete setup test for AI Voice Loan Agent.
Tests all components: Twilio, Speech APIs, Database, etc.
"""

import os
import sys
import asyncio
import requests
import json
from typing import Optional

# Add backend to path
sys.path.append('backend')

async def test_environment_variables():
    """Test that all required environment variables are set."""
    print("🔧 Testing Environment Variables...")
    
    required_vars = {
        "TWILIO_ACCOUNT_SID": "Twilio Account SID",
        "TWILIO_AUTH_TOKEN": "Twilio Auth Token",
        "TWILIO_PHONE_NUMBER": "Twilio Phone Number",
        "OPENAI_API_KEY": "OpenAI API Key",
        "SARVAM_API_KEY": "Sarvam AI API Key",
        "WEBHOOK_BASE_URL": "Webhook Base URL (ngrok)"
    }
    
    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Missing ({description})")
            all_good = False
    
    return all_good

async def test_database_connection():
    """Test MongoDB connection."""
    print("\n📊 Testing Database Connection...")
    
    try:
        from app.database import get_database
        db = await get_database()
        
        # Test connection
        await db.command("ping")
        print("✅ MongoDB connection successful")
        
        # Test collections
        collections = await db.list_collection_names()
        print(f"✅ Found {len(collections)} collections")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_twilio_connection():
    """Test Twilio connection and credentials."""
    print("\n📞 Testing Twilio Connection...")
    
    try:
        from app.integrations.twilio_adapter import TwilioAdapter
        
        adapter = TwilioAdapter()
        if not adapter.client:
            print("❌ Twilio client not initialized")
            return False
        
        # Test account info
        account = adapter.client.api.accounts(adapter.account_sid).fetch()
        print(f"✅ Twilio account: {account.friendly_name}")
        print(f"✅ Account status: {account.status}")
        print(f"✅ Phone number: {adapter.phone_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio connection failed: {e}")
        return False

async def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🧠 Testing OpenAI Connection...")
    
    try:
        import openai
        from config import settings
        
        openai.api_key = settings.openai_api_key
        
        # Test with a simple completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful")
        print(f"✅ Model response: {response.choices[0].message.content.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

async def test_sarvam_connection():
    """Test Sarvam AI connection."""
    print("\n🗣️ Testing Sarvam AI Connection...")
    
    try:
        from app.integrations.sarvam_speech_adapter import SarvamSpeechAdapter
        
        adapter = SarvamSpeechAdapter()
        if not adapter.enabled:
            print("❌ Sarvam AI adapter not enabled")
            return False
        
        # Test TTS
        test_text = "नमस्ते, यह एक टेस्ट है।"
        audio_data = await adapter.synthesize_speech(test_text, "hi-IN")
        
        if audio_data and len(audio_data) > 0:
            print("✅ Sarvam AI TTS working")
            print(f"✅ Generated {len(audio_data)} bytes of audio")
            return True
        else:
            print("❌ Sarvam AI TTS failed - no audio data")
            return False
            
    except Exception as e:
        print(f"❌ Sarvam AI connection failed: {e}")
        return False

async def test_backend_server():
    """Test if backend server is running."""
    print("\n🖥️ Testing Backend Server...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            
            # Test API endpoints
            endpoints = [
                "/api/v1/calls/inbound/webhook",
                "/api/v1/calls/status/webhook",
                "/api/v1/auth/login"
            ]
            
            for endpoint in endpoints:
                try:
                    resp = requests.get(f"http://localhost:8000{endpoint}", timeout=3)
                    # 405 Method Not Allowed is expected for POST endpoints
                    if resp.status_code in [200, 405]:
                        print(f"✅ {endpoint} - Available")
                    else:
                        print(f"⚠️ {endpoint} - Status: {resp.status_code}")
                except:
                    print(f"❌ {endpoint} - Not accessible")
            
            return True
        else:
            print(f"❌ Backend server returned status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running")
        print("   Start it with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Backend server test failed: {e}")
        return False

async def test_ngrok_connection():
    """Test ngrok connection."""
    print("\n🌐 Testing ngrok Connection...")
    
    try:
        webhook_url = os.getenv("WEBHOOK_BASE_URL")
        if not webhook_url or "localhost" in webhook_url:
            print("❌ ngrok URL not configured")
            return False
        
        # Test ngrok URL
        response = requests.get(f"{webhook_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ ngrok URL accessible: {webhook_url}")
            return True
        else:
            print(f"❌ ngrok URL returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ngrok connection failed: {e}")
        return False

async def test_authentication():
    """Test authentication system."""
    print("\n🔐 Testing Authentication...")
    
    try:
        # Test login
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Authentication working")
            print(f"✅ JWT token generated: {token[:20]}...")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🧪 AI Voice Loan Agent - Comprehensive Setup Test")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("Twilio Connection", test_twilio_connection),
        ("OpenAI Connection", test_openai_connection),
        ("Sarvam AI Connection", test_sarvam_connection),
        ("Backend Server", test_backend_server),
        ("ngrok Connection", test_ngrok_connection),
        ("Authentication", test_authentication),
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
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your AI Voice Agent is ready!")
        print("\n🚀 Next Steps:")
        print("1. Start frontend: cd frontend && npm start")
        print("2. Login at: http://localhost:3000")
        print("3. Make test calls from the dashboard")
        print("4. Call your Twilio number: +19789517407")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please fix the issues above.")
        
        if not results.get("Backend Server"):
            print("\n🔧 Quick Fix: Start your backend server:")
            print("   cd backend && python main.py")
        
        if not results.get("ngrok Connection"):
            print("\n🔧 Quick Fix: Check your ngrok setup:")
            print("   Make sure ngrok is running: ngrok http 8000")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())