🥷 Privacy Scrubbing Skill

Skill Name: redact_sensitive_info
Location: skills/document_auditor/scripts/mask_pii.py

Overview

In enterprise environments, uploading raw corporate documents to public Large Language Models poses a severe data privacy risk. This skill acts as a Zero-Trust Interceptor.

It runs locally on the host machine before the main AI agents are invoked.

How It Works

It utilizes strict Python Regular Expressions (re) to identify and replace Personally Identifiable Information (PII) with safe template tags.

Supported Redactions:

Email Addresses: john.smith@company.com ➡️ [REDACTED_EMAIL]

Credit Cards: 1234-5678-9012-3456 ➡️ [REDACTED_CREDIT_CARD]

Phone Numbers: (555) 123-4567 ➡️ [REDACTED_PHONE]

Architecture Integration

This skill is dynamically called by the process_fastapi_upload orchestrator immediately after text extraction (OCR). By doing this, we guarantee that the Triage, Auditor, and Reporter AI agents never have access to sensitive employee or customer data in their context windows.