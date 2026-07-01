🌟 Smart Document Auditor (Multi-Agent Swarm) 🌟

An enterprise-grade, zero-trust AI backend built for Kaggle's "Concierge Agents" Capstone Project. This architecture utilizes a Multi-Agent Swarm powered by Gemini 3.1 Flash Lite to autonomously ingest, anonymize, classify, and audit corporate documents.

🏗️ The Pipeline Architecture

When a document (TXT, PDF, JPG) is uploaded to the system, it passes through this exact pipeline:

🛡️ Validator (validator.py): Ensures the file is a safe format and within size limits.

👁️ OCR Agent (Agent 0): Dynamically calls Google's Vision APIs to extract raw text from PDFs and images, instantly deleting the cloud file afterward for security.

🥷 Privacy Skill (mask_pii.py): A zero-trust script that uses regex to permanently scrub emails, credit cards, and phone numbers from the text before the main logic sees it.

🗂️ Triage Agent (Agent 1): Analyzes the scrubbed text to classify the document type (e.g., invoice, certificate).

⚖️ Auditor Agent (Agent 2): Uses the Model Context Protocol (MCP) to load specific JSON compliance rules based on the triage category, then evaluates the document.

✍️ Reporter Agent (Agent 3): Takes the raw JSON audit and drafts a boardroom-ready executive summary.

💾 SQLite Ledger (database.py): Saves the entire transaction into a permanent database for legal compliance.

🚀 How to Run the Server

1. Install Dependencies:

uv pip install fastapi uvicorn sqlalchemy pydantic pillow google-genai python-dotenv python-multipart


2. Configure Environment:
Make sure you have a .env file in the root directory with your API key:

GEMINI_API_KEY=your_google_api_key_here


3. Start the Server:

uv run uvicorn main:app --reload


4. Test the API:
Open your browser and navigate to:
👉 http://127.0.0.1:8000/docs

Built with ❤️ utilizing FastAPI, Pydantic, and Gemini.