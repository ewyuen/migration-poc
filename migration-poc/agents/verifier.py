"""Verifier Agent: Validate modernization quality and compliance"""
import os
import subprocess
import glob
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import logging
from llm_client import call_llm_json
from .reqnroll_test_runner import ReqnrollTestRunner

logger = logging.getLogger(__name__)

# Retain existing LLM-based verification for backward compatibility
def verify_modernization(
    legacy_code: str,
    modernized_code: str,
    domain_logic: str,
    bdd_tests: str
) -> dict:
    """
    Verify that modernized code is correct and compliant.

    Returns:
        Verification report as dictionary
    """
    prompt = f"""
Verify this code modernization for correctness and compliance.

ORIGINAL LEGACY CODE:
```csharp
{legacy_code}
```

EXTRACTED DOMAIN LOGIC:
```csharp
{domain_logic}
```

MODERNIZED CODE:
```csharp
{modernized_code}
```

BDD TEST SCENARIOS:
```gherkin
{bdd_tests}
```

Provide a verification report in JSON with:
1. **behavioral_equivalence**: Does modern code do what legacy code did?
2. **test_coverage**: Are all scenarios covered?
3. **compliance_check**: Is CFR Part 11 preserved?
4. **security_check**: No credentials/PII hardcoded?
5. **performance_analysis**: Any major regressions?
6. **net10_alignment**: Uses .NET 10 features properly?
7. **risks**: Any concerns?
8. **recommendations**: Improvements?
9. **overall_status**: PASS/FAIL/CAUTION

Return only valid JSON.
"""

    system = """You are a code verification expert for medical software.
Carefully check behavioral equivalence, compliance, and security.
Be thorough but fair in assessment."""

    print(f"✔️ Verifier: Validating modernization...")
    result = call_llm_json(prompt, system, max_tokens=2500)
    print(f"✅ Verifier: Verification complete")
    return result


def _parse_trx_results(trx_path: str) -> tuple:
    """Parse test results from .trx file. Returns (total, passed, failed, skipped, failures_list)"""
    failures = []
    total, passed, failed, skipped = 0, 0, 0, 0
    try:
        tree = ET.parse(trx_path)
        root = tree.getroot()
        
        # Handle XML Namespaces
        ns = {}
        if root.tag.startswith('{'):
            ns_url = root.tag.split('}')[0].strip('{')
            ns = {'ns': ns_url}
            
        counters = root.find('.//ns:Counters', ns)
        if counters is not None:
            total = int(counters.attrib.get('total', 0))
            passed = int(counters.attrib.get('passed', 0))
            failed = int(counters.attrib.get('failed', 0))
            skipped = int(counters.attrib.get('skipped', 0))
            
        for result in root.findall('.//ns:UnitTestResult', ns):
            outcome = result.attrib.get('outcome')
            if outcome == 'Failed':
                test_name = result.attrib.get('testName', 'UnknownTest')
                message_el = result.find('.//ns:Message', ns)
                stack_el = result.find('.//ns:StackTrace', ns)
                message = message_el.text.strip() if message_el is not None and message_el.text else "No error message"
                stack = stack_el.text.strip() if stack_el is not None and stack_el.text else "No stack trace"
                failures.append({
                    "test_name": test_name,
                    "message": message,
                    "stack_trace": stack
                })
    except Exception as e:
        print(f"⚠️ Error parsing TRX file: {e}")
    return total, passed, failed, skipped, failures


def _parse_coverage_results(tests_dir: str) -> tuple:
    """Find and parse Cobertura coverage report. Returns (line_coverage, branch_coverage)"""
    search_path = os.path.join(tests_dir, "TestResults", "**", "coverage.cobertura.xml")
    coverage_files = glob.glob(search_path, recursive=True)
    if not coverage_files:
        return 0.0, 0.0
        
    try:
        tree = ET.parse(coverage_files[0])
        root = tree.getroot()
        line_rate = float(root.attrib.get('line-rate', 0.0)) * 100
        branch_rate = float(root.attrib.get('branch-rate', 0.0)) * 100
        return line_rate, branch_rate
    except Exception as e:
        print(f"⚠️ Error parsing Cobertura XML: {e}")
        return 0.0, 0.0


def run_tests_and_collect_coverage(
    component_name: str,
    run_id: str,
    base_output_dir: str = "migrated-output",
    commented_tests: list = None,
    commented_classes: list = None,
    step_definitions_enhanced: str = None,
) -> dict:
    """
    Compile, execute unit tests (traditional + Reqnroll BDD), and collect code coverage.

    Args:
        component_name: Name of the migrated service
        run_id: Per-run identifier used to locate this run's output directory
        base_output_dir: Base output directory
        commented_tests: Test methods Stage 5 commented out after exhausting its self-healing
            retries (surfaced here so the final report shows what couldn't be made to compile)
        commented_classes: Helper classes (fixtures/fakes) Stage 5 commented out for the same reason
        step_definitions_enhanced: Optional StepDefinitions.cs content (Reqnroll BDD tests)

    Returns:
        Dictionary verification report
    """
    print(f"🧪 Starting test runner agent for component: {component_name}...")
    component_dir = os.path.join(base_output_dir, run_id)
    tests_dir = os.path.join(component_dir, "tests")

    report = {
        "status": "FAIL",
        "compiled": False,
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "skipped_tests": 0,
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "failures": [],
        "errors": [],
        "commented_tests": commented_tests or [],
        "commented_classes": commented_classes or [],
        "step_definitions_available": step_definitions_enhanced is not None,
        "reqnroll_scenarios": 0,
        "reqnroll_scenarios_passed": 0,
        "reqnroll_scenarios_failed": 0,
        "step_failures": [],
    }
    
    if not os.path.exists(tests_dir):
        msg = f"Tests directory not found: {tests_dir}"
        report["errors"].append(msg)
        print(f"❌ {msg}")
        return report

    # Note: tests.csproj was already created in Stage 5 by test_compiler.
    # Stage 6 only runs tests, does not regenerate project file.

    # Run dotnet test
    print(f"🏃 Running dotnet test with coverage collection...")
    cmd = ["dotnet", "test", "--collect:XPlat Code Coverage", "--logger:trx;LogFileName=results.trx"]
    try:
        # Run with UTF-8 environment variable
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            cmd,
            cwd=tests_dir,
            capture_output=True,
            text=True,
            env=env,
            timeout=180 # 3 minute timeout
        )
        
        trx_search = os.path.join(tests_dir, "TestResults", "results.trx")
        
        if os.path.exists(trx_search):
            report["compiled"] = True
            total, passed, failed, skipped, failures = _parse_trx_results(trx_search)
            report["total_tests"] = total
            report["passed_tests"] = passed
            report["failed_tests"] = failed
            report["skipped_tests"] = skipped
            report["failures"] = failures
            
            if failed == 0 and total > 0:
                report["status"] = "PASS"
            else:
                report["status"] = "FAIL"
                
            # Parse coverage
            line_cov, branch_cov = _parse_coverage_results(tests_dir)
            report["line_coverage"] = line_cov
            report["branch_coverage"] = branch_cov
        else:
            # Did not compile or no test results produced
            report["compiled"] = False
            report["status"] = "FAIL"
            # Extract compilation errors from output
            build_errors = []
            for line in (result.stdout + "\n" + result.stderr).split('\n'):
                if "error CS" in line or "Build FAILED" in line or "error NETSDK" in line:
                    build_errors.append(line.strip())
            report["errors"] = build_errors or [result.stdout[:2000]]
            print("❌ Compilation or project build failed.")

    except subprocess.TimeoutExpired:
        report["errors"].append("dotnet test execution timed out after 180 seconds.")
        print("❌ dotnet test execution timed out.")
    except Exception as e:
        report["errors"].append(f"Unexpected error running tests: {str(e)}")
        print(f"❌ Unexpected error: {e}")

    # Run Reqnroll BDD tests if step definitions are available
    if step_definitions_enhanced:
        print(f"\n🎭 Running Reqnroll BDD tests...")
        try:
            reqnroll_runner = ReqnrollTestRunner(base_output_dir)
            reqnroll_results = reqnroll_runner.run_tests(component_name, run_id)

            report["reqnroll_scenarios"] = reqnroll_results["scenarios_run"]
            report["reqnroll_scenarios_passed"] = reqnroll_results["scenarios_passed"]
            report["reqnroll_scenarios_failed"] = reqnroll_results["scenarios_failed"]
            report["step_failures"] = reqnroll_results["step_failures"]

            # Update overall status if BDD tests failed
            if not reqnroll_results["success"]:
                report["status"] = "FAIL"
                print(f"⚠️  Some BDD scenarios failed")
            else:
                print(f"✅ All {reqnroll_results['scenarios_run']} BDD scenarios passed")
        except Exception as e:
            report["step_failures"].append(f"Reqnroll test execution error: {str(e)}")
            print(f"⚠️  Reqnroll execution error: {e}")

    # 3. Generate Reports
    _write_reports(component_name, run_id, report)

    return report


def _write_reports(component_name: str, run_id: str, report: dict) -> None:
    """Save markdown and JSON reports under result-log and tests directories"""
    # Create output folders
    log_dir = os.path.join("migrated-output", "result-log")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create Markdown report
    status_emoji = "✅" if report["status"] == "PASS" else "❌"
    compile_emoji = "✅" if report["compiled"] else "❌"
    
    md_content = f"""# Verification & Coverage Report: {component_name}

## Summary
- **Overall Status**: {status_emoji} **{report["status"]}**
- **Compilation Success**: {compile_emoji} {report["compiled"]}
- **Total Tests**: {report["total_tests"]}
- **Passed**: {report["passed_tests"]}
- **Failed**: {report["failed_tests"]}
- **Skipped**: {report["skipped_tests"]}
- **Line Coverage**: {report["line_coverage"]:.2f}%
- **Branch Coverage**: {report["branch_coverage"]:.2f}%

"""

    commented_tests = report.get("commented_tests") or []
    commented_classes = report.get("commented_classes") or []
    if commented_tests or commented_classes:
        md_content += "## Commented-Out Tests (Stage 5 self-healing exhausted)\n"
        md_content += "The following could not be made to compile after Stage 5's self-healing attempts and were commented out:\n\n"
        if commented_tests:
            md_content += "### Test Methods\n"
            for name in commented_tests:
                md_content += f"- {name}\n"
        if commented_classes:
            md_content += "### Related Classes (fixtures/fakes)\n"
            for name in commented_classes:
                md_content += f"- {name}\n"
        md_content += "\n"

    if not report["compiled"]:
        md_content += "## Build/Compilation Errors\n```\n"
        md_content += "\n".join(report["errors"])
        md_content += "\n```\n"
    elif report["failed_tests"] > 0:
        md_content += "## Failed Tests Details\n"
        for fail in report["failures"]:
            md_content += f"### ❌ {fail['test_name']}\n"
            md_content += f"**Error Message**:\n```\n{fail['message']}\n```\n"
            md_content += f"**Stack Trace**:\n```\n{fail['stack_trace']}\n```\n"
            md_content += "---\n"
    else:
        md_content += "🎉 All tests passed successfully with zero failures!\n"

    # Write Markdown to tests folder
    tests_md_path = os.path.join("migrated-output", run_id, "tests", "verification_report.md")
    try:
        with open(tests_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"💾 Saved: {tests_md_path}")
    except Exception as e:
        print(f"⚠️ Failed to save {tests_md_path}: {e}")

    # Write Markdown to result-log folder
    log_md_path = os.path.join(log_dir, f"{component_name}_verification_report.md")
    try:
        with open(log_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"💾 Saved: {log_md_path}")
    except Exception as e:
        print(f"⚠️ Failed to save {log_md_path}: {e}")

    # Write JSON to result-log folder
    log_json_path = os.path.join(log_dir, f"{component_name}_verification_report.json")
    try:
        with open(log_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report, indent=2))
        print(f"💾 Saved: {log_json_path}")
    except Exception as e:
        print(f"⚠️ Failed to save {log_json_path}: {e}")
