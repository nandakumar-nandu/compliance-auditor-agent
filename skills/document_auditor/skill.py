# ============================================================
# 🎯 DOCUMENT AUDITOR SKILL — ADK AGENT SKILL
# ============================================================
#
# 🏗️  Architecture Role: Reusable, Portable Agent Capability
# 📚 Course Concepts Demonstrated:
#      ✅ Agent Skills (Day 3: Building Skilled Agents)
#      ✅ Skill encapsulation — any ADK agent can import and use this
#      ✅ Versioned, documented, self-contained capability module
#      ✅ Zero-Trust security skill (PII masking before LLM calls)
#
# What is an Agent Skill?
# A Skill is a self-contained, reusable capability that can be plugged
# into any ADK agent. It follows the course's "Agents CLI" pattern:
# skills are registered, versioned, and documented independently of
# the agents that use them. This makes them composable and testable.
#
# How to use this skill:
#   from skills.document_auditor.skill import DocumentAuditorSkill
#   skill = DocumentAuditorSkill()
#   result = skill.execute(raw_text)
# ============================================================

import logging
from .scripts.mask_pii import PrivacySkill

logger = logging.getLogger("DocumentAuditorSkill")


class DocumentAuditorSkill:
    """
    An ADK-compatible Agent Skill for Zero-Trust document privacy processing.

    This skill encapsulates the PII masking capability as a versioned,
    self-contained module. Any ADK agent in any pipeline can import and
    use this skill without needing to know its internal implementation.

    Skill Metadata:
        name:        document_auditor
        version:     1.0.0
        capability:  PII detection and redaction
        author:      Kaggle Capstone — Smart Document Auditor
        input:       Raw document text (str)
        output:      Scrubbed text + PII detection report (dict)

    Security Guarantee:
        This skill guarantees that NO raw PII (emails, credit cards, phones,
        government IDs) will appear in any text passed to an LLM after
        this skill is applied.
    """

    # ── Skill Metadata ─────────────────────────────────────────────────────────
    # These attributes make the skill discoverable by Agents CLI and ADK registries
    name: str = "document_auditor"
    version: str = "1.0.0"
    description: str = "Zero-Trust PII masking skill for pre-LLM document sanitization"
    author: str = "Smart Document Auditor — Kaggle Capstone 2026"
    input_type: str = "str (raw document text)"
    output_type: str = "dict (scrubbed_text, pii_detected, redaction_summary)"

    def __init__(self):
        """
        Initializes the skill by instantiating the underlying PrivacySkill engine.
        The PrivacySkill contains the regex-based PII detection and redaction logic.
        """
        self._privacy_engine = PrivacySkill()
        logger.info(f"✅ Skill initialized: {self.name} v{self.version}")

    def execute(self, raw_text: str) -> dict:
        """
        Executes the PII masking skill on the provided raw text.

        This is the standard ADK Skill execution interface.
        It applies all PII redaction patterns and returns a structured
        result that includes both the scrubbed text and a detection report.

        Args:
            raw_text: The original document text, potentially containing PII.

        Returns:
            dict with keys:
                - scrubbed_text (str):      Text with all PII replaced by [REDACTED_*] tags
                - pii_detected (bool):      True if any PII was found
                - original_length (int):    Character count of input
                - scrubbed_length (int):    Character count of output
                - skill (str):              Skill name for audit traceability
                - version (str):            Skill version for audit traceability
                - redaction_tags_used (list): List of redaction tags that were inserted

        Example:
            Input:  "Contact john@corp.com or call +91-9876543210"
            Output: "Contact [REDACTED_EMAIL] or call [REDACTED_PHONE]"
        """
        if not raw_text or not raw_text.strip():
            logger.warning("⚠️  Skill received empty text — returning as-is")
            return {
                "scrubbed_text": raw_text,
                "pii_detected": False,
                "original_length": 0,
                "scrubbed_length": 0,
                "skill": self.name,
                "version": self.version,
                "redaction_tags_used": []
            }

        logger.info(f"🔐 Executing {self.name} skill on {len(raw_text)} characters...")

        # Apply PII redaction via the PrivacySkill engine
        scrubbed_text = self._privacy_engine.redact_sensitive_info(raw_text)

        # Detect which redaction tags were actually inserted
        import re
        redaction_tags_used = list(set(re.findall(r'\[REDACTED_\w+\]', scrubbed_text)))

        pii_detected = scrubbed_text != raw_text

        if pii_detected:
            logger.warning(
                f"🚨 PII detected and redacted | "
                f"Tags used: {redaction_tags_used} | "
                f"Length change: {len(raw_text)} → {len(scrubbed_text)} chars"
            )
        else:
            logger.info("✅ No PII detected — text is clean")

        return {
            "scrubbed_text": scrubbed_text,
            "pii_detected": pii_detected,
            "original_length": len(raw_text),
            "scrubbed_length": len(scrubbed_text),
            "skill": self.name,
            "version": self.version,
            "redaction_tags_used": redaction_tags_used
        }

    def get_metadata(self) -> dict:
        """
        Returns the skill's metadata for Agents CLI registration and discovery.

        Returns:
            dict: Skill metadata compatible with ADK skill registries.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "input_type": self.input_type,
            "output_type": self.output_type,
            "capabilities": ["pii_masking", "email_redaction", "phone_redaction",
                             "credit_card_redaction", "government_id_redaction"]
        }
