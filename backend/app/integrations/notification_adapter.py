"""
Notification Adapter for WhatsApp and SMS integration.

This module provides an adapter for sending notifications via
WhatsApp and SMS using SuprSend or Gupshup APIs.
"""

import os
from typing import Optional, Dict, Any
import logging
import httpx

logger = logging.getLogger(__name__)


class NotificationAdapter:
    """
    Adapter class for notification services (WhatsApp/SMS).
    
    Handles:
    - WhatsApp message sending
    - SMS sending
    - Template-based messaging
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "gupshup"
    ):
        """
        Initialize notification adapter with credentials.
        
        Args:
            api_url: Notification API base URL (defaults to env var)
            api_key: Notification API key (defaults to env var)
            provider: Provider name (gupshup or suprsend)
        """
        self.provider = provider
        self.api_url = api_url or os.getenv("NOTIFICATION_API_URL", "https://api.gupshup.io")
        self.api_key = api_key or os.getenv("NOTIFICATION_API_KEY")
        
        if not self.api_key:
            logger.warning("Notification API key not provided. Notifications will be disabled.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"NotificationAdapter initialized with provider: {self.provider}")
    
    async def send_whatsapp(
        self,
        phone: str,
        message: str,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message with template support.
        
        Args:
            phone: Phone number (E.164 format)
            message: Message text
            template_id: Optional template identifier
            template_params: Optional template parameters
        
        Returns:
            Dictionary with success status and message_id or error
        """
        if not self.api_key:
            logger.warning("Notification API key not configured, skipping WhatsApp message")
            return {"success": False, "error": "API key not configured"}
        
        try:
            logger.info(f"Sending WhatsApp message to {phone}")
            
            payload = {
                "phone": phone,
                "channel": "whatsapp"
            }
            
            # Use template if provided, otherwise send plain message
            if template_id:
                payload["template_id"] = template_id
                payload["template_params"] = template_params or {}
                logger.info(f"Using template: {template_id}")
            else:
                payload["message"] = message
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/messages/whatsapp",
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                message_id = result.get("message_id") or result.get("id")
                logger.info(f"WhatsApp message sent successfully to {phone}, message_id: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "channel": "whatsapp"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} error sending WhatsApp: {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.RequestError as e:
            logger.error(f"Request error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": "Network error",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": "Unknown error",
                "details": str(e)
            }
    
    async def send_sms(
        self,
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send SMS message.
        
        Args:
            phone: Phone number (E.164 format)
            message: Message text
        
        Returns:
            Dictionary with success status and message_id or error
        """
        if not self.api_key:
            logger.warning("Notification API key not configured, skipping SMS")
            return {"success": False, "error": "API key not configured"}
        
        try:
            logger.info(f"Sending SMS to {phone}")
            
            payload = {
                "phone": phone,
                "message": message,
                "channel": "sms"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/messages/sms",
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                message_id = result.get("message_id") or result.get("id")
                logger.info(f"SMS sent successfully to {phone}, message_id: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "channel": "sms"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} error sending SMS: {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.RequestError as e:
            logger.error(f"Request error sending SMS: {str(e)}")
            return {
                "success": False,
                "error": "Network error",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                "success": False,
                "error": "Unknown error",
                "details": str(e)
            }
    
    async def send_callback_confirmation(
        self,
        phone: str,
        language: str,
        callback_time: str,
        lead_name: Optional[str] = None
    ) -> bool:
        """
        Send callback confirmation message.
        
        Args:
            phone: Phone number
            language: Message language
            callback_time: Scheduled callback time
            lead_name: Optional lead name
        
        Returns:
            True if sent successfully
        """
        messages = {
            "hinglish": f"Namaste{' ' + lead_name if lead_name else ''}! Aapka callback {callback_time} par scheduled hai. Humara expert aapko call karega. Dhanyavaad!",
            "english": f"Hello{' ' + lead_name if lead_name else ''}! Your callback is scheduled for {callback_time}. Our expert will call you. Thank you!",
            "telugu": f"Namaskaram{' ' + lead_name if lead_name else ''}! Mee callback {callback_time} ki schedule chesamu. Maa expert meeku call chestaru. Dhanyavadalu!"
        }
        
        message = messages.get(language, messages["english"])
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result["success"]
    
    async def send_handoff_summary(
        self,
        phone: str,
        language: str,
        eligibility_category: Optional[str] = None,
        next_steps: Optional[str] = None
    ) -> bool:
        """
        Send post-handoff summary message.
        
        Args:
            phone: Phone number
            language: Message language
            eligibility_category: Loan eligibility category
            next_steps: Next steps information
        
        Returns:
            True if sent successfully
        """
        category_text = {
            "public_secured": {
                "hinglish": "Public Bank Secured Loan",
                "english": "Public Bank Secured Loan",
                "telugu": "Public Bank Secured Loan"
            },
            "private_unsecured": {
                "hinglish": "Private NBFC Unsecured Loan",
                "english": "Private NBFC Unsecured Loan",
                "telugu": "Private NBFC Unsecured Loan"
            },
            "intl_usd": {
                "hinglish": "International USD Loan",
                "english": "International USD Loan",
                "telugu": "International USD Loan"
            }
        }
        
        category = category_text.get(eligibility_category, {}).get(language, eligibility_category or "")
        
        messages = {
            "hinglish": f"Aapki call ke liye dhanyavaad! Aap {category} ke liye eligible hain. {next_steps or 'Humara expert jaldi hi aapse contact karega.'}",
            "english": f"Thank you for your call! You are eligible for {category}. {next_steps or 'Our expert will contact you soon.'}",
            "telugu": f"Mee call ki dhanyavadalu! Meeru {category} ki eligible. {next_steps or 'Maa expert త్వరలో meeku contact chestaru.'}"
        }
        
        message = messages.get(language, messages["english"])
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result["success"]

    async def send_post_call_summary(
        self,
        phone: str,
        language: str,
        lead_name: Optional[str],
        eligibility_category: Optional[str],
        loan_amount: Optional[float],
        next_steps: str,
        callback_scheduled: bool = False,
        callback_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send post-call follow-up summary after call completion.
        
        Args:
            phone: Phone number
            language: Message language
            lead_name: Lead name
            eligibility_category: Loan eligibility category
            loan_amount: Requested loan amount
            next_steps: Next steps information
            callback_scheduled: Whether callback is scheduled
            callback_time: Scheduled callback time if applicable
        
        Returns:
            Dictionary with success status
        """
        logger.info(f"Sending post-call summary to {phone}")
        
        # Category display names
        category_names = {
            "public_secured": {
                "hinglish": "Public Bank Secured Loan",
                "english": "Public Bank Secured Loan",
                "telugu": "Public Bank Secured Loan"
            },
            "private_unsecured": {
                "hinglish": "Private NBFC Unsecured Loan",
                "english": "Private NBFC Unsecured Loan",
                "telugu": "Private NBFC Unsecured Loan"
            },
            "intl_usd": {
                "hinglish": "International USD Loan",
                "english": "International USD Loan",
                "telugu": "International USD Loan"
            }
        }
        
        category_display = category_names.get(eligibility_category, {}).get(
            language,
            eligibility_category or "loan"
        )
        
        # Build message based on language
        if language == "hinglish":
            greeting = f"Namaste {lead_name}!" if lead_name else "Namaste!"
            message = f"{greeting}\n\n"
            message += f"Aapki call ke liye dhanyavaad! 🙏\n\n"
            
            if eligibility_category:
                message += f"✅ Aap {category_display} ke liye eligible hain"
                if loan_amount:
                    message += f" (₹{loan_amount:,.0f})"
                message += ".\n\n"
            
            message += f"📋 Next Steps:\n{next_steps}\n\n"
            
            if callback_scheduled and callback_time:
                message += f"📞 Callback: {callback_time}\n\n"
            
            message += "Koi bhi sawal ho toh humse contact karein!"
            
        elif language == "telugu":
            greeting = f"Namaskaram {lead_name}!" if lead_name else "Namaskaram!"
            message = f"{greeting}\n\n"
            message += f"Mee call ki dhanyavadalu! 🙏\n\n"
            
            if eligibility_category:
                message += f"✅ Meeru {category_display} ki eligible"
                if loan_amount:
                    message += f" (₹{loan_amount:,.0f})"
                message += ".\n\n"
            
            message += f"📋 Next Steps:\n{next_steps}\n\n"
            
            if callback_scheduled and callback_time:
                message += f"📞 Callback: {callback_time}\n\n"
            
            message += "Emaina questions unte mమమ్మల్ని contact cheyandi!"
            
        else:  # English
            greeting = f"Hello {lead_name}!" if lead_name else "Hello!"
            message = f"{greeting}\n\n"
            message += f"Thank you for your call! 🙏\n\n"
            
            if eligibility_category:
                message += f"✅ You are eligible for {category_display}"
                if loan_amount:
                    message += f" (₹{loan_amount:,.0f})"
                message += ".\n\n"
            
            message += f"📋 Next Steps:\n{next_steps}\n\n"
            
            if callback_scheduled and callback_time:
                message += f"📞 Callback scheduled: {callback_time}\n\n"
            
            message += "Feel free to contact us if you have any questions!"
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result
    
    async def send_eligibility_summary(
        self,
        phone: str,
        language: str,
        lead_name: Optional[str],
        eligibility_category: str,
        lenders: list,
        urgency: str
    ) -> Dict[str, Any]:
        """
        Send detailed eligibility summary with lender recommendations.
        
        Args:
            phone: Phone number
            language: Message language
            lead_name: Lead name
            eligibility_category: Loan eligibility category
            lenders: List of recommended lenders
            urgency: Urgency level (high, medium, low)
        
        Returns:
            Dictionary with success status
        """
        logger.info(f"Sending eligibility summary to {phone}")
        
        # Build lender list
        lender_list = "\n".join([f"• {lender}" for lender in lenders[:3]])  # Top 3 lenders
        
        # Urgency messages
        urgency_messages = {
            "high": {
                "hinglish": "⚡ High Priority - Jaldi action lena zaroori hai!",
                "english": "⚡ High Priority - Quick action needed!",
                "telugu": "⚡ High Priority - త్వరగా action తీసుకోవాలి!"
            },
            "medium": {
                "hinglish": "📅 Medium Priority - Agle kuch weeks mein proceed karein",
                "english": "📅 Medium Priority - Proceed in the next few weeks",
                "telugu": "📅 Medium Priority - వచ్చే కొన్ని weeks లో proceed చేయండి"
            },
            "low": {
                "hinglish": "✅ Low Priority - Aapke paas time hai",
                "english": "✅ Low Priority - You have time",
                "telugu": "✅ Low Priority - Meeku time undi"
            }
        }
        
        urgency_msg = urgency_messages.get(urgency, urgency_messages["medium"]).get(
            language,
            urgency_messages["medium"]["english"]
        )
        
        # Build message
        if language == "hinglish":
            greeting = f"Namaste {lead_name}!" if lead_name else "Namaste!"
            message = f"{greeting}\n\n"
            message += f"{urgency_msg}\n\n"
            message += f"🏦 Recommended Lenders:\n{lender_list}\n\n"
            message += "Humara expert aapse jaldi contact karega aur process mein help karega."
            
        elif language == "telugu":
            greeting = f"Namaskaram {lead_name}!" if lead_name else "Namaskaram!"
            message = f"{greeting}\n\n"
            message += f"{urgency_msg}\n\n"
            message += f"🏦 Recommended Lenders:\n{lender_list}\n\n"
            message += "Maa expert త్వరలో meeku contact chesi process lo help chestaru."
            
        else:  # English
            greeting = f"Hello {lead_name}!" if lead_name else "Hello!"
            message = f"{greeting}\n\n"
            message += f"{urgency_msg}\n\n"
            message += f"🏦 Recommended Lenders:\n{lender_list}\n\n"
            message += "Our expert will contact you soon to help with the process."
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result

    async def send_no_answer_followup(
        self,
        phone: str,
        language: str,
        lead_name: Optional[str],
        callback_link: Optional[str] = None,
        retry_schedule: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send follow-up message when call is not answered.
        
        Args:
            phone: Phone number
            language: Message language
            lead_name: Lead name
            callback_link: Optional link to schedule callback
            retry_schedule: Information about retry schedule
        
        Returns:
            Dictionary with success status
        """
        logger.info(f"Sending no-answer follow-up to {phone}")
        
        # Build message based on language
        if language == "hinglish":
            greeting = f"Namaste {lead_name}!" if lead_name else "Namaste!"
            message = f"{greeting}\n\n"
            message += "Humne aapko call karne ki koshish ki lekin aap available nahi the.\n\n"
            message += "📞 Hum aapko dobara call karenge"
            
            if retry_schedule:
                message += f" {retry_schedule}"
            message += ".\n\n"
            
            if callback_link:
                message += f"Ya aap apna preferred time select kar sakte hain:\n{callback_link}\n\n"
            
            message += "Education loan ke baare mein baat karne ke liye hum aapka intezaar kar rahe hain!"
            
        elif language == "telugu":
            greeting = f"Namaskaram {lead_name}!" if lead_name else "Namaskaram!"
            message = f"{greeting}\n\n"
            message += "Memu meeku call cheyyataniki try chesamu kani meeru available ledu.\n\n"
            message += "📞 Memu meeku మళ్ళీ call chestamu"
            
            if retry_schedule:
                message += f" {retry_schedule}"
            message += ".\n\n"
            
            if callback_link:
                message += f"Leda meeru mee preferred time select cheyochu:\n{callback_link}\n\n"
            
            message += "Education loan gurinchi matladataniki memu meeku wait chestunnamu!"
            
        else:  # English
            greeting = f"Hello {lead_name}!" if lead_name else "Hello!"
            message = f"{greeting}\n\n"
            message += "We tried calling you but you were unavailable.\n\n"
            message += "📞 We'll try calling you again"
            
            if retry_schedule:
                message += f" {retry_schedule}"
            message += ".\n\n"
            
            if callback_link:
                message += f"Or you can select your preferred time:\n{callback_link}\n\n"
            
            message += "We're looking forward to discussing your education loan!"
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result
    
    async def send_retry_notification(
        self,
        phone: str,
        language: str,
        lead_name: Optional[str],
        retry_count: int,
        next_retry_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification about retry attempt.
        
        Args:
            phone: Phone number
            language: Message language
            lead_name: Lead name
            retry_count: Current retry attempt number
            next_retry_time: Time of next retry if applicable
        
        Returns:
            Dictionary with success status
        """
        logger.info(f"Sending retry notification to {phone} (attempt {retry_count})")
        
        # Build message based on language and retry count
        if language == "hinglish":
            greeting = f"Namaste {lead_name}!" if lead_name else "Namaste!"
            message = f"{greeting}\n\n"
            
            if retry_count == 1:
                message += "Humne aapko pehle call kiya tha lekin connect nahi ho paye.\n\n"
            elif retry_count == 2:
                message += "Hum aapse dobara connect karne ki koshish kar rahe hain.\n\n"
            else:
                message += "Yeh humari aakhri koshish hai aapse connect karne ki.\n\n"
            
            if next_retry_time:
                message += f"📞 Hum aapko {next_retry_time} par call karenge.\n\n"
            
            message += "Agar aap abhi baat karna chahte hain toh humein reply karein!"
            
        elif language == "telugu":
            greeting = f"Namaskaram {lead_name}!" if lead_name else "Namaskaram!"
            message = f"{greeting}\n\n"
            
            if retry_count == 1:
                message += "Memu meeku mundu call chesamu kani connect కాలేదు.\n\n"
            elif retry_count == 2:
                message += "Memu meeto మళ్ళీ connect avvataniki try chestunnamu.\n\n"
            else:
                message += "Idi maa చివరి attempt meeto connect avvataniki.\n\n"
            
            if next_retry_time:
                message += f"📞 Memu meeku {next_retry_time} ki call chestamu.\n\n"
            
            message += "Meeru ippudu matladali ante మాకు reply cheyandi!"
            
        else:  # English
            greeting = f"Hello {lead_name}!" if lead_name else "Hello!"
            message = f"{greeting}\n\n"
            
            if retry_count == 1:
                message += "We called you earlier but couldn't connect.\n\n"
            elif retry_count == 2:
                message += "We're trying to reach you again.\n\n"
            else:
                message += "This is our final attempt to connect with you.\n\n"
            
            if next_retry_time:
                message += f"📞 We'll call you at {next_retry_time}.\n\n"
            
            message += "If you'd like to talk now, just reply to this message!"
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result
    
    async def send_unreachable_notification(
        self,
        phone: str,
        language: str,
        lead_name: Optional[str],
        callback_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send final notification when lead is marked as unreachable.
        
        Args:
            phone: Phone number
            language: Message language
            lead_name: Lead name
            callback_link: Optional link to schedule callback
        
        Returns:
            Dictionary with success status
        """
        logger.info(f"Sending unreachable notification to {phone}")
        
        # Build message based on language
        if language == "hinglish":
            greeting = f"Namaste {lead_name}!" if lead_name else "Namaste!"
            message = f"{greeting}\n\n"
            message += "Humne aapko kai baar call karne ki koshish ki lekin connect nahi ho paye. 😔\n\n"
            message += "Agar aap education loan ke baare mein baat karna chahte hain:\n\n"
            
            if callback_link:
                message += f"📞 Apna preferred time select karein:\n{callback_link}\n\n"
            
            message += "Ya humein message karein aur hum aapse jaldi contact karenge!\n\n"
            message += "Dhanyavaad! 🙏"
            
        elif language == "telugu":
            greeting = f"Namaskaram {lead_name}!" if lead_name else "Namaskaram!"
            message = f"{greeting}\n\n"
            message += "Memu meeku చాలా సార్లు call cheyyataniki try chesamu kani connect కాలేదు. 😔\n\n"
            message += "Meeru education loan gurinchi matladali ante:\n\n"
            
            if callback_link:
                message += f"📞 Mee preferred time select cheyandi:\n{callback_link}\n\n"
            
            message += "Leda మాకు message cheyandi, memu త్వరగా meeku contact chestamu!\n\n"
            message += "Dhanyavadalu! 🙏"
            
        else:  # English
            greeting = f"Hello {lead_name}!" if lead_name else "Hello!"
            message = f"{greeting}\n\n"
            message += "We tried calling you multiple times but couldn't connect. 😔\n\n"
            message += "If you'd like to discuss your education loan:\n\n"
            
            if callback_link:
                message += f"📞 Select your preferred time:\n{callback_link}\n\n"
            
            message += "Or message us and we'll get back to you quickly!\n\n"
            message += "Thank you! 🙏"
        
        # Try WhatsApp first, fallback to SMS
        result = await self.send_whatsapp(phone, message)
        if not result["success"]:
            logger.info("WhatsApp failed, falling back to SMS")
            result = await self.send_sms(phone, message)
        
        return result
