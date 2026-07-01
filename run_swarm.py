from audit_engine.swarm import ComplianceSwarm
import json

def main():
    swarm = ComplianceSwarm()
    
    # You can pass a .txt file OR an actual .jpg/.png image here!
    result = swarm.process_document("test_invoice.txt")
    
    print("\n=== FINAL SWARM OUTPUT ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()