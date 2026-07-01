import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

from database import get_db, AuditLog
from audit_engine.swarm import ComplianceSwarm  # Assumes your swarm.py is still here

load_dotenv()

app = FastAPI(
    title="Smart Document Auditor API",
    description="Multi-Agent AI Compliance Backend",
    version="2.0.0"
)

# Enable CORS for your MERN/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ADVANCED SWARM LOGIC ---
class EnterpriseSwarm(ComplianceSwarm):
    """Extends your base swarm to handle FastAPI file objects natively."""
    
    def process_fastapi_upload(self, file_path: str):
        print(f"=== Processing Enterprise Upload: {file_path} ===")
        try:
            # Multi-agent handoffs using the base logic
            doc_type = self.triage_agent(file_path)
            audit_data = self.auditor_agent(file_path, doc_type)
            final_report = self.reporter_agent(audit_data, doc_type)

            return {
                "doc_type": doc_type,
                "status": audit_data.get("status", "ERROR"),
                "audit_result": audit_data,
                "executive_summary": final_report
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# --- API ENDPOINTS ---

@app.post("/api/audit/upload")
async def upload_and_audit(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Ingests a document (PDF, PNG, JPG, TXT), runs the multi-agent swarm, 
    and logs the result to the SQLite database.
    """
    # 1. Save uploaded file securely to disk
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Trigger the AI Swarm
    swarm = EnterpriseSwarm()
    result = swarm.process_fastapi_upload(file_path)

    # 3. Persist the audit log to the SQLite Database
    db_log = AuditLog(
        filename=file.filename,
        doc_type=result["doc_type"],
        status=result["status"],
        full_report=result
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    # Clean up temp file
    os.remove(file_path)

    return {"message": "Audit complete", "data": result, "log_id": db_log.id}

@app.get("/api/audit/logs")
def get_audit_logs(limit: int = 10, db: Session = Depends(get_db)):
    """Fetches historical audits for your frontend dashboard."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return {"logs": logs}