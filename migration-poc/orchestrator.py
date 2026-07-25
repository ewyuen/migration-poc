"""Orchestrator Agent: Coordinate multi-agent extraction pipeline"""
import os
import json
from datetime import datetime
from pathlib import Path

from agents.explorer import explore_code
from agents.extractor import extract_domain_logic
from agents.modernizer import modernize_code
from agents.bdd_test_agent import generate_bdd_tests
from agents.verifier import verify_modernization
from config import OUTPUT_DIR, TARGET_FRAMEWORK, COMPLIANCE_CONTEXT, DOMAIN


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)


def save_output(filename: str, content: str):
    """Save agent output to file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📁 Saved: {filepath}")


def orchestrate_extraction(legacy_code_path: str, component_name: str = "Observation"):
    """
    Main orchestration: coordinate all agents sequentially

    Args:
        legacy_code_path: Path to legacy C# file
        component_name: Name of component being extracted

    Returns:
        Dictionary with all results
    """
    ensure_output_dir()

    print("\n" + "="*70)
    print(f"🎭 ORCHESTRATOR: Starting extraction pipeline for {component_name}")
    print("="*70)
    print(f"Target Framework: {TARGET_FRAMEWORK}")
    print(f"Compliance Context: {COMPLIANCE_CONTEXT}")
    print(f"Domain: {DOMAIN}")
    print("="*70 + "\n")

    # Load legacy code
    with open(legacy_code_path, "r", encoding="utf-8") as f:
        legacy_code = f.read()

    results = {
        "timestamp": datetime.now().isoformat(),
        "component_name": component_name,
        "legacy_code_path": legacy_code_path,
        "target_framework": TARGET_FRAMEWORK,
        "compliance_context": COMPLIANCE_CONTEXT,
        "domain": DOMAIN,
    }

    # STEP 1: EXPLORER AGENT
    print("\n[STEP 1/6] EXPLORER AGENT")
    print("-" * 70)
    exploration = explore_code(legacy_code, component_name)
    results["exploration"] = exploration
    save_output("1_exploration_report.json", json.dumps(exploration, indent=2))
    print()

    # STEP 2: EXTRACTOR AGENT
    print("[STEP 2/6] EXTRACTOR AGENT")
    print("-" * 70)
    domain_logic = extract_domain_logic(legacy_code, exploration)
    results["domain_logic"] = domain_logic
    save_output("2_extracted_domain_logic.cs", domain_logic)
    print()

    # STEP 3: MODERNIZER AGENT
    print("[STEP 3/6] MODERNIZER AGENT")
    print("-" * 70)
    modernized_code = modernize_code(legacy_code, domain_logic, exploration)
    results["modernized_code"] = modernized_code
    save_output("3_modernized_code.cs", modernized_code)
    print()

    # STEP 4: BDD TEST AGENT
    print("[STEP 4/6] BDD TEST AGENT")
    print("-" * 70)
    bdd_tests = generate_bdd_tests(domain_logic, modernized_code, exploration)
    results["bdd_tests"] = bdd_tests
    save_output("4_bdd_test_scenarios.feature", bdd_tests)
    print()

    # STEP 5: VERIFIER AGENT
    print("[STEP 5/6] VERIFIER AGENT")
    print("-" * 70)
    verification = verify_modernization(legacy_code, modernized_code, domain_logic, bdd_tests)
    results["verification"] = verification
    save_output("5_verification_report.json", json.dumps(verification, indent=2))
    print()

    # STEP 6: COMPILE RESULTS
    print("[STEP 6/6] COMPILE RESULTS")
    print("-" * 70)
    save_output("0_complete_results.json", json.dumps(results, indent=2, default=str))
    print("✅ All results saved\n")

    print("="*70)
    print(f"✨ ORCHESTRATION COMPLETE")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"  Component: {component_name}")
    print(f"  Status: {verification.get('overall_status', 'N/A')}")
    print(f"  Verification Risks: {verification.get('risks', [])}")
    print(f"\n📁 All outputs saved to: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("  1. Review exploration report: 1_exploration_report.json")
    print("  2. Review extracted logic: 2_extracted_domain_logic.cs")
    print("  3. Review modernized code: 3_modernized_code.cs")
    print("  4. Review BDD tests: 4_bdd_test_scenarios.feature")
    print("  5. Review verification: 5_verification_report.json")
    print("="*70 + "\n")

    return results


if __name__ == "__main__":
    # Example: Run on the Observation component
    legacy_code_path = "legacy-code/Observation.cs"

    if os.path.exists(legacy_code_path):
        results = orchestrate_extraction(legacy_code_path, "Observation")
    else:
        print(f"Error: Legacy code file not found at {legacy_code_path}")
        print("Please ensure the legacy code file exists before running.")
