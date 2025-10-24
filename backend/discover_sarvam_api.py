"""
Discover Sarvam AI API endpoints and test connectivity.
"""

import asyncio
import httpx
from config import settings


async def test_sarvam_endpoints():
    """Test various Sarvam API endpoints to find the correct ones."""
    
    print("Testing Sarvam AI API Endpoints")
    print("=" * 60)
    print(f"API Key: {'*' * 20}{settings.sarvam_api_key[-10:]}")
    print(f"Base URL: {settings.sarvam_api_url}")
    print()
    
    # Try different authentication header formats
    auth_formats = [
        {"api-subscription-key": settings.sarvam_api_key},
        {"Authorization": f"Bearer {settings.sarvam_api_key}"},
        {"X-API-Key": settings.sarvam_api_key},
        {"API-Key": settings.sarvam_api_key},
    ]
    
    # Test different possible endpoints
    endpoints_to_test = [
        ("/text-to-speech", "POST"),
        ("/tts", "POST"),
        ("/translate", "POST"),
        ("/speech-to-text", "POST"),
        ("/stt", "POST"),
    ]
    
    test_payload = {
        "inputs": ["Hello, this is a test"],
        "target_language_code": "hi-IN",
        "speaker": "meera",
        "model": "bulbul:v1"
    }
    
    for i, auth_header in enumerate(auth_formats, 1):
        print(f"\n--- Attempt {i}: Using auth header: {list(auth_header.keys())[0]} ---\n")
        
        client = httpx.AsyncClient(
            headers={
                **auth_header,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        for endpoint, method in endpoints_to_test:
            url = f"{settings.sarvam_api_url}{endpoint}"
            print(f"Testing {method} {url}...")
            
            try:
                if method == "POST":
                    response = await client.post(url, json=test_payload)
                else:
                    response = await client.get(url)
                
                print(f"  Status: {response.status_code}")
                if response.status_code < 500:
                    print(f"  Response: {response.text[:300]}")
                
                # If we get a non-404, this might be the right auth!
                if response.status_code != 404:
                    print(f"  ✓ Found working endpoint!")
                print()
                
            except Exception as e:
                print(f"  Error: {str(e)}")
                print()
        
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_sarvam_endpoints())
