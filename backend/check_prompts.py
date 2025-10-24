"""
Script to check prompts in MongoDB.
"""
import asyncio
from app.database import database


async def check_prompts():
    """Check prompts in the database."""
    
    print("🔍 Checking prompts in MongoDB...")
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Connected to MongoDB")
        
        # Get database instance
        db = database.get_database()
        
        # Check configurations collection
        config_collection = db.configurations
        
        # Count all documents
        total_count = await config_collection.count_documents({})
        print(f"\n📊 Total documents in configurations collection: {total_count}")
        
        # Count prompts with _type field
        prompt_count = await config_collection.count_documents({"_type": "prompt"})
        print(f"📊 Documents with _type='prompt': {prompt_count}")
        
        # Count documents without _type field
        no_type_count = await config_collection.count_documents({"_type": {"$exists": False}})
        print(f"📊 Documents without _type field: {no_type_count}")
        
        # Show sample documents
        print("\n📄 Sample documents:")
        cursor = config_collection.find().limit(3)
        async for doc in cursor:
            print(f"\n  Document ID: {doc.get('_id')}")
            print(f"  Has _type: {doc.get('_type', 'NO')}")
            print(f"  prompt_id: {doc.get('prompt_id', 'N/A')}")
            print(f"  state: {doc.get('state', 'N/A')}")
            print(f"  language: {doc.get('language', 'N/A')}")
        
        # Count by language
        print("\n📊 Prompts by language:")
        for lang in ['hinglish', 'english', 'telugu']:
            count = await config_collection.count_documents({"language": lang})
            print(f"  {lang}: {count}")
        
        # If no _type field, let's add it
        if no_type_count > 0:
            print(f"\n⚠️  Found {no_type_count} documents without _type field")
            print("🔧 Adding _type='prompt' to all documents with prompt_id...")
            
            result = await config_collection.update_many(
                {"prompt_id": {"$exists": True}, "_type": {"$exists": False}},
                {"$set": {"_type": "prompt"}}
            )
            print(f"✅ Updated {result.modified_count} documents")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()
        print("\n👋 Disconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(check_prompts())
