"""Test code generator: Generate language-specific test code from Gherkin scenarios"""
import logging
from typing import List, Dict, Optional
from agents.gherkin_processor import GherkinFeature, GherkinScenario, GherkinStep
from agents.step_mapper import StepRegistry, UnmappedStepHandler


class TestCodeGenerator:
    """Generate executable test code from Gherkin features"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.step_registry = StepRegistry()
        self.unmapped_handler = UnmappedStepHandler()

    def generate_csharp_tests(self, feature: GherkinFeature, service_name: str) -> str:
        """Generate C# NUnit test class from Gherkin feature"""
        class_name = self._to_pascal_case(feature.name.replace(' ', '_'))
        test_class_name = f"{class_name}Tests"

        code = self._generate_csharp_header(test_class_name)

        for scenario in feature.scenarios:
            method_code = self._generate_csharp_test_method(scenario, service_name)
            code += "\n" + method_code

        code += "\n    }\n}\n"
        return code

    def generate_java_tests(self, feature: GherkinFeature, service_name: str) -> str:
        """Generate Java JUnit 5 test class from Gherkin feature"""
        class_name = self._to_pascal_case(feature.name.replace(' ', '_'))
        test_class_name = f"{class_name}Tests"
        package = self._derive_package_from_service(service_name)

        code = self._generate_java_header(package, test_class_name)

        for scenario in feature.scenarios:
            method_code = self._generate_java_test_method(scenario, service_name)
            code += "\n" + method_code

        code += "\n}\n"
        return code

    def generate_python_tests(self, feature: GherkinFeature, service_name: str) -> str:
        """Generate Python pytest test module from Gherkin feature"""
        code = self._generate_python_header(feature, service_name)

        for scenario in feature.scenarios:
            method_code = self._generate_python_test_function(scenario, service_name)
            code += "\n" + method_code

        return code

    # C# Code Generation
    def _generate_csharp_header(self, class_name: str) -> str:
        """Generate C# test class header"""
        return f'''using NUnit.Framework;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace TestGenerated
{{
    [TestFixture]
    public class {class_name} : NUnitTestBase
    {{
'''

    def _generate_csharp_test_method(self, scenario: GherkinScenario, service_name: str) -> str:
        """Generate C# test method for a scenario"""
        method_name = self._to_pascal_case(scenario.name)
        code = f'''        [Test]
        [Description("{scenario.name}")]
        public void {method_name}()
        {{
            // Arrange
            InitializeServiceClient("{service_name}");
'''

        for step in scenario.steps:
            step_code = self._generate_csharp_step_code(step, service_name)
            code += step_code

        code += '''
        }
'''
        return code

    def _generate_csharp_step_code(self, step: GherkinStep, service_name: str) -> str:
        """Generate C# code for a single step"""
        mapping = self.step_registry.find_mapping(step.text)

        if mapping:
            params = self.step_registry.extract_step_params(step.text, mapping)
            return self._generate_csharp_action(mapping.action, params, service_name)
        else:
            placeholder = self.unmapped_handler.generate_placeholder_code("csharp", step.text, service_name)
            return f"\n            // TODO: {step.text}\n            Assert.Inconclusive(\"Unmapped step\");\n"

    @staticmethod
    def _generate_csharp_action(action: str, params: List[str], service_name: str) -> str:
        """Generate C# code for specific actions"""
        if action == "initialize_service":
            return f"            // Initialize {params[0] if params else service_name}\n"
        elif action == "call_api":
            return f"            // Call API: {params[0] if params else 'operation'}\n"
        elif action == "assert_response_contains":
            return f"            AssertResponseContains(response, null, \"{params[0] if params else 'value'}\");\n"
        else:
            return f"            // Action: {action}\n"

    # Java Code Generation
    def _generate_java_header(self, package: str, class_name: str) -> str:
        """Generate Java test class header"""
        return f'''package {package}.test;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Test scenarios")
public class {class_name} extends JUnitTestBase {{

'''

    def _generate_java_test_method(self, scenario: GherkinScenario, service_name: str) -> str:
        """Generate Java test method for a scenario"""
        method_name = self._to_camel_case(scenario.name)
        code = f'''    @Test
    @DisplayName("{scenario.name}")
    public void {method_name}() {{
        // Arrange
        initializeServiceClient("{service_name}");
'''

        for step in scenario.steps:
            step_code = self._generate_java_step_code(step, service_name)
            code += step_code

        code += "    }\n"
        return code

    def _generate_java_step_code(self, step: GherkinStep, service_name: str) -> str:
        """Generate Java code for a single step"""
        mapping = self.step_registry.find_mapping(step.text)

        if mapping:
            params = self.step_registry.extract_step_params(step.text, mapping)
            return self._generate_java_action(mapping.action, params, service_name)
        else:
            return f"        // TODO: {step.text}\n        fail(\"Unmapped step\");\n"

    @staticmethod
    def _generate_java_action(action: str, params: List[str], service_name: str) -> str:
        """Generate Java code for specific actions"""
        if action == "initialize_service":
            return f"        // Initialize {params[0] if params else service_name}\n"
        elif action == "call_api":
            return f"        // Call API: {params[0] if params else 'operation'}\n"
        elif action == "assert_response_contains":
            return f"        assertResponseContains(response, null, \"{params[0] if params else 'value'}\");\n"
        else:
            return f"        // Action: {action}\n"

    # Python Code Generation
    def _generate_python_header(self, feature: GherkinFeature, service_name: str) -> str:
        """Generate Python test module header"""
        return f'''"""Generated test module for: {feature.name}"""
import pytest
from test.generated.pytest_test_base import PytestTestBase


class Test{self._to_pascal_case(feature.name.replace(' ', '_'))}(PytestTestBase):
    """Test class for {feature.name}"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()
        self.service_name = "{service_name}"
        self.initialize_service_client(self.service_name)
'''

    def _generate_python_test_function(self, scenario: GherkinScenario, service_name: str) -> str:
        """Generate Python test function for a scenario"""
        method_name = self._to_snake_case(scenario.name)
        code = f'''
    def test_{method_name}(self):
        """
        Test: {scenario.name}
        """
        # Arrange
        self.initialize_service_client(self.service_name)

'''

        for step in scenario.steps:
            step_code = self._generate_python_step_code(step, service_name)
            code += step_code

        return code

    def _generate_python_step_code(self, step: GherkinStep, service_name: str) -> str:
        """Generate Python code for a single step"""
        mapping = self.step_registry.find_mapping(step.text)

        if mapping:
            params = self.step_registry.extract_step_params(step.text, mapping)
            return self._generate_python_action(mapping.action, params, service_name)
        else:
            return f"        # TODO: {step.text}\n        pytest.skip(\"Unmapped step\")\n"

    @staticmethod
    def _generate_python_action(action: str, params: List[str], service_name: str) -> str:
        """Generate Python code for specific actions"""
        if action == "initialize_service":
            return f"        # Initialize {params[0] if params else service_name}\n"
        elif action == "call_api":
            return f"        # Call API: {params[0] if params else 'operation'}\n"
        elif action == "assert_response_contains":
            return f"        self.assert_response_contains(response, None, \"{params[0] if params else 'value'}\")\n"
        else:
            return f"        # Action: {action}\n"

    # Utility methods
    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase"""
        return ''.join(word.capitalize() for word in text.split('_'))

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert text to camelCase"""
        words = text.split()
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower().replace(' ', '_')

    @staticmethod
    def _derive_package_from_service(service_name: str) -> str:
        """Derive Java package name from service name"""
        return f"com.service.{service_name.lower()}"
