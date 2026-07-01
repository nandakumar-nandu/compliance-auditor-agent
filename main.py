# ==========================================
# 🚀 ENTERPRISE FASTAPI BACKEND 🚀
# ==========================================

import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

# 🧱 Internal Architecture Imports
from database import get_db, AuditLog
from audit_engine.swarm import ComplianceSwarm
from audit_engine.validator import DocumentValidator

# 🌐 Initialize the FastAPI Application
app = FastAPI(
    title="Smart Document Auditor API", 
    version="4.0.0 (Enterprise Swarm Edition)",
    description="Zero-Trust Multi-Agent Compliance Backend"
)

# 🔓 Allow external frontends (like React) to communicate with this API
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# ------------------------------------------
# 🏠 SYSTEM ROUTES
# ------------------------------------------
@app.get("/", include_in_schema=False)
def root():
    """Redirects visitors from the root URL to our beautiful Swagger UI."""
    return RedirectResponse(url="/docs")

# ------------------------------------------
# 📤 CORE ENDPOINT: UPLOAD & AUDIT
# ------------------------------------------
@app.post("/api/audit/upload")
async def upload_and_audit(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    The master pipeline endpoint:
    1. Saves the file securely.
    2. Validates it.
    3. Runs the multi-agent AI Swarm.
    4. Logs the result to the SQL database.
    """
    # 📂 Securely save the uploaded file temporarily
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 🛡️ PHASE 1: Security Validation
        DocumentValidator.validate_file(file_path, file.filename)

        # 🐝 PHASE 2: Trigger the AI Swarm (includes OCR & Privacy Scrubbing)
        swarm = ComplianceSwarm()
        result = swarm.process_fastapi_upload(file_path)

        # 💾 PHASE 3: Persist transaction to SQLite Database
        db_log = AuditLog(
            filename=file.filename,
            doc_type=result["doc_type"],
            status=result["status"],
            full_report=result
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        print(f"🎉 [Pipeline Complete]: Audit saved with Log ID: {db_log.id}")
        return {"message": "Audit complete", "data": result, "log_id": db_log.id}
    
    except Exception as e:
        # 🚨 Handle errors gracefully
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 🧹 ALWAYS clean up the temporary file, no matter what happens
        if os.path.exists(file_path):
            os.remove(file_path)

# ------------------------------------------
# 📊 ANALYTICS ENDPOINT: GET LOGS
# ------------------------------------------
@app.get("/api/audit/logs")
def get_audit_logs(limit: int = 10, db: Session = Depends(get_db)):
    """Fetches the history of audited documents for the frontend dashboard."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return {"logs": logs}