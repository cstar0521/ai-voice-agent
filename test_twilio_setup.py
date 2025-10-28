#!/usr/bin/env python3
"""
Test script to verify Twilio integration setup.
"""

import os
import sys
import asyncio
from typing import Optional

# Add backend to path
sys.path.append('backend')

async def test_twilio_connection():
    """Test Twilio connection and credentials."""
    try:
        from app.integrations.twilio_adapter import TwilioAdapter
        
        # Initialize Twilio adapter
        adapter = TwilioAdapter()
        
        if not adapter.client:
            print("❌ Twilio client not initialized. Check your credentials:")
            print("   - TWILIO_ACCOUNT_SID")
            print("   - TWILIO_AUTH_TOKEN") 
            print("   - TWILIO_PHONE_NUMBER")
            return False
        
        print("✅ Twilio client initialized successfully")
        print(f"📞 Phone number: {adapter.phone_number}")
        
        # Test getting account info
        try:
            account = adapter.client.api.accounts(adapter.account_sid).fetch()
            print(f"✅ Account verified: {account.friendly_name}")
            print(f"📊 Account status: {account.status}")
            return True
        except Exception as e:
            print(f"❌ Failed to fetch account info: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Twilio connection: {e}")
        return False

async def test_webhook_endpoints():
    """Test that webhook endpoints are accessible."""
    import requests
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/api/v1/calls/inbound/webhook",
        "/api/v1/calls/status/webhook", 
        "/api/v1/calls/recording/webhook",
        "/api/v1/calls/speech/webhook"
    ]
    
    print("\n🔗 Testing webhook endpoints...")
    
    for endpoint in endpoints:
        try:
            # Test with GET (should return 405 Method Not Allowed, but endpoint exists)
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 405:
                print(f"✅ {endpoint} - Endpoint exists")
            else:
                print(f"⚠️  {endpoint} - Unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Server not running")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def check_environment_variables():
    """Check if required environment variables are set."""
    print("🔧 Checking environment variables...")
    
    required_vars = {
        "TWILIO_ACCOUNT_SID": "Twilio Account SID",
        "TWILIO_AUTH_TOKEN": "Twilio Auth Token", 
        "TWILIO_PHONE_NUMBER": "Twilio Phone Number",
        "WEBHOOK_BASE_URL": "Webhook Base URL (ngrok)",
    }
    
    optional_vars = {
        "OPENAI_API_KEY": "OpenAI API Key (for NLU)",
        "SARVAM_API_KEY": "Sarvam AI Key (for Indian languages)",
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "TOKEN" in var or "KEY" in var:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set ({description})")
            all_good = False
    
    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"⚠️  {var}: Not set ({description})")
    
    return all_good

async def main():
    print("🧪 Testing Twilio Integration Setup")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n❌ Some required environment variables are missing!")
        print("Please set them in backend/.env file")
        return
    
    print("\n📞 Testing Twilio connection...")
    twilio_ok = await test_twilio_connection()
    
    print("\n🌐 Testing webhook endpoints...")
    await test_webhook_endpoints()
    
    if twilio_ok:
        print("\n🎉 Twilio integration setup looks good!")
        print("\nNext steps:")
        print("1. Make sure ngrok is running: ngrok http 8000")
        print("2. Run setup_ngrok.py to configure webhooks")
        print("3. Update Twilio phone number configuration")
        print("4. Test with a phone call!")
    else:
        print("\n❌ Twilio setup needs attention. Check your credentials.")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    asyncio.run(main())