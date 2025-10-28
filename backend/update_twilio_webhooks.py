#!/usr/bin/env python3
"""
Script to update Twilio phone number webhook URLs with the current ngrok URL.
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def update_twilio_webhooks():
    """Update Twilio phone number webhook URLs."""
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    base_url = os.getenv('BASE_URL')
    
    if not all([account_sid, auth_token, phone_number, base_url]):
        print("❌ Missing required environment variables")
        print("Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, BASE_URL")
        return False
    
    print("🔧 Updating Twilio Webhook URLs")
    print(f"Phone Number: {phone_number}")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Construct webhook URLs
        voice_url = f"{base_url}/api/v1/calls/inbound/webhook"
        status_callback_url = f"{base_url}/api/v1/calls/status/webhook"
        
        print(f"Voice URL: {voice_url}")
        print(f"Status Callback URL: {status_callback_url}")
        print()
        
        # Find the phone number
        phone_numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not phone_numbers:
            print(f"❌ Phone number {phone_number} not found in your Twilio account")
            return False
        
        phone_number_resource = phone_numbers[0]
        print(f"📞 Found phone number: {phone_number_resource.phone_number}")
        print(f"Current Voice URL: {phone_number_resource.voice_url}")
        print(f"Current Status Callback URL: {phone_number_resource.status_callback}")
        print()
        
        # Update the phone number configuration
        print("🔄 Updating webhook URLs...")
        phone_number_resource.update(
            voice_url=voice_url,
            voice_method='POST',
            status_callback=status_callback_url,
            status_callback_method='POST'
        )
        
        print("✅ Successfully updated Twilio webhook URLs!")
        print()
        print("Updated Configuration:")
        print(f"  Voice URL: {voice_url}")
        print(f"  Status Callback URL: {status_callback_url}")
        print()
        print("🎉 Your Twilio phone number is now configured with the new ngrok URL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Twilio webhooks: {e}")
        return False

if __name__ == "__main__":
    success = update_twilio_webhooks()
    if not success:
        exit(1)