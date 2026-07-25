"""Test Writer Pipeline Stage: Orchestrator integration for filling C# test skeletons"""
import logging
import os
from typing import Dict, List, Optional
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

    def execute(self, component_name: str, feedback_errors: Optional[List[str]] = None) -> Dict:
        """
        Execute test writing (filling skeletons) for a component.

        Args:
            component_name: Name of the migrated service
            feedback_errors: List of compiler build errors if correcting compilation issues

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

            # Directory containing the migrated service components (source code)
            service_dir = os.path.join(self.base_output_dir, component_name)
            if not os.path.exists(service_dir):
                self.logger.warning(f"Service directory not found: {service_dir}")
                result["status"] = "skipped"
                return result

            # Find skeleton test files (usually *.Tests.cs or similar) in the service directory
            test_files = []
            for root, _, files in os.walk(service_dir):
                for file in files:
                    if file.endswith(".Tests.cs") or file.endswith("Tests.cs"):
                        test_files.append(os.path.join(root, file))

            if not test_files:
                self.logger.warning(f"No skeleton test files found for {component_name}")
                result["status"] = "skipped"
                return result

            # Fill each skeleton test file
            for test_file in test_files:
                if feedback_errors:
                    self.logger.info(f"Healing test file due to compile errors: {test_file}")
                    success, error, code = self.agent.heal_tests(
                        test_file_path=test_file,
                        service_dir_path=service_dir,
                        errors=feedback_errors
                    )
                else:
                    self.logger.info(f"Writing implementations for skeleton test file: {test_file}")
                    success, error, code = self.agent.write_tests(
                        skeleton_file_path=test_file,
                        service_dir_path=service_dir,
                        output_file_path=test_file
                    )
                
                if success:
                    self.logger.info(f"Successfully processed test file: {test_file}")
                    result["filled_tests"].append(test_file)
                    self.filled_tests.append(test_file)
                else:
                    self.logger.error(f"Failed to process test file {test_file}: {error}")
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
