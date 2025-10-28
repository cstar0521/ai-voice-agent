#!/usr/bin/env python3
"""
Simple script to test making an outbound call to a lead.
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from config import settings
from app.auth import create_access_token

# API endpoint
BASE_URL = "http://localhost:8000"
OUTBOUND_CALL_ENDPOINT = f"{BASE_URL}/api/v1/calls/outbound"

# Test call data
call_data = {
    "phone_number": "+919934455873",
    "preferred_language": "hinglish",
    "lead_source": "test_script",
    "metadata": {
        "campaign": "education_loan_2025",
        "test": True
    }
}

def make_test_call():
    """Make a test outbound call."""
    print("=" * 60)
    print("AI Voice Loan Agent - Test Call")
    print("=" * 60)
    print(f"\nCalling: {call_data['phone_number']}")
    print(f"Language: {call_data['preferred_language']}")
    print(f"Lead Source: {call_data['lead_source']}")
    print("\nTwilio Configuration:")
    print(f"  Account SID: {settings.twilio_account_sid[:10]}...")
    print(f"  Phone Number: {settings.twilio_phone_number}")
    print("\n" + "-" * 60)
    
    # Generate a test JWT token
    print("\nGenerating authentication token...")
    token_data = {
        "sub": "test_user",
        "email": "test@example.com",
        "role": "admin"
    }
    access_token = create_access_token(token_data)
    
    print("\nAttempting to initiate call...")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(
            OUTBOUND_CALL_ENDPOINT,
            json=call_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("\n✅ Call initiated successfully!")
            print(f"\nCall Details:")
            print(f"  Call ID: {result['call_id']}")
            print(f"  Lead ID: {result['lead_id']}")
            print(f"  Status: {result['status']}")
            print(f"  Created At: {result['created_at']}")
            print("\n" + "=" * 60)
            print("The call should now be connecting to +919934455873")
            print("Check your Twilio dashboard for real-time status:")
            print("https://console.twilio.com/us1/monitor/logs/calls")
            print("=" * 60)
        else:
            print(f"\n❌ Call failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    make_test_call()
