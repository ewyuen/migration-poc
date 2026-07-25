"""Test Generation Pipeline Stage: Orchestrator integration for SpecKit test generation"""
import logging
import os
from typing import Dict, Optional
from agents.gherkin_processor import GherkinFileLocator, GherkinParser, GherkinValidator
from agents.test_code_generator import TestCodeGenerator
from agents.test_output_manager import TestOutputManager


class TestGenerationStage:
    """
    Pipeline stage for test generation.
    Runs after code modernization to generate executable tests from Gherkin files.
    """

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize components
        self.file_locator = GherkinFileLocator(base_output_dir)
        self.parser = GherkinParser()
        self.validator = GherkinValidator()
        self.code_generator = TestCodeGenerator()
        self.output_manager = TestOutputManager(base_output_dir)

        # Configuration
        self.enabled = self.config.get("enabled", True)
        self.fail_on_error = self.config.get("fail_on_error", False)
        self.languages = self.config.get("languages", ["csharp", "java", "python"])
        self.overwrite_existing = self.config.get("overwrite_existing", False)

        # Tracking
        self.generated_tests = {}
        self.errors = []
        self.skipped_files = []

    def execute(self, component_name: str) -> Dict:
        """
        Execute test generation for a component.

        Args:
            component_name: Name of the migrated service

        Returns:
            Result dictionary with status and generated files
        """
        result = {
            "component": component_name,
            "status": "success",
            "generated_tests": [],
            "errors": [],
            "skipped": []
        }

        if not self.enabled:
            self.logger.info(f"Test generation disabled, skipping {component_name}")
            result["status"] = "skipped"
            return result

        try:
            self.logger.info(f"Starting test generation for {component_name}")

            # Find Gherkin files
            feature_files = self.file_locator.find_feature_files(component_name)
            if not feature_files:
                self.logger.warning(f"No Gherkin files found for {component_name}")
                result["status"] = "skipped"
                return result

            # Process each Gherkin file
            for feature_file in feature_files:
                self._process_feature_file(feature_file, component_name, result)

            # Set final status
            if result["errors"] and self.fail_on_error:
                result["status"] = "failed"
            elif result["generated_tests"]:
                result["status"] = "success"
            else:
                result["status"] = "completed_with_issues"

        except Exception as e:
            self.logger.error(f"Error in test generation stage: {e}", exc_info=True)
            result["status"] = "failed"
            result["errors"].append(str(e))

        return result

    def _process_feature_file(self, feature_file: str, component_name: str, result: Dict):
        """Process a single Gherkin feature file"""
        try:
            self.logger.info(f"Processing {feature_file}")

            # Parse Gherkin file
            feature = self.parser.parse_feature_file(feature_file)
            if not feature:
                error = f"Failed to parse {feature_file}"
                self.logger.error(error)
                result["errors"].append(error)
                result["skipped"].append(feature_file)
                return

            # Validate Gherkin
            if not self.validator.validate_feature(feature):
                error = f"Validation failed for {feature_file}: {self.validator.errors}"
                self.logger.error(error)
                result["errors"].append(error)
                result["skipped"].append(feature_file)
                return

            # Infer target language from component
            target_language = self._infer_language(component_name)

            # Generate test code
            test_code = self._generate_test_code(feature, component_name, target_language)
            if not test_code:
                self.logger.warning(f"No test code generated for {feature_file}")
                result["skipped"].append(feature_file)
                return

            # Save test file
            test_filename = self.output_manager.get_test_filename(feature.name, target_language)
            output_path = self.output_manager.save_test_file(
                component_name,
                target_language,
                test_filename,
                test_code
            )

            result["generated_tests"].append({
                "source": feature_file,
                "output": output_path,
                "language": target_language,
                "scenarios": len(feature.scenarios)
            })

            self.logger.info(f"Generated test file: {output_path}")

        except Exception as e:
            error = f"Error processing {feature_file}: {e}"
            self.logger.error(error, exc_info=True)
            result["errors"].append(error)
            if self.fail_on_error:
                raise

    def _generate_test_code(self, feature, component_name: str, language: str) -> Optional[str]:
        """Generate test code for feature in target language"""
        try:
            if language.lower() in ['csharp', 'c#']:
                return self.code_generator.generate_csharp_tests(feature, component_name)
            elif language.lower() == 'java':
                return self.code_generator.generate_java_tests(feature, component_name)
            elif language.lower() == 'python':
                return self.code_generator.generate_python_tests(feature, component_name)
            else:
                self.logger.warning(f"Unsupported language: {language}")
                return None
        except Exception as e:
            self.logger.error(f"Error generating test code for {language}: {e}")
            return None

    @staticmethod
    def _infer_language(component_name: str) -> str:
        """
        Infer target programming language from component structure or naming.

        Args:
            component_name: Name of the component

        Returns:
            Language identifier (csharp, java, python)
        """
        # Check for language hints in component name
        name_lower = component_name.lower()
        if 'java' in name_lower:
            return 'java'
        elif 'python' in name_lower or 'py' in name_lower:
            return 'python'
        else:
            # Default to C#
            return 'csharp'

    def get_summary(self) -> Dict:
        """Get summary of test generation results"""
        total_generated = len(self.generated_tests)
        total_errors = len(self.errors)

        return {
            "total_generated": total_generated,
            "total_errors": total_errors,
            "generated_by_language": self._summarize_by_language(),
            "generated_tests": self.generated_tests,
            "errors": self.errors
        }

    def _summarize_by_language(self) -> Dict[str, int]:
        """Summarize generated tests by language"""
        summary = {}
        for test in self.generated_tests:
            language = test.get("language", "unknown")
            summary[language] = summary.get(language, 0) + 1
        return summary
