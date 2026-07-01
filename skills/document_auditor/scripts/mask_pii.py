# ==========================================
# 🥷 ZERO-TRUST PRIVACY SKILL 🥷
# ==========================================

import re

class PrivacySkill:
    """
    A strict security layer that scrubs Personally Identifiable Information (PII)
    from raw text before it is ever sent to the external LLM models.
    """
    
    @staticmethod
    def redact_sensitive_info(text: str) -> str:
        """Uses Regular Expressions to find and mask secrets."""
        print("🥷  [Privacy Skill]: Scrubbing sensitive data (Zero-Trust active)...")
        
        # 📧 1. Mask Email Addresses (e.g., john.doe@company.com -> [REDACTED_EMAIL])
        text = re.sub(
            r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', 
            '[REDACTED_EMAIL]', 
            text
        )
        
        # 💳 2. Mask Credit Card Numbers (Finds 13-16 digit numbers)
        text = re.sub(
            r'\b(?:\d[ -]*?){13,16}\b', 
            '[REDACTED_CREDIT_CARD]', 
            text
        )
        
        # 📱 3. Mask Phone Numbers (Catches basic international and local formats)
        text = re.sub(
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', 
            '[REDACTED_PHONE]', 
            text
        )
        
        return text