#!/usr/bin/env python3
"""
Script to make a test outbound call via the API.
"""

import requests
import json
import sys
import os
from typing import Optional

def get_jwt_token(email: str = "admin@example.com", password: str = "admin123") -> Optional[str]:
    """Get JWT token for API authentication."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def make_outbound_call(phone_number: str, language: str = "hinglish") -> bool:
    """Make an outbound call via the API."""
    try:
        # Get authentication token
        token = get_jwt_token()
        if not token:
            return False
        
        # Make the call
        response = requests.post(
            "http://localhost:8000/api/v1/calls/outbound",
            json={
                "phone_number": phone_number,
                "language": language,
                "lead_source": "test_script"
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"✅ Call initiated successfully!")
            print(f"📞 Call ID: {call_data.get('call_id')}")
            print(f"📱 Phone: {phone_number}")
            print(f"🗣️  Language: {language}")
            print(f"🆔 Lead ID: {call_data.get('lead_id')}")
            return True
        else:
            print(f"❌ Call failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making call: {e}")
        return False

def main():
    print("📞 AI Voice Loan Agent - Test Call Script")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding correctly")
            sys.exit(1)
    except:
        print("❌ Backend server is not running!")
        print("Please start it with: cd backend && python main.py")
        sys.exit(1)
    
    print("✅ Backend server is running")
    
    # Get phone number from user
    if len(sys.argv) > 1:
        phone_number = sys.argv[1]
    else:
        phone_number = input("Enter phone number (E.164 format, e.g., +1234567890): ").strip()
    
    # Validate phone number format
    if not phone_number.startswith('+') or len(phone_number) < 10:
        print("❌ Invalid phone number format. Use E.164 format: +1234567890")
        sys.exit(1)
    
    # Get language preference
    if len(sys.argv) > 2:
        language = sys.argv[2]
    else:
        print("\nAvailable languages:")
        print("1. hinglish (default)")
        print("2. english") 
        print("3. telugu")
        choice = input("Select language (1-3) or press Enter for hinglish: ").strip()
        
        language_map = {"1": "hinglish", "2": "english", "3": "telugu"}
        language = language_map.get(choice, "hinglish")
    
    print(f"\n🚀 Making test call to {phone_number} in {language}...")
    
    # Make the call
    success = make_outbound_call(phone_number, language)
    
    if success:
        print("\n🎉 Test call initiated!")
        print("\nWhat happens next:")
        print("1. The phone will ring")
        print("2. When answered, you'll hear a greeting")
        print("3. The AI will ask about education loans")
        print("4. Check your backend logs for webhook activity")
        print("5. Check the frontend dashboard for call status")
    else:
        print("\n❌ Test call failed!")
        print("\nTroubleshooting:")
        print("1. Check your Twilio credentials in .env")
        print("2. Verify your Twilio account balance")
        print("3. Make sure ngrok is running and webhooks are configured")
        print("4. Check backend logs for errors")

if __name__ == "__main__":
    main()