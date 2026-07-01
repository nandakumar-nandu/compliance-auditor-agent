import re

def redact_sensitive_info(text):
    """
    Demonstrates Security Pillar 4: PII Masking.
    Masks Indian mobile formats and emails.
    """
    # Mask Email
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text)
    # Mask 10-digit Indian mobile
    text = re.sub(r'\d{10}', '[REDACTED_PHONE]', text)
    return text