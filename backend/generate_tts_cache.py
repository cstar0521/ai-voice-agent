"""
Script to generate and cache TTS audio for all voice prompts.
Run this script after seeding prompts to pre-generate audio files.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from app.repositories.prompt_repository import PromptRepository
from app.services.tts_cache_service import TTSCacheService


async def generate_all_audio():
    """Generate TTS audio for all prompts."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Extract database name from URI
    db_name = settings.mongodb_uri.split('/')[-1].split('?')[0] or 'voice_agent'
    db = client[db_name]
    
    # Initialize repositories and services
    prompt_repo = PromptRepository(db)
    tts_service = TTSCacheService(prompt_repo)
    
    print("Starting TTS audio generation for all prompts...")
    print("=" * 60)
    
    # Check if TTS providers are configured
    if not tts_service.use_google and not tts_service.use_aws:
        print("\n⚠️  WARNING: No TTS provider configured!")
        print("Please set either:")
        print("  - Google Cloud: GOOGLE_CLOUD_PROJECT and credentials")
        print("  - AWS: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("\nSkipping audio generation...")
        client.close()
        return
    
    provider = "Google Cloud TTS" if tts_service.use_google else "AWS Polly"
    print(f"Using TTS provider: {provider}")
    print()
    
    # Generate audio for all languages
    for language in ["hinglish", "english", "telugu"]:
        print(f"\n📢 Generating audio for {language.upper()} prompts...")
        print("-" * 60)
        
        results = await tts_service.cache_all_prompts(language)
        
        print(f"\n✅ {language.upper()} Results:")
        print(f"   - Success: {results['success']}")
        print(f"   - Failed: {results['failed']}")
        print(f"   - Skipped: {results['skipped']}")
    
    print("\n" + "=" * 60)
    print("TTS audio generation complete!")
    
    # Close connection
    client.close()


async def regenerate_single_prompt(prompt_id: str):
    """Regenerate audio for a single prompt."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Extract database name from URI
    db_name = settings.mongodb_uri.split('/')[-1].split('?')[0] or 'voice_agent'
    db = client[db_name]
    
    # Initialize repositories and services
    prompt_repo = PromptRepository(db)
    tts_service = TTSCacheService(prompt_repo)
    
    print(f"Regenerating audio for prompt: {prompt_id}")
    
    audio_url = await tts_service.regenerate_prompt_audio(prompt_id)
    
    if audio_url:
        print(f"✅ Successfully generated audio: {audio_url}")
    else:
        print(f"❌ Failed to generate audio for {prompt_id}")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Regenerate specific prompt
        prompt_id = sys.argv[1]
        asyncio.run(regenerate_single_prompt(prompt_id))
    else:
        # Generate all
        asyncio.run(generate_all_audio())
