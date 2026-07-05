import os
import glob
from fpdf import FPDF

# Ensure the samples directory exists
os.makedirs("samples", exist_ok=True)

# 1. Clean up all old files in samples/
for f in glob.glob("samples/*"):
    try:
        os.remove(f)
        print(f"Deleted old sample: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")

# Helper function to generate a simple PDF
def create_pdf(filename: str, title: str, content: list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 10)
    for line in content:
        if line.startswith("---"):
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        elif line.startswith("[SECTION]"):
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, line.replace("[SECTION] ", ""), ln=True)
            pdf.set_font("helvetica", "", 10)
        else:
            pdf.multi_cell(0, 5, line)
            pdf.ln(1.5)
            
    pdf.output(os.path.join("samples", filename))
    print(f"Generated perfect sample: samples/{filename}")

# ── 1. INVOICES ───────────────────────────────────────────────────────────────
create_pdf(
    "compliant_invoice.pdf",
    "TAX INVOICE",
    [
        "Invoice No: INV-2026-99214",
        "Invoice Date: 2026-06-20",
        "Due Date: 2026-07-20",
        "---",
        "[SECTION] Seller Details",
        "Name: TechPro Hardware Solutions Pvt. Ltd.",
        "Address: 55 Mount Road, Guindy, Chennai, Tamil Nadu - 600032",
        "Seller GSTIN: 33AABCT9988D1Z8",
        "Seller PAN: AABCT9988D",
        "---",
        "[SECTION] Buyer Details",
        "Name: Innovate Labs Solutions Ltd.",
        "Address: 12 Barakhamba Road, Connaught Place, New Delhi - 110001",
        "Buyer GSTIN: 29AADCP4422F2Z1",
        "---",
        "[SECTION] Line Items",
        "1. Laptop Charger (Qty: 2) - Rate: 2,500.00 - HSN: 85044090 - Total: 5,000.00",
        "2. Wireless Mouse (Qty: 5) - Rate: 1,000.00 - HSN: 84716060 - Total: 5,000.00",
        "---",
        "Subtotal: INR 10,000.00",
        "GST (18%): INR 1,800.00",
        "Total Amount Due: INR 11,800.00",
        "---",
        "Authorized Signatory: TechPro Hardware Solutions Ltd."
    ]
)

create_pdf(
    "non_compliant_invoice.pdf",
    "INVOICE",
    [
        "Invoice Number: INV-2026-002",
        "Date: June 2026",
        "---",
        "[SECTION] From",
        "Some Random Hardware Vendor",
        "---",
        "[SECTION] To",
        "Our Company",
        "---",
        "[SECTION] Items",
        "- Consulting work done: 50,000",
        "- Keyboard and Mouse: 20,000",
        "---",
        "Total Amount: Rs. 70,000",
        "Please pay soon. Thank you.",
        "(No GSTIN, no PAN, no HSN codes, and no signatures are present on this document)"
    ]
)

# ── 2. CERTIFICATES ───────────────────────────────────────────────────────────
create_pdf(
    "compliant_certificate.pdf",
    "FOOD SAFETY AND STANDARDS AUTHORITY OF INDIA",
    [
        "REGULATORY COMPLIANCE CERTIFICATE OF REGISTRATION",
        "---",
        "Certificate Number: FSSAI-2026-88741",
        "Date of Issuance: 2026-06-15",
        "Valid From: 2026-06-15",
        "Valid Until: 2029-06-14",
        "---",
        "This is to certify that the business entity named below has been verified and registered under the Food Safety and Standards Act, 2006.",
        "---",
        "[SECTION] Certified Entity details",
        "Entity Name: Organic Delights Food Processing Pvt. Ltd.",
        "Registered Address: 55 Mount Road, Guindy, Chennai, Tamil Nadu - 600032",
        "---",
        "Authorized Signatory Status: Signed and stamped by Commissioner of Food Safety, Chennai.",
        "Signature: Dr. Sandeep Kumar (Authorized Officer)"
    ]
)

create_pdf(
    "non_compliant_certificate.pdf",
    "FOOD REGISTRY CERTIFICATE",
    [
        "STATE LICENSE CERTIFICATE",
        "---",
        "Valid From: 2020-01-01",
        "Valid Until: 2023-01-01",
        "(This certificate has expired)",
        "---",
        "Certified Entity: Fresh and Pure Foods",
        "Address: MIDC Industrial Area, Pune",
        "---",
        "Note: The 14-digit FSSAI Registration number is missing from this document.",
        "No authorized signature or regulatory stamp is present."
    ]
)

# ── 3. CONTRACTS ──────────────────────────────────────────────────────────────
create_pdf(
    "compliant_contract.pdf",
    "SERVICE AGREEMENT",
    [
        "Effective Date: 2026-07-01",
        "---",
        "[SECTION] Clause 1 - Parties",
        "This Service Agreement is entered into on 2026-07-01 by and between:",
        "1. CLIENT: Apex Consulting Group Services, 120 Barakhamba Road, Connaught Place, New Delhi - 110001",
        "2. SERVICE PROVIDER: CloudScale Solutions Inc., 45 MG Road, Bengaluru, Karnataka - 560001",
        "---",
        "[SECTION] Clause 2 - Scope of Deliverables",
        "CloudScale Solutions will deliver custom software engineering, architectural reviews, and consulting services as defined in Exhibit A.",
        "---",
        "[SECTION] Clause 3 - Dispute Resolution & Jurisdiction",
        "All disputes arising out of this agreement shall be settled through arbitration under the laws of India, and the parties agree to submit to the exclusive jurisdiction of the courts of New Delhi, India.",
        "---",
        "[SECTION] Clause 4 - Execution Signatures",
        "IN WITNESS WHEREOF, the parties hereto have executed this Agreement on the dates below.",
        "Signed by Client Representative: Mr. Anil Mehta, Managing Director",
        "Signed by Provider Representative: Mr. Rajesh Sen, Chief Operating Officer"
    ]
)

create_pdf(
    "non_compliant_contract.pdf",
    "MEMORANDUM OF AGREEMENT",
    [
        "CONTRACT REFERENCE: CONTRACT-2026-089",
        "---",
        "[SECTION] Parties",
        "Party A: Horizon Enterprises Pvt. Ltd.",
        "Party B: Global Trade Solutions Inc.",
        "---",
        "[SECTION] Scope of Deliverables",
        "Deliver computer parts and software components.",
        "---",
        "[SECTION] Signatures",
        "Signed by Party A: __________________________ (Blank)",
        "Signed by Party B: __________________________ (Blank)",
        "---",
        "(This document is non-compliant because signatures are blank, there are no effective or expiry dates, and it lacks a dispute resolution or jurisdiction clause)"
    ]
)

# ── 4. REPORTS ────────────────────────────────────────────────────────────────
create_pdf(
    "compliant_report.pdf",
    "REGULATORY COMPLIANCE SUMMARY REPORT",
    [
        "Issuing Organization: Global Compliance Standards Ltd.",
        "Reporting Period: April 2026 - June 2026 (Q2 FY2026)",
        "Date of Issue: 2026-06-30",
        "---",
        "[SECTION] Executive Summary",
        "This report summarizes the compliance auditing trial database outputs for all ingested business records. The system has successfully validated transactions in accordance with applicable corporate accounting regulations and Ind AS standards.",
        "---",
        "[SECTION] Governance Approvals",
        "Approved and signed on behalf of the Board of Directors.",
        "Signature: Sunita Sharma, Director",
        "Accounting Standards applied: Indian Accounting Standards (Ind AS)"
    ]
)

create_pdf(
    "non_compliant_report.pdf",
    "ANNUAL AUDIT SUMMARY",
    [
        "Date of Issue: June 2026",
        "---",
        "[SECTION] Summary",
        "This is a general summary of company operations.",
        "---",
        "(This document is non-compliant because it misses the mandatory reporting period covered by the report and has no authorized signatories or approvals)"
    ]
)

# ── 5. PII DOCUMENT ───────────────────────────────────────────────────────────
create_pdf(
    "non_compliant_pii.pdf",
    "RESTRICTED CUSTOMER DATABASE EXPORT",
    [
        "WARNING: CONTAINS UNMASKED PERSONALLY IDENTIFIABLE INFORMATION (PII)",
        "---",
        "[SECTION] Customer Account Details",
        "Customer Name: John Doe",
        "Customer Email: john.doe@example.com",
        "Customer Phone: +91-98765-43210",
        "Aadhaar Number: 1234-5678-9012",
        "Credit Card Details: 4111-1111-1111-1111",
        "PAN Card: ABCDE1234F",
        "---",
        "(This document is non-compliant because it exposes raw, unmasked credit cards, government IDs, and contact info, violating data privacy regulations)"
    ]
)
