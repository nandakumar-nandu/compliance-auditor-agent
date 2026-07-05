# 🌟 Smart Document Auditor (Multi-Agent Swarm)

> An enterprise-grade, zero-trust AI backend built for Kaggle's "Concierge Agents" Capstone Project.

## 📖 Overview

This architecture utilizes a **Multi-Agent Swarm** powered by Gemini (`gemini-2.0-flash-lite` or custom models) to autonomously ingest, anonymize, classify, and audit corporate documents. Instead of relying on a single massive prompt, it distributes the workload across specialized AI agents to ensure high accuracy, strict security, and comprehensive legal logging.

## ✨ Key Features

*   **Zero-Trust Security:** Local PII scrubbing (emails, credit cards, phones, PAN, Aadhaar, GSTIN) runs *before* data ever hits the LLM. Includes Luhn checksum filtering to prevent false-positives.
*   **Native OCR Integration:** Seamlessly extracts text from binary PDFs and scanned Images.
*   **Agentic Swarm Routing:** 3 distinct agents (Triage, Auditor, Reporter) handle separate analytical concerns.
*   **LLM Provider Toggle:** Configurable switching between Google Gemini API and OpenAI-compatible local servers (Ollama, LiteLLM) to avoid quota limits.
*   **Dynamic Rules (MCP Pattern):** Loads specific JSON compliance rules dynamically based on the document's classification.
*   **Human Override Governance:** Support for human reviewers to override AI decisions and log auditor review notes.
*   **Boardroom-Ready PDF Reports:** Generate polished corporate PDF reports (verdict badges, risk dashboards, violations tables) on-demand.
*   **Persistent Legal Ledger:** Automatically logs all API audits to a local SQLite database.

## 🏗️ The Pipeline Architecture

When a document (TXT, PDF, JPG) is uploaded to the system, it passes through this exact control flow:

1.  **🛡️ Validator (`validator.py`):** Ensures the file is a safe format and within server size limits.
2.  **👁️ OCR Agent (Agent 0):** Calls Google's Vision APIs to extract raw text from PDFs/images, instantly deleting the cloud file afterward for data privacy.
3.  **🥷 Privacy Skill (`mask_pii.py`):** A zero-trust script that uses regex and validation algorithms to permanently scrub sensitive data from the text.
4.  **🗂️ Triage Agent (Agent 1):** Analyzes the scrubbed text to classify the document type (e.g., `invoice`, `certificate`).
5.  **⚖️ Auditor Agent (Agent 2):** Uses the Model Context Protocol to load specific rules based on the triage category, then evaluates the document.
6.  **✍️ Reporter Agent (Agent 3):** Takes the raw JSON audit data and drafts a boardroom-ready executive summary.
7.  **💾 SQLite Ledger (`database.py`):** Saves the full transaction payload into a permanent database table.

---

## 🚀 Getting Started

### 1. Install Dependencies
Ensure you have Python installed, clone the repository, and set up your environment:

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Windows
source .venv/bin/activate    # On macOS/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file at the root:
```env
# Cloud Gemini Model Selection
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite

# ── Option B: Local / Offline LLM Toggle ──
# Set LLM_PROVIDER to "local" to bypass AI Studio quota limits
LLM_PROVIDER=gemini
LOCAL_LLM_API_BASE=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama-local
LOCAL_LLM_API_KEY=local-key
```

### 3. Start the Server
Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```
Open `http://localhost:8000/docs` in your browser to access the interactive Swagger UI.

---

## 📂 Submission Samples
All submission sample documents are placed in the `/samples` folder at the root directory of the project for easy reviewer access. E.g.:
*   `compliant_invoice.pdf` / `non_compliant_invoice.pdf`
*   `compliant_certificate.pdf` / `non_compliant_certificate.pdf`
*   `compliant_contract.pdf` / `non_compliant_contract.pdf`
*   `compliant_report.pdf` / `non_compliant_report.pdf`
*   `non_compliant_pii.pdf` (demonstrates raw credit cards and Aadhaar leaks)
