"""
Smart LLM service that uses Groq as primary and OpenAI as fallback.
Automatically switches based on availability and cost optimization.
"""

import logging
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)


class SmartLLMService:
    """
    Smart LLM service with automatic provider switching.
    
    Priority:
    1. Groq (Primary - 90% cheaper)
    2. OpenAI (Fallback - reliable but expensive)
    """
    
    def __init__(self):
        """Initialize both LLM clients."""
        self.groq_client = None
        self.openai_client = None
        
        # Initialize Groq if API key is available
        if settings.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.groq_api_key)
                logger.info("✅ Groq client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq: {e}")
                self.groq_client = None
        else:
            self.groq_client = None
        
        # Initialize OpenAI as fallback if API key is available  
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("✅ OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
        
        # Check if at least one client is available
        if not self.groq_client and not self.openai_client:
            raise Exception("❌ No LLM provider available! Please configure Groq or OpenAI API keys in your .env file.")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        force_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using smart provider selection.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Response creativity (0-1)
            force_provider: Force specific provider ("groq" or "openai")
            
        Returns:
            Dictionary with response, provider used, and metadata
        """
        
        # Determine which provider to use
        if force_provider == "groq" and self.groq_client:
            return await self._generate_with_groq(messages, max_tokens, temperature)
        elif force_provider == "openai" and self.openai_client:
            return await self._generate_with_openai(messages, max_tokens, temperature)
        
        # Smart selection: Try Groq first (cheaper), fallback to OpenAI
        if settings.use_groq_primary and self.groq_client:
            try:
                logger.info("🚀 Using Groq (Primary - Cost Optimized)")
                return await self._generate_with_groq(messages, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"⚠️ Groq failed, falling back to OpenAI: {e}")
                if self.openai_client:
                    return await self._generate_with_openai(messages, max_tokens, temperature)
                else:
                    raise Exception("❌ Both Groq and OpenAI unavailable")
        
        # Fallback to OpenAI if Groq is not primary or unavailable
        if self.openai_client:
            logger.info("🔄 Using OpenAI (Fallback)")
            return await self._generate_with_openai(messages, max_tokens, temperature)
        
        raise Exception("❌ No LLM provider available")
    
    async def _generate_with_groq(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate response using Groq."""
        try:
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "response": response.choices[0].message.content,
                "provider": "groq",
                "model": settings.groq_model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "cost_estimate": self._calculate_groq_cost(response.usage.total_tokens if response.usage else 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Groq generation failed: {e}")
            raise
    
    async def _generate_with_openai(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate response using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using cheaper model
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "response": response.choices[0].message.content,
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "cost_estimate": self._calculate_openai_cost(response.usage.total_tokens if response.usage else 0)
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI generation failed: {e}")
            raise
    
    def _calculate_groq_cost(self, tokens: int) -> float:
        """Calculate estimated cost for Groq usage."""
        # Groq pricing: ~$0.00027 per 1K tokens
        return (tokens / 1000) * 0.00027
    
    def _calculate_openai_cost(self, tokens: int) -> float:
        """Calculate estimated cost for OpenAI usage."""
        # OpenAI GPT-3.5 pricing: ~$0.002 per 1K tokens
        return (tokens / 1000) * 0.002
    
    async def test_providers(self) -> Dict[str, Any]:
        """Test both providers and return status."""
        results = {
            "groq": {"available": False, "error": None},
            "openai": {"available": False, "error": None}
        }
        
        # Test Groq
        if self.groq_client:
            try:
                test_response = await self._generate_with_groq(
                    [{"role": "user", "content": "Say 'Hello' in one word"}],
                    max_tokens=10,
                    temperature=0
                )
                results["groq"]["available"] = True
                results["groq"]["response"] = test_response["response"]
                results["groq"]["cost"] = test_response["cost_estimate"]
            except Exception as e:
                results["groq"]["error"] = str(e)
        
        # Test OpenAI
        if self.openai_client:
            try:
                test_response = await self._generate_with_openai(
                    [{"role": "user", "content": "Say 'Hello' in one word"}],
                    max_tokens=10,
                    temperature=0
                )
                results["openai"]["available"] = True
                results["openai"]["response"] = test_response["response"]
                results["openai"]["cost"] = test_response["cost_estimate"]
            except Exception as e:
                results["openai"]["error"] = str(e)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "groq_available": self.groq_client is not None,
            "openai_available": self.openai_client is not None,
            "primary_provider": "groq" if settings.use_groq_primary else "openai",
            "groq_model": settings.groq_model if self.groq_client else None,
            "openai_model": "gpt-3.5-turbo" if self.openai_client else None
        }


# Global instance
_smart_llm_service: Optional[SmartLLMService] = None


def get_smart_llm_service() -> SmartLLMService:
    """Get or create SmartLLM service instance."""
    global _smart_llm_service
    # Always create a new instance to avoid cached initialization errors
    _smart_llm_service = SmartLLMService()
    return _smart_llm_service