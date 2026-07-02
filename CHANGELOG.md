## [v1.5.0] - Intermediary Architecture & Security Update
*Date: July 2, 2026*

### 📝 Overview
This release focuses on bridging the gap between the initial prototype and a production-ready enterprise architecture. It addresses critical feedback regarding security, validation, and documentation prior to the full Google ADK migration.

### 🔒 Security & Validation (Zero-Trust)
* **Enhanced PII Redaction:** Upgraded the `mask_pii.py` skill with advanced regex patterns to scrub sensitive data locally *before* LLM ingestion.
* **Strict Validation Layer:** Implemented `validator.py` to intercept and reject files with invalid extensions or excessive file sizes, protecting the server from malicious payloads.

### 🏗️ Architecture & Documentation
* **Model Accuracy:** Fixed the model identifier to correctly reference `gemini-2.0-flash`, ensuring stable API communication.
* **System Observability (Visual):** Added a comprehensive Mermaid.js architecture diagram to the `README.md` to clearly visualize the sequential agent pipeline and Human-in-the-Loop (HITL) pathways.
* **Skill Documentation:** Added `SKILL.md` to properly document the privacy tool's integration and zero-trust mandate.

### ⚙️ Backend Enhancements
* **Data Schemas:** Hardened the Pydantic schemas (`TriageResult`, `AuditResult`) to guarantee strict JSON output from the Gemini API.
* **Persistent Auditing:** Minor enhancements to the `database.py` SQLite ledger to ensure all pipeline events are properly logged.