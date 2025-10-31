"""
Direct HTTP-based LLM service - bypasses SDK issues completely
"""
import logging
import httpx
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class DirectLLMService:
    """Direct HTTP calls to Groq API - no SDK dependencies"""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1"
        
        if self.api_key:
            logger.info("✅ Direct LLM service initialized with Groq API")
        else:
            logger.error("❌ No Groq API key found")
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using direct HTTP calls to Groq API"""
        
        if not self.api_key:
            return "बहुत अच्छा! आप कौन सी डिग्री करना चाहते हैं? Bachelor's, Master's या PhD?"
        
        try:
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            # Make direct HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    logger.info(f"✅ Direct LLM response generated: '{ai_response[:50]}...'")
                    return ai_response
                else:
                    logger.error(f"❌ Groq API error: {response.status_code} - {response.text}")
                    return "बहुत अच्छा! आप कौन सी डिग्री करना चाहते हैं? Bachelor's, Master's या PhD?"
                    
        except Exception as e:
            logger.error(f"❌ Direct LLM failed: {e}")
            return "बहुत अच्छा! आप कौन सी डिग्री करना चाहते हैं? Bachelor's, Master's या PhD?"


# Global instance
_direct_llm = None

def get_direct_llm() -> DirectLLMService:
    global _direct_llm
    if _direct_llm is None:
        _direct_llm = DirectLLMService()
    return _direct_llm