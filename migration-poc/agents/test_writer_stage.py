"""Test Writer Pipeline Stage: Orchestrator integration for filling C# test skeletons"""
import logging
import os
from typing import Dict, Optional, List
from agents.test_writer.test_writer_agent import TestWriterAgent


class TestWriterStage:
    """
    Pipeline stage for test implementation/writing.
    Runs after skeleton test generation to fill in test bodies with real code.
    """

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize core agent
        self.agent = TestWriterAgent()

        # Configuration
        self.enabled = self.config.get("enabled", True)
        self.fail_on_error = self.config.get("fail_on_error", False)
        self.overwrite_existing = self.config.get("overwrite_existing", True)

        # Tracking
        self.filled_tests = []
        self.errors = []

    def execute(
        self,
        component_name: str,
        skeleton_content: Optional[str] = None,
        feedback_errors: Optional[Dict[str, List[str]]] = None,
    ) -> Dict:
        """
        Execute test writing (filling skeletons) for a component.

        Args:
            component_name: Name of the migrated service
            skeleton_content: Pristine skeleton content to fill from (always used over re-reading
                disk when provided, so retries never compound on a previous attempt's output)
            feedback_errors: Optional mapping of method_name -> compiler errors from the previous
                failed attempt, used to steer the LLM's retry

        Returns:
            Result dictionary with status and filled files
        """
        result = {
            "component": component_name,
            "status": "success",
            "filled_tests": [],
            "errors": []
        }

        if not self.enabled:
            self.logger.info(f"Test writer stage disabled, skipping {component_name}")
            result["status"] = "skipped"
            return result

        try:
            self.logger.info(f"Starting test writer stage for {component_name}")

            if feedback_errors:
                total_errors = sum(len(v) for v in feedback_errors.values())
                self.logger.info(f"📝 Feedback errors passed ({total_errors} errors across {len(feedback_errors)} methods): using for context in test generation")

            # Directory containing this component's actual Stage 4 output (modernized source).
            # This must be scoped to src/ specifically, not the whole component directory --
            # older pipeline runs can leave stale generated files (e.g. Models.cs) sitting at
            # the component root, and introspecting those would ground the LLM in interfaces
            # that were never really part of Stage 4's current output.
            component_dir = os.path.join(self.base_output_dir, component_name)
            service_dir = os.path.join(component_dir, "src")
            if not os.path.exists(service_dir):
                self.logger.warning(f"Service source directory not found: {service_dir}")
                result["status"] = "skipped"
                return result

            # Find skeleton test files (usually *.Tests.cs or similar) under the component directory
            test_files = []
            for root, _, files in os.walk(component_dir):
                for file in files:
                    if file.endswith(".Tests.cs") or file.endswith("Tests.cs"):
                        test_files.append(os.path.join(root, file))

            if not test_files:
                self.logger.warning(f"No skeleton test files found for {component_name}")
                result["status"] = "skipped"
                return result

            # Fill each skeleton test file
            for test_file in test_files:
                self.logger.info(f"Writing implementations for skeleton test file: {test_file}")
                
                success, error, code = self.agent.write_tests(
                    skeleton_file_path=test_file,
                    service_dir_path=service_dir,
                    output_file_path=test_file,
                    skeleton_content=skeleton_content,
                    feedback_errors=feedback_errors,
                )
                
                if success:
                    self.logger.info(f"Successfully implemented test file: {test_file}")
                    result["filled_tests"].append(test_file)
                    self.filled_tests.append(test_file)
                else:
                    self.logger.error(f"Failed to implement test file {test_file}: {error}")
                    result["errors"].append(f"{test_file}: {error}")
                    self.errors.append(f"{test_file}: {error}")

            # Set final status
            if result["errors"]:
                if self.fail_on_error:
                    result["status"] = "failed"
                else:
                    result["status"] = "completed_with_issues"
            elif result["filled_tests"]:
                result["status"] = "success"
            else:
                result["status"] = "skipped"

        except Exception as e:
            self.logger.error(f"Error in test writer stage: {e}", exc_info=True)
            result["status"] = "failed"
            result["errors"].append(str(e))
            self.errors.append(str(e))

        return result
