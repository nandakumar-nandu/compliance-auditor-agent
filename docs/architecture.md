# 🏗️ Smart Document Auditor — Architecture Documentation

## Overview

The Smart Document Auditor is an enterprise-grade, zero-trust AI compliance
backend built on Google's Agent Development Kit (ADK). It uses a
Multi-Agent Swarm to autonomously ingest, anonymize, classify, and audit
corporate documents through a sequential pipeline of specialized agents.

---

## 🎯 Design Philosophy

### "Slicing the Elephant" (Day 5 Course Concept)
Instead of one massive agent trying to do everything, the system is
sliced into specialized micro-agents — each with a single clear
responsibility. This approach:

- Protects each agent's context window from overflow
- Makes individual agents testable and replaceable in isolation
- Enables parallel development of each pipeline stage
- Allows swapping one agent without affecting any other

### Zero-Trust Security Model
> "Never trust the input. Always scrub before processing."

PII is removed **locally using regex** before any text reaches
an external LLM API. The AI agents never see raw sensitive data.

### Dual-Provider LLM Switching (Gemini & Local LLM)
To prevent API rate-limit exhaustion and allow off-grid deployments, the swarm supports a configurable LLM provider toggle:
- **`gemini` (Cloud Backend):** Standard Google GenAI connection to `gemini-2.0-flash-lite`.
- **`local` (Local Backend):** Connects to any OpenAI-compatible API base URL (like Ollama or LiteLLM) running local models (e.g. `llama3`).
- Fully integrated with the ADK framework using custom base URL overrides for the sub-agents.


---

## 🔄 Pipeline Flow

```
User Upload (TXT / PDF / JPG)
        │
        ▼
┌─────────────────────────┐
│  1. Validator           │  ← Rejects bad extensions, MIME,
│     validator.py        │     size over 5MB, empty files
└──────────┬──────────────┘
           │ SAFE FILE
           ▼
┌─────────────────────────┐
│  2. OCR Agent (Agent 0) │  ← PDF/Image: Gemini Vision API
│                         │  ← TXT: read directly
│                         │  ← 🔐 Cloud file deleted after
└──────────┬──────────────┘
           │ RAW TEXT
           ▼
┌─────────────────────────┐
│  3. Privacy Skill       │  ← Regex scrubs: email, credit cards,
│     mask_pii.py         │     Aadhaar, PAN, GSTIN, phones
│     ADK Agent Skill     │  ← Runs LOCALLY (no network calls)
└──────────┬──────────────┘
           │ SCRUBBED TEXT
           ▼
┌──────────────────────────────────────────────────────────┐
│  4. ADK SequentialAgent Pipeline                         │
│                                                          │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────┐  │
│  │Triage Agent │ → │  Auditor Agent   │ → │ Reporter │  │
│  │  (Agent 1)  │   │   (Agent 2)      │   │(Agent 3) │  │
│  │             │   │       ↕          │   │          │  │
│  │ Classifies  │   │   MCP Server     │   │ Writes   │  │
│  │  doc type   │   │  (loads rules)   │   │ summary  │  │
│  └─────────────┘   └──────────────────┘   └──────────┘  │
└──────────┬───────────────────────────────────────────────┘
           │ AUDIT RESULT + SUMMARY
           ▼
┌─────────────────────────┐
│  5. Human-in-the-Loop   │  ← HIGH/CRITICAL → pause,
│     Checkpoint          │     return session_id to caller
│                         │  ← LOW/MEDIUM → auto-proceed
└──────────┬──────────────┘
           │ APPROVED (human or auto)
           ▼
┌─────────────────────────┐
│  6. SQLite Ledger       │  ← Permanent, immutable
│     database.py         │     compliance record
└──────────┬──────────────┘
           │
           ▼
    ✅ JSON API Response
    (doc_type, status, severity,
     violations, executive summary)
```

---

## 🗂️ Component Breakdown

### 1. API Gateway — `main.py`
- **Framework:** FastAPI (async, production-ready)
- **Role:** Receives file uploads, orchestrates the pipeline,
  manages Human-in-the-Loop sessions
- **Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/audit/upload` | POST | Triggers full ADK pipeline |
| `/api/audit/approve` | POST | Human approval for critical findings |
| `/api/audit/logs` | GET | Audit history dashboard |
| `/health` | GET | Docker / Cloud Run health check |

---

### 2. Security Validator — `audit_engine/validator.py`
- **Role:** API bouncer — rejects bad files before the AI pipeline
- **Why first?** Cheap CPU checks prevent expensive LLM API calls
  on invalid or malicious inputs
- **Checks performed in order:**

| Check | What It Catches |
|-------|----------------|
| Extension whitelist | `.exe`, `.sh`, `.js` and other dangerous types |
| MIME type verification | Renamed files (e.g., `malware.exe` renamed to `invoice.pdf`) |
| File size limit (5MB) | DoS attacks, token overflow, slow processing |
| Empty file guard | Zero-byte files that crash the AI pipeline |

---

### 3. OCR Agent — Agent 0 (`audit_engine/swarm.py`)
- **Technology:** Google Gemini Vision API via Files API
- **Role:** Extracts raw text from binary PDFs and scanned images
- **Security:** Uploaded file is **deleted from Google servers
  immediately** after text extraction completes

---

### 4. Privacy Skill — `skills/document_auditor/`
- **Technology:** Pure Python regex (zero network calls, zero API cost)
- **Role:** Scrubs PII before any LLM agent sees the document
- **ADK Role:** Registered as a versioned, reusable Agent Skill
- **PII patterns covered:**

| Pattern | Example Input | Redacted As |
|---------|--------------|-------------|
| Email | `cfo@company.com` | `[REDACTED_EMAIL]` |
| Credit Card | `4111 1111 1111 1111` | `[REDACTED_CREDIT_CARD]` |
| Aadhaar | `1234 5678 9012` | `[REDACTED_AADHAAR]` |
| PAN Card | `ABCDE1234F` | `[REDACTED_PAN]` |
| GSTIN | `22AAAAA0000A1Z5` | `[REDACTED_GSTIN]` |
| Phone | `+91-9876543210` | `[REDACTED_PHONE]` |

---

### 5. ADK Multi-Agent Pipeline — `audit_engine/swarm.py`
Three specialized agents orchestrated by ADK `SequentialAgent`:

| Agent | Name | Input | Output |
|-------|------|-------|--------|
| Agent 1 | TriageAgent | Scrubbed text | `doc_type`, `confidence` |
| Agent 2 | AuditorAgent | Text + doc_type + MCP rules | `status`, `violations`, `severity` |
| Agent 3 | ReporterAgent | Raw audit JSON | Markdown executive summary |

---

### 6. MCP Server — `mcp_server/compliance_server.py`
- **Technology:** FastMCP (Model Context Protocol)
- **Role:** Serves compliance rules as MCP tools and resources
- **Why MCP?** Any MCP-compatible agent — ADK, LangChain, Claude —
  can connect to this server. The rules engine is not locked to
  any single agent framework.
- **Registered Tools:**

| Tool | Purpose |
|------|---------|
| `get_compliance_rules(doc_type)` | Returns merged rules for a document type |
| `list_supported_document_types()` | Lists all auditable document categories |
| `get_rule_by_id(rule_id)` | Fetches one specific rule by ID |

- **Registered Resources:**

| Resource URI | Purpose |
|-------------|---------|
| `rules://all` | Full compliance_rules.json as readable resource |
| `rules://summary` | Human-readable summary of all rule categories |

---

### 7. Compliance Rules — `policies/compliance_rules.json`
- **Role:** Single source of truth for all compliance checks
- **Served by:** MCP Server tools (primary) + ADK FunctionTool (fallback)
- **Coverage:**

| Category | Rules | Regulation |
|----------|-------|-----------|
| General | 4 rules | PCI-DSS, India IT Act, UIDAI |
| Invoice | 5 rules | India GST Act 2017 |
| Certificate | 4 rules | India FSSAI Act 2006 |
| Contract | 4 rules | Indian Contract Act 1872 |
| Report | 3 rules | India Companies Act 2013 |

---

### 8. SQLite Audit Ledger — `database.py`
- **Technology:** SQLAlchemy ORM + SQLite
- **Role:** Immutable compliance trail — every AI audit decision
  is permanently recorded with a timestamp
- **In production:** Replace SQLite with PostgreSQL or Google Cloud SQL

---

## 🔒 Security Architecture

### Threat Model

| Threat Vector | Mitigation Applied |
|--------------|-------------------|
| Malicious file uploads | Validator: extension + MIME + size checks |
| PII leakage to LLM | Privacy Skill: regex scrubs before any API call |
| API key exposure | `.env` file + `.gitignore` + never hardcoded |
| Prompt injection via doc | PII scrubbing removes structured attack patterns |
| DoS via large files | 5MB hard cap at validation layer |
| Data on Google servers | OCR file deleted from cloud immediately after |
| Unreviewed critical findings | Human-in-the-Loop checkpoint for HIGH/CRITICAL |

---

## 🚀 Deployment Architecture

```
Local Development       Docker Container        Google Cloud Run
──────────────────      ────────────────        ────────────────
uvicorn main:app   →    docker build .    →     gcloud run deploy
port 8000               port 8080               auto-scaled HTTPS
.env file               ENV variables           Secret Manager
sqlite file             volume mount            Cloud SQL (prod)
```

### Local Development Commands
```bash
uvicorn main:app --reload --port 8000
```

### Docker Commands
```bash
docker build -t smart-doc-auditor .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key smart-doc-auditor
curl http://localhost:8080/health
```

### Google Cloud Run Deployment
```bash
gcloud run deploy smart-doc-auditor \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key
```

---

## 📚 Course Concepts Mapping

| Course Day | Concept Taught | Where Implemented in This Project |
|-----------|---------------|----------------------------------|
| Day 1 | Vibe Coding & Natural Language Programming | Built using Claude + Gemini Chat as primary interface |
| Day 2 | Agent Tools & Interoperability | ADK FunctionTool + real MCP Server |
| Day 3 | Agent Skills & Memory/State | DocumentAuditorSkill + SQLite ledger |
| Day 4 | Security & Evaluation | Validator + PII masking + pytest test suite |
| Day 5 | Production Deployment | FastAPI + Dockerfile + Cloud Run |

---

## 📁 Project Structure

```
compliance-auditor-agent/
├── main.py                    # FastAPI Gateway + Human-in-the-Loop
├── database.py                # SQLite Audit Ledger (SQLAlchemy ORM)
├── Dockerfile                 # Production container configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development and test dependencies
├── .env.example               # API key template (safe to commit)
├── .gitignore                 # Prevents secrets from reaching GitHub
├── README.md                  # Full project documentation
│
├── audit_engine/
│   ├── __init__.py
│   ├── swarm.py               # ADK SequentialAgent pipeline
│   └── validator.py           # Security validation layer
│
├── mcp_server/
│   ├── __init__.py
│   └── compliance_server.py   # Real FastMCP MCP Server
│
├── skills/
│   └── document_auditor/
│       ├── __init__.py
│       ├── skill.py           # ADK Agent Skill class
│       ├── SKILL.md           # Skill documentation
│       └── scripts/
│           ├── __init__.py
│           └── mask_pii.py    # Zero-Trust PII engine
│
├── policies/
│   └── compliance_rules.json  # Compliance ruleset (MCP-served)
│
├── tests/
│   ├── __init__.py
│   ├── test_validator.py      # Validator security tests
│   ├── test_mask_pii.py       # PII masking tests
│   └── test_pipeline.py       # Full pipeline integration tests
│
└── docs/
    ├── architecture.md        # This file — full architecture docs
    └── diagrams/
        └── pipeline.png       # Visual pipeline diagram (from Mermaid)
```

## 🏗️ System Workflow

```mermaid
flowchart TD
    A["👤 User\nUploads Document\nTXT / PDF / JPG"] --> B

    subgraph SECURITY ["🛡️ SECURITY LAYER"]
        B["Validator\nvalidator.py\nExtension + MIME + Size + Empty check"]
    end

    B -->|"❌ Invalid"| ERR["400 Error Response\nRejected"]
    B -->|"✅ Valid"| C

    subgraph INGESTION ["👁️ INGESTION LAYER"]
        C{"File Type?"}
        C -->|"TXT"| D1["Read Directly\nUTF-8 decode"]
        C -->|"PDF / Image"| D2["OCR Agent - Agent 0\nGemini Vision API\n🔐 Cloud file deleted after"]
    end

    D1 --> E
    D2 --> E

    subgraph PRIVACY ["🥷 ZERO-TRUST PRIVACY"]
        E["DocumentAuditorSkill\nmask_pii.py\nScrubs: Email, Cards, Aadhaar,\nPAN, GSTIN, Phone"]
    end

    E --> F

    subgraph ADK ["🤖 ADK SEQUENTIAL AGENT PIPELINE"]
        F["Triage Agent - Agent 1\nClassifies: invoice / certificate\ncontract / report / unknown"]
        F --> G["Auditor Agent - Agent 2\nCalls MCP Server for rules\nEvaluates compliance"]
        G <-->|"MCP Protocol"| MCP["MCP Server\ncompliance_server.py\nTools: get_rules\nlist_types, get_rule_by_id"]
        G --> H["Reporter Agent - Agent 3\nGenerates executive summary\nMarkdown format"]
    end

    H --> I

    subgraph HITL ["🧑 HUMAN-IN-THE-LOOP"]
        I{"Severity?"}
        I -->|"HIGH or CRITICAL"| J["Pause Pipeline\nReturn session_id\nAwait human approval"]
        I -->|"LOW or MEDIUM"| K["Auto Proceed"]
        J -->|"POST approve"| K
    end

    K --> L

    subgraph PERSISTENCE ["💾 PERSISTENCE LAYER"]
        L["SQLite Audit Ledger\ndatabase.py\nPermanent compliance record"]
    end

    L --> M["✅ JSON Response\nFull audit report\n+ executive summary"]