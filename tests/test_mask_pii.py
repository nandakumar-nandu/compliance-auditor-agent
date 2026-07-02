# tests/test_mask_pii.py
# ============================================================
# 🧪 TESTS: Zero-Trust PII Masking Engine
# ============================================================

from skills.document_auditor.scripts.mask_pii import PrivacySkill


class TestPrivacySkill:
    """Tests for the Zero-Trust PII redaction engine."""

    def test_email_is_redacted(self):
        """Email addresses must be replaced with [REDACTED_EMAIL]."""
        result = PrivacySkill.redact_sensitive_info(
            "Contact us at billing@company.co.in for invoices."
        )
        assert "[REDACTED_EMAIL]" in result
        assert "@" not in result

    def test_credit_card_is_redacted(self):
        """Credit card numbers must be replaced with [REDACTED_CREDIT_CARD]."""
        result = PrivacySkill.redact_sensitive_info(
            "Payment processed on card 4111 1111 1111 1111."
        )
        assert "[REDACTED_CREDIT_CARD]" in result
        assert "4111" not in result

    def test_phone_is_redacted(self):
        """Phone numbers must be replaced with [REDACTED_PHONE]."""
        result = PrivacySkill.redact_sensitive_info(
            "Call us at +91-9876543210 for support."
        )
        assert "[REDACTED_PHONE]" in result

    def test_pan_card_is_redacted(self):
        """Indian PAN card numbers must be replaced with [REDACTED_PAN]."""
        result = PrivacySkill.redact_sensitive_info(
            "Taxpayer PAN: ABCDE1234F as per records."
        )
        assert "[REDACTED_PAN]" in result
        assert "ABCDE1234F" not in result

    def test_clean_text_unchanged(self):
        """Text without PII must pass through completely unchanged."""
        clean_text = "This invoice covers services rendered in Q2 2026."
        result = PrivacySkill.redact_sensitive_info(clean_text)
        assert result == clean_text

    def test_multiple_pii_types_redacted(self):
        """Multiple PII types in one document must all be redacted."""
        text = "Email: admin@firm.com, Card: 4111111111111111, PAN: ABCDE1234F"
        result = PrivacySkill.redact_sensitive_info(text)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_CREDIT_CARD]" in result
        assert "[REDACTED_PAN]" in result
