# ==========================================
# 💾 SQLITE AUDIT LEDGER 💾
# ==========================================

from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 🗄️ Database Connection URL (Local SQLite database)
SQLALCHEMY_DATABASE_URL = "sqlite:///./audit_logs.db"

# ⚙️ Initialize the SQLAlchemy Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite + FastAPI
)

# 🎫 Create a local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------------------------------
# 📊 DATABASE MODEL: AUDIT LOG
# ------------------------------------------
class AuditLog(Base):
    """Defines the structure of our historical compliance ledger."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow) # 🕒 When did it happen?
    filename = Column(String, index=True)                          # 📄 What was the file?
    doc_type = Column(String)                                      # 🗂️ Was it an invoice/cert?
    status = Column(String)                                        # ⚖️ COMPLIANT or NON_COMPLIANT
    full_report = Column(JSON)                                     # 📦 The full Swarm output

# 🛠️ Create the actual table inside the SQLite database if it doesn't exist
Base.metadata.create_all(bind=engine)

# ------------------------------------------
# 🔌 DATABASE DEPENDENCY
# ------------------------------------------
def get_db():
    """Provides a database session for FastAPI endpoints to use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()