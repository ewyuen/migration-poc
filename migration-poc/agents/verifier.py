"""Verifier Agent: Validate modernization quality and compliance"""
import os
import subprocess
import glob
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from llm_client import call_llm_json

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


def _generate_test_csproj(tests_dir: str) -> None:
    """Generate a tests.csproj file dynamically under the tests subdirectory"""
    csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
    <IsTestProject>true</IsTestProject>
  </PropertyGroup>

  <ItemGroup>
    <Compile Include="..\\*.cs" Exclude="..\\obj\\**;..\\bin\\**" />
  </ItemGroup>

  <ItemGroup>
    <Using Include="FluentValidation" />
    <Using Include="Microsoft.Extensions.Options" />
    <Using Include="System.Text" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.1" />
    <PackageReference Include="xunit" Version="2.9.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.8.2">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="coverlet.collector" Version="6.0.2">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
    <PackageReference Include="FluentValidation" Version="11.9.0" />
    <PackageReference Include="Microsoft.Extensions.Options" Version="8.0.2" />
  </ItemGroup>
</Project>
"""
    csproj_path = os.path.join(tests_dir, "tests.csproj")
    with open(csproj_path, "w", encoding="utf-8") as f:
        f.write(csproj_content)
    print(f"🛠️ Generated test project file: {csproj_path}")


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


def run_tests_and_collect_coverage(component_name: str, base_output_dir: str = "migrated-output") -> dict:
    """
    Compile, execute unit tests, and collect code coverage.
    
    Returns:
        Dictionary verification report
    """
    print(f"🧪 Starting test runner agent for component: {component_name}...")
    component_dir = os.path.join(base_output_dir, component_name)
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
        "errors": []
    }
    
    if not os.path.exists(tests_dir):
        msg = f"Tests directory not found: {tests_dir}"
        report["errors"].append(msg)
        print(f"❌ {msg}")
        return report

    # 1. Generate tests.csproj
    _generate_test_csproj(tests_dir)
    
    # 2. Run dotnet test
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

    # 3. Generate Reports
    _write_reports(component_name, report)

    return report


def verify_test_results(component_name: str, runner_report: dict, base_output_dir: str = "migrated-output") -> dict:
    """
    Parses test execution results and generates reports.
    Handles both test execution reports and modernization failure reports.
    """
    # Check if this is a modernization failure report
    if runner_report.get("modernization_failed"):
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
            "errors": runner_report.get("errors", []),
            "commented_tests": [],
            "attempts": 0,
            "modernization_failed": True,
            "modernization_errors": runner_report.get("modernization_errors", [])
        }
        _write_reports(component_name, report)
        return report

    # Otherwise, parse test results
    tests_dir = runner_report.get("tests_dir", os.path.join(base_output_dir, component_name, "tests"))
    report = {
        "status": "FAIL",
        "compiled": runner_report.get("compiled", False),
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "skipped_tests": 0,
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "failures": [],
        "errors": runner_report.get("errors", []),
        "commented_tests": runner_report.get("commented_tests", []),
        "attempts": runner_report.get("attempts", 0),
        "modernization_failed": False,
        "modernization_errors": []
    }

    if runner_report.get("compiled"):
        trx_search = os.path.join(tests_dir, "TestResults", "results.trx")
        if os.path.exists(trx_search):
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
            report["status"] = "FAIL"
            report["errors"].append("TRX test result file not found.")
    else:
        report["status"] = "FAIL"

    # Save reports
    _write_reports(component_name, report)
    return report


def _write_reports(component_name: str, report: dict) -> None:
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
- **Commented Out Tests**: {len(report.get("commented_tests", []))}
- **Line Coverage**: {report["line_coverage"]:.2f}%
- **Branch Coverage**: {report["branch_coverage"]:.2f}%

"""

    # Handle modernization failures
    if report.get("modernization_failed"):
        md_content += "## ❌ Modernization Failed\n\n"
        md_content += "The modernized code failed to compile after maximum attempts.\n\n"
        md_content += "### Compilation Errors\n"
        for error in report.get("modernization_errors", []):
            md_content += f"- **Line {error.get('line', '?')}**: [{error.get('error_code', 'ERROR')}] {error.get('message', 'Unknown error')}\n"
        md_content += "\n"

    if report.get("commented_tests"):
        md_content += "## Commented Out Tests (After Max Attempts)\n"
        md_content += "The following tests could not be fixed after max attempts and were commented out:\n"
        for test_name in report["commented_tests"]:
            md_content += f"- `{test_name}` - **TODO: Fix compilation error - test needs dependencies to be defined**\n"
        md_content += "\n"

    if not report["compiled"] and not report.get("modernization_failed"):
        md_content += "## Build/Compilation Errors\n```\n"
        md_content += "\n".join(report.get("errors", [])[:20])
        md_content += "\n```\n"
    elif report["failed_tests"] > 0:
        md_content += "## Failed Tests Details\n"
        for fail in report.get("failures", []):
            md_content += f"### ❌ {fail['test_name']}\n"
            md_content += f"**Error Message**:\n```\n{fail['message']}\n```\n"
            md_content += f"**Stack Trace**:\n```\n{fail['stack_trace']}\n```\n"
            md_content += "---\n"
    elif not report.get("modernization_failed"):
        md_content += "🎉 All tests passed successfully with zero failures!\n"

    # Write Markdown to tests folder
    tests_md_path = os.path.join("migrated-output", component_name, "tests", "verification_report.md")
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
