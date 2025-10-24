"""
Unit tests for Eligibility Engine - category determination, urgency calculation, and lender recommendations.
"""
import pytest
from datetime import datetime, timedelta

from app.services.eligibility_engine import EligibilityEngine


class TestEligibilityEngine:
    """Test suite for Eligibility Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create eligibility engine instance."""
        return EligibilityEngine()
    
    # Category Determination Tests
    
    def test_determine_category_public_secured_with_collateral(self, engine):
        """Test public_secured category when collateral is available."""
        lead_data = {
            "collateral": "yes",
            "coapplicant_itr": "no",
            "country": "UK"
        }
        category = engine.determine_category(lead_data)
        assert category == "public_secured"
    
    def test_determine_category_public_secured_with_collateral_and_itr(self, engine):
        """Test public_secured category when both collateral and ITR available."""
        lead_data = {
            "collateral": "yes",
            "coapplicant_itr": "yes",
            "country": "Australia"
        }
        category = engine.determine_category(lead_data)
        assert category == "public_secured"
    
    def test_determine_category_private_unsecured_no_collateral_with_itr(self, engine):
        """Test private_unsecured category when no collateral but ITR available."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "yes",
            "country": "UK"
        }
        category = engine.determine_category(lead_data)
        assert category == "private_unsecured"
    
    def test_determine_category_intl_usd_us_high_merit(self, engine):
        """Test intl_usd category for US with high merit."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "yes",
            "country": "US",
            "high_merit": True
        }
        category = engine.determine_category(lead_data)
        assert category == "intl_usd"
    
    def test_determine_category_intl_usd_canada_high_merit(self, engine):
        """Test intl_usd category for Canada with high merit."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "no",
            "country": "Canada",
            "high_merit": True
        }
        category = engine.determine_category(lead_data)
        assert category == "intl_usd"

    def test_determine_category_escalate_no_collateral_no_itr(self, engine):
        """Test escalate category when neither collateral nor ITR available."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "no",
            "country": "UK"
        }
        category = engine.determine_category(lead_data)
        assert category == "escalate"
    
    def test_determine_category_escalate_no_high_merit_us(self, engine):
        """Test that US without high merit doesn't get intl_usd."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "yes",
            "country": "US",
            "high_merit": False
        }
        category = engine.determine_category(lead_data)
        assert category == "private_unsecured"
    
    def test_determine_category_case_insensitive(self, engine):
        """Test that category determination is case insensitive."""
        lead_data = {
            "collateral": "YES",
            "coapplicant_itr": "NO",
            "country": "uk"
        }
        category = engine.determine_category(lead_data)
        assert category == "public_secured"
    
    def test_determine_category_missing_fields(self, engine):
        """Test escalate when required fields are missing."""
        lead_data = {}
        category = engine.determine_category(lead_data)
        assert category == "escalate"
    
    # Urgency Calculation Tests
    
    def test_determine_urgency_high_less_than_30_days(self, engine):
        """Test high urgency for timeline less than 30 days."""
        urgency = engine.determine_urgency("25 days")
        assert urgency == "high"
    
    def test_determine_urgency_high_2_weeks(self, engine):
        """Test high urgency for 2 weeks (14 days)."""
        urgency = engine.determine_urgency("2 weeks")
        assert urgency == "high"
    
    def test_determine_urgency_medium_30_days(self, engine):
        """Test medium urgency for exactly 30 days."""
        urgency = engine.determine_urgency("30 days")
        assert urgency == "medium"
    
    def test_determine_urgency_medium_60_days(self, engine):
        """Test medium urgency for 60 days."""
        urgency = engine.determine_urgency("60 days")
        assert urgency == "medium"
    
    def test_determine_urgency_medium_90_days(self, engine):
        """Test medium urgency for exactly 90 days."""
        urgency = engine.determine_urgency("90 days")
        assert urgency == "medium"
    
    def test_determine_urgency_medium_2_months(self, engine):
        """Test medium urgency for 2 months (60 days)."""
        urgency = engine.determine_urgency("2 months")
        assert urgency == "medium"
    
    def test_determine_urgency_low_more_than_90_days(self, engine):
        """Test low urgency for timeline more than 90 days."""
        urgency = engine.determine_urgency("120 days")
        assert urgency == "low"
    
    def test_determine_urgency_low_6_months(self, engine):
        """Test low urgency for 6 months (180 days)."""
        urgency = engine.determine_urgency("6 months")
        assert urgency == "low"
    
    def test_determine_urgency_iso_date_format(self, engine):
        """Test urgency calculation with ISO date format."""
        # Create a date 45 days in the future
        future_date = datetime.utcnow() + timedelta(days=45)
        date_str = future_date.strftime("%Y-%m-%d")
        urgency = engine.determine_urgency(date_str)
        assert urgency == "medium"
    
    def test_determine_urgency_iso_date_high(self, engine):
        """Test high urgency with ISO date less than 30 days away."""
        future_date = datetime.utcnow() + timedelta(days=20)
        date_str = future_date.strftime("%Y-%m-%d")
        urgency = engine.determine_urgency(date_str)
        assert urgency == "high"
    
    def test_determine_urgency_empty_string(self, engine):
        """Test default low urgency for empty string."""
        urgency = engine.determine_urgency("")
        assert urgency == "low"
    
    def test_determine_urgency_unparseable_string(self, engine):
        """Test default low urgency for unparseable string."""
        urgency = engine.determine_urgency("sometime next year")
        assert urgency == "low"
    
    def test_determine_urgency_plural_forms(self, engine):
        """Test urgency calculation with plural forms."""
        assert engine.determine_urgency("1 day") == "high"
        assert engine.determine_urgency("5 weeks") == "medium"
        assert engine.determine_urgency("4 month") == "low"
    
    # Lender Recommendations Tests
    
    def test_get_lender_recommendations_public_secured_low_urgency(self, engine):
        """Test lender recommendations for public_secured with low urgency."""
        lenders = engine.get_lender_recommendations("public_secured", "low")
        assert len(lenders) == 4
        assert "State Bank of India" in lenders
        assert "Bank of Baroda" in lenders
        assert "Punjab National Bank" in lenders
        assert "Canara Bank" in lenders
    
    def test_get_lender_recommendations_public_secured_high_urgency(self, engine):
        """Test fast-track lenders for public_secured with high urgency."""
        lenders = engine.get_lender_recommendations("public_secured", "high")
        assert len(lenders) == 4
        # Fast-track lenders should be first
        assert lenders[0] in ["Bank of Baroda", "Canara Bank"]
        assert lenders[1] in ["Bank of Baroda", "Canara Bank"]
    
    def test_get_lender_recommendations_private_unsecured_medium_urgency(self, engine):
        """Test lender recommendations for private_unsecured with medium urgency."""
        lenders = engine.get_lender_recommendations("private_unsecured", "medium")
        assert len(lenders) == 4
        assert "Auxilo" in lenders
        assert "Avanse" in lenders
        assert "Credila" in lenders
        assert "InCred" in lenders
    
    def test_get_lender_recommendations_private_unsecured_high_urgency(self, engine):
        """Test fast-track lenders for private_unsecured with high urgency."""
        lenders = engine.get_lender_recommendations("private_unsecured", "high")
        assert len(lenders) == 4
        # Fast-track lenders should be first
        assert lenders[0] in ["Auxilo", "InCred"]
        assert lenders[1] in ["Auxilo", "InCred"]
    
    def test_get_lender_recommendations_intl_usd_low_urgency(self, engine):
        """Test lender recommendations for intl_usd with low urgency."""
        lenders = engine.get_lender_recommendations("intl_usd", "low")
        assert len(lenders) == 3
        assert "Prodigy Finance" in lenders
        assert "MPower Financing" in lenders
        assert "Leap Finance" in lenders
    
    def test_get_lender_recommendations_intl_usd_high_urgency(self, engine):
        """Test fast-track lenders for intl_usd with high urgency."""
        lenders = engine.get_lender_recommendations("intl_usd", "high")
        assert len(lenders) == 3
        # Leap Finance should be first for fast-track
        assert lenders[0] == "Leap Finance"
    
    def test_get_lender_recommendations_escalate_category(self, engine):
        """Test empty lender list for escalate category."""
        lenders = engine.get_lender_recommendations("escalate", "high")
        assert lenders == []
        
        lenders = engine.get_lender_recommendations("escalate", "low")
        assert lenders == []
    
    def test_get_lender_recommendations_invalid_category(self, engine):
        """Test empty lender list for invalid category."""
        lenders = engine.get_lender_recommendations("invalid_category", "medium")
        assert lenders == []
    
    # Integration Tests - Full Flow
    
    def test_full_flow_public_secured_high_urgency(self, engine):
        """Test complete flow for public secured loan with high urgency."""
        lead_data = {
            "collateral": "yes",
            "coapplicant_itr": "yes",
            "country": "UK",
            "visa_timeline": "20 days"
        }
        
        category = engine.determine_category(lead_data)
        urgency = engine.determine_urgency(lead_data["visa_timeline"])
        lenders = engine.get_lender_recommendations(category, urgency)
        
        assert category == "public_secured"
        assert urgency == "high"
        assert len(lenders) > 0
        assert lenders[0] in ["Bank of Baroda", "Canara Bank"]
    
    def test_full_flow_private_unsecured_medium_urgency(self, engine):
        """Test complete flow for private unsecured loan with medium urgency."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "yes",
            "country": "Australia",
            "visa_timeline": "2 months"
        }
        
        category = engine.determine_category(lead_data)
        urgency = engine.determine_urgency(lead_data["visa_timeline"])
        lenders = engine.get_lender_recommendations(category, urgency)
        
        assert category == "private_unsecured"
        assert urgency == "medium"
        assert len(lenders) == 4
    
    def test_full_flow_intl_usd_low_urgency(self, engine):
        """Test complete flow for international USD loan with low urgency."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "no",
            "country": "US",
            "high_merit": True,
            "visa_timeline": "6 months"
        }
        
        category = engine.determine_category(lead_data)
        urgency = engine.determine_urgency(lead_data["visa_timeline"])
        lenders = engine.get_lender_recommendations(category, urgency)
        
        assert category == "intl_usd"
        assert urgency == "low"
        assert len(lenders) == 3
    
    def test_full_flow_escalate_no_lenders(self, engine):
        """Test complete flow for escalate case with no lenders."""
        lead_data = {
            "collateral": "no",
            "coapplicant_itr": "no",
            "country": "Germany",
            "visa_timeline": "45 days"
        }
        
        category = engine.determine_category(lead_data)
        urgency = engine.determine_urgency(lead_data["visa_timeline"])
        lenders = engine.get_lender_recommendations(category, urgency)
        
        assert category == "escalate"
        assert urgency == "medium"
        assert lenders == []
