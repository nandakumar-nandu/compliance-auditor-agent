# ============================================================
# 🔌 MCP SERVER — COMPLIANCE RULES SERVER
# ============================================================
#
# 🏗️  Architecture Role: Real Model Context Protocol Server
# 📚 Course Concepts Demonstrated:
#      ✅ Real MCP Server (NOT just a pattern or JSON loader)
#      ✅ FastMCP framework for tool + resource exposure
#      ✅ Agent interoperability (any MCP client can connect)
#      ✅ Dynamic rule serving based on document context
#
# What is MCP?
# The Model Context Protocol (MCP) is an open standard that lets AI agents
# securely call external tools and resources over a defined protocol.
# Instead of hardcoding tool logic inside the agent, MCP externalizes it —
# so ANY agent (ADK, LangChain, Claude, etc.) can call the same server.
#
# How to run this server:
#   python mcp_server/compliance_server.py
#
# How the ADK agent connects to it (see swarm.py):
#   MCPToolset(connection_params=StdioServerParameters(...))
# ============================================================

import json
import logging
from pathlib import Path

# FastMCP: Google's recommended framework for building MCP servers quickly.
# Install: pip install mcp fastmcp
from mcp.server.fastmcp import FastMCP

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComplianceMCPServer")

# ── Policy File Location ──────────────────────────────────────────────────────
# Navigate from mcp_server/ up to the project root, then to policies/
RULES_PATH = Path(__file__).parent.parent / "policies" / "compliance_rules.json"

# ── Initialize FastMCP Server ─────────────────────────────────────────────────
# This creates an MCP-compliant server that exposes tools and resources.
# ADK agents connect via StdioServerParameters or SSE transport.
mcp = FastMCP(
    name="ComplianceRulesServer",
    instructions=(
        "An MCP server that serves dynamic compliance rules for document auditing. "
        "Supports invoice, certificate, contract, report, and general rules."
    )
)


# ============================================================
# 🔧 MCP TOOLS
# ============================================================
# Tools are functions that MCP client agents can CALL to get data or perform actions.
# The @mcp.tool() decorator registers them in the MCP tool registry.

@mcp.tool()
def get_compliance_rules(document_type: str) -> dict:
    """
    Retrieves the compliance ruleset for a specific document type.

    This is the primary tool called by the ADK Auditor Agent.
    It merges general rules (apply to ALL documents) with
    document-specific rules (apply only to this type).

    Args:
        document_type: Type of document to retrieve rules for.
                       Supported: 'invoice', 'certificate', 'contract', 'report', 'unknown'

    Returns:
        dict: Contains document_type, merged rules list, rule count, and jurisdiction.
    """
    logger.info(f"📖 MCP Tool called: get_compliance_rules('{document_type}')")

    with open(RULES_PATH, "r") as f:
        all_rules = json.load(f)

    # Always apply general rules + document-specific rules
    general_rules = all_rules.get("general", [])
    specific_rules = all_rules.get(document_type.lower(), [])
    merged_rules = general_rules + specific_rules

    result = {
        "document_type": document_type,
        "rules": merged_rules,
        "rule_count": len(merged_rules),
        "jurisdiction": all_rules.get("_metadata", {}).get("jurisdiction", "India / General"),
        "version": all_rules.get("_metadata", {}).get("version", "1.0.0")
    }
    logger.info(f"✅ Returned {len(merged_rules)} rule(s) for '{document_type}'")
    return result


@mcp.tool()
def list_supported_document_types() -> dict:
    """
    Lists all document types that have dedicated compliance rules.

    Useful for agents to discover what categories they can audit
    before classifying a document.

    Returns:
        dict: List of supported document types and total count.
    """
    logger.info("📋 MCP Tool called: list_supported_document_types()")

    with open(RULES_PATH, "r") as f:
        all_rules = json.load(f)

    # Exclude metadata key, include only document type keys
    supported_types = [k for k in all_rules.keys() if not k.startswith("_")]
    return {
        "supported_types": supported_types,
        "count": len(supported_types)
    }


@mcp.tool()
def get_rule_by_id(rule_id: str) -> dict:
    """
    Retrieves a single compliance rule by its unique ID.

    Useful when an agent needs to explain or reference a specific rule
    in its audit report.

    Args:
        rule_id: The rule identifier (e.g., 'INV-01', 'GEN-01', 'CERT-01').

    Returns:
        dict: The matching rule, or an error if not found.
    """
    logger.info(f"🔍 MCP Tool called: get_rule_by_id('{rule_id}')")

    with open(RULES_PATH, "r") as f:
        all_rules = json.load(f)

    # Search across all document type categories
    for category, rules in all_rules.items():
        if category.startswith("_"):
            continue
        if isinstance(rules, list):
            for rule in rules:
                if rule.get("id") == rule_id:
                    logger.info(f"✅ Found rule '{rule_id}' in category '{category}'")
                    return {"found": True, "category": category, "rule": rule}

    logger.warning(f"⚠️  Rule '{rule_id}' not found")
    return {"found": False, "rule_id": rule_id, "error": "Rule not found"}


# ============================================================
# 📦 MCP RESOURCES
# ============================================================
# Resources are static or dynamic data that MCP clients can READ.
# Unlike tools (which perform actions), resources provide context.

@mcp.resource("rules://all")
def get_all_rules_resource() -> str:
    """
    Exposes the entire compliance_rules.json as an MCP readable resource.

    An ADK agent can include this resource in its context window
    to have full knowledge of all rules before starting an audit.

    Returns:
        str: Pretty-printed JSON of all compliance rules.
    """
    with open(RULES_PATH, "r") as f:
        content = f.read()
    logger.info("📦 MCP Resource accessed: rules://all")
    return content


@mcp.resource("rules://summary")
def get_rules_summary() -> str:
    """
    Returns a human-readable summary of all available rule categories.

    Returns:
        str: Formatted text summary of rule categories and counts.
    """
    with open(RULES_PATH, "r") as f:
        all_rules = json.load(f)

    lines = ["=== Compliance Rules Summary ===\n"]
    for category, rules in all_rules.items():
        if category.startswith("_"):
            continue
        if isinstance(rules, list):
            lines.append(f"📁 {category.upper()}: {len(rules)} rule(s)")
            for rule in rules:
                lines.append(f"   • [{rule['id']}] {rule['description']}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# 🚀 SERVER ENTRY POINT
# ============================================================

if __name__ == "__main__":
    logger.info("🔌 Starting ComplianceRulesServer (FastMCP)...")
    logger.info(f"📂 Rules file: {RULES_PATH}")
    logger.info("🛠️  Registered Tools: get_compliance_rules, list_supported_document_types, get_rule_by_id")
    logger.info("📦 Registered Resources: rules://all, rules://summary")
    logger.info("✅ MCP Server ready — waiting for ADK agent connections...\n")

    # Run via stdio transport (standard for ADK MCPToolset integration)
    mcp.run(transport="stdio")
