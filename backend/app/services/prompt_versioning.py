"""
Prompt versioning system for managing different versions of voice prompts.
Supports A/B testing, rollback capabilities, and version tracking.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PromptStatus(Enum):
    """Status of a prompt version."""
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ABTestStatus(Enum):
    """Status of A/B test."""
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PromptVersion(BaseModel):
    """Model for prompt version."""
    version_id: str
    prompt_id: str
    state: str
    language: str
    text: str
    voice: Optional[str] = "default"
    audio_url: Optional[str] = None
    version_number: str
    status: PromptStatus = PromptStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance metrics
    usage_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction: float = 0.0


class ABTest(BaseModel):
    """Model for A/B test configuration."""
    test_id: str
    name: str
    description: str
    prompt_id: str
    state: str
    language: str
    
    # Test configuration
    version_a: str  # Control version
    version_b: str  # Test version
    traffic_split: float = 0.5  # Percentage for version B (0.0 to 1.0)
    
    # Test parameters
    status: ABTestStatus = ABTestStatus.PLANNED
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_sample_size: int = 1000
    confidence_level: float = 0.95
    
    # Results
    current_sample_size: int = 0
    version_a_metrics: Dict[str, float] = Field(default_factory=dict)
    version_b_metrics: Dict[str, float] = Field(default_factory=dict)
    statistical_significance: Optional[bool] = None
    winner: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str


class PromptVersioningService:
    """Service for managing prompt versions and A/B testing."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.versions_collection = database.prompt_versions
        self.ab_tests_collection = database.ab_tests
        self.usage_logs_collection = database.prompt_usage_logs
    
    async def create_version(
        self,
        prompt_id: str,
        state: str,
        language: str,
        text: str,
        created_by: str,
        voice: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptVersion:
        """
        Create a new version of a prompt.
        
        Args:
            prompt_id: Unique identifier for the prompt
            state: Conversation state (greeting, qualification, etc.)
            language: Language code
            text: Prompt text
            created_by: User who created the version
            voice: Voice identifier
            notes: Optional notes about the version
            metadata: Additional metadata
            
        Returns:
            Created prompt version
        """
        try:
            # Get next version number
            version_number = await self._get_next_version_number(prompt_id, state, language)
            
            # Create version ID
            version_id = f"{prompt_id}_{state}_{language}_v{version_number}"
            
            # Create version object
            version = PromptVersion(
                version_id=version_id,
                prompt_id=prompt_id,
                state=state,
                language=language,
                text=text,
                voice=voice,
                version_number=version_number,
                created_by=created_by,
                notes=notes,
                metadata=metadata or {}
            )
            
            # Insert into database
            await self.versions_collection.insert_one(version.model_dump())
            
            logger.info(f"Created prompt version: {version_id}")
            return version
            
        except Exception as e:
            logger.error(f"Error creating prompt version: {e}")
            raise
    
    async def get_version(self, version_id: str) -> Optional[PromptVersion]:
        """Get a specific prompt version."""
        try:
            version_doc = await self.versions_collection.find_one({"version_id": version_id})
            if version_doc:
                return PromptVersion(**version_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting prompt version: {e}")
            return None
    
    async def get_active_version(
        self,
        prompt_id: str,
        state: str,
        language: str
    ) -> Optional[PromptVersion]:
        """
        Get the currently active version of a prompt.
        
        Args:
            prompt_id: Prompt identifier
            state: Conversation state
            language: Language code
            
        Returns:
            Active prompt version or None if not found
        """
        try:
            version_doc = await self.versions_collection.find_one({
                "prompt_id": prompt_id,
                "state": state,
                "language": language,
                "status": PromptStatus.ACTIVE.value
            })
            
            if version_doc:
                return PromptVersion(**version_doc)
            
            # If no active version, get the latest version
            latest_doc = await self.versions_collection.find_one(
                {
                    "prompt_id": prompt_id,
                    "state": state,
                    "language": language
                },
                sort=[("version_number", -1)]
            )
            
            if latest_doc:
                return PromptVersion(**latest_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active prompt version: {e}")
            return None
    
    async def get_version_for_ab_test(
        self,
        prompt_id: str,
        state: str,
        language: str,
        user_id: str
    ) -> Optional[PromptVersion]:
        """
        Get prompt version considering A/B tests.
        
        Args:
            prompt_id: Prompt identifier
            state: Conversation state
            language: Language code
            user_id: User identifier for consistent assignment
            
        Returns:
            Prompt version (considering A/B test assignment)
        """
        try:
            # Check for active A/B test
            ab_test = await self._get_active_ab_test(prompt_id, state, language)
            
            if ab_test:
                # Determine which version to use based on user assignment
                version_id = await self._assign_ab_test_version(ab_test, user_id)
                version = await self.get_version(version_id)
                
                if version:
                    # Log usage for A/B test tracking
                    await self._log_ab_test_usage(ab_test.test_id, version_id, user_id)
                    return version
            
            # No A/B test, return active version
            return await self.get_active_version(prompt_id, state, language)
            
        except Exception as e:
            logger.error(f"Error getting version for A/B test: {e}")
            return await self.get_active_version(prompt_id, state, language)
    
    async def activate_version(self, version_id: str) -> bool:
        """
        Activate a specific version (deactivates others).
        
        Args:
            version_id: Version to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the version to activate
            version = await self.get_version(version_id)
            if not version:
                logger.error(f"Version not found: {version_id}")
                return False
            
            # Deactivate all other versions for the same prompt/state/language
            await self.versions_collection.update_many(
                {
                    "prompt_id": version.prompt_id,
                    "state": version.state,
                    "language": version.language,
                    "status": PromptStatus.ACTIVE.value
                },
                {"$set": {"status": PromptStatus.ARCHIVED.value}}
            )
            
            # Activate the specified version
            await self.versions_collection.update_one(
                {"version_id": version_id},
                {"$set": {"status": PromptStatus.ACTIVE.value}}
            )
            
            logger.info(f"Activated prompt version: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating version: {e}")
            return False
    
    async def list_versions(
        self,
        prompt_id: Optional[str] = None,
        state: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[PromptStatus] = None,
        limit: int = 50
    ) -> List[PromptVersion]:
        """
        List prompt versions with optional filters.
        
        Args:
            prompt_id: Filter by prompt ID
            state: Filter by conversation state
            language: Filter by language
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of prompt versions
        """
        try:
            query = {}
            
            if prompt_id:
                query["prompt_id"] = prompt_id
            if state:
                query["state"] = state
            if language:
                query["language"] = language
            if status:
                query["status"] = status.value
            
            cursor = self.versions_collection.find(query).sort("created_at", -1).limit(limit)
            versions_docs = await cursor.to_list(length=limit)
            
            return [PromptVersion(**doc) for doc in versions_docs]
            
        except Exception as e:
            logger.error(f"Error listing versions: {e}")
            return []
    
    async def create_ab_test(
        self,
        name: str,
        description: str,
        prompt_id: str,
        state: str,
        language: str,
        version_a: str,
        version_b: str,
        created_by: str,
        traffic_split: float = 0.5,
        target_sample_size: int = 1000,
        confidence_level: float = 0.95
    ) -> ABTest:
        """
        Create a new A/B test.
        
        Args:
            name: Test name
            description: Test description
            prompt_id: Prompt identifier
            state: Conversation state
            language: Language code
            version_a: Control version ID
            version_b: Test version ID
            created_by: User who created the test
            traffic_split: Percentage for version B (0.0 to 1.0)
            target_sample_size: Target number of samples
            confidence_level: Statistical confidence level
            
        Returns:
            Created A/B test
        """
        try:
            # Validate versions exist
            version_a_obj = await self.get_version(version_a)
            version_b_obj = await self.get_version(version_b)
            
            if not version_a_obj or not version_b_obj:
                raise ValueError("One or both versions not found")
            
            # Generate test ID
            test_id = f"ab_{prompt_id}_{state}_{language}_{int(datetime.now().timestamp())}"
            
            # Create A/B test object
            ab_test = ABTest(
                test_id=test_id,
                name=name,
                description=description,
                prompt_id=prompt_id,
                state=state,
                language=language,
                version_a=version_a,
                version_b=version_b,
                traffic_split=traffic_split,
                target_sample_size=target_sample_size,
                confidence_level=confidence_level,
                created_by=created_by
            )
            
            # Insert into database
            await self.ab_tests_collection.insert_one(ab_test.model_dump())
            
            logger.info(f"Created A/B test: {test_id}")
            return ab_test
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    async def start_ab_test(self, test_id: str) -> bool:
        """Start an A/B test."""
        try:
            result = await self.ab_tests_collection.update_one(
                {"test_id": test_id, "status": ABTestStatus.PLANNED.value},
                {
                    "$set": {
                        "status": ABTestStatus.RUNNING.value,
                        "start_date": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Started A/B test: {test_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error starting A/B test: {e}")
            return False
    
    async def stop_ab_test(self, test_id: str, winner: Optional[str] = None) -> bool:
        """Stop an A/B test and optionally declare a winner."""
        try:
            update_data = {
                "status": ABTestStatus.COMPLETED.value,
                "end_date": datetime.now(timezone.utc)
            }
            
            if winner:
                update_data["winner"] = winner
            
            result = await self.ab_tests_collection.update_one(
                {"test_id": test_id, "status": ABTestStatus.RUNNING.value},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Stopped A/B test: {test_id}, winner: {winner}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error stopping A/B test: {e}")
            return False
    
    async def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test results and analysis."""
        try:
            ab_test_doc = await self.ab_tests_collection.find_one({"test_id": test_id})
            if not ab_test_doc:
                return None
            
            ab_test = ABTest(**ab_test_doc)
            
            # Calculate metrics for both versions
            version_a_metrics = await self._calculate_version_metrics(ab_test.version_a, test_id)
            version_b_metrics = await self._calculate_version_metrics(ab_test.version_b, test_id)
            
            # Perform statistical analysis
            statistical_significance = await self._calculate_statistical_significance(
                version_a_metrics, version_b_metrics, ab_test.confidence_level
            )
            
            return {
                "test_id": test_id,
                "status": ab_test.status.value,
                "sample_size": ab_test.current_sample_size,
                "target_sample_size": ab_test.target_sample_size,
                "version_a": {
                    "version_id": ab_test.version_a,
                    "metrics": version_a_metrics
                },
                "version_b": {
                    "version_id": ab_test.version_b,
                    "metrics": version_b_metrics
                },
                "statistical_significance": statistical_significance,
                "winner": ab_test.winner,
                "confidence_level": ab_test.confidence_level
            }
            
        except Exception as e:
            logger.error(f"Error getting A/B test results: {e}")
            return None
    
    async def rollback_to_version(self, version_id: str) -> bool:
        """
        Rollback to a previous version.
        
        Args:
            version_id: Version to rollback to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the version
            version = await self.get_version(version_id)
            if not version:
                logger.error(f"Version not found for rollback: {version_id}")
                return False
            
            # Stop any active A/B tests for this prompt
            await self.ab_tests_collection.update_many(
                {
                    "prompt_id": version.prompt_id,
                    "state": version.state,
                    "language": version.language,
                    "status": ABTestStatus.RUNNING.value
                },
                {
                    "$set": {
                        "status": ABTestStatus.CANCELLED.value,
                        "end_date": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Activate the rollback version
            success = await self.activate_version(version_id)
            
            if success:
                logger.info(f"Successfully rolled back to version: {version_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error rolling back to version: {e}")
            return False
    
    async def _get_next_version_number(self, prompt_id: str, state: str, language: str) -> str:
        """Get the next version number for a prompt."""
        try:
            # Find the highest version number
            latest_version = await self.versions_collection.find_one(
                {
                    "prompt_id": prompt_id,
                    "state": state,
                    "language": language
                },
                sort=[("version_number", -1)]
            )
            
            if latest_version:
                # Extract numeric part and increment
                current_version = latest_version["version_number"]
                if current_version.startswith("v"):
                    current_version = current_version[1:]
                
                try:
                    version_num = int(current_version) + 1
                except ValueError:
                    version_num = 1
            else:
                version_num = 1
            
            return f"v{version_num}"
            
        except Exception as e:
            logger.error(f"Error getting next version number: {e}")
            return "v1"
    
    async def _get_active_ab_test(
        self,
        prompt_id: str,
        state: str,
        language: str
    ) -> Optional[ABTest]:
        """Get active A/B test for a prompt."""
        try:
            ab_test_doc = await self.ab_tests_collection.find_one({
                "prompt_id": prompt_id,
                "state": state,
                "language": language,
                "status": ABTestStatus.RUNNING.value
            })
            
            if ab_test_doc:
                return ABTest(**ab_test_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active A/B test: {e}")
            return None
    
    async def _assign_ab_test_version(self, ab_test: ABTest, user_id: str) -> str:
        """Assign user to A/B test version consistently."""
        # Use hash of user_id to ensure consistent assignment
        import hashlib
        
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        assignment_value = (hash_value % 100) / 100.0
        
        if assignment_value < ab_test.traffic_split:
            return ab_test.version_b
        else:
            return ab_test.version_a
    
    async def _log_ab_test_usage(self, test_id: str, version_id: str, user_id: str):
        """Log A/B test usage for tracking."""
        try:
            await self.usage_logs_collection.insert_one({
                "test_id": test_id,
                "version_id": version_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"Error logging A/B test usage: {e}")
    
    async def _calculate_version_metrics(self, version_id: str, test_id: str) -> Dict[str, float]:
        """Calculate metrics for a version in an A/B test."""
        try:
            # This is a simplified implementation
            # In practice, you'd calculate real metrics from usage logs
            
            usage_count = await self.usage_logs_collection.count_documents({
                "test_id": test_id,
                "version_id": version_id
            })
            
            # Placeholder metrics - replace with real calculations
            return {
                "usage_count": float(usage_count),
                "success_rate": 0.85,  # Calculate from actual data
                "avg_response_time": 1.2,  # Calculate from actual data
                "user_satisfaction": 4.2  # Calculate from actual data
            }
            
        except Exception as e:
            logger.error(f"Error calculating version metrics: {e}")
            return {}
    
    async def _calculate_statistical_significance(
        self,
        version_a_metrics: Dict[str, float],
        version_b_metrics: Dict[str, float],
        confidence_level: float
    ) -> bool:
        """Calculate statistical significance of A/B test results."""
        try:
            # Simplified statistical significance calculation
            # In practice, you'd use proper statistical tests (t-test, chi-square, etc.)
            
            a_success_rate = version_a_metrics.get("success_rate", 0)
            b_success_rate = version_b_metrics.get("success_rate", 0)
            
            a_sample_size = version_a_metrics.get("usage_count", 0)
            b_sample_size = version_b_metrics.get("usage_count", 0)
            
            # Simple check: need minimum sample size and meaningful difference
            min_sample_size = 100
            min_difference = 0.05  # 5% difference
            
            if (a_sample_size >= min_sample_size and 
                b_sample_size >= min_sample_size and
                abs(a_success_rate - b_success_rate) >= min_difference):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return False


# Dependency injection
_prompt_versioning_service: Optional[PromptVersioningService] = None


async def get_prompt_versioning_service() -> PromptVersioningService:
    """Get prompt versioning service instance."""
    global _prompt_versioning_service
    if _prompt_versioning_service is None:
        from app.database import get_database
        
        database = await get_database()
        _prompt_versioning_service = PromptVersioningService(database)
    
    return _prompt_versioning_service