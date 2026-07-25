"""Test Output Manager: Handle test file generation and directory structure"""
import os
from pathlib import Path
from typing import Dict, Optional


class TestOutputManager:
    """Manages test output directory structure for multiple languages"""

    def __init__(self, base_output_dir: str = "migrated-output"):
        self.base_output_dir = base_output_dir

    def setup_test_directories(self, component_name: str, languages: list) -> Dict[str, str]:
        """
        Set up test output directories for each language.

        Args:
            component_name: Name of the migrated service
            languages: List of target languages (e.g., ['csharp', 'java', 'python'])

        Returns:
            Dictionary mapping language to test directory path
        """
        component_dir = os.path.join(self.base_output_dir, component_name)
        test_dir_map = {}

        for language in languages:
            if language.lower() in ['csharp', 'c#']:
                test_subdir = os.path.join(component_dir, "Tests")
            elif language.lower() == 'java':
                test_subdir = os.path.join(component_dir, "src", "test", "java")
            elif language.lower() == 'python':
                test_subdir = os.path.join(component_dir, "tests")
            else:
                test_subdir = os.path.join(component_dir, "Tests")

            Path(test_subdir).mkdir(parents=True, exist_ok=True)
            test_dir_map[language] = test_subdir

        return test_dir_map

    def get_test_output_path(self, component_name: str, language: str, filename: str) -> str:
        """
        Get the full output path for a generated test file.

        Args:
            component_name: Name of the migrated service
            language: Target language
            filename: Name of the test file to generate

        Returns:
            Full file path for the test
        """
        test_dirs = self.setup_test_directories(component_name, [language])
        test_dir = test_dirs[language]
        return os.path.join(test_dir, filename)

    def save_test_file(self, component_name: str, language: str, filename: str, content: str) -> str:
        """
        Save generated test file to appropriate directory.

        Args:
            component_name: Name of the migrated service
            language: Target language
            filename: Name of the test file
            content: Test file content

        Returns:
            Path where file was saved
        """
        filepath = self.get_test_output_path(component_name, language, filename)

        # Avoid overwriting existing test files
        base_path = filepath
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(
                os.path.dirname(filepath),
                f"{name}_generated_{counter}{ext}"
            )
            counter += 1

        # Ensure directory exists
        Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def get_generated_tests_summary(self, component_name: str) -> Dict[str, list]:
        """
        Get summary of generated test files for a component.

        Returns:
            Dictionary mapping language to list of generated test files
        """
        component_dir = os.path.join(self.base_output_dir, component_name)
        summary = {}

        # Check all known test directories
        test_locations = {
            "csharp": "Tests",
            "java": os.path.join("src", "test", "java"),
            "python": "tests"
        }

        for language, relative_path in test_locations.items():
            full_path = os.path.join(component_dir, relative_path)
            if os.path.exists(full_path):
                test_files = [f for f in os.listdir(full_path) if f.endswith('Tests.cs') or f.endswith('_tests.py') or f.endswith('Tests.java')]
                if test_files:
                    summary[language] = test_files

        return summary

    def get_test_filename(self, scenario_name: str, language: str) -> str:
        """
        Get appropriate test filename for language.

        Args:
            scenario_name: Name of the scenario or feature
            language: Target language

        Returns:
            Appropriate filename with extension
        """
        safe_name = scenario_name.replace(' ', '_')

        if language.lower() in ['csharp', 'c#']:
            return f"Generated{safe_name}Tests.cs"
        elif language.lower() == 'java':
            return f"Generated{safe_name}Tests.java"
        elif language.lower() == 'python':
            return f"test_generated_{safe_name.lower()}.py"
        else:
            return f"{safe_name}.generated"

    def generate_file_header(self, language: str, filename: str, description: str) -> str:
        """
        Generate file header with metadata.

        Args:
            language: Target language
            filename: Name of the file
            description: Description of what's in the file

        Returns:
            File header as string
        """
        if language.lower() in ['csharp', 'c#']:
            return f'''// Auto-generated test file: {filename}
// Description: {description}
// Generated using SpecKit
//
'''
        elif language.lower() == 'java':
            return f'''/*
 * Auto-generated test file: {filename}
 * Description: {description}
 * Generated using SpecKit
 */
'''
        elif language.lower() == 'python':
            return f'''"""Auto-generated test file: {filename}

Description: {description}
Generated using SpecKit
"""
'''
        else:
            return f"# {filename}\n# {description}\n"
