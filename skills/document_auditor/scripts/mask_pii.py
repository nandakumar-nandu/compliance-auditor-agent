import re

class PrivacySkill:
    @staticmethod
    def redact_sensitive_info(text: str) -> str:
        """Scrubs PII (Credit Cards, Emails, SSNs) from raw text."""
        print("-> [Privacy Skill]: Scrubbing Personally Identifiable Information (PII)...")
        
        # Mask Emails
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
        
        # Mask Credit Cards (16 digits)
        text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CREDIT_CARD]', text)
        
        # Mask Phone Numbers (Basic international)
        text = re.sub(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', '[REDACTED_PHONE]', text)
        
        return text