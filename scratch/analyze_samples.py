import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the root directory
sys.path.append(os.getcwd())

load_dotenv()

from audit_engine.swarm import ComplianceSwarm

async def main():
    swarm = ComplianceSwarm()
    samples_dir = "samples"
    
    files = [
        "compliant_invoice.pdf",
        "non_compliant_invoice.pdf",
        "compliant_certificate.pdf",
        "non_compliant_certificate.pdf",
        "compliant_contract.pdf",
        "non_compliant_contract.pdf",
        "compliant_report.pdf",
        "non_compliant_report.pdf",
        "non_compliant_pii.pdf"
    ]
    
    print(f"{'Filename':<30} | {'Status':<15} | {'Severity':<10} | {'Violations Count':<16}")
    print("-" * 80)
    
    for f in files:
        file_path = os.path.join(samples_dir, f)
        if not os.path.exists(file_path):
            print(f"{f:<30} | File does not exist")
            continue
            
        try:
            result = await swarm.process_document(file_path)
            status = result.get("status", "UNKNOWN")
            severity = result.get("severity", "UNKNOWN")
            violations = result.get("audit_result", {}).get("violations", [])
            print(f"{f:<30} | {status:<15} | {severity:<10} | {len(violations):<16}")
        except Exception as e:
            print(f"{f:<30} | Error: {str(e)[:40]}")

if __name__ == "__main__":
    asyncio.run(main())
