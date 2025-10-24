"""
Script to seed sample data into MongoDB for testing.
"""
import asyncio
from datetime import datetime, timedelta
import sys

from app.database import database
from app.models.lead import Lead
from app.models.call import Call
from app.models.conversation import Conversation, Turn
from app.repositories.lead_repository import LeadRepository
from app.repositories.call_repository import CallRepository
from app.repositories.conversation_repository import ConversationRepository


async def seed_sample_data():
    """Seed sample leads, calls, and conversations into the database."""
    
    print("🌱 Starting database seeding...")
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Connected to MongoDB")
        
        # Get database instance
        db = database.get_database()
        
        # Initialize repositories
        lead_repo = LeadRepository(db)
        call_repo = CallRepository(db)
        conversation_repo = ConversationRepository(db)
        
        # Sample Leads
        sample_leads = [
            Lead(
                lead_id="lead_001",
                phone="+919876543210",
                name="Rajesh Kumar",
                language="hinglish",
                country="US",
                degree="masters",
                loan_amount=50000.0,
                offer_letter="yes",
                coapplicant_itr="yes",
                collateral="yes",
                visa_timeline="2 months",
                eligibility_category="public_secured",
                urgency="high",
                status="qualified"
            ),
            Lead(
                lead_id="lead_002",
                phone="+919876543211",
                name="Priya Sharma",
                language="english",
                country="UK",
                degree="bachelors",
                loan_amount=30000.0,
                offer_letter="yes",
                coapplicant_itr="no",
                collateral="no",
                visa_timeline="3 months",
                eligibility_category="private_unsecured",
                urgency="medium",
                status="qualified"
            ),
            Lead(
                lead_id="lead_003",
                phone="+919876543212",
                name="Venkat Reddy",
                language="telugu",
                country="Canada",
                degree="masters",
                loan_amount=60000.0,
                offer_letter="yes",
                coapplicant_itr="yes",
                collateral="yes",
                visa_timeline="1 month",
                eligibility_category="public_secured",
                urgency="high",
                status="qualified"
            ),
            Lead(
                lead_id="lead_004",
                phone="+919876543213",
                name="Anita Desai",
                language="hinglish",
                country="Australia",
                degree="masters",
                loan_amount=45000.0,
                offer_letter="yes",
                coapplicant_itr="no",
                collateral="no",
                visa_timeline="4 months",
                eligibility_category="private_unsecured",
                urgency="low",
                status="new"
            ),
            Lead(
                lead_id="lead_005",
                phone="+919876543214",
                name="Amit Patel",
                language="english",
                country="Germany",
                degree="masters",
                loan_amount=70000.0,
                offer_letter="yes",
                coapplicant_itr="yes",
                collateral="yes",
                visa_timeline="2 months",
                eligibility_category="intl_usd",
                urgency="high",
                status="qualified"
            )
        ]
        
        print(f"\n📝 Creating {len(sample_leads)} sample leads...")
        for lead in sample_leads:
            try:
                await lead_repo.create(lead)
                print(f"  ✅ Created lead: {lead.name} ({lead.lead_id})")
            except Exception as e:
                print(f"  ⚠️  Lead {lead.lead_id} might already exist: {str(e)}")
        
        # Sample Calls
        sample_calls = [
            Call(
                call_id="call_001",
                lead_id="lead_001",
                call_sid="CA1234567890",
                direction="outbound",
                status="completed",
                duration=180,
                recording_url="https://example.com/recording1.mp3"
            ),
            Call(
                call_id="call_002",
                lead_id="lead_002",
                call_sid="CA1234567891",
                direction="outbound",
                status="completed",
                duration=240,
                recording_url="https://example.com/recording2.mp3"
            ),
            Call(
                call_id="call_003",
                lead_id="lead_003",
                call_sid="CA1234567892",
                direction="inbound",
                status="completed",
                duration=300,
                recording_url="https://example.com/recording3.mp3"
            ),
            Call(
                call_id="call_004",
                lead_id="lead_004",
                call_sid="CA1234567893",
                direction="outbound",
                status="no_answer",
                duration=0,
                retry_count=1
            ),
            Call(
                call_id="call_005",
                lead_id="lead_005",
                call_sid="CA1234567894",
                direction="outbound",
                status="in_progress",
                duration=0
            )
        ]
        
        print(f"\n📞 Creating {len(sample_calls)} sample calls...")
        for call in sample_calls:
            try:
                await call_repo.create(call)
                print(f"  ✅ Created call: {call.call_id} for {call.lead_id}")
            except Exception as e:
                print(f"  ⚠️  Call {call.call_id} might already exist: {str(e)}")
        
        # Sample Conversations
        sample_conversations = [
            Conversation(
                conversation_id="conv_001",
                call_id="call_001",
                lead_id="lead_001",
                language="hinglish",
                turn_history=[
                    Turn(
                        turn_id=1,
                        speaker="agent",
                        text="Namaste! Main aapki education loan mein madad karne ke liye yahan hoon.",
                        intent="greeting",
                        sentiment_score=0.8,
                        timestamp=datetime.utcnow() - timedelta(minutes=5)
                    ),
                    Turn(
                        turn_id=2,
                        speaker="user",
                        text="Hello, mujhe US ke liye loan chahiye.",
                        intent="loan_inquiry",
                        sentiment_score=0.6,
                        timestamp=datetime.utcnow() - timedelta(minutes=4)
                    )
                ],
                current_state="qualification",
                collected_data={
                    "country": "US",
                    "degree": "masters",
                    "loan_amount": 50000
                }
            ),
            Conversation(
                conversation_id="conv_002",
                call_id="call_002",
                lead_id="lead_002",
                language="english",
                turn_history=[
                    Turn(
                        turn_id=1,
                        speaker="agent",
                        text="Hello! I'm here to help you with your education loan.",
                        intent="greeting",
                        sentiment_score=0.9,
                        timestamp=datetime.utcnow() - timedelta(minutes=10)
                    ),
                    Turn(
                        turn_id=2,
                        speaker="user",
                        text="I need a loan for studying in the UK.",
                        intent="loan_inquiry",
                        sentiment_score=0.7,
                        timestamp=datetime.utcnow() - timedelta(minutes=9)
                    )
                ],
                current_state="eligibility_check",
                collected_data={
                    "country": "UK",
                    "degree": "bachelors",
                    "loan_amount": 30000
                }
            )
        ]
        
        print(f"\n💬 Creating {len(sample_conversations)} sample conversations...")
        for conversation in sample_conversations:
            try:
                await conversation_repo.create(conversation)
                print(f"  ✅ Created conversation: {conversation.conversation_id}")
            except Exception as e:
                print(f"  ⚠️  Conversation {conversation.conversation_id} might already exist: {str(e)}")
        
        # Print summary
        print("\n" + "="*50)
        print("📊 Database Seeding Summary")
        print("="*50)
        
        total_leads = await lead_repo.count()
        total_calls = len(await call_repo.list(limit=1000))
        
        print(f"Total Leads: {total_leads}")
        print(f"Total Calls: {total_calls}")
        print(f"Total Conversations: {len(sample_conversations)}")
        
        print("\n✅ Database seeding completed successfully!")
        print("\n🔗 You can now test the API:")
        print("   - GET http://localhost:8000/api/v1/leads")
        print("   - GET http://localhost:8000/api/v1/calls")
        print("   - GET http://localhost:8000/health")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await database.disconnect()
        print("\n👋 Disconnected from MongoDB")


if __name__ == "__main__":
    print("="*50)
    print("🌱 MongoDB Sample Data Seeder")
    print("="*50)
    asyncio.run(seed_sample_data())
