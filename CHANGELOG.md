# Changelog

All notable changes to this project will be documented in this file.

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


## [v2.0.0] - Multi-Provider LLM Switch & Logging Aesthetics
*Date: July 2, 2026*

### 📝 Overview
This release introduces dynamic LLM provider switching to prevent Google API quota exhaustion. It also refines terminal logging formats to ensure high readability and cleans up repository artifacts for final Kaggle Capstone package submission.

### ⚙️ Multi-Provider LLM Toggle
* **Flexible LLM Backends:** Added support in `swarm.py` for routing requests to either standard Google Gemini API (`LLM_PROVIDER=gemini`) or any local/OpenAI-compatible LLM endpoint (`LLM_PROVIDER=local`, such as Ollama or LiteLLM).
* **ADK Integration:** Configured custom `base_url` overrides on sub-agents using ADK's `google.adk.models.Gemini` properties, mapping agent reasoning routes to local networks.
* **Mocks & Testing:** Integrated new unit test coverage checks validating client and swarm provider configuration behaviors.

### 📊 Console Logging Aesthetics & Rate limit Guard
* **Compact Terminal Output:** Streamlined FastAPI system logging to formatting prefix `[TIME] MESSAGE` for instant CLI clarity.
* **Noisy Log Suppression:** Silenced verbose debug loggers from upstream libraries (`httpx`, `watchfiles`, `google`) to keep output focused on agent pipeline milestones.
* **429 Quota Error Intercept:** Modified the upload router in `main.py` to catch `RESOURCE_EXHAUSTED` errors gracefully, logging concise warnings and returning an HTTP 429 status indicating that the user can retry or toggle `LLM_PROVIDER=local`.

### 🐞 Bugfixes & Code Alignments
* **FastMCP Initialization:** Fixed `FastMCP` startup crash in `compliance_server.py` by replacing the unsupported `description` parameter with `instructions`.
* **Workspace Housekeeping:** Removed unused mock file `test_invoice.txt` at the root directory of the workspace.

### 📖 Documentation & Guidelines
* **README.md:** Clarified model definitions, documented environment configurations, and recommended placing submission PDFs under the `/samples` folder.
* **docs/architecture.md:** Documented the dynamic provider toggle architecture.
* **SKILL.md:** Updated skill path targets, corrected orchestrator method signatures, and fully documented all 6 implemented PII regex patterns.

---

## [v1.5.0] - Intermediary Architecture & Security Update
*Date: July 2, 2026*

### 📝 Overview
This release focuses on bridging the gap between the initial prototype and a production-ready enterprise architecture. It addresses critical feedback regarding security, validation, and documentation prior to the full Google ADK migration.

### 🔒 Security & Validation (Zero-Trust)
* **Enhanced PII Redaction:** Upgraded the `mask_pii.py` skill with advanced regex patterns to scrub sensitive data locally *before* LLM ingestion.
* **Strict Validation Layer:** Implemented `validator.py` to intercept and reject files with invalid extensions or excessive file sizes, protecting the server from malicious payloads.

### 🏗️ Architecture & Documentation
* **Model Accuracy:** Fixed the model identifier to correctly reference `gemini-2.0-flash`, ensuring stable API communication.
* **System Observability (Visual):** Added a comprehensive Mermaid.js architecture diagram to the `README.md` to visualize the sequential agent pipeline and Human-in-the-Loop (HITL) pathways.
* **Skill Documentation:** Added `SKILL.md` to properly document the privacy tool's integration and zero-trust mandate.

### ⚙️ Backend Enhancements
* **Data Schemas:** Hardened the Pydantic schemas (`TriageResult`, `AuditResult`) to guarantee strict JSON output from the Gemini API.
* **Persistent Auditing:** Minor enhancements to the `database.py` SQLite ledger to ensure all pipeline events are properly logged.
