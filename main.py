import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db, AuditLog
from audit_engine.swarm import ComplianceSwarm
from audit_engine.validator import DocumentValidator

app = FastAPI(title="Smart Document Auditor API", version="3.0.0 (Advanced)")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.post("/api/audit/upload")
async def upload_and_audit(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. SECURITY VALIDATION LAYER
        DocumentValidator.validate_file(file_path, file.filename)

        # 2. MULTI-AGENT SWARM (Which now includes PII Masking)
        swarm = ComplianceSwarm()
        result = swarm.process_fastapi_upload(file_path)

        # 3. DATABASE PERSISTENCE
        db_log = AuditLog(
            filename=file.filename,
            doc_type=result["doc_type"],
            status=result["status"],
            full_report=result
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        return {"message": "Audit complete", "data": result, "log_id": db_log.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/api/audit/logs")
def get_audit_logs(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return {"logs": logs}