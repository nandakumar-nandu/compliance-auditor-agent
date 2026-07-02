# ============================================================
# 🐳 DOCKERFILE — PRODUCTION DEPLOYMENT CONFIG
# ============================================================
#
# 🏗️  Architecture Role: Deployability demonstration
# 📚 Course Concepts Demonstrated:
#      ✅ Deployability (Day 5: From Vibe to Live)
#      ✅ Production-grade containerization
#      ✅ Health check for cloud orchestrators (Cloud Run, GKE)
#      ✅ Zero API key exposure (keys via environment variables only)
#
# How to build and run:
#   docker build -t smart-doc-auditor .
#   docker run -p 8080:8080 -e GEMINI_API_KEY=your_key smart-doc-auditor
#
# Deploy to Google Cloud Run:
#   gcloud run deploy smart-doc-auditor \
#     --source . \
#     --region us-central1 \
#     --set-env-vars GEMINI_API_KEY=your_key
# ============================================================

# ── Base Image ────────────────────────────────────────────────────────────────
# Python 3.11 slim: minimal footprint, production-stable, security-patched
FROM python:3.11-slim

# ── Working Directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install uv (Fast Python Package Manager) ──────────────────────────────────
# uv is significantly faster than pip — recommended for production images
RUN pip install uv --quiet

# ── Copy Dependencies First (Docker Layer Cache Optimization) ─────────────────
# Copying requirements.txt before the full source code means Docker only
# re-runs pip install when dependencies change, not on every code change.
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# ── Copy Application Source ───────────────────────────────────────────────────
COPY . .

# ── Environment Variables (Keys are NEVER hardcoded in images) ────────────────
# These are placeholders — actual values are injected at runtime via:
#   docker run -e GEMINI_API_KEY=... or Cloud Run --set-env-vars
ENV GEMINI_API_KEY=""
ENV GOOGLE_CLOUD_PROJECT=""
ENV PORT=8080

# ── Health Check ──────────────────────────────────────────────────────────────
# Tells Docker/Cloud Run/GKE that the container is healthy.
# The /health endpoint is defined in main.py.
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=15s \
    --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ── Expose Port ───────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Startup Command ───────────────────────────────────────────────────────────
# Uvicorn serves the FastAPI app in production mode.
# --host 0.0.0.0 makes it accessible outside the container.
# --workers 2 enables parallel request handling.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
