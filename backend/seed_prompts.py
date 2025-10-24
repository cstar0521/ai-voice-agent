"""
Script to seed voice prompts into MongoDB.
"""
import asyncio
from app.database import database
from app.models.configuration import VoicePrompt
from app.repositories.configuration_repository import ConfigurationRepository


async def seed_prompts():
    """Seed sample voice prompts into the database."""
    
    print("🌱 Starting prompts seeding...")
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Connected to MongoDB")
        
        # Get database instance
        db = database.get_database()
        config_repo = ConfigurationRepository(db)
        
        # Sample prompts for different states and languages
        sample_prompts = [
            # English prompts
            VoicePrompt(
                prompt_id="greeting_english",
                state="greeting",
                language="english",
                text="Hello! Thank you for your interest in education loans. I'm here to help you find the best loan option for your studies abroad. May I know your name?",
                is_active=True,
                version=1
            ),
            VoicePrompt(
                prompt_id="qualification_english",
                state="qualification",
                language="english",
                text="Great! Now, let me ask you a few questions to understand your requirements better. Which country are you planning to study in?",
                is_active=True,
                version=1
            ),
            VoicePrompt(
                prompt_id="eligibility_english",
                state="eligibility_check",
                language="english",
                text="Thank you for providing that information. Based on your details, let me check your eligibility for our education loan programs.",
                is_active=True,
                version=1
            ),
            
            # Hinglish prompts
            VoicePrompt(
                prompt_id="greeting_hinglish",
                state="greeting",
                language="hinglish",
                text="Namaste! Education loan ke liye aapka interest dekhkar bahut khushi hui. Main aapki madad karunga best loan option dhoondhne mein. Aapka naam kya hai?",
                is_active=True,
                version=1
            ),
            VoicePrompt(
                prompt_id="qualification_hinglish",
                state="qualification",
                language="hinglish",
                text="Bahut accha! Ab main aapse kuch sawal poochunga taaki main aapki zarooraton ko samajh sakun. Aap kis country mein padhna chahte hain?",
                is_active=True,
                version=1
            ),
            VoicePrompt(
                prompt_id="eligibility_hinglish",
                state="eligibility_check",
                language="hinglish",
                text="Aapki jaankari dene ke liye dhanyavaad. Aapke details ke basis par, main aapki eligibility check karta hoon hamare education loan programs ke liye.",
                is_active=True,
                version=1
            ),
            
            # Hindi prompts
            VoicePrompt(
                prompt_id="greeting_hindi",
                state="greeting",
                language="hindi",
                text="नमस्ते! शिक्षा ऋण में आपकी रुचि देखकर बहुत खुशी हुई। मैं आपकी मदद करूंगा सबसे अच्छा ऋण विकल्प ढूंढने में। आपका नाम क्या है?",
                is_active=True,
                version=1
            ),
            
            # Telugu prompts
            VoicePrompt(
                prompt_id="greeting_telugu",
                state="greeting",
                language="telugu",
                text="నమస్కారం! విద్యా రుణంలో మీ ఆసక్తి చూసి చాలా సంతోషంగా ఉంది. మీ విదేశ చదువుల కోసం ఉత్తమ రుణ ఎంపికను కనుగొనడంలో నేను మీకు సహాయం చేస్తాను. మీ పేరు ఏమిటి?",
                is_active=True,
                version=1
            ),
            
            # Tamil prompts
            VoicePrompt(
                prompt_id="greeting_tamil",
                state="greeting",
                language="tamil",
                text="வணக்கம்! கல்விக் கடனில் உங்கள் ஆர்வத்தைக் கண்டு மகிழ்ச்சி. உங்கள் வெளிநாட்டுப் படிப்புக்கு சிறந்த கடன் விருப்பத்தைக் கண்டறிய நான் உங்களுக்கு உதவுவேன். உங்கள் பெயர் என்ன?",
                is_active=True,
                version=1
            ),
        ]
        
        print(f"\n📝 Creating {len(sample_prompts)} sample prompts...")
        created_count = 0
        
        for prompt in sample_prompts:
            try:
                # Check if prompt already exists
                existing = await config_repo.get_prompt(prompt.state, prompt.language)
                if existing:
                    print(f"  ⚠️  Prompt already exists: {prompt.state}/{prompt.language}")
                    continue
                
                await config_repo.create_prompt(prompt)
                print(f"  ✅ Created prompt: {prompt.state}/{prompt.language}")
                created_count += 1
            except Exception as e:
                print(f"  ❌ Failed to create prompt {prompt.prompt_id}: {str(e)}")
        
        print(f"\n✅ Prompts seeding completed! Created {created_count} new prompts.")
        
    except Exception as e:
        print(f"\n❌ Error seeding prompts: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()
        print("\n👋 Disconnected from MongoDB")


if __name__ == "__main__":
    print("="*50)
    print("🌱 MongoDB Prompts Seeder")
    print("="*50)
    asyncio.run(seed_prompts())
