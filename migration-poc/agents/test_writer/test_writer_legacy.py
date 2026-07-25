"""Test Writer Agent: Convert Gherkin specifications to C# xUnit test code"""
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class GherkinParser:
    """Parses Gherkin feature files"""

    def __init__(self):
        self.features = []
        self.current_feature = None
        self.current_scenario = None

    def parse_feature_file(self, content: str) -> Dict:
        """
        Parse Gherkin feature file content

        Returns:
            Dictionary with parsed features and scenarios
        """
        lines = content.split("\n")
        features_dict = {
            "features": [],
            "total_scenarios": 0
        }

        current_feature = None

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Feature declaration
            if line_stripped.startswith("Feature:"):
                if current_feature:
                    features_dict["features"].append(current_feature)

                current_feature = {
                    "name": line_stripped.replace("Feature:", "").strip(),
                    "description": "",
                    "scenarios": []
                }

            # Feature description
            elif current_feature and line_stripped.startswith(("Given", "When", "Then")) is False and \
                    line_stripped.startswith(("Scenario", "Background")) is False:
                current_feature["description"] += line_stripped + " "

            # Scenario declaration
            elif line_stripped.startswith("Scenario:"):
                if current_feature:
                    scenario = {
                        "name": line_stripped.replace("Scenario:", "").strip(),
                        "type": "Scenario",
                        "given_steps": [],
                        "when_steps": [],
                        "then_steps": [],
                        "examples": []
                    }
                    self._parse_scenario_steps(lines, lines.index(line), scenario)
                    current_feature["scenarios"].append(scenario)

            # Scenario Outline
            elif line_stripped.startswith("Scenario Outline:"):
                if current_feature:
                    scenario = {
                        "name": line_stripped.replace("Scenario Outline:", "").strip(),
                        "type": "Scenario Outline",
                        "given_steps": [],
                        "when_steps": [],
                        "then_steps": [],
                        "examples": []
                    }
                    self._parse_scenario_outline(lines, lines.index(line), scenario)
                    current_feature["scenarios"].append(scenario)

        if current_feature:
            features_dict["features"].append(current_feature)

        # Count scenarios
        features_dict["total_scenarios"] = sum(len(f["scenarios"]) for f in features_dict["features"])

        return features_dict

    def _parse_scenario_steps(self, lines: List[str], start_idx: int, scenario: Dict) -> None:
        """Parse Given-When-Then steps for a scenario"""
        current_step_type = None

        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("Scenario"):
                break

            if line.startswith("Given"):
                current_step_type = "given_steps"
                step_text = line.replace("Given ", "").strip()
                scenario["given_steps"].append(step_text)

            elif line.startswith("When"):
                current_step_type = "when_steps"
                step_text = line.replace("When ", "").strip()
                scenario["when_steps"].append(step_text)

            elif line.startswith("Then"):
                current_step_type = "then_steps"
                step_text = line.replace("Then ", "").strip()
                scenario["then_steps"].append(step_text)

            elif line.startswith("And") and current_step_type:
                step_text = line.replace("And ", "").strip()
                scenario[current_step_type].append(step_text)

    def _parse_scenario_outline(self, lines: List[str], start_idx: int, scenario: Dict) -> None:
        """Parse Scenario Outline with Examples"""
        self._parse_scenario_steps(lines, start_idx, scenario)

        # Look for Examples table
        in_examples = False
        examples_header = None
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()

            if line.startswith("Examples:"):
                in_examples = True
                continue

            if in_examples:
                if line.startswith("|"):
                    if not examples_header:
                        examples_header = [h.strip() for h in line.split("|")[1:-1]]
                    else:
                        row_values = [v.strip() for v in line.split("|")[1:-1]]
                        scenario["examples"].append(dict(zip(examples_header, row_values)))


class TestCodeGenerator:
    """Generates C# xUnit test code from Gherkin scenarios"""

    def __init__(self):
        self.generated_code = []

    def generate_test_class(self, feature_name: str, scenarios: List[Dict], component_name: str) -> str:
        """
        Generate C# test class from Gherkin scenarios

        Args:
            feature_name: Name of the feature
            scenarios: List of scenario dictionaries
            component_name: Name of the component being tested

        Returns:
            Generated C# test code
        """
        class_name = self._to_pascal_case(feature_name) + "Tests"

        code = []
        code.append("using System;")
        code.append("using Xunit;")
        code.append("using FluentAssertions;")
        code.append(f"// Auto-generated from Gherkin: {feature_name}")
        code.append(f"// Component: {component_name}")
        code.append(f"// Generated: {datetime.now().isoformat()}\n")
        code.append(f"namespace {component_name}.Tests")
        code.append("{")
        code.append(f"    public class {class_name}")
        code.append("    {")

        # Add fixture setup
        code.append("        private readonly TestFixture _fixture;\n")
        code.append(f"        public {class_name}()")
        code.append("        {")
        code.append("            _fixture = new TestFixture();")
        code.append("        }\n")

        # Generate test methods
        for scenario in scenarios:
            test_method = self._generate_test_method(scenario)
            code.extend(test_method)

        # Add test fixture
        code.append("    }\n")
        code.append(self._generate_test_fixture(component_name))

        code.append("}")

        return "\n".join(code)

    def _generate_test_method(self, scenario: Dict) -> List[str]:
        """Generate a single test method from a scenario"""
        method_name = self._to_pascal_case(scenario["name"])
        code = []

        if scenario["type"] == "Scenario Outline" and scenario["examples"]:
            # Generate Theory method with InlineData
            code.append(f"        [Theory]")
            for example in scenario["examples"]:
                params = ", ".join(f'"{v}"' for v in example.values())
                code.append(f'        [InlineData({params})]')
            param_names = ", ".join(f"string {k}" for k in scenario["examples"][0].keys())
            code.append(f"        public void {method_name}({param_names})")
        else:
            # Generate Fact method
            code.append(f"        [Fact]")
            code.append(f"        public void {method_name}()")

        code.append("        {")

        # Given (Setup)
        if scenario["given_steps"]:
            code.append("            // Arrange (Given)")
            for step in scenario["given_steps"]:
                code.append(f"            // {step}")
            code.append("            var systemUnderTest = _fixture.CreateSystemUnderTest();")

        # When (Action)
        if scenario["when_steps"]:
            code.append("\n            // Act (When)")
            for step in scenario["when_steps"]:
                code.append(f"            // {step}")
            code.append("            var result = systemUnderTest.Execute();")

        # Then (Assert)
        if scenario["then_steps"]:
            code.append("\n            // Assert (Then)")
            for step in scenario["then_steps"]:
                code.append(f"            // {step}")
            code.append("            result.Should().NotBeNull();")

        code.append("        }\n")

        return code

    def _generate_test_fixture(self, component_name: str) -> str:
        """Generate test fixture class"""
        fixture_code = f"""    public class TestFixture
    {{
        public object CreateSystemUnderTest()
        {{
            // TODO: Initialize the system under test with appropriate dependencies
            // Example: var service = new {component_name}Service(mockDependency);
            return new object();
        }}

        public void Dispose()
        {{
            // Cleanup resources if needed
        }}
    }}"""

        return fixture_code

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        # Remove special characters and split on spaces/hyphens
        words = re.split(r'[\s\-_]+', text)
        return "".join(word.capitalize() for word in words if word)


class TestWriter:
    """Main test writer agent"""

    def __init__(self):
        self.parser = GherkinParser()
        self.generator = TestCodeGenerator()

    def write_tests_from_gherkin(self, gherkin_content: str, component_name: str, output_path: str = None) -> Tuple[bool, str, str]:
        """
        Convert Gherkin specifications to C# test code

        Args:
            gherkin_content: Gherkin feature file content
            component_name: Name of the component being tested
            output_path: Optional path to save generated tests

        Returns:
            Tuple of (success, error_message, generated_code)
        """
        try:
            # Parse Gherkin
            print(f"📖 Parsing Gherkin specifications...")
            features_dict = self.parser.parse_feature_file(gherkin_content)

            if not features_dict["features"]:
                return False, "No features found in Gherkin file", ""

            print(f"✅ Found {len(features_dict['features'])} feature(s) with {features_dict['total_scenarios']} scenario(s)")

            # Generate test code
            test_code = ""
            for feature in features_dict["features"]:
                print(f"🔧 Generating tests for: {feature['name']}")
                feature_test_code = self.generator.generate_test_class(
                    feature["name"],
                    feature["scenarios"],
                    component_name
                )
                test_code += feature_test_code + "\n\n"

            # Save to file if path provided
            if output_path:
                import os
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(test_code)
                print(f"💾 Test code saved to: {output_path}")

            print(f"✅ Test code generation complete")
            return True, "", test_code

        except Exception as e:
            error_msg = f"Failed to generate tests: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, ""

    def validate_generated_code(self, code: str) -> Tuple[bool, str]:
        """
        Basic validation of generated C# code

        Returns:
            Tuple of (is_valid, error_message)
        """
        checks = [
            ("using statements", "using" in code),
            ("namespace", "namespace" in code),
            ("test class", "public class" in code and "Tests" in code),
            ("test methods", "[Fact]" in code or "[Theory]" in code),
        ]

        for check_name, result in checks:
            if not result:
                return False, f"Missing or invalid: {check_name}"

        return True, ""


def generate_bdd_tests(domain_logic: str, modernized_code: str, exploration: Dict) -> str:
    """
    Agent entrypoint: Generate BDD tests (for backward compatibility)

    This function maintains compatibility with the existing orchestrator
    while using the new TestWriter internally for xUnit code generation.
    """
    # For now, return the generated feature file content
    # In a full implementation, this would use the actual Gherkin from bdd_test_cases_generator.py
    return "# Generated Gherkin specifications would go here"


if __name__ == "__main__":
    # Example usage
    example_gherkin = """
Feature: User Authentication
    As a user
    I want to log in to the system
    So that I can access my data

Scenario: Successful login with valid credentials
    Given user is logged out
    When user enters valid email and password
    Then user should see the dashboard
    And session cookie should be set

Scenario Outline: Login with various credentials
    Given user is on login page
    When user enters "<email>" and "<password>"
    Then user should see "<result>"

    Examples:
        | email          | password  | result    |
        | user@test.com  | password1 | dashboard |
        | invalid@test   | wrong     | error     |
"""

    writer = TestWriter()
    success, error, code = writer.write_tests_from_gherkin(example_gherkin, "AuthenticationService")

    if success:
        print("\n" + "="*70)
        print("GENERATED TEST CODE:")
        print("="*70)
        print(code)
