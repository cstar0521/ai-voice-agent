"""
Simple LLM service - minimal implementation to avoid any conflicts
"""
import logging
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class SimpleLLMService:
    """Simple LLM service with just Groq support"""
    
    def __init__(self):
        self.client = None
        
        if settings.groq_api_key:
            try:
                import groq
                self.client = groq.Groq(api_key=settings.groq_api_key)
                logger.info("✅ Simple Groq client initialized")
            except Exception as e:
                logger.error(f"❌ Simple Groq failed: {e}")
                self.client = None
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a simple response"""
        if not self.client:
            return "माफ करें, कुछ तकनीकी समस्या है। कृपया बाद में कॉल करें।"
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Simple LLM generation failed: {e}")
            return "बहुत अच्छा! आप कौन सी डिग्री करना चाहते हैं? Bachelor's, Master's या PhD?"


# Global instance
_simple_llm = None

def get_simple_llm() -> SimpleLLMService:
    global _simple_llm
    if _simple_llm is None:
        _simple_llm = SimpleLLMService()
    return _simple_llm