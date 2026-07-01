import os
import json
from google import genai
from dotenv import load_dotenv

# Load API key securely from .env file
load_dotenv()

class AuditorAgent:
    def __init__(self, policy_path):
        self.policy_path = policy_path
        self.rules = self.load_policies()
        # Initialize the modern GenAI Client
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    def load_policies(self):
        """MCP Tool: Dynamically loads the compliance rules from the data layer."""
        with open(self.policy_path, 'r') as f:
            return json.load(f)

    def audit_document(self, doc_text):
        """Routes text through the security skill, then uses the LLM to reason."""
        print(f"Agent is analyzing the document against {len(self.rules['rules'])} rules...")
        
        from skills.document_auditor.scripts.mask_pii import redact_sensitive_info
        clean_text = redact_sensitive_info(doc_text)
        
        prompt = f"""
        You are a strict, professional Compliance Auditor Agent.
        
        YOUR POLICIES TO ENFORCE:
        {json.dumps(self.rules, indent=2)}
        
        THE DOCUMENT TO AUDIT:
        "{clean_text}"
        
        INSTRUCTIONS:
        1. Evaluate the document against the policies.
        2. Determine if it is COMPLIANT or NON_COMPLIANT.
        3. Respond ONLY in valid JSON format using this exact structure:
        {{"status": "COMPLIANT" or "NON_COMPLIANT", "reason": "A brief explanation of why."}}
        """
        
        try:
            # Pointing to the new ultra-fast, budget-friendly Lite model
            response = self.client.models.generate_content(
                model='gemini-3.1-flash-lite', 
                contents=prompt
            )
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}
        
if __name__ == "__main__":
    agent = AuditorAgent("policies/compliance_rules.json")
    result = agent.audit_document("Invoice from GST verified vendor.")
    print(json.dumps(result, indent=2))