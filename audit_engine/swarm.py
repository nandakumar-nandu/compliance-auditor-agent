# ==========================================
# 🌟 MULTI-AGENT COMPLIANCE SWARM 🌟
# ==========================================

# 📦 Standard Library Imports
import os
import json

# 🤖 AI & Validation Imports
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

# 🛡️ Custom Security Skills
from skills.document_auditor.scripts.mask_pii import PrivacySkill

# Load environment variables (like our GEMINI_API_KEY)
load_dotenv()

# ==========================================
# 📋 STRICT DATA SCHEMAS (PYDANTIC)
# Forces the AI to always return perfect JSON!
# ==========================================

class TriageResult(BaseModel):
    """How the Triage Agent structures its classification."""
    doc_type: str
    confidence: float

class AuditResult(BaseModel):
    """How the Auditor Agent structures its final verdict."""
    status: str
    violations: list[str]
    
# ==========================================
# 🐝 THE SWARM ARCHITECTURE
# ==========================================

class ComplianceSwarm:
    def __init__(self, policy_path="policies/compliance_rules.json"):
        """Initializes the Swarm, loads the AI model, and preps our rulebook."""
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # ⚡ Using Flash Lite for high speed and generous free-tier rate limits
        self.model_id = 'gemini-3.1-flash-lite' 
        
        # 📖 Load our compliance policies from the JSON file
        with open(policy_path, 'r') as f:
            self.policies = json.load(f)
            
        # 🥷 Instantiate our Zero-Trust privacy scrubber
        self.privacy_skill = PrivacySkill()

    # ------------------------------------------
    # 🕵️‍♂️ AGENT 0: THE VISION / OCR AGENT
    # ------------------------------------------
    def extract_text_agent(self, file_path: str) -> str:
        """Reads binary files (PDFs/Images) and extracts raw text."""
        print(f"👁️  [OCR Agent]: Reading raw text from {os.path.basename(file_path)}...")
        
        # 1. Upload the file securely to Google's temporary File API
        uploaded_file = self.client.files.upload(file=file_path)
        
        # 2. Ask Gemini to extract the text exactly as written
        prompt = "Extract all text from this document exactly as it is written. Do not summarize or format. Just return the raw text."
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[uploaded_file, prompt]
        )
        
        # 3. 🚨 SECURITY FEATURE: Immediately delete the file from Google's servers!
        self.client.files.delete(name=uploaded_file.name)
        
        return response.text

    # ------------------------------------------
    # 🗂️ AGENT 1: THE TRIAGE AGENT
    # ------------------------------------------
    def triage_agent(self, document_content: str) -> str:
        """Looks at the document and figures out what category it belongs to."""
        print("🗂️  [Triage Agent]: Categorizing document type...")
        
        prompt = "Analyze this document. Is it an 'invoice', a 'certificate', or 'unknown'? Return ONLY valid JSON."
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, document_content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult,
                temperature=0.1  # Keep it strict and deterministic
            )
        )
        return json.loads(response.text)["doc_type"]

    # ------------------------------------------
    # ⚖️ AGENT 2: THE AUDITOR AGENT
    # ------------------------------------------
    def auditor_agent(self, document_content: str, doc_type: str) -> dict:
        """Takes the categorized document and audits it against specific rules."""
        print(f"⚖️  [Auditor Agent]: Checking compliance rules for '{doc_type}'...")
        
        # 🧠 MCP Pattern: Dynamically load ONLY the rules that apply to this document type
        active_rules = self.policies.get("general", []) + self.policies.get(doc_type, [])
        
        prompt = f"Evaluate the document against these rules: {json.dumps(active_rules)}. Return valid JSON."
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, document_content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AuditResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)

    # ------------------------------------------
    # ✍️ AGENT 3: THE REPORTER AGENT
    # ------------------------------------------
    def reporter_agent(self, audit_data: dict, doc_type: str) -> str:
        """Takes the raw JSON audit data and writes a boardroom-ready summary."""
        print("✍️  [Reporter Agent]: Drafting executive summary...")
        
        prompt = f"Draft a professional, 2-sentence executive summary for an audited '{doc_type}'. Data: {json.dumps(audit_data)}"
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4) # Slightly more creative for natural language
        )
        return response.text

    # ==========================================
    # 🚀 THE MASTER PIPELINE ORCHESTRATOR
    # ==========================================
    def process_fastapi_upload(self, file_path: str):
        """The main control flow that runs the entire swarm from start to finish."""
        try:
            # --- STEP 1: INGESTION & OCR ---
            # If it's just a text file, read it directly.
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            # If it's a PDF/Image, let Agent 0 handle it!
            else:
                raw_text = self.extract_text_agent(file_path)

            # --- STEP 2: ZERO-TRUST PRIVACY SCRUBBING ---
            # Scrub emails, credit cards, etc., before the main swarm sees the text!
            document_content = self.privacy_skill.redact_sensitive_info(raw_text)

            # --- STEP 3: THE SWARM EXECUTION ---
            doc_type = self.triage_agent(document_content)
            audit_data = self.auditor_agent(document_content, doc_type)
            final_report = self.reporter_agent(audit_data, doc_type)

            # --- STEP 4: PACKAGE THE RESULTS ---
            return {
                "doc_type": doc_type,
                "status": audit_data.get("status", "ERROR"),
                "audit_result": audit_data,
                "executive_summary": final_report,
                "extracted_text": document_content  # Includes the safely scrubbed text!
            }
            
        except Exception as e:
            # 🚨 Catch any errors gracefully so the server doesn't crash
            print(f"❌ [Swarm Error]: {str(e)}")
            raise Exception(f"Swarm failure: {str(e)}")