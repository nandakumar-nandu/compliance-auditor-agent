# ============================================================
# 🚀 SMART DOCUMENT AUDITOR — ENTERPRISE FASTAPI BACKEND 🚀
# ============================================================
#
# 🏗️  Architecture Role: API Gateway & Pipeline Orchestrator
# 📚 Course Concepts Demonstrated:
#      - Multi-Agent System (ADK) via ComplianceSwarm
#      - Security Features via Validator + PII Masking
#      - Deployability via FastAPI + Dockerfile
#      - Human-in-the-Loop checkpoint for critical findings
#      - Persistent audit ledger via SQLite
#
# ⚠️  NEVER hardcode API keys. Always use .env file.
# ============================================================

import os
import uuid
import shutil
import logging

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

# ── Internal Module Imports ───────────────────────────────────────────────────
from database import get_db, AuditLog
from audit_engine.swarm import ComplianceSwarm
from audit_engine.validator import DocumentValidator

# ── Structured Logging Setup (Day 5: Observability) ──────────────────────────
# Using structured logging instead of print() for production observability.
# In a real deployment, these logs can be shipped to Google Cloud Logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger("SmartDocumentAuditor")

# ── FastAPI Application Initialization ───────────────────────────────────────
app = FastAPI(
    title="Smart Document Auditor API",
    version="5.0.0 (ADK + MCP Edition)",
    description=(
        "An enterprise-grade, zero-trust AI compliance backend powered by "
        "Google ADK Multi-Agent Swarm and a real MCP Server for dynamic rule loading."
    ),
    contact={
        "name": "Kaggle Capstone Project",
        "url": "https://github.com/your-repo/compliance-auditor-agent"
    }
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
# Allows external frontends (React, Streamlit, etc.) to communicate with this API.
# In production, replace "*" with your specific frontend domain for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── In-Memory Session Store (Human-in-the-Loop) ───────────────────────────────
# Temporarily holds HIGH/CRITICAL audit results awaiting human approval.
# In production, replace with Redis for scalability.
pending_reviews: dict = {}


# ============================================================
# 🏠 SYSTEM ROUTES
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    """
    Root redirect — sends browser visitors to the interactive Swagger UI.
    This makes it easy for evaluators to test the API without a frontend.
    """
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint required for production deployments (Docker, Cloud Run).
    Returns API status and version. Used by Dockerfile HEALTHCHECK instruction.
    """
    return {
        "status": "healthy",
        "version": "5.0.0",
        "agent_system": "Google ADK Multi-Agent Swarm",
        "mcp_server": "ComplianceRulesServer (FastMCP)"
    }


# ============================================================
# 📤 CORE ENDPOINT: UPLOAD & AUDIT
# ============================================================

@app.post("/api/audit/upload", tags=["Audit"])
async def upload_and_audit(
    file: UploadFile = File(...),
    auto_approve: bool = Query(
        default=False,
        description="If True, skips human review even for CRITICAL findings."
    ),
    db: Session = Depends(get_db)
):
    """
    The master pipeline endpoint — triggers the full ADK Multi-Agent Swarm.

    Pipeline Stages:
        1. 🛡️  Validate the uploaded file (type + size check)
        2. 🤖  Run the ADK Compliance Swarm (OCR → PII Masking → Triage → Audit → Report)
        3. 🚨  Human-in-the-Loop: Pause if severity is HIGH or CRITICAL
        4. 💾  Persist the result to the SQLite audit ledger
        5. 📤  Return the full compliance report

    Args:
        file (UploadFile): The document to audit (TXT, PDF, PNG, JPG, JPEG).
        auto_approve (bool): Bypass the human review checkpoint (default: False).
        db (Session): Injected SQLAlchemy database session.

    Returns:
        dict: Full audit report or a pending-review notice for critical findings.
    """
    logger.info(f"📥 New upload received: '{file.filename}'")

    # ── Secure Temporary File Storage ────────────────────────────────────────
    # Files are saved locally only for the duration of this request,
    # then deleted in the `finally` block regardless of success or failure.
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # ── PHASE 1: Security Validation ─────────────────────────────────────
        # The Validator acts as the API's "bouncer" — rejecting bad files
        # before they ever reach the expensive AI pipeline.
        logger.info("🛡️  Phase 1: Validating file...")
        DocumentValidator.validate_file(file_path, file.filename)

        # ── PHASE 2: ADK Multi-Agent Swarm ───────────────────────────────────
        # Initializes the ComplianceSwarm and runs the full agent pipeline:
        # OCR Agent → PII Masking Skill → Triage Agent → Auditor Agent (MCP) → Reporter Agent
        logger.info("🤖 Phase 2: Triggering ADK Compliance Swarm...")
        swarm = ComplianceSwarm()
        result = await swarm.process_document(file_path)

        # ── PHASE 3: Human-in-the-Loop Checkpoint ────────────────────────────
        # (Day 4 + Day 5 concept: Safety guardrails in agentic systems)
        # If the Auditor Agent detects HIGH or CRITICAL severity, we pause
        # the pipeline and ask a human to review before generating the report.
        severity = result.get("severity", "LOW")
        if severity in ["HIGH", "CRITICAL"] and not auto_approve:
            # Generate a unique session ID to track this pending review
            session_id = str(uuid.uuid4())
            pending_reviews[session_id] = {
                "file_path": file_path,
                "result": result
            }
            logger.warning(
                f"⚠️  HUMAN REVIEW REQUIRED | Severity: {severity} | "
                f"Session: {session_id} | File: '{file.filename}'"
            )
            return {
                "status": "AWAITING_HUMAN_REVIEW",
                "severity": severity,
                "message": (
                    f"🚨 {len(result.get('audit_result', {}).get('violations', []))} "
                    f"critical violation(s) detected. Human approval required. "
                    f"Call POST /api/audit/approve?session_id={session_id} to proceed."
                ),
                "preview_violations": result.get("audit_result", {}).get("violations", [])[:3],
                "session_id": session_id
            }

        # ── PHASE 4: Persist to Audit Ledger ─────────────────────────────────
        # Every audit is permanently logged to the SQLite database.
        # This creates an immutable compliance trail for legal/enterprise use.
        logger.info("💾 Phase 4: Saving audit to SQLite ledger...")
        db_log = AuditLog(
            filename=file.filename,
            doc_type=result["doc_type"],
            status=result["status"],
            severity=result.get("severity", "LOW"),
            full_report=result
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)

        logger.info(f"✅ Pipeline complete | Log ID: {db_log.id} | Status: {result['status']}")
        return {
            "message": "✅ Audit complete.",
            "log_id": db_log.id,
            "data": result
        }

    except HTTPException:
        # Re-raise HTTP exceptions (from Validator) as-is
        raise

    except Exception as e:
        # Catch unexpected errors and return a clean 500 response
        logger.error(f"❌ Pipeline failure for '{file.filename}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Swarm pipeline failure: {str(e)}")

    finally:
        # ── Guaranteed Cleanup ────────────────────────────────────────────────
        # The temp file is ALWAYS deleted — even if the pipeline crashes.
        # This is a critical Zero-Trust data hygiene practice.
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Temp file deleted: '{file.filename}'")


# ============================================================
# ✅ HUMAN APPROVAL ENDPOINT
# ============================================================

@app.post("/api/audit/approve", tags=["Audit"])
async def approve_pending_audit(
    session_id: str = Query(..., description="The session ID from the pending review response."),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-Loop approval endpoint.

    After a HIGH/CRITICAL audit is flagged, a human reviewer calls this endpoint
    to authorize the pipeline to continue and generate the final report.

    Args:
        session_id (str): The unique session ID returned by the upload endpoint.
        db (Session): Injected SQLAlchemy database session.

    Returns:
        dict: The completed audit report after human approval.
    """
    # Check if the session exists in our pending store
    if session_id not in pending_reviews:
        raise HTTPException(
            status_code=404,
            detail="Session not found. It may have already been approved or expired."
        )

    logger.info(f"✅ Human approval received for session: {session_id}")

    # Retrieve the cached result and release it
    cached = pending_reviews.pop(session_id)
    result = cached["result"]

    # Persist the human-approved audit to the ledger
    db_log = AuditLog(
        filename=result.get("filename", "unknown"),
        doc_type=result["doc_type"],
        status=result["status"],
        severity=result.get("severity", "HIGH"),
        full_report=result
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    logger.info(f"✅ Human-approved audit saved | Log ID: {db_log.id}")
    return {
        "message": "✅ Human approval confirmed. Audit committed to ledger.",
        "log_id": db_log.id,
        "data": result
    }


# ============================================================
# 📊 ANALYTICS ENDPOINT: AUDIT HISTORY
# ============================================================

@app.get("/api/audit/logs", tags=["Analytics"])
def get_audit_logs(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns paginated audit history from the SQLite ledger.
    Used by a frontend dashboard to display compliance trends over time.

    Args:
        limit (int): Number of recent logs to return (1–100, default: 10).
        db (Session): Injected SQLAlchemy database session.

    Returns:
        dict: List of recent audit log records.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    logger.info(f"📊 Audit log query: returned {len(logs)} record(s)")
    return {"total": len(logs), "logs": logs}
