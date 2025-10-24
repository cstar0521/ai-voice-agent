"""
CRM Adapter for lead management integration.

This module provides an adapter for integrating with CRM systems
to create, update, and sync lead data.
"""

import os
from typing import Optional, Dict, Any
import logging
import httpx

logger = logging.getLogger(__name__)


class CRMAdapter:
    """
    Adapter class for CRM integration.
    
    Handles:
    - Lead creation and updates
    - Expert notification for handoffs
    - Lead data synchronization
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize CRM adapter with credentials.
        
        Args:
            api_url: CRM API base URL (defaults to env var)
            api_key: CRM API key (defaults to env var)
        """
        self.api_url = api_url or os.getenv("CRM_API_URL", "https://api.crm.example.com")
        self.api_key = api_key or os.getenv("CRM_API_KEY")
        
        if not self.api_key:
            logger.warning("CRM API key not provided. CRM integration will be disabled.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"CRMAdapter initialized with URL: {self.api_url}")
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new lead in CRM.
        
        Args:
            lead_data: Dictionary with lead information
        
        Returns:
            CRM lead ID if successful, None otherwise
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping lead creation")
            return None
        
        try:
            logger.info(f"Creating lead in CRM: {lead_data.get('phone')}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/leads",
                    json=lead_data,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                crm_lead_id = result.get("id") or result.get("lead_id")
                logger.info(f"Lead created in CRM with ID: {crm_lead_id}")
                
                return crm_lead_id
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating lead in CRM: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating lead in CRM: {str(e)}")
            return None
    
    async def update_lead(
        self,
        lead_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing lead in CRM.
        
        Args:
            lead_id: CRM lead identifier
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping lead update")
            return False
        
        try:
            logger.info(f"Updating lead in CRM: {lead_id}")
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/leads/{lead_id}",
                    json=updates,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                logger.info(f"Lead {lead_id} updated successfully in CRM")
                
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error updating lead in CRM: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error updating lead in CRM: {str(e)}")
            return False
    
    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve lead data from CRM.
        
        Args:
            lead_id: CRM lead identifier
        
        Returns:
            Lead data dictionary if found, None otherwise
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping lead retrieval")
            return None
        
        try:
            logger.info(f"Retrieving lead from CRM: {lead_id}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/leads/{lead_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                lead_data = response.json()
                
                logger.info(f"Lead {lead_id} retrieved successfully from CRM")
                return lead_data
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error retrieving lead from CRM: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving lead from CRM: {str(e)}")
            return None
    
    async def notify_expert(
        self,
        lead_id: str,
        expert_id: Optional[str],
        handoff_summary: Dict[str, Any]
    ) -> bool:
        """
        Notify human expert about handoff.
        
        Args:
            lead_id: Lead identifier
            expert_id: Expert identifier (optional)
            handoff_summary: Summary of lead and handoff details
        
        Returns:
            True if notification successful, False otherwise
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping expert notification")
            return False
        
        try:
            logger.info(f"Notifying expert about handoff for lead {lead_id}")
            
            notification_data = {
                "lead_id": lead_id,
                "expert_id": expert_id,
                "handoff_summary": handoff_summary,
                "notification_type": "handoff",
                "priority": handoff_summary.get("priority", "medium")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/notifications/expert",
                    json=notification_data,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                logger.info(f"Expert notified successfully for lead {lead_id}")
                
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error notifying expert: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error notifying expert: {str(e)}")
            return False
    
    async def check_expert_availability(
        self,
        language: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if expert is available for handoff.
        
        Args:
            language: Preferred language for expert
            priority: Priority level (high, medium, low)
        
        Returns:
            Expert details if available, None otherwise
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping availability check")
            return None
        
        try:
            logger.info(f"Checking expert availability (language: {language}, priority: {priority})")
            
            params = {}
            if language:
                params["language"] = language
            if priority:
                params["priority"] = priority
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/experts/available",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                expert_data = response.json()
                
                if expert_data.get("available"):
                    logger.info(f"Expert available: {expert_data.get('expert_id')}")
                    return expert_data
                else:
                    logger.info("No expert currently available")
                    return None
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking expert availability: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error checking expert availability: {str(e)}")
            return None

    async def sync_lead_summary(
        self,
        lead_id: str,
        lead_summary: Dict[str, Any],
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Push structured lead summary to CRM after qualification.
        
        Args:
            lead_id: Lead identifier
            lead_summary: Complete lead summary with all collected data
            retry_count: Current retry attempt
            max_retries: Maximum number of retry attempts
        
        Returns:
            Dictionary with sync status and details
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping lead sync")
            return {
                "success": False,
                "error": "CRM not configured",
                "should_retry": False
            }
        
        try:
            logger.info(f"Syncing lead summary to CRM: {lead_id} (attempt {retry_count + 1}/{max_retries})")
            
            # Prepare structured summary
            sync_data = {
                "lead_id": lead_id,
                "summary": lead_summary,
                "sync_timestamp": lead_summary.get("timestamp"),
                "retry_count": retry_count
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/leads/{lead_id}/sync",
                    json=sync_data,
                    headers=self.headers,
                    timeout=15.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Lead {lead_id} synced successfully to CRM")
                
                return {
                    "success": True,
                    "crm_lead_id": result.get("crm_lead_id"),
                    "sync_id": result.get("sync_id"),
                    "should_retry": False
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} error syncing lead: {e.response.text}")
            
            # Determine if we should retry based on status code
            should_retry = e.response.status_code >= 500 and retry_count < max_retries
            
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text,
                "should_retry": should_retry,
                "retry_count": retry_count
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error syncing lead: {str(e)}")
            
            # Retry on network errors
            should_retry = retry_count < max_retries
            
            return {
                "success": False,
                "error": "Network error",
                "details": str(e),
                "should_retry": should_retry,
                "retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"Unexpected error syncing lead: {str(e)}")
            
            return {
                "success": False,
                "error": "Unknown error",
                "details": str(e),
                "should_retry": False,
                "retry_count": retry_count
            }
    
    async def batch_sync_leads(
        self,
        lead_summaries: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync multiple leads in a single batch request.
        
        Args:
            lead_summaries: List of lead summaries to sync
        
        Returns:
            Dictionary with batch sync results
        """
        if not self.api_key:
            logger.warning("CRM API key not configured, skipping batch sync")
            return {
                "success": False,
                "error": "CRM not configured"
            }
        
        try:
            logger.info(f"Batch syncing {len(lead_summaries)} leads to CRM")
            
            batch_data = {
                "leads": lead_summaries,
                "batch_size": len(lead_summaries)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/leads/batch-sync",
                    json=batch_data,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                success_count = result.get("success_count", 0)
                failed_count = result.get("failed_count", 0)
                
                logger.info(f"Batch sync completed: {success_count} succeeded, {failed_count} failed")
                
                return {
                    "success": True,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "failed_leads": result.get("failed_leads", [])
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in batch sync: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error in batch sync: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def prepare_lead_summary(
        self,
        lead: Any,
        eligibility_data: Optional[Dict[str, Any]] = None,
        call_data: Optional[Dict[str, Any]] = None,
        conversation_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare structured lead summary for CRM sync.
        
        Args:
            lead: Lead model object
            eligibility_data: Eligibility determination results
            call_data: Call information
            conversation_data: Conversation context and history
        
        Returns:
            Structured lead summary dictionary
        """
        from datetime import datetime
        
        summary = {
            # Lead identification
            "lead_id": lead.lead_id,
            "phone": lead.phone,
            "name": lead.name,
            "language": lead.language,
            
            # Lead data
            "country": lead.country,
            "degree": lead.degree,
            "loan_amount": lead.loan_amount,
            "offer_letter": lead.offer_letter,
            "coapplicant_itr": lead.coapplicant_itr,
            "collateral": lead.collateral,
            "visa_timeline": lead.visa_timeline,
            
            # Status and categorization
            "status": lead.status,
            "eligibility_category": lead.eligibility_category,
            "urgency": lead.urgency,
            
            # Timestamps
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Metadata
            "metadata": lead.metadata
        }
        
        # Add eligibility data if provided
        if eligibility_data:
            summary["eligibility"] = {
                "category": eligibility_data.get("category"),
                "lenders": eligibility_data.get("lenders", []),
                "urgency": eligibility_data.get("urgency"),
                "reasoning": eligibility_data.get("reasoning")
            }
        
        # Add call data if provided
        if call_data:
            summary["call"] = {
                "call_id": call_data.get("call_id"),
                "call_sid": call_data.get("call_sid"),
                "duration": call_data.get("duration"),
                "status": call_data.get("status"),
                "direction": call_data.get("direction"),
                "recording_url": call_data.get("recording_url")
            }
        
        # Add conversation data if provided
        if conversation_data:
            summary["conversation"] = {
                "turn_count": conversation_data.get("turn_count"),
                "average_sentiment": conversation_data.get("average_sentiment"),
                "clarification_count": conversation_data.get("clarification_count"),
                "language_switches": conversation_data.get("language_switches", 0),
                "key_intents": conversation_data.get("key_intents", [])
            }
        
        return summary
