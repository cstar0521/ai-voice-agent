"""
Eligibility Engine for determining loan categories and lender recommendations.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import re


class EligibilityEngine:
    """
    Engine for determining loan eligibility categories and lender recommendations.
    
    This engine applies business rules to map collected lead data to appropriate
    loan categories and provides lender recommendations based on urgency.
    """
    
    # Lender mappings for each category
    LENDERS = {
        "public_secured": [
            "State Bank of India",
            "Bank of Baroda",
            "Punjab National Bank",
            "Canara Bank"
        ],
        "private_unsecured": [
            "Auxilo",
            "Avanse",
            "Credila",
            "InCred"
        ],
        "intl_usd": [
            "Prodigy Finance",
            "MPower Financing",
            "Leap Finance"
        ],
        "escalate": []
    }
    
    # Fast-track lenders for high urgency cases
    FAST_TRACK_LENDERS = {
        "public_secured": ["Bank of Baroda", "Canara Bank"],
        "private_unsecured": ["Auxilo", "InCred"],
        "intl_usd": ["Leap Finance"]
    }
    
    # High merit countries for international USD loans (uppercase for comparison)
    HIGH_MERIT_COUNTRIES = ["US", "CANADA"]
    
    def determine_category(self, lead_data: Dict) -> str:
        """
        Determine loan category based on collected lead data.
        
        Business Rules:
        1. If collateral available -> public_secured (public bank secured loans)
        2. If no collateral BUT co-applicant ITR available -> private_unsecured (NBFC loans)
        3. If country is US/Canada AND high merit -> intl_usd (international lenders)
        4. If no collateral AND no ITR -> escalate (needs human expert)
        
        Args:
            lead_data: Dictionary containing lead information with keys:
                - collateral: "yes" or "no"
                - coapplicant_itr: "yes" or "no"
                - country: Country code (e.g., "US", "UK", "Canada")
                - high_merit: Optional boolean for high merit status
        
        Returns:
            Category string: "public_secured", "private_unsecured", "intl_usd", or "escalate"
        """
        collateral = lead_data.get("collateral", "").lower()
        coapplicant_itr = lead_data.get("coapplicant_itr", "").lower()
        country = lead_data.get("country", "").upper()
        high_merit = lead_data.get("high_merit", False)
        
        # Rule 1: Collateral available -> public secured loans
        if collateral == "yes":
            return "public_secured"
        
        # Rule 3: US/Canada + high merit -> international USD loans
        # Check this before other rules to prioritize international options
        if country in self.HIGH_MERIT_COUNTRIES and high_merit:
            return "intl_usd"
        
        # Rule 2: No collateral but ITR available -> private unsecured loans
        if collateral == "no" and coapplicant_itr == "yes":
            return "private_unsecured"
        
        # Rule 4: No collateral and no ITR -> escalate to human expert
        # (unless already handled by intl_usd rule above)
        if collateral == "no" and coapplicant_itr == "no":
            return "escalate"
        
        # Default to escalate for unclear cases
        return "escalate"
    
    def determine_urgency(self, visa_timeline: str) -> str:
        """
        Determine urgency level based on visa timeline.
        
        Parses the visa_timeline string to extract the deadline and calculates
        days until the visa deadline.
        
        Urgency Levels:
        - high: < 30 days until deadline
        - medium: 30-90 days until deadline
        - low: > 90 days until deadline
        
        Args:
            visa_timeline: String describing visa timeline, e.g.:
                - "30 days"
                - "2 months"
                - "3 weeks"
                - "2025-12-31"
                - "December 31, 2025"
        
        Returns:
            Urgency level: "high", "medium", or "low"
        """
        if not visa_timeline:
            return "low"
        
        days_until_deadline = self._parse_visa_timeline(visa_timeline)
        
        if days_until_deadline < 30:
            return "high"
        elif days_until_deadline <= 90:
            return "medium"
        else:
            return "low"
    
    def _parse_visa_timeline(self, visa_timeline: str) -> int:
        """
        Parse visa timeline string and return days until deadline.
        
        Supports multiple formats:
        - "X days" -> X days
        - "X weeks" -> X * 7 days
        - "X months" -> X * 30 days
        - ISO date format "YYYY-MM-DD"
        - Natural date formats
        
        Args:
            visa_timeline: Timeline string
        
        Returns:
            Number of days until deadline (defaults to 365 if unparseable)
        """
        timeline_lower = visa_timeline.lower().strip()
        
        # Pattern: "X days"
        days_match = re.search(r'(\d+)\s*days?', timeline_lower)
        if days_match:
            return int(days_match.group(1))
        
        # Pattern: "X weeks"
        weeks_match = re.search(r'(\d+)\s*weeks?', timeline_lower)
        if weeks_match:
            return int(weeks_match.group(1)) * 7
        
        # Pattern: "X months"
        months_match = re.search(r'(\d+)\s*months?', timeline_lower)
        if months_match:
            return int(months_match.group(1)) * 30
        
        # Try to parse as ISO date (YYYY-MM-DD)
        iso_date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', visa_timeline)
        if iso_date_match:
            try:
                deadline = datetime.strptime(iso_date_match.group(0), "%Y-%m-%d")
                days_diff = (deadline - datetime.utcnow()).days
                return max(0, days_diff)
            except ValueError:
                pass
        
        # Default to low urgency (365 days) if unable to parse
        return 365
    
    def get_lender_recommendations(
        self,
        category: str,
        urgency: str
    ) -> List[str]:
        """
        Get lender recommendations based on category and urgency.
        
        For high urgency cases, returns fast-track lenders that can process
        applications quickly. For medium/low urgency, returns all lenders
        in the category.
        
        Args:
            category: Loan category ("public_secured", "private_unsecured", "intl_usd", "escalate")
            urgency: Urgency level ("high", "medium", "low")
        
        Returns:
            List of recommended lender names. Empty list for "escalate" category.
        """
        # No lender recommendations for escalate category
        if category == "escalate":
            return []
        
        # Get base lenders for the category
        base_lenders = self.LENDERS.get(category, [])
        
        # For high urgency, prioritize fast-track lenders
        if urgency == "high":
            fast_track = self.FAST_TRACK_LENDERS.get(category, [])
            if fast_track:
                # Return fast-track lenders first, then others
                other_lenders = [l for l in base_lenders if l not in fast_track]
                return fast_track + other_lenders
        
        # For medium/low urgency, return all lenders
        return base_lenders
