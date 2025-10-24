#!/usr/bin/env python3
"""
Direct Twilio test - bypassing the API to test Twilio connection.
"""
from twilio.rest import Client
from config import settings

def test_twilio_direct():
    """Test Twilio connection directly."""
    print("=" * 60)
    print("Direct Twilio Connection Test")
    print("=" * 60)
    
    print(f"\nTwilio Configuration:")
    print(f"  Account SID: {settings.twilio_account_sid}")
    print(f"  Phone Number: {settings.twilio_phone_number}")
    print(f"  Auth Token: {'*' * 20}")
    
    try:
        # Initialize Twilio client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        
        print("\n✅ Twilio client initialized successfully")
        
        # Test: Fetch account details
        print("\nFetching account details...")
        account = client.api.accounts(settings.twilio_account_sid).fetch()
        print(f"  Account Status: {account.status}")
        print(f"  Account Type: {account.type}")
        
        # Test: Make a call
        print(f"\n📞 Initiating call to +919934455873...")
        print("   This will use a simple TwiML that says 'Hello'")
        
        call = client.calls.create(
            to="+919934455873",
            from_=settings.twilio_phone_number,
            twiml='<Response><Say voice="Polly.Aditi" language="hi-IN">Namaste! Yeh ek test call hai. Dhanyavaad!</Say></Response>'
        )
        
        print(f"\n✅ Call initiated successfully!")
        print(f"  Call SID: {call.sid}")
        print(f"  Status: {call.status}")
        print(f"  Direction: {call.direction}")
        print(f"  To: {call.to}")
        print(f"  From: {call.from_}")
        
        print("\n" + "=" * 60)
        print("Check your phone - you should receive a call!")
        print("Also check Twilio Console:")
        print(f"https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_twilio_direct()
