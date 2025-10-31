#!/usr/bin/env python3
"""
Automatically update Twilio webhook URLs with current ngrok URL.
"""

import os
import requests
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

def get_ngrok_url():
    """Get current ngrok URL."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
        return None
    except:
        return None

def update_twilio_webhooks():
    """Update Twilio phone number webhooks."""
    
    # Get credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, twilio_number]):
        print("❌ Missing Twilio credentials in .env file")
        return False
    
    # Get ngrok URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ ngrok is not running!")
        return False
    
    print(f"🔗 Using ngrok URL: {ngrok_url}")
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    try:
        # Find the phone number
        phone_numbers = client.incoming_phone_numbers.list()
        target_number = None
        
        for number in phone_numbers:
            if number.phone_number == twilio_number:
                target_number = number
                break
        
        if not target_number:
            print(f"❌ Phone number {twilio_number} not found in your Twilio account")
            return False
        
        # Update webhooks
        webhook_url = f"{ngrok_url}/api/v1/calls/inbound/webhook"
        status_callback_url = f"{ngrok_url}/api/v1/calls/status/webhook"
        
        target_number.update(
            voice_url=webhook_url,
            voice_method='POST',
            status_callback=status_callback_url,
            status_callback_method='POST'
        )
        
        print("✅ Twilio webhooks updated successfully!")
        print(f"📞 Voice webhook: {webhook_url}")
        print(f"📊 Status callback: {status_callback_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Twilio webhooks: {e}")
        return False

def main():
    print("🔧 Updating Twilio Webhooks with ngrok URL")
    print("=" * 50)
    
    success = update_twilio_webhooks()
    
    if success:
        print("\n🎉 Setup complete! You can now:")
        print("1. Start backend: cd backend && python main.py")
        print("2. Test call: python test_real_call.py")
        print("3. Or call your Twilio number directly")
    else:
        print("\n❌ Setup failed. Please check your configuration.")

if __name__ == "__main__":
    main()