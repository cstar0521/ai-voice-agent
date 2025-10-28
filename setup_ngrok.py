#!/usr/bin/env python3
"""
Setup script for ngrok integration with Twilio webhooks.
This script helps configure ngrok URLs for local development.
"""

import os
import sys
import subprocess
import requests
import json
from typing import Optional

def check_ngrok_installed() -> bool:
    """Check if ngrok is installed."""
    try:
        subprocess.run(["ngrok", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_ngrok_url() -> Optional[str]:
    """Get the current ngrok public URL."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
        return None
    except requests.RequestException:
        return None

def update_env_file(ngrok_url: str):
    """Update .env file with ngrok URL."""
    env_path = "backend/.env"
    
    # Read existing .env file
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update webhook base URL
    env_vars['WEBHOOK_BASE_URL'] = ngrok_url
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        f.write("# AI Voice Loan Agent Configuration\n\n")
        f.write("# Database\n")
        f.write(f"MONGODB_URI={env_vars.get('MONGODB_URI', 'mongodb://localhost:27017/voice_agent')}\n\n")
        
        f.write("# Twilio Configuration\n")
        f.write(f"TWILIO_ACCOUNT_SID={env_vars.get('TWILIO_ACCOUNT_SID', '')}\n")
        f.write(f"TWILIO_AUTH_TOKEN={env_vars.get('TWILIO_AUTH_TOKEN', '')}\n")
        f.write(f"TWILIO_PHONE_NUMBER={env_vars.get('TWILIO_PHONE_NUMBER', '')}\n\n")
        
        f.write("# Webhook URLs (ngrok for development)\n")
        f.write(f"WEBHOOK_BASE_URL={ngrok_url}\n")
        f.write(f"BASE_URL={ngrok_url}\n\n")
        
        f.write("# OpenAI\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', '')}\n\n")
        
        f.write("# Speech Provider\n")
        f.write(f"SPEECH_PROVIDER={env_vars.get('SPEECH_PROVIDER', 'sarvam_ai')}\n")
        f.write(f"SARVAM_API_KEY={env_vars.get('SARVAM_API_KEY', '')}\n\n")
        
        f.write("# Security\n")
        f.write(f"JWT_SECRET_KEY={env_vars.get('JWT_SECRET_KEY', 'change-this-to-a-secure-secret-key')}\n")
        f.write(f"API_KEY={env_vars.get('API_KEY', 'your-webhook-api-key')}\n\n")
        
        f.write("# Environment\n")
        f.write(f"ENVIRONMENT={env_vars.get('ENVIRONMENT', 'development')}\n")

def print_twilio_setup_instructions(ngrok_url: str):
    """Print instructions for setting up Twilio webhooks."""
    webhook_url = f"{ngrok_url}/api/v1/calls/inbound/webhook"
    status_callback_url = f"{ngrok_url}/api/v1/calls/status/webhook"
    
    print("\n" + "="*60)
    print("🎉 NGROK SETUP COMPLETE!")
    print("="*60)
    print(f"Your ngrok URL: {ngrok_url}")
    print(f"Webhook URL: {webhook_url}")
    print(f"Status Callback URL: {status_callback_url}")
    
    print("\n📞 TWILIO SETUP INSTRUCTIONS:")
    print("-" * 40)
    print("1. Go to Twilio Console: https://console.twilio.com/")
    print("2. Navigate to Phone Numbers → Manage → Active numbers")
    print("3. Click on your Twilio phone number")
    print("4. In the 'Voice' section, set:")
    print(f"   - Webhook URL: {webhook_url}")
    print("   - HTTP Method: POST")
    print("5. In the 'Status Callback' section, set:")
    print(f"   - Status Callback URL: {status_callback_url}")
    print("   - HTTP Method: POST")
    print("6. Click 'Save configuration'")
    
    print("\n🔧 ENVIRONMENT VARIABLES:")
    print("-" * 40)
    print("Make sure to set these in your backend/.env file:")
    print("- TWILIO_ACCOUNT_SID=your_account_sid")
    print("- TWILIO_AUTH_TOKEN=your_auth_token")
    print("- TWILIO_PHONE_NUMBER=your_twilio_number")
    print("- OPENAI_API_KEY=your_openai_key (for NLU)")
    print("- SARVAM_API_KEY=your_sarvam_key (for Indian languages)")
    
    print("\n🚀 NEXT STEPS:")
    print("-" * 40)
    print("1. Start your backend server: cd backend && python main.py")
    print("2. Test with a call to your Twilio number")
    print("3. Check logs for webhook calls")
    
    print("\n⚠️  IMPORTANT:")
    print("-" * 40)
    print("- Keep ngrok running while testing")
    print("- Restart this script if ngrok URL changes")
    print("- For production, replace ngrok URL with your domain")

def main():
    print("🔧 Setting up ngrok for Twilio webhooks...")
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("❌ ngrok is not installed!")
        print("Please install ngrok:")
        print("1. Go to https://ngrok.com/download")
        print("2. Download and install ngrok")
        print("3. Sign up and get your auth token")
        print("4. Run: ngrok authtoken YOUR_AUTH_TOKEN")
        sys.exit(1)
    
    # Check if ngrok is running
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ ngrok is not running!")
        print("Please start ngrok in another terminal:")
        print("ngrok http 8000")
        print("Then run this script again.")
        sys.exit(1)
    
    print(f"✅ Found ngrok URL: {ngrok_url}")
    
    # Update .env file
    update_env_file(ngrok_url)
    print("✅ Updated .env file with ngrok URL")
    
    # Print setup instructions
    print_twilio_setup_instructions(ngrok_url)

if __name__ == "__main__":
    main()