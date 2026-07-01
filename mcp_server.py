# mcp_server.py - Demonstrates the Model Context Protocol concept
def get_compliance_policy(policy_name):
    """MCP Tool to fetch policies dynamically."""
    try:
        with open(f"policies/{policy_name}.json", 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Policy not found."

if __name__ == "__main__":
    # Simulate an MCP call
    print(get_compliance_policy("compliance_rules"))