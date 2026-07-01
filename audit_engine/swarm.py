import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# --- PYDANTIC SCHEMAS (Production-grade data validation) ---
class TriageResult(BaseModel):
    doc_type: str  # e.g., "invoice", "certificate", "unknown"
    confidence: float

class AuditResult(BaseModel):
    status: str    # "COMPLIANT" or "NON_COMPLIANT"
    violations: list[str]
    
# --- THE SWARM ARCHITECTURE ---
class ComplianceSwarm:
    def __init__(self, policy_path="policies/compliance_rules.json"):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # Use the high-volume, multimodal Lite model
        self.model_id = 'gemini-3.1-flash-lite' 
        
        with open(policy_path, 'r') as f:
            self.policies = json.load(f)

    def triage_agent(self, document) -> str:
        """Agent 1: Looks at the document and categorizes it."""
        print("-> [Triage Agent]: Classifying document type...")
        prompt = "Analyze this document. Is it an 'invoice', a 'certificate', or 'unknown'? Return ONLY valid JSON matching this schema: {\"doc_type\": \"string\", \"confidence\": 0.0}"
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, document],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)["doc_type"]

    def auditor_agent(self, document, doc_type: str) -> dict:
        """Agent 2: Loads specific rules via MCP and audits the document."""
        print(f"-> [Auditor Agent]: Applying rules for type: '{doc_type}'...")
        
        # MCP Logic: Only load rules relevant to this specific document
        active_rules = self.policies.get("general", []) + self.policies.get(doc_type, [])
        
        prompt = f"""
        You are a strict Compliance Auditor. 
        Evaluate the provided document against these specific rules: {json.dumps(active_rules)}
        
        Return ONLY valid JSON matching this schema: 
        {{"status": "COMPLIANT" or "NON_COMPLIANT", "violations": ["List of rule IDs broken, if any"]}}
        """
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, document],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AuditResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)

    def reporter_agent(self, audit_data: dict, doc_type: str) -> str:
        """Agent 3: Synthesizes the final human-readable report."""
        print("-> [Reporter Agent]: Drafting final summary...")
        prompt = f"Draft a professional, 2-sentence executive summary for an audited '{doc_type}'. The audit data is: {json.dumps(audit_data)}"
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4)
        )
        return response.text

    def process_document(self, file_path: str):
        """The Orchestrator Loop that routes data between the agents."""
        print(f"\n=== Starting Swarm Audit for: {file_path} ===")
        try:
            # 1. Load Document (Supports both Text and Images!)
            if file_path.endswith(('.png', '.jpg', '.jpeg')):
                document = Image.open(file_path)
            else:
                with open(file_path, 'r') as f:
                    document = f.read()

            # 2. Swarm Execution
            doc_type = self.triage_agent(document)
            audit_data = self.auditor_agent(document, doc_type)
            final_report = self.reporter_agent(audit_data, doc_type)

            return {
                "doc_type": doc_type,
                "audit_result": audit_data,
                "executive_summary": final_report
            }
            
        except Exception as e:
            return {"status": "SWARM_ERROR", "details": str(e)}