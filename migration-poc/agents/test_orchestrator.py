"""Test Orchestrator Agent: Coordinates self-healing testing loop"""
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from .test_writer_stage import TestWriterStage
from .test_compiler import run_test_compiler
from .test_writer.skeleton_reader import SkeletonReader

# Compiler error format: path(line,col): error CSxxxx: message [project]
# (same pattern used in agents/modernizer.py -- kept identical to avoid divergence)
CS_ERROR_PATTERN = re.compile(r"(.*?)\((\d+),(\d+)\):\s+error\s+(CS\d+):\s+(.*?)(?:\s*\[|$)")


class TestOrchestrator:
    """Coordinates the Test Writer and Test Runner in a self-healing loop"""

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.max_attempts = self.config.get("max_attempts", 4)
        self.reader = SkeletonReader()

    def _test_file_path(self, component_name: str) -> str:
        return os.path.join(self.base_output_dir, component_name, "tests", f"{component_name}.Tests.cs")

    def _map_errors(self, component_name: str, errors: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str]]:
        """
        Parse compiler errors and locate each one to the test method or helper class it falls
        inside, using the file that actually produced them (the current on-disk test file).

        Returns:
            (method_errors: name -> errors, class_errors: name -> errors, unresolvable: errors
            that can't be mapped -- e.g. they point into src/ (Stage 4) or have no location info)
        """
        method_errors: Dict[str, List[str]] = {}
        class_errors: Dict[str, List[str]] = {}
        unresolvable: List[str] = []

        test_file_path = self._test_file_path(component_name)
        if not os.path.exists(test_file_path):
            return method_errors, class_errors, list(errors)

        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        methods = self.reader.extract_test_methods(content)
        classes = self.reader.extract_test_classes(content)
        test_file_name = os.path.basename(test_file_path)

        for raw_error in errors:
            match = CS_ERROR_PATTERN.search(raw_error)
            if not match:
                unresolvable.append(raw_error)
                continue

            file_path, line_num, _col, _code, _msg = match.groups()
            if os.path.basename(file_path.strip()) != test_file_name:
                # Points into src/ (Stage 4 output) or an SDK/project-level message --
                # Stage 5 cannot fix this by editing tests.
                unresolvable.append(raw_error)
                continue

            loc = SkeletonReader.locate_error(content, methods, classes, int(line_num))
            if loc is None:
                unresolvable.append(raw_error)
                continue

            if loc["kind"] == "method":
                method_errors.setdefault(loc["name"], []).append(raw_error)
            else:
                class_errors.setdefault(loc["name"], []).append(raw_error)

        return method_errors, class_errors, unresolvable

    def _comment_out_blocks(self, component_name: str, method_names: List[str], class_names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Comment out the named test methods and/or helper classes by splicing /* ... */ around
        their exact source ranges (from SkeletonReader). Never comments out the primary test
        class container. Returns the names actually commented out.
        """
        if not method_names and not class_names:
            return [], []

        test_file_path = self._test_file_path(component_name)
        if not os.path.exists(test_file_path):
            self.logger.warning(f"Test file not found: {test_file_path}")
            return [], []

        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        all_methods = {m["name"]: m for m in self.reader.extract_test_methods(content)}
        all_classes = {c["name"]: c for c in self.reader.extract_test_classes(content)}

        blocks = []
        commented_classes = []
        commented_methods = []

        for name in class_names:
            block = all_classes.get(name)
            if block:
                blocks.append(block)
                commented_classes.append(name)

        for name in method_names:
            block = all_methods.get(name)
            if not block:
                continue
            # Skip if this method already sits inside a class block we're commenting out
            if any(b["start_idx"] <= block["start_idx"] and block["end_idx"] <= b["end_idx"] for b in blocks):
                continue
            blocks.append(block)
            commented_methods.append(name)

        if not blocks:
            return [], []

        blocks.sort(key=lambda b: b["start_idx"], reverse=True)
        for b in blocks:
            start, end = b["start_idx"], b["end_idx"]
            original = content[start:end]
            comment = (
                f"// Commented out: compilation error could not be resolved after {self.max_attempts} attempts\n"
                f"        /*\n{original}\n        */"
            )
            content = content[:start] + comment + content[end:]
            self.logger.info(f"⏸️ Commented out: {b['name']}")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info(f"✏️ Commented out {len(commented_methods)} test method(s) and {len(commented_classes)} class(es) in {test_file_path}")
        return commented_methods, commented_classes

    def execute(self, component_name: str) -> Dict:
        """
        Executes the self-healing loop: Write -> Compile -> Check -> Repeat.
        Every attempt composes the test file fresh from the pristine skeleton (never from a
        previous attempt's output), with the previous attempt's compiler errors threaded in,
        scoped per-method, as LLM retry context.
        After max_attempts, comments out the specific failing tests/classes (located from the
        compiler's own file/line, not guessed) and tries one final compile.
        """
        attempt = 1
        errors: List[str] = []
        errors_by_method: Dict[str, List[str]] = {}
        runner_report: Dict = {}

        writer_stage = TestWriterStage(self.base_output_dir, self.config)

        test_file_path = self._test_file_path(component_name)
        skeleton_content = None
        if os.path.exists(test_file_path):
            with open(test_file_path, "r", encoding="utf-8") as f:
                skeleton_content = f.read()

        while attempt <= self.max_attempts:
            self.logger.info(f"🔄 Test Orchestrator: Attempt {attempt} of {self.max_attempts} for {component_name}")

            # 1. Run Test Writer Stage, composing fresh from the pristine skeleton every time
            self.logger.info(f"✍️ Test Orchestrator: Invoking Test Writer Stage...")
            writer_result = writer_stage.execute(component_name, skeleton_content=skeleton_content, feedback_errors=errors_by_method)

            if writer_result["status"] == "failed":
                self.logger.error("❌ Test Writer failed to implement test skeleton. Aborting loop.")
                return {
                    "status": "failed",
                    "compiled": False,
                    "errors": writer_result["errors"],
                    "attempts": attempt,
                    "tests_dir": writer_result.get("filled_tests")[0] if writer_result.get("filled_tests") else "",
                    "commented_tests": [],
                    "commented_classes": [],
                    "uncommentable_errors": [],
                }

            # 2. Run Test Compiler
            self.logger.info(f"🏃 Test Orchestrator: Running Test Compiler...")
            runner_report = run_test_compiler(component_name, self.base_output_dir)

            if runner_report["compiled"]:
                self.logger.info(f"✅ Test Orchestrator: Tests compiled cleanly on attempt {attempt}!")
                runner_report["attempts"] = attempt
                runner_report["commented_tests"] = []
                runner_report["commented_classes"] = []
                runner_report["uncommentable_errors"] = []
                return runner_report

            # Scope compiler errors to the specific method that produced them for the next attempt
            errors = runner_report["errors"]
            errors_by_method, _, _ = self._map_errors(component_name, errors)
            self.logger.warning(f"⚠️ Test Orchestrator: Compilation failed on attempt {attempt}. Compile errors parsed.")
            attempt += 1

        # Max attempts reached - locate and comment out the specific failing tests/classes.
        # This can take more than one pass: commenting out one broken block can unmask a
        # different, previously-shadowed compiler error elsewhere, so keep resolving until
        # the project compiles or nothing new can be commented out. Bounded by max_attempts
        # again so this can't loop indefinitely.
        self.logger.warning(f"⚠️ Test Orchestrator: Max attempts ({self.max_attempts}) reached. Commenting out failing tests/classes...")

        all_commented_tests: List[str] = []
        all_commented_classes: List[str] = []
        unresolvable: List[str] = []

        for cleanup_pass in range(1, self.max_attempts + 1):
            method_errors, class_errors, unresolvable = self._map_errors(component_name, errors)
            newly_commented_tests, newly_commented_classes = self._comment_out_blocks(
                component_name, list(method_errors.keys()), list(class_errors.keys())
            )

            if not newly_commented_tests and not newly_commented_classes:
                break

            all_commented_tests.extend(newly_commented_tests)
            all_commented_classes.extend(newly_commented_classes)

            self.logger.info(f"🏃 Test Orchestrator: Running test compilation after cleanup pass {cleanup_pass}...")
            runner_report = run_test_compiler(component_name, self.base_output_dir)

            if runner_report["compiled"]:
                unresolvable = []
                break

            errors = runner_report["errors"]

        runner_report["attempts"] = self.max_attempts
        runner_report["commented_tests"] = all_commented_tests
        runner_report["commented_classes"] = all_commented_classes
        runner_report["uncommentable_errors"] = unresolvable

        if unresolvable:
            self.logger.warning(f"⚠️ Test Orchestrator: {len(unresolvable)} error(s) could not be mapped to a test/class (likely Stage 4 source or project-level issues) and remain unresolved.")

        return runner_report
