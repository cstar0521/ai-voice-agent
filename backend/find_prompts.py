"""
Script to find prompts in MongoDB.
"""
import asyncio
from app.database import database


async def find_prompts():
    """Find where prompts are stored in the database."""
    
    print("🔍 Searching for prompts in MongoDB...")
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Connected to MongoDB")
        
        # Get database instance
        db = database.get_database()
        
        # List all collections
        collections = await db.list_collection_names()
        print(f"\n📚 Available collections: {collections}")
        
        # Search for prompts in each collection
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            print(f"\n📊 Collection '{collection_name}': {count} documents")
            
            # Check if it has prompt-like documents
            sample = await collection.find_one({})
            if sample:
                print(f"  Sample keys: {list(sample.keys())[:10]}")
                
                # Check for prompt_id or state fields
                prompt_count = await collection.count_documents({"prompt_id": {"$exists": True}})
                if prompt_count > 0:
                    print(f"  ⭐ Found {prompt_count} documents with 'prompt_id' field!")
                    
                    # Show a sample prompt
                    sample_prompt = await collection.find_one({"prompt_id": {"$exists": True}})
                    print(f"\n  Sample prompt document:")
                    for key, value in sample_prompt.items():
                        if key != '_id':
                            print(f"    {key}: {value}")
                    
                    # Count by language
                    print(f"\n  Prompts by language:")
                    for lang in ['hinglish', 'english', 'telugu']:
                        lang_count = await collection.count_documents({"language": lang})
                        if lang_count > 0:
                            print(f"    {lang}: {lang_count}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()
        print("\n👋 Disconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(find_prompts())
