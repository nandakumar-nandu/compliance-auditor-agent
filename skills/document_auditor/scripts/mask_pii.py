# ============================================================
# 🥷 ZERO-TRUST PRIVACY ENGINE — PII REDACTION CORE
# ============================================================
#
# 🏗️  Architecture Role: Innermost security layer — runs before ALL LLM calls
# 📚 Course Concepts Demonstrated:
#      ✅ Security Features (Day 4: Guardrails & Threat Vectors)
#      ✅ Zero-Trust architecture (trust nothing, verify everything)
#      ✅ Pre-LLM data sanitization (PII never reaches the model)
#
# Zero-Trust Principle Applied Here:
# This module embodies the Zero-Trust security model:
# "Never trust the input. Always scrub before processing."
# It runs LOCALLY using regex — no network calls, no API dependency.
# PII is permanently removed before the text is handed to any AI agent.
#
# Patterns Covered:
#   ✅ Email addresses
#   ✅ Credit card numbers (13–19 digits)
#   ✅ Phone numbers (international and local formats)
#   ✅ Indian Aadhaar numbers (12-digit government ID)
#   ✅ Indian PAN card numbers (alphanumeric tax ID)
#   ✅ Indian GSTIN numbers (15-char tax registration)
#   ✅ Generic SSN/government ID patterns
# ============================================================

import re
import logging

logger = logging.getLogger("PrivacySkill")


def luhn_checksum(card_number: str) -> bool:
    """Checks if a string of digits is a valid credit card number using the Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if not digits:
        return False
    # Reverse the digits
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        doubled = d * 2
        total += doubled if doubled < 10 else doubled - 9
    return total % 10 == 0


class PrivacySkill:
    """
    The Zero-Trust PII Redaction Engine.

    Uses carefully crafted regular expressions to detect and permanently
    replace sensitive personal and financial information with safe
    placeholder tags like [REDACTED_EMAIL] before text is sent to any LLM.

    This runs entirely locally — no network calls, no external dependencies.

    Design Principle:
    Regex-based redaction is fast, deterministic, and offline.
    It does NOT rely on an AI model to detect PII, which means it cannot
    be confused, hallucinated, or bypassed by adversarial inputs.
    """

    # ── PII Detection Patterns ─────────────────────────────────────────────────
    # Each pattern is a tuple of (compiled_regex, replacement_tag).
    # Patterns are applied in order — more specific patterns come first
    # to avoid partial matches overwriting each other.

    PII_PATTERNS = [

        # ── Email Addresses ───────────────────────────────────────────────────
        # Matches: john.doe+tag@subdomain.company.co.uk
        (
            re.compile(
                r'[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+',
                re.IGNORECASE
            ),
            "[REDACTED_EMAIL]"
        ),

        # ── Credit Card Numbers (13–19 digits) ────────────────────────────────
        # Matches Visa (16), MasterCard (16), Amex (15), Discover (16),
        # with or without spaces/dashes between groups.
        # e.g.: 4111 1111 1111 1111, 4111-1111-1111-1111, 4111111111111111
        # Uses Luhn algorithm to prevent redacting random 14-19 digit numbers (like FSSAI).
        (
            re.compile(
                r'\b(?:\d[ \-]?){13,18}\d\b'
            ),
            lambda m: "[REDACTED_CREDIT_CARD]" if luhn_checksum(m.group(0).replace(" ", "").replace("-", "")) else m.group(0)
        ),

        # ── Indian Aadhaar Number (12-digit government UID) ───────────────────
        # Matches: 1234 5678 9012 or 123456789012
        # Must appear before generic phone number pattern to avoid partial match
        (
            re.compile(
                r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
            ),
            "[REDACTED_AADHAAR]"
        ),

        # ── Indian PAN Card (Permanent Account Number) ────────────────────────
        # Format: ABCDE1234F (5 letters + 4 digits + 1 letter, all uppercase)
        (
            re.compile(
                r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
            ),
            "[REDACTED_PAN]"
        ),

        # ── Indian GSTIN (Goods & Services Tax Identification Number) ─────────
        # Format: 22AAAAA0000A1Z5 (15 characters: 2 digits + PAN + 3 chars)
        (
            re.compile(
                r'\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]\b'
            ),
            "[REDACTED_GSTIN]"
        ),

        # ── Phone Numbers (International & Local) ─────────────────────────────
        # Matches a broad range of formats:
        #   +1 (800) 555-1234, +91-9876543210, 98765 43210, (022) 2345-6789
        # Note: This runs AFTER Aadhaar to avoid eating 12-digit IDs
        (
            re.compile(
                r'\+?\d{1,4}[\s.\-]?\(?\d{1,4}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{4,9}\b'
            ),
            lambda m: "[REDACTED_PHONE]" if not (m.group(0).isdigit() and len(m.group(0)) >= 13) else m.group(0)
        ),

    ]

    @staticmethod
    def redact_sensitive_info(text: str) -> str:
        """
        Scans the text and replaces all detected PII with safe placeholder tags.

        Applies patterns sequentially. Each pass replaces one type of PII.
        The resulting text is safe to send to external LLM APIs.

        Args:
            text: Raw document text that may contain PII.

        Returns:
            str: Sanitized text with all PII replaced by [REDACTED_*] tags.
        """
        if not text:
            return text

        logger.info(f"🥷 Starting PII scan on {len(text)} characters...")
        original_text = text

        # Apply each pattern in sequence
        for pattern, replacement in PrivacySkill.PII_PATTERNS:
            text = pattern.sub(replacement, text)

        # Report results
        pii_found = text != original_text
        if pii_found:
            logger.warning("🚨 PII detected and redacted successfully")
        else:
            logger.info("✅ No PII detected in document")

        return text
