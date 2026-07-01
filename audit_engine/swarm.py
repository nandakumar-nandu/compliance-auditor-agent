import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image
from skills.document_auditor.scripts.mask_pii import PrivacySkill

load_dotenv()

class TriageResult(BaseModel):
    doc_type: str
    confidence: float

class AuditResult(BaseModel):
    status: str
    violations: list[str]
    
class ComplianceSwarm:
    def __init__(self, policy_path="policies/compliance_rules.json"):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_id = 'gemini-3.1-flash-lite' 
        with open(policy_path, 'r') as f:
            self.policies = json.load(f)
        self.privacy_skill = PrivacySkill()

    def triage_agent(self, document_content) -> str:
        print("-> [Triage Agent]: Classifying document type...")
        prompt = "Analyze this document. Is it an 'invoice', a 'certificate', or 'unknown'? Return ONLY valid JSON."
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, document_content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)["doc_type"]

    def auditor_agent(self, document_content, doc_type: str) -> dict:
        print(f"-> [Auditor Agent]: Applying rules for type: '{doc_type}'...")
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

    def reporter_agent(self, audit_data: dict, doc_type: str) -> str:
        print("-> [Reporter Agent]: Drafting final summary...")
        prompt = f"Draft a professional, 2-sentence executive summary for an audited '{doc_type}'. Data: {json.dumps(audit_data)}"
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4)
        )
        return response.text

    def process_fastapi_upload(self, file_path: str):
        """The Main Pipeline"""
        try:
            # 1. Read the file
            if file_path.endswith(('.png', '.jpg', '.jpeg')):
                document_content = Image.open(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                # 2. TRIGGER THE PRIVACY SKILL (Zero-Trust layer applied!)
                document_content = self.privacy_skill.redact_sensitive_info(raw_text)

            # 3. Swarm Execution
            doc_type = self.triage_agent(document_content)
            audit_data = self.auditor_agent(document_content, doc_type)
            final_report = self.reporter_agent(audit_data, doc_type)

            return {
                "doc_type": doc_type,
                "status": audit_data.get("status", "ERROR"),
                "audit_result": audit_data,
                "executive_summary": final_report
            }
        except Exception as e:
            raise Exception(f"Swarm failure: {str(e)}")