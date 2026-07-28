"""Reqnroll Test Runner: Execute Reqnroll BDD tests and collect results"""
import os
import subprocess
import logging
import re
from typing import Dict, List, Tuple
from pathlib import Path


class ReqnrollTestRunner:
    """Run Reqnroll tests via dotnet test"""

    def __init__(self, base_output_dir: str = "migrated-output"):
        self.base_output_dir = base_output_dir
        self.logger = logging.getLogger(__name__)

    def run_tests(self, component_name: str, run_id: str) -> Dict:
        """
        Run Reqnroll tests via dotnet test.

        Returns dict with:
        - success: bool
        - scenarios_run: int
        - scenarios_passed: int
        - scenarios_failed: int
        - scenarios_pending: int
        - step_failures: List[str]
        - coverage: float
        - raw_output: str
        """
        tests_dir = os.path.join(self.base_output_dir, run_id, "tests")

        if not os.path.exists(tests_dir):
            return {
                "success": False,
                "scenarios_run": 0,
                "scenarios_passed": 0,
                "scenarios_failed": 0,
                "scenarios_pending": 0,
                "step_failures": [f"Tests directory not found: {tests_dir}"],
                "coverage": 0.0,
                "raw_output": ""
            }

        self.logger.info(f"🎭 Reqnroll: Running BDD tests in {tests_dir}")

        try:
            # Run dotnet test with coverage
            result = subprocess.run(
                ["dotnet", "test", "--collect:XPlat Code Coverage"],
                cwd=tests_dir,
                capture_output=True,
                text=True,
                timeout=180
            )

            # Parse output
            output = result.stdout + "\n" + result.stderr
            scenarios = self._parse_scenarios(output)
            step_failures = self._parse_step_failures(output)
            coverage = self._parse_coverage(tests_dir)

            success = result.returncode == 0

            self.logger.info(
                f"✅ Reqnroll: Tests completed - "
                f"{scenarios['passed']}/{scenarios['run']} scenarios passed"
            )

            return {
                "success": success,
                "scenarios_run": scenarios["run"],
                "scenarios_passed": scenarios["passed"],
                "scenarios_failed": scenarios["failed"],
                "scenarios_pending": scenarios["pending"],
                "step_failures": step_failures,
                "coverage": coverage,
                "raw_output": output
            }

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Reqnroll: Test execution timed out after 180 seconds")
            return {
                "success": False,
                "scenarios_run": 0,
                "scenarios_passed": 0,
                "scenarios_failed": 0,
                "scenarios_pending": 0,
                "step_failures": ["Test execution timed out"],
                "coverage": 0.0,
                "raw_output": ""
            }
        except Exception as e:
            self.logger.error(f"❌ Reqnroll: Error: {e}")
            return {
                "success": False,
                "scenarios_run": 0,
                "scenarios_passed": 0,
                "scenarios_failed": 0,
                "scenarios_pending": 0,
                "step_failures": [f"dotnet test failed to run: {str(e)}"],
                "coverage": 0.0,
                "raw_output": ""
            }

    def _parse_scenarios(self, output: str) -> Dict[str, int]:
        """Parse scenario counts from dotnet test output"""
        scenarios = {"run": 0, "passed": 0, "failed": 0, "pending": 0}

        # Look for Reqnroll summary lines
        # Example: "3 scenarios (1 failed, 2 passed)"
        scenario_pattern = r'(\d+)\s+scenarios?\s*\((.*?)\)'
        match = re.search(scenario_pattern, output)
        if match:
            scenarios["run"] = int(match.group(1))
            summary = match.group(2)

            passed_match = re.search(r'(\d+)\s+passed', summary)
            if passed_match:
                scenarios["passed"] = int(passed_match.group(1))

            failed_match = re.search(r'(\d+)\s+failed', summary)
            if failed_match:
                scenarios["failed"] = int(failed_match.group(1))

            pending_match = re.search(r'(\d+)\s+pending', summary)
            if pending_match:
                scenarios["pending"] = int(pending_match.group(1))

        return scenarios

    def _parse_step_failures(self, output: str) -> List[str]:
        """Extract step failure messages"""
        failures = []

        # Look for "Given/When/Then step not implemented" or "step binding not found"
        step_patterns = [
            r'Step binding not found for (.+)',
            r'\.Steps\..+\(\).*failed',
            r'Assertion failed: (.+)',
        ]

        for pattern in step_patterns:
            for match in re.finditer(pattern, output, re.IGNORECASE):
                failure = match.group(0)[:200]  # Limit to 200 chars
                if failure not in failures:
                    failures.append(failure)

        return failures[:10]  # Limit to first 10

    def _parse_coverage(self, tests_dir: str) -> float:
        """Parse line coverage from Cobertura XML"""
        import glob
        import xml.etree.ElementTree as ET

        search_path = os.path.join(tests_dir, "TestResults", "**", "coverage.cobertura.xml")
        coverage_files = glob.glob(search_path, recursive=True)

        if not coverage_files:
            return 0.0

        try:
            tree = ET.parse(coverage_files[0])
            root = tree.getroot()
            line_rate = float(root.attrib.get('line-rate', 0.0)) * 100
            return line_rate
        except Exception:
            return 0.0
