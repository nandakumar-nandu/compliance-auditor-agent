# ============================================================
# 💾 SQLITE AUDIT LEDGER — PERSISTENT COMPLIANCE LOG
# ============================================================
#
# 🏗️  Architecture Role: Immutable Compliance Trail / Legal Ledger
# 📚 Course Concepts Demonstrated:
#      - Persistent state management for agent outputs
#      - Structured audit logging (Day 3: Agent Memory & State)
#      - Production-ready database design with SQLAlchemy ORM
#
# Every document that passes through the ADK Swarm is permanently
# recorded here. This creates an enterprise-grade compliance trail
# that can be queried, exported, and used for legal reporting.
# ============================================================

import datetime
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Database Connection ───────────────────────────────────────────────────────
# SQLite is used here for simplicity and zero-infrastructure cost.
# In a production cloud deployment, replace with:
#   PostgreSQL: "postgresql://user:password@host/dbname"
#   Cloud SQL:  "postgresql+asyncpg://..." (Google Cloud SQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./audit_logs.db"

# ── SQLAlchemy Engine ─────────────────────────────────────────────────────────
# `check_same_thread=False` is required when using SQLite with FastAPI's
# async threading model (multiple threads may share one connection).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ── Session Factory ───────────────────────────────────────────────────────────
# Each API request gets its own isolated database session via `get_db()`.
# `autocommit=False` ensures transactions are explicit and controlled.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── ORM Base Class ────────────────────────────────────────────────────────────
Base = declarative_base()


# ============================================================
# 📊 DATABASE MODEL: AUDIT LOG
# ============================================================

class AuditLog(Base):
    """
    Represents a single compliance audit record in the SQLite database.

    Each record captures:
    - WHAT was audited (filename, doc_type)
    - WHEN it was audited (timestamp)
    - WHAT the outcome was (status, severity)
    - THE FULL REPORT (all agent outputs in JSON)

    This is the "legal ledger" of the system — every AI decision is traceable.
    """
    __tablename__ = "audit_logs"

    # Primary key — unique ID for every audit event
    id = Column(Integer, primary_key=True, index=True)

    # Timestamp — auto-set to UTC time of creation (immutable audit trail)
    timestamp = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    # The original filename of the uploaded document
    filename = Column(String, index=True, nullable=False)

    # Document classification from the Triage Agent (e.g., "invoice", "certificate")
    doc_type = Column(String, nullable=True)

    # Final compliance verdict from the Auditor Agent (e.g., "COMPLIANT", "NON_COMPLIANT")
    status = Column(String, nullable=True)

    # Risk level determined by the Auditor Agent (LOW / MEDIUM / HIGH / CRITICAL)
    severity = Column(String, nullable=True, default="LOW")

    # The complete JSON payload from all agents — full traceability
    full_report = Column(JSON, nullable=True)


# ── Initialize Database Tables ────────────────────────────────────────────────
# Creates the `audit_logs` table on first run if it doesn't already exist.
# Safe to call on every startup — SQLAlchemy skips creation if table exists.
Base.metadata.create_all(bind=engine)


# ============================================================
# 🔌 DATABASE SESSION DEPENDENCY
# ============================================================

def get_db():
    """
    FastAPI dependency that provides a scoped database session per request.

    Uses Python's generator pattern with try/finally to guarantee that
    the session is always closed — even if an exception occurs mid-request.
    This prevents connection leaks in production.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
