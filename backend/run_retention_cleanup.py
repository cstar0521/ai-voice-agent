"""
Background job for data retention cleanup.
Run this script daily via cron or scheduler to delete old recordings.

Example cron entry (runs daily at 2 AM):
0 2 * * * cd /path/to/backend && python run_retention_cleanup.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from app.services.data_retention_service import DataRetentionService
from app.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", log_file="/var/log/voice-agent-retention.log")
logger = get_logger('security')


async def run_cleanup():
    """Run the retention cleanup job."""
    logger.info("=" * 60)
    logger.info("Starting data retention cleanup job")
    logger.info("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Extract database name from URI
    db_name = settings.mongodb_uri.split('/')[-1].split('?')[0] or 'voice_agent'
    db = client[db_name]
    
    # Initialize service
    retention_service = DataRetentionService(db)
    
    try:
        # Run cleanup
        result = await retention_service.schedule_retention_cleanup()
        
        logger.info("Cleanup job completed successfully")
        logger.info(f"Deleted recordings: {result['deletion_stats']['deleted_count']}")
        logger.info(f"Failed deletions: {result['deletion_stats']['failed_count']}")
        logger.info(f"Pending old recordings: {result['retention_stats']['old_recordings_pending_deletion']}")
        
        print("\n" + "=" * 60)
        print("Data Retention Cleanup Summary")
        print("=" * 60)
        print(f"Deleted recordings: {result['deletion_stats']['deleted_count']}")
        print(f"Failed deletions: {result['deletion_stats']['failed_count']}")
        print(f"Pending old recordings: {result['retention_stats']['old_recordings_pending_deletion']}")
        print(f"Total recordings: {result['retention_stats']['total_recordings']}")
        print(f"Retention period: {result['retention_stats']['retention_days']} days")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}", exc_info=True)
        print(f"\nERROR: Cleanup job failed: {e}\n")
        sys.exit(1)
    finally:
        # Close connection
        client.close()
    
    logger.info("=" * 60)
    logger.info("Data retention cleanup job finished")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_cleanup())
