#!/usr/bin/env python3
"""
Script to check current Twilio phone number webhook configuration.
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def check_twilio_config():
    """Check current Twilio phone number webhook configuration."""
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, phone_number]):
        print("❌ Missing required environment variables")
        return False
    
    print("🔍 Checking Current Twilio Configuration")
    print(f"Phone Number: {phone_number}")
    print("-" * 50)
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Find the phone number
        phone_numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not phone_numbers:
            print(f"❌ Phone number {phone_number} not found in your Twilio account")
            return False
        
        phone_number_resource = phone_numbers[0]
        
        print(f"📞 Phone Number: {phone_number_resource.phone_number}")
        print(f"📞 Phone Number SID: {phone_number_resource.sid}")
        print()
        print("Current Configuration:")
        print(f"  Voice URL: {phone_number_resource.voice_url}")
        print(f"  Voice Method: {phone_number_resource.voice_method}")
        print(f"  Status Callback: {phone_number_resource.status_callback}")
        print(f"  Status Callback Method: {phone_number_resource.status_callback_method}")
        print()
        
        # Check if URLs match expected
        expected_base = os.getenv('BASE_URL')
        expected_voice = f"{expected_base}/api/v1/calls/inbound/webhook"
        expected_status = f"{expected_base}/api/v1/calls/status/webhook"
        
        print("Expected Configuration:")
        print(f"  Voice URL: {expected_voice}")
        print(f"  Status Callback: {expected_status}")
        print()
        
        voice_match = phone_number_resource.voice_url == expected_voice
        status_match = phone_number_resource.status_callback == expected_status
        
        print("Configuration Status:")
        print(f"  Voice URL: {'✅ Match' if voice_match else '❌ Mismatch'}")
        print(f"  Status Callback: {'✅ Match' if status_match else '❌ Mismatch'}")
        
        if voice_match and status_match:
            print("\n🎉 All webhook URLs are correctly configured!")
        else:
            print("\n⚠️  Webhook URLs need to be updated!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Twilio configuration: {e}")
        return False

if __name__ == "__main__":
    check_twilio_config()