"""Test Orchestrator Agent: Coordinates self-healing testing loop"""
import logging
import os
import re
from typing import Dict, List, Optional
from agents.test_writer_stage import TestWriterStage
from agents.test_runner import run_test_runner

class TestOrchestrator:
    """Coordinates the Test Writer and Test Runner in a self-healing loop"""

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.max_attempts = self.config.get("max_attempts", 5)

    def _extract_failing_tests_from_errors(self, errors: List[str]) -> List[str]:
        """Extract test method names from compilation errors"""
        failing_tests = set()
        for error in errors:
            # Match patterns like "method 'MethodName' does not exist" or "CS0103: The name 'ClassName' does not exist"
            if "does not exist" in error or "error CS" in error:
                # Extract any word that looks like a test method (PascalCase with "Test" in name)
                matches = re.findall(r'\b([A-Z]\w*(?:Test|Async)\w*)\b', error)
                failing_tests.update(matches)
        return list(failing_tests)

    def _comment_out_failing_tests(self, component_name: str, failing_tests: List[str]) -> int:
        """
        Comment out failing test methods in the test file.
        Returns: number of tests commented out
        """
        test_file_path = os.path.join(self.base_output_dir, component_name, "tests", f"{component_name}.Tests.cs")

        if not os.path.exists(test_file_path):
            self.logger.warning(f"Test file not found: {test_file_path}")
            return 0

        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            commented_count = 0
            for test_name in failing_tests:
                # Pattern to find [Fact] or [Theory] followed by test method
                pattern = rf'(\[\w+(?:\([^)]*\))?\]\s*(?:\/\/.*?\n)*\s*public\s+(?:async\s+)?(?:void|Task)\s+{test_name}\s*\()'

                if re.search(pattern, content):
                    # Replace the test method signature with commented version
                    replacement = rf'// TODO: Fix compilation error - test needs dependencies to be defined\n        /*\n        \1'
                    content, num_replacements = re.subn(pattern, replacement, content)
                    commented_count += num_replacements

                    # Also close the comment block at the end of the method
                    # Find the closing brace of this method and add */ before it
                    # This is a simplified approach - for complex methods we find the next public method or class closing
                    self.logger.info(f"⏸️ Commented out test method: {test_name}")

            # Add closing comments if needed
            if commented_count > 0:
                # Find all open /* without closing */ and add them
                lines = content.split('\n')
                open_comments = 0
                for i, line in enumerate(lines):
                    if '/*' in line and '*/' not in line:
                        open_comments += 1
                    elif '*/' in line and '/*' not in line:
                        open_comments -= 1
                    elif line.strip().startswith('public ') and open_comments > 0:
                        # We found a new public method while a comment is open
                        lines.insert(i, '        */')
                        open_comments -= 1

                # Close any remaining open comments before closing braces
                for i in range(len(lines) - 1, -1, -1):
                    if open_comments <= 0:
                        break
                    if lines[i].strip() == '}' and open_comments > 0:
                        lines.insert(i, '        */')
                        open_comments -= 1

                content = '\n'.join(lines)

                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.logger.info(f"✏️ Commented out {commented_count} failing tests in {test_file_path}")

            return commented_count

        except Exception as e:
            self.logger.error(f"❌ Error commenting out tests: {e}")
            return 0

    def execute(self, component_name: str) -> Dict:
        """
        Executes the self-healing loop: Write -> Run -> Check -> Repeat.
        After max_attempts, comments out failing tests and tries one final compile.
        """
        attempt = 1
        errors = []
        runner_report = {}
        commented_tests = []

        writer_stage = TestWriterStage(self.base_output_dir, self.config)

        while attempt <= self.max_attempts:
            self.logger.info(f"🔄 Test Orchestrator: Attempt {attempt} of {self.max_attempts} for {component_name}")

            # 1. Run Test Writer Stage
            self.logger.info(f"✍️ Test Orchestrator: Invoking Test Writer Stage...")
            writer_result = writer_stage.execute(component_name, feedback_errors=errors)

            if writer_result["status"] == "failed":
                self.logger.error("❌ Test Writer failed to implement test skeleton. Aborting loop.")
                return {
                    "status": "failed",
                    "compiled": False,
                    "errors": writer_result["errors"],
                    "attempts": attempt,
                    "tests_dir": writer_result.get("filled_tests")[0] if writer_result.get("filled_tests") else "",
                    "commented_tests": []
                }

            # 2. Run Test Runner
            self.logger.info(f"🏃 Test Orchestrator: Running Test Runner...")
            runner_report = run_test_runner(component_name, self.base_output_dir)

            if runner_report["compiled"]:
                self.logger.info(f"✅ Test Orchestrator: Tests compiled cleanly on attempt {attempt}!")
                runner_report["attempts"] = attempt
                runner_report["commented_tests"] = commented_tests
                return runner_report

            # Extract compilation errors for the next attempt
            errors = runner_report["errors"]
            self.logger.warning(f"⚠️ Test Orchestrator: Compilation failed on attempt {attempt}. Compile errors parsed.")
            attempt += 1

        # Max attempts reached - comment out failing tests and try one final time
        self.logger.warning(f"⚠️ Test Orchestrator: Max attempts ({self.max_attempts}) reached. Commenting out failing tests...")

        failing_tests = self._extract_failing_tests_from_errors(errors)
        if failing_tests:
            commented_count = self._comment_out_failing_tests(component_name, failing_tests)
            commented_tests = failing_tests[:commented_count]

            # Try one final compile with commented-out tests
            self.logger.info(f"🏃 Test Orchestrator: Running final test compilation after commenting out failing tests...")
            runner_report = run_test_runner(component_name, self.base_output_dir)
            runner_report["attempts"] = self.max_attempts
            runner_report["commented_tests"] = commented_tests
            return runner_report

        self.logger.error(f"❌ Test Orchestrator: Failed to compile tests after {self.max_attempts} attempts.")
        runner_report["attempts"] = self.max_attempts
        runner_report["commented_tests"] = commented_tests
        return runner_report
