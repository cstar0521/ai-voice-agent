#!/usr/bin/env python3
"""
Debug script to test LLM initialization in web server context
"""
import sys
import os
sys.path.append('.')

# Test in the same environment as the web server
def test_in_server_context():
    """Test LLM initialization in server context"""
    print("Testing in server context...")
    
    # Import exactly like the web server does
    from config import settings
    print(f"Groq API Key available: {bool(settings.groq_api_key)}")
    print(f"OpenAI API Key available: {bool(settings.openai_api_key)}")
    
    # Test Groq directly
    try:
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        print("✅ Direct Groq works in server context")
    except Exception as e:
        print(f"❌ Direct Groq failed: {e}")
    
    # Test OpenAI directly  
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        print("✅ Direct OpenAI works in server context")
    except Exception as e:
        print(f"❌ Direct OpenAI failed: {e}")
    
    # Test via SmartLLMService
    try:
        from app.services.smart_llm import SmartLLMService
        service = SmartLLMService()
        print("✅ SmartLLMService works in server context")
    except Exception as e:
        print(f"❌ SmartLLMService failed: {e}")

if __name__ == "__main__":
    test_in_server_context()