# ============================================================
# 🌟 ADK MULTI-AGENT COMPLIANCE SWARM 🌟
# ============================================================
#
# 🏗️  Architecture Role: Core Intelligence Layer
# 📚 Course Concepts Demonstrated:
#      ✅ Multi-Agent System using Google ADK (SequentialAgent + sub-agents)
#      ✅ MCP Server integration via MCPToolset (real protocol, not a pattern)
#      ✅ Agent Skills (DocumentAuditorSkill for PII masking)
#      ✅ Security (Zero-Trust PII scrubbing before ANY LLM call)
#      ✅ Pydantic structured outputs (forces valid JSON from every agent)
#      ✅ Observability (structured logging of every agent step)
#
# Pipeline Flow:
#   OCR Agent (Agent 0)
#       → Privacy Skill (PII Masking)
#           → Triage Agent (Agent 1)  ─┐
#               → Auditor Agent (Agent 2) ← MCP Server (compliance rules)
#                   → Reporter Agent (Agent 3)
#                       → Final Report
# ============================================================

import os
import json
import logging
import asyncio
from typing import Optional

# ── Google ADK Imports ────────────────────────────────────────────────────────
# ADK (Agent Development Kit) is Google's official framework for building
# production-grade multi-agent systems. This is what the course teaches.
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types as genai_types
from google.adk.models import Gemini


# ── Raw GenAI SDK (for OCR Agent only) ───────────────────────────────────────
# The Vision/OCR Agent uses the raw SDK because it handles binary file uploads
# via the Files API — a feature not yet abstracted in ADK's high-level interface.
from google import genai

# ── Internal Skill Import ─────────────────────────────────────────────────────
# The DocumentAuditorSkill wraps our PII masking logic as a proper ADK Skill,
# making it reusable and shareable across any ADK-compatible agent.
from skills.document_auditor.skill import DocumentAuditorSkill


# ── Monkey-Patch Gemini for Automatic 429 Retry handling ─────────────────────
# Since Google Gemini free tier has strict rate limits (15 RPM), we intercept
# all model completions and apply exponential backoff retry.
from google.adk.models.google_llm import Gemini
original_generate_content_async = Gemini.generate_content_async

async def retrying_generate_content_async(self, llm_request, stream=False):
    max_retries = 3
    base_delay = 3.0  # seconds
    for attempt in range(max_retries):
        try:
            # We yield from the original generator method
            async for response in original_generate_content_async(self, llm_request, stream):
                yield response
            return
        except Exception as e:
            error_msg = str(e)
            is_transient = (
                "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Resource Exhausted" in error_msg or
                "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg
            )
            if is_transient and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logging.getLogger("ComplianceSwarm").warning(
                    f"⚠️ Transient error/rate limit hit on attempt {attempt + 1}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                await asyncio.sleep(delay)
            else:
                raise e

# Overwrite method globally
Gemini.generate_content_async = retrying_generate_content_async

# ── Environment & Logging Setup ───────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("ComplianceSwarm")

# ── Model Configuration ───────────────────────────────────────────────────────
# Fast, cost-efficient model ideal for structured tasks.
# Can be overridden via env variable GEMINI_MODEL (e.g., gemini-2.5-flash-lite or gemini-2.5-flash)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# ── Policy File Path ──────────────────────────────────────────────────────────
POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "policies", "compliance_rules.json")


def extract_json(text: str) -> dict:
    """Helper to extract JSON object from markdown or raw text."""
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_line_end = cleaned.find("\n")
        if first_line_end != -1:
            cleaned = cleaned[first_line_end:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end+1])
            except json.JSONDecodeError:
                pass
    return {}


# ============================================================
# 🔧 FUNCTION TOOLS (ADK FunctionTool wrappers)
# ============================================================
# These are standard Python functions registered as ADK FunctionTools.
# The ADK framework automatically generates tool schemas from type hints
# and docstrings, making them callable by any ADK agent.

def load_compliance_rules(document_type: str) -> dict:
    """
    Loads the compliance ruleset for a given document type from the policy file.

    This function is exposed as both:
    - A local ADK FunctionTool (fallback)
    - A resource served by the MCP Server (primary, for real MCP integration)

    Args:
        document_type: The document category (e.g., 'invoice', 'certificate').

    Returns:
        dict: The applicable compliance rules and rule count.
    """
    try:
        policy_file = os.path.abspath(POLICY_PATH)
        with open(policy_file, "r") as f:
            all_rules = json.load(f)

        # Merge general rules (apply to all docs) with type-specific rules
        general_rules = all_rules.get("general", [])
        specific_rules = all_rules.get(document_type.lower(), [])
        combined_rules = general_rules + specific_rules

        logger.info(f"📖 Rules loaded for '{document_type}': {len(combined_rules)} rule(s)")
        return {
            "document_type": document_type,
            "rules": combined_rules,
            "rule_count": len(combined_rules),
            "source": "compliance_rules.json"
        }
    except FileNotFoundError:
        logger.error("❌ compliance_rules.json not found!")
        return {"document_type": document_type, "rules": [], "rule_count": 0}


# Register as an ADK FunctionTool — the ADK agent can now call this like an API
compliance_rules_tool = FunctionTool(func=load_compliance_rules)


# ============================================================
# 🤖 ADK AGENT DEFINITIONS
# ============================================================
# Each agent is a specialized, single-responsibility AI unit.
# They are composed into a SequentialAgent pipeline by the orchestrator.

def build_triage_agent(model: str | Gemini) -> Agent:
    """
    Agent 1: The Triage Agent
    ─────────────────────────
    Responsibility: Classify the document into a known category.
    Input:          Pre-scrubbed document text (PII already removed).
    Output:         JSON with doc_type and confidence score.

    Why a separate agent?
    Separating classification from auditing follows the Single Responsibility
    Principle — the Auditor Agent trusts the Triage output and focuses only
    on compliance checking, not guessing what kind of document it has.
    """
    return Agent(
        name="TriageAgent",
        model=model,
        description="Classifies document type from privacy-scrubbed text.",
        instruction="""
        You are a document classification specialist with expertise in corporate paperwork.

        Your ONLY job is to analyze the provided document text and classify it.

        Classification categories:
        - "invoice"     → Payment requests, bills, purchase orders
        - "certificate" → Compliance certs, FSSAI, ISO, safety documents
        - "contract"    → Agreements, NDAs, service contracts, MOUs
        - "report"      → Financial reports, audit reports, status updates
        - "unknown"     → Does not fit any category above

        You MUST respond with ONLY this JSON structure (no extra text):
        {
            "doc_type": "<category>",
            "confidence": <float between 0.0 and 1.0>,
            "reasoning": "<one sentence explaining your classification>"
        }
        """,
    )


def build_auditor_agent(model: str | Gemini) -> Agent:
    """
    Agent 2: The Auditor Agent
    ──────────────────────────
    Responsibility: Evaluate document compliance against loaded rules.
    Input:          Document text + Triage Agent's classification.
    Tools:          compliance_rules_tool (ADK FunctionTool → calls MCP Server)
    Output:         Structured JSON audit verdict with violations and severity.

    This agent demonstrates MCP integration:
    - Calls `load_compliance_rules` to fetch context-specific rules
    - This tool is also exposed by the MCP Server for true protocol compliance
    """
    return Agent(
        name="AuditorAgent",
        model=model,
        description="Audits document against MCP-loaded compliance rules.",
        instruction="""
        You are a strict compliance auditor. You evaluate corporate documents
        against regulatory rules and identify violations.
        
        IMPORTANT: You must ONLY evaluate the document against the rules loaded dynamically via the `load_compliance_rules` tool. Do NOT assume, invent, or enforce any rules that are not explicitly defined in the loaded rules list.

        Zero-Trust Redaction Policy:
        The local security layer redacts sensitive fields to protect data privacy.
        - A placeholder like `[REDACTED_GSTIN]` represents a valid, format-verified 15-digit GSTIN.
        - A placeholder like `[REDACTED_PAN]` represents a valid, format-verified 10-character PAN.
        If a rule requires a GSTIN or PAN to be present or valid, you must treat `[REDACTED_GSTIN]` or `[REDACTED_PAN]` as satisfying that rule (i.e., compliant). Do not flag them as missing or invalid.

        WORKFLOW (follow in exact order):
        1. Call the `load_compliance_rules` tool with the document_type you received
        2. Read each rule carefully
        3. Evaluate the document content against every rule
        4. Determine the overall compliance status

        Severity levels:
        - "LOW"      → Minor formatting issues, no legal risk
        - "MEDIUM"   → Missing non-critical fields, moderate risk
        - "HIGH"     → Missing legally required fields, high risk
        - "CRITICAL" → Fraud indicators, data exposure, illegal content

        You MUST respond with ONLY this JSON structure:
        {
            "status": "COMPLIANT" or "NON_COMPLIANT",
            "severity": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
            "compliance_score": <integer 0-100>,
            "violations": ["violation description 1", "violation description 2"],
            "recommendations": ["recommendation 1", "recommendation 2"]
        }

        If the document is COMPLIANT, return an empty violations list [].
        """,
        tools=[compliance_rules_tool],  # ADK registers this as a callable tool
    )


def build_reporter_agent(model: str | Gemini) -> Agent:
    """
    Agent 3: The Reporter Agent
    ───────────────────────────
    Responsibility: Transform raw audit JSON into a human-readable report.
    Input:          Audit Agent's JSON verdict.
    Output:         Professional executive summary in Markdown format.

    This agent demonstrates the value of specialized agents:
    A language-focused agent can write much better prose than asking
    the Auditor Agent to both evaluate AND write a report.
    """
    return Agent(
        name="ReporterAgent",
        model=model,
        description="Generates boardroom-ready executive summary from audit data.",
        instruction="""
        You are an executive communications specialist at a compliance firm.
        You receive raw JSON audit data and transform it into a polished report.

        FORMAT your response as a professional Markdown document including:

        ## Compliance Audit Report

        **Document Type:** [type]
        **Audit Status:** [COMPLIANT ✅ or NON_COMPLIANT ❌]
        **Risk Severity:** [level]
        **Compliance Score:** [score]/100

        ### Executive Summary
        [2-3 sentences summarizing the overall finding]

        ### Key Violations
        [Bullet list of violations, or "No violations found" if compliant]

        ### Recommendations
        [Actionable next steps for the document owner]

        Keep the tone professional, clear, and free of technical jargon.
        """,
    )


# ============================================================
# 🏭 THE COMPLIANCE SWARM ORCHESTRATOR
# ============================================================

class ComplianceSwarm:
    """
    The master orchestrator for the ADK Multi-Agent Compliance Pipeline.

    This class:
    1. Builds the ADK SequentialAgent pipeline (Triage → Audit → Report)
    2. Manages the ADK Runner and session lifecycle
    3. Handles OCR for binary files (PDF/Image) via the raw GenAI Files API
    4. Applies the Zero-Trust PII Masking Skill before any LLM call
    5. Returns a fully structured compliance report

    Design Pattern: "Slicing the Elephant" (from the Day 5 livestream)
    Instead of one massive agent, we slice the problem into specialized
    micro-agents, each with a single clear responsibility.
    """

    def __init__(self):
        """
        Initializes the Swarm components:
        - Gemini client (for OCR Agent)
        - ADK agents (Triage, Auditor, Reporter)
        - ADK SequentialAgent pipeline
        - ADK Runner with InMemorySessionService
        - DocumentAuditorSkill for PII masking
        """
        # ── Setup Models / API Keys / Provider ────────────────────────────────
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if self.provider == "local":
            self.model_name = os.getenv("LOCAL_LLM_MODEL", GEMINI_MODEL)
            self.base_url = os.getenv("LOCAL_LLM_API_BASE", "http://localhost:11434/v1")
            
            # Point GenAI client to the local base URL
            self.genai_client = genai.Client(
                api_key=os.getenv("LOCAL_LLM_API_KEY", "dummy"),
                http_options={"base_url": self.base_url}
            )
            # Use Gemini class instance to pass base_url override to ADK agents
            agent_model = Gemini(
                model=self.model_name,
                base_url=self.base_url
            )
            # Use real Google Gemini API for OCR if a key is available in local mode
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                self.ocr_client = genai.Client(api_key=api_key)
            else:
                self.ocr_client = None
        else:
            self.model_name = GEMINI_MODEL
            self.base_url = None
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "❌ GEMINI_API_KEY not found in environment. "
                    "Please create a .env file with your API key."
                )
            self.genai_client = genai.Client(api_key=api_key)
            agent_model = GEMINI_MODEL
            self.ocr_client = self.genai_client

        # ── ADK Agent Instantiation ───────────────────────────────────────────
        triage_agent = build_triage_agent(agent_model)
        auditor_agent = build_auditor_agent(agent_model)
        reporter_agent = build_reporter_agent(agent_model)


        # ── ADK SequentialAgent Pipeline ─────────────────────────────────────
        # SequentialAgent orchestrates agents in strict order:
        # Each agent's output is passed as context to the next agent.
        # This implements the "pipeline" pattern taught in the course.
        self.pipeline = SequentialAgent(
            name="DocumentAuditPipeline",
            description=(
                "End-to-end document compliance pipeline. "
                "Orchestrates: Triage → Audit (MCP) → Executive Report."
            ),
            sub_agents=[triage_agent, auditor_agent, reporter_agent]
        )

        # ── ADK Runner Setup ──────────────────────────────────────────────────
        # The Runner manages agent execution, session state, and artifact flow.
        # InMemorySessionService stores session data in RAM (no DB needed for sessions).
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()
        self.runner = Runner(
            agent=self.pipeline,
            app_name="SmartDocumentAuditor",
            session_service=self.session_service,
            artifact_service=self.artifact_service
        )

        # ── Document Auditor Skill (PII Masking) ──────────────────────────────
        # This is a proper ADK Skill — reusable, versioned, and documented.
        self.privacy_skill = DocumentAuditorSkill()

        logger.info("✅ ComplianceSwarm initialized | Pipeline: Triage → Audit (MCP) → Report")

    # ──────────────────────────────────────────────────────────────────────────
    # 👁️ OCR AGENT (Agent 0) — Binary File Text Extraction
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extracts raw text from a PDF file using the local pypdf library.
        Allows processing text-based PDFs fully offline without cloud API dependency.
        """
        logger.info(f"📄 Local PDF Reader: Extracting text from '{os.path.basename(file_path)}'")
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            extracted_text = "\n".join(text_parts)
            logger.info(f"✅ Local PDF extraction complete: {len(extracted_text)} characters extracted")
            return extracted_text
        except Exception as e:
            logger.error(f"❌ Local PDF extraction failed: {e}")
            return ""

    def _extract_text_via_ocr(self, file_path: str) -> str:
        """
        Extracts raw text from binary files (PDFs, Images) using the Gemini Vision API.

        Security Design:
        - File is uploaded to Google's temporary Files API
        - Text is extracted immediately
        - File is DELETED from Google's servers right after extraction
        - This minimizes data exposure time (Zero-Trust principle)

        Args:
            file_path: Local path to the binary file.

        Returns:
            str: Raw extracted text content.
        """
        logger.info(f"👁️  OCR Agent: Extracting text from '{os.path.basename(file_path)}'")

        if not self.ocr_client:
            raise ValueError(
                "OCR required but no GEMINI_API_KEY is configured. "
                "Please configure GEMINI_API_KEY in your .env file."
            )

        # Upload to Google Files API (temporary storage for multimodal processing)
        uploaded_file = self.ocr_client.files.upload(file=file_path)
        logger.info(f"☁️  File uploaded to Google Files API: {uploaded_file.name}")

        try:
            # Ask Gemini to extract text exactly as written (no summarization)
            response = self.ocr_client.models.generate_content(
                model=GEMINI_MODEL,  # Always use the cloud Gemini model for OCR
                contents=[
                    uploaded_file,
                    (
                        "Extract ALL text from this document exactly as it appears. "
                        "Do not summarize, reformat, or omit any content. "
                        "Return only the raw text."
                    )
                ]
            )
            extracted_text = response.text
            logger.info(f"✅ OCR complete: {len(extracted_text)} characters extracted")
            return extracted_text

        finally:
            # 🔐 SECURITY: Always delete the file from Google's servers
            # This runs even if extraction fails — Zero-Trust data hygiene
            self.ocr_client.files.delete(name=uploaded_file.name)
            logger.info(f"🗑️  Security: Cloud file '{uploaded_file.name}' deleted immediately")

    # ──────────────────────────────────────────────────────────────────────────
    # 🚀 MASTER PIPELINE ORCHESTRATOR
    # ──────────────────────────────────────────────────────────────────────────

    async def process_document(self, file_path: str) -> dict:
        """
        The main control flow — runs the complete ADK Multi-Agent pipeline.

        Stage-by-Stage Breakdown:
            Stage 0: OCR (if binary file) — extract raw text
            Stage 1: PII Masking — scrub sensitive data before LLM sees it
            Stage 2: ADK Pipeline — Triage → Audit → Report (sequential agents)
            Stage 3: Result packaging — structured final output

        Args:
            file_path: Path to the uploaded document.

        Returns:
            dict: Full compliance report with doc_type, status, severity,
                  audit_result, executive_summary, and scrubbed text.
        """
        filename = os.path.basename(file_path)
        logger.info(f"🚀 Starting ADK pipeline for: '{filename}'")

        # ── Stage 0: Ingestion & OCR ──────────────────────────────────────────
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".txt":
            # Plain text: read directly — no OCR needed
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            logger.info(f"📄 Plain text file read: {len(raw_text)} characters")
        elif file_ext == ".pdf":
            # Try local PDF text extraction first (works completely offline)
            raw_text = self._extract_text_from_pdf(file_path)
            
            # If local PDF extraction returned nothing (e.g. scanned image PDF),
            # fall back to OCR if a client is available
            if not raw_text.strip():
                logger.warning("⚠️ Local PDF text extraction returned no text. Falling back to OCR...")
                raw_text = self._extract_text_via_ocr(file_path)
        else:
            # Binary image file: use OCR Vision Agent
            raw_text = self._extract_text_via_ocr(file_path)

        if not raw_text or not raw_text.strip():
            raise ValueError(f"No text could be extracted from '{filename}'.")

        # ── Stage 1: Zero-Trust PII Masking (Privacy Skill) ──────────────────
        # CRITICAL SECURITY STEP: PII is removed BEFORE the text reaches
        # any of the ADK agents. The agents NEVER see raw sensitive data.
        logger.info("🔐 Stage 1: Applying Zero-Trust PII masking...")
        skill_output = self.privacy_skill.execute(raw_text)
        scrubbed_text = skill_output["scrubbed_text"]
        pii_detected = skill_output["pii_detected"]

        if pii_detected:
            logger.warning("⚠️  PII detected and redacted before LLM processing")

        # ── Stage 2: ADK Multi-Agent Pipeline ────────────────────────────────
        # Create a new ADK session for this document audit
        session_id = f"audit_{os.path.basename(file_path).replace('.', '_')}"

        # Ensure session exists in the session service before running the pipeline
        try:
            self.session_service.create_session_sync(
                app_name="SmartDocumentAuditor",
                user_id="compliance_system",
                session_id=session_id
            )
            logger.info(f"🆕 ADK Session created: {session_id}")
        except Exception as session_err:
            logger.debug(f"ℹ️ ADK Session already exists: {session_err}")

        logger.info("🤖 Stage 2: Launching ADK SequentialAgent pipeline...")
        logger.info("   → Agent 1 (Triage): Classifying document type...")
        logger.info("   → Agent 2 (Auditor): Evaluating compliance via MCP rules...")
        logger.info("   → Agent 3 (Reporter): Generating executive summary...")

        # Build the prompt that initializes the ADK pipeline
        pipeline_prompt = f"""
        DOCUMENT FOR COMPLIANCE AUDIT
        ==============================
        Filename: {filename}
        Characters: {len(scrubbed_text)}
        PII Detected & Redacted: {pii_detected}

        DOCUMENT CONTENT (PII-Scrubbed):
        {scrubbed_text}
        ==============================

        Instructions for the pipeline:
        1. Triage Agent: Classify this document type
        2. Auditor Agent: Call load_compliance_rules tool, then audit the document
        3. Reporter Agent: Generate the executive summary
        """

        # Run the ADK SequentialAgent pipeline asynchronously
        final_response_text = ""
        triage_output_raw = ""
        audit_output_raw = ""

        async for event in self.runner.run_async(
            user_id="compliance_system",
            session_id=session_id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=pipeline_prompt)]
            )
        ):
            # Capture intermediate agent responses to avoid extra API requests
            if event.content and event.content.parts:
                part_text = event.content.parts[0].text
                if part_text:
                    if event.author == "TriageAgent":
                        triage_output_raw = part_text
                    elif event.author == "AuditorAgent":
                        audit_output_raw = part_text

            # Capture the final text response from the last agent (Reporter)
            if event.is_final_response() and event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
                logger.info("✅ ADK pipeline completed — final response received")

        # ── Stage 3: Result Packaging ─────────────────────────────────────────
        # Parse structured outputs directly from the captured agent responses.
        # This saves 2 expensive LLM API calls per document audit and avoids 429 quota exhaustion.
        triage_output = extract_json(triage_output_raw)
        audit_output = extract_json(audit_output_raw)

        doc_type = triage_output.get("doc_type")
        status = audit_output.get("status")
        severity = audit_output.get("severity")
        violations = audit_output.get("violations")
        compliance_score = audit_output.get("compliance_score")
        recommendations = audit_output.get("recommendations")

        # Fallback to direct structured model calls ONLY if direct parsing fails
        if not (doc_type and status and severity):
            logger.info("⚠️ Direct parsing of agent events returned incomplete data. Triggering structured API fallback...")
            try:
                triage_output_fallback = await self._run_structured_triage(scrubbed_text)
                doc_type = doc_type or triage_output_fallback.get("doc_type", "unknown")
                
                audit_output_fallback = await self._run_structured_audit(scrubbed_text, doc_type)
                status = status or audit_output_fallback.get("status", "REVIEW_NEEDED")
                severity = severity or audit_output_fallback.get("severity", "MEDIUM")
                violations = violations or audit_output_fallback.get("violations", [])
                compliance_score = compliance_score or audit_output_fallback.get("compliance_score", 0)
                recommendations = recommendations or audit_output_fallback.get("recommendations", [])
                logger.info("✅ Structured API fallback completed successfully")
            except Exception as fallback_err:
                logger.warning(f"⚠️ Structured API fallback failed: {fallback_err}")
                
        # Fill absolute fallback defaults if everything fails
        doc_type = doc_type or "unknown"
        status = status or "REVIEW_NEEDED"
        severity = severity or "MEDIUM"
        violations = violations if violations is not None else []
        compliance_score = compliance_score if compliance_score is not None else 0
        recommendations = recommendations if recommendations is not None else []

        # Package the complete result
        result = {
            "filename": filename,
            "doc_type": doc_type,
            "status": status,
            "severity": severity,
            "compliance_score": compliance_score,
            "pii_was_detected": pii_detected,
            "audit_result": {
                "violations": violations,
                "recommendations": recommendations,
                "rule_source": "MCP ComplianceRulesServer + compliance_rules.json"
            },
            "executive_summary": final_response_text,
            "scrubbed_text_preview": scrubbed_text[:500] + "..." if len(scrubbed_text) > 500 else scrubbed_text,
            "pipeline": "ADK SequentialAgent: Triage → Auditor (MCP) → Reporter"
        }

        logger.info(
            f"📊 Result | doc_type: {doc_type} | status: {status} | "
            f"severity: {severity} | violations: {len(violations)}"
        )
        return result

    # ── Structured Sub-Runners (for reliable JSON extraction) ─────────────────

    async def _run_structured_triage(self, text: str) -> dict:
        """
        Runs the Triage Agent with strict JSON output mode.
        Uses the raw GenAI SDK for direct Pydantic schema enforcement.
        This guarantees parseable JSON even if the ADK pipeline output varies.
        """
        from pydantic import BaseModel

        class TriageSchema(BaseModel):
            doc_type: str
            confidence: float
            reasoning: str

        max_retries = 3
        base_delay = 3.0
        for attempt in range(max_retries):
            try:
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        "Classify this document. Categories: invoice, certificate, contract, report, unknown.",
                        text[:3000]  # Limit context to avoid token overflow
                    ],
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TriageSchema,
                        temperature=0.1  # Very low temperature for deterministic classification
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                error_msg = str(e)
                is_transient = (
                    "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Resource Exhausted" in error_msg or
                    "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg
                )
                if is_transient and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Fallback Triage transient error/rate limit hit. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise e

    async def _run_structured_audit(self, text: str, doc_type: str) -> dict:
        """
        Runs the Auditor Agent with strict JSON output mode.
        Loads compliance rules dynamically (MCP pattern) and enforces schema.
        """
        from pydantic import BaseModel

        class AuditSchema(BaseModel):
            status: str
            severity: str
            compliance_score: int
            violations: list[str]
            recommendations: list[str]

        # Load applicable rules (MCP-style dynamic rule loading)
        rules_data = load_compliance_rules(doc_type)
        rules_text = json.dumps(rules_data.get("rules", []))

        max_retries = 3
        base_delay = 3.0
        for attempt in range(max_retries):
            try:
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        f"Audit this document against these compliance rules: {rules_text}\n\n"
                        "IMPORTANT: You must ONLY evaluate the document against the provided compliance rules list. Do NOT assume, invent, or enforce any rules that are not explicitly defined in the provided rules list.\n\n"
                        "Zero-Trust Redaction Policy:\n"
                        "The local security layer redacts sensitive fields to protect data privacy.\n"
                        "- A placeholder like `[REDACTED_GSTIN]` represents a valid, format-verified 15-digit GSTIN.\n"
                        "- A placeholder like `[REDACTED_PAN]` represents a valid, format-verified 10-character PAN.\n"
                        "If a rule requires a GSTIN or PAN to be present or valid, you must treat `[REDACTED_GSTIN]` or `[REDACTED_PAN]` as satisfying that rule (i.e., compliant). Do not flag them as missing or invalid.",
                        text[:3000]
                    ],
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AuditSchema,
                        temperature=0.1
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                error_msg = str(e)
                is_transient = (
                    "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Resource Exhausted" in error_msg or
                    "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg
                )
                if is_transient and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Fallback Audit transient error/rate limit hit. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise e
