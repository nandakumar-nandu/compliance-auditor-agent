# Changelog

All notable changes to this project will be documented in this file.

## [v1.5.0] - Intermediary Architecture & Security Update
*Date: June 29, 2026*

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
*Date: July 1, 2026*

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

## [v2.5.0] - Intermediary Architecture & Security Update
*Date: July 3, 2026*

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

---

## [v3.0.0] - PDF Reporting, Human Override Governance & Clean Samples
*Date: July 6, 2026*

### 📝 Overview
This major release introduces boardroom-ready PDF compliance reports, robust Human-in-the-Loop override capabilities, and standardizes the samples folder to provide exactly one compliant and one non-compliant pair for each document category.

### 📄 Boardroom-Ready PDF Reports
* **In-Memory PDF Generation:** Created `pdf_generator.py` using `fpdf2` to build beautiful, highly-polished corporate reports with risk indicators, verdict badges, violation tables, and footers.
* **Unicode Emoji Safety:** Implemented smart translation filters to replace emoji status indicators (like `✅` and `❌`) and smart quotes with standard ASCII equivalents, preventing PDF compilation crashes.
* **Streamed Endpoint:** Added a `GET /api/audit/logs/{log_id}/pdf` endpoint to retrieve and download reports on-demand directly from the database ledger.

### ⚖️ Human Override Governance
* **Verdict Modification:** Upgraded `POST /api/audit/approve` to support `override_status` (allowing humans to change the AI's verdict to correct false-positives).
* **Commentary Auditing:** Added `reviewer_notes` parameter to log human comments, storing override metadata directly in the database audit logs.
* **Test Coverage:** Added comprehensive unit tests in `test_pipeline.py` verifying status modification and validation inputs.

### 📂 Sample Directory Standardization
* **Lightweight Test Pairings:** Rebuilt `/samples` folder to contain exactly 1 compliant and 1 non-compliant pair for Invoice, Certificate, Contract, and Report categories (along with 1 raw PII data exposure demo).
* **Swarm prompt tightening:** Enhanced Auditor Agent Swarm prompts in `swarm.py` to prevent rule hallucinations, ensuring compliant contract and report files pass audits successfully.

### 🛡️ PII Engine Refinements
* **Luhn Check Filtering:** Implemented a Luhn algorithm check on the Credit Card pattern to prevent redacting valid 14-digit FSSAI numbers as credit cards.
* **Phone Regex Safeguard:** Modified phone number replacements to ignore contiguous 13+ digit numbers, preventing false-positive redaction of FSSAI and registration IDs.
