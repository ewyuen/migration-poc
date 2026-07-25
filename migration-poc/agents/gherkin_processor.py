"""Gherkin processor: Parse Gherkin feature files and extract scenarios"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GherkinStep:
    """Represents a single Gherkin step (Given/When/Then)"""
    keyword: str  # Given, When, Then, And, But
    text: str     # Step text
    line_number: int


@dataclass
class GherkinScenario:
    """Represents a Gherkin scenario"""
    name: str
    steps: List[GherkinStep]
    tags: List[str]
    line_number: int


@dataclass
class GherkinFeature:
    """Represents a complete Gherkin feature file"""
    name: str
    description: str
    tags: List[str]
    scenarios: List[GherkinScenario]
    filepath: str


class GherkinFileLocator:
    """Locate Gherkin feature files in migrated service directories"""

    def __init__(self, base_dir: str = "migrated-output"):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)

    def find_feature_files(self, component_name: str) -> List[str]:
        """
        Find all .feature files for a component.

        Args:
            component_name: Name of the migrated service

        Returns:
            List of paths to .feature files
        """
        component_path = os.path.join(self.base_dir, component_name)
        feature_files = []

        if not os.path.exists(component_path):
            self.logger.warning(f"Component path not found: {component_path}")
            return feature_files

        for root, dirs, files in os.walk(component_path):
            for file in files:
                if file.endswith('.feature'):
                    feature_files.append(os.path.join(root, file))

        self.logger.info(f"Found {len(feature_files)} feature files for {component_name}")
        return feature_files

    def find_all_feature_files(self, base_search_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Find all feature files across all components.

        Returns:
            Dictionary mapping component names to list of feature files
        """
        search_dir = base_search_dir or self.base_dir
        features_by_component = {}

        if not os.path.exists(search_dir):
            self.logger.warning(f"Search directory not found: {search_dir}")
            return features_by_component

        for component_dir in os.listdir(search_dir):
            component_path = os.path.join(search_dir, component_dir)
            if os.path.isdir(component_path) and component_dir != "result-log":
                feature_files = self.find_feature_files(component_dir)
                if feature_files:
                    features_by_component[component_dir] = feature_files

        return features_by_component


class GherkinParser:
    """Parse Gherkin feature files and extract structure"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_feature_file(self, filepath: str) -> Optional[GherkinFeature]:
        """
        Parse a .feature file and extract feature structure.

        Args:
            filepath: Path to the .feature file

        Returns:
            GherkinFeature object or None if parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._parse_content(content, filepath)
        except Exception as e:
            self.logger.error(f"Error parsing {filepath}: {e}")
            return None

    def _parse_content(self, content: str, filepath: str) -> Optional[GherkinFeature]:
        """Parse Gherkin content and return feature structure"""
        lines = content.split('\n')
        feature_name = ""
        feature_description = []
        feature_tags = []
        scenarios = []
        current_scenario = None
        current_steps = []
        scenario_tags = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            # Parse feature tags
            if stripped.startswith('@'):
                feature_tags.extend(self._extract_tags(stripped))
                i += 1
                continue

            # Parse Feature header
            if stripped.startswith('Feature:'):
                feature_name = stripped.replace('Feature:', '').strip()
                # Get feature description (lines until first scenario)
                i += 1
                while i < len(lines):
                    desc_line = lines[i].strip()
                    if not desc_line or desc_line.startswith('Scenario') or desc_line.startswith('@'):
                        break
                    if not desc_line.startswith('Feature:'):
                        feature_description.append(desc_line)
                    i += 1
                continue

            # Parse scenario tags
            if stripped.startswith('@'):
                scenario_tags.extend(self._extract_tags(stripped))
                i += 1
                continue

            # Parse Scenario
            if stripped.startswith('Scenario:') or stripped.startswith('Scenario Outline:'):
                # Save previous scenario
                if current_scenario:
                    scenario = GherkinScenario(
                        name=current_scenario,
                        steps=current_steps,
                        tags=scenario_tags,
                        line_number=i
                    )
                    scenarios.append(scenario)

                current_scenario = stripped.replace('Scenario:', '').replace('Scenario Outline:', '').strip()
                current_steps = []
                scenario_tags = []
                i += 1
                continue

            # Parse steps (Given, When, Then, And, But)
            for keyword in ['Given', 'When', 'Then', 'And', 'But']:
                if stripped.startswith(keyword + ' '):
                    step_text = stripped[len(keyword):].strip()
                    current_steps.append(GherkinStep(
                        keyword=keyword,
                        text=step_text,
                        line_number=i + 1
                    ))
                    break

            i += 1

        # Save last scenario
        if current_scenario:
            scenario = GherkinScenario(
                name=current_scenario,
                steps=current_steps,
                tags=scenario_tags,
                line_number=i
            )
            scenarios.append(scenario)

        if not feature_name:
            self.logger.warning(f"No feature found in {filepath}")
            return None

        return GherkinFeature(
            name=feature_name,
            description='\n'.join(feature_description),
            tags=feature_tags,
            scenarios=scenarios,
            filepath=filepath
        )

    @staticmethod
    def _extract_tags(tag_line: str) -> List[str]:
        """Extract tags from a tag line"""
        return [tag.strip() for tag in tag_line.split() if tag.startswith('@')]


class GherkinValidator:
    """Validate Gherkin files for correctness"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors = []

    def validate_feature(self, feature: GherkinFeature) -> bool:
        """
        Validate a parsed feature.

        Args:
            feature: GherkinFeature to validate

        Returns:
            True if valid, False otherwise
        """
        self.errors.clear()

        if not feature.name:
            self.errors.append("Feature must have a name")

        if not feature.scenarios:
            self.errors.append("Feature must have at least one scenario")
            return False

        for scenario in feature.scenarios:
            if not scenario.name:
                self.errors.append(f"Scenario at line {scenario.line_number} must have a name")

            if not scenario.steps:
                self.errors.append(f"Scenario '{scenario.name}' must have at least one step")

            # Validate step structure (should have Given, When, Then)
            has_given = any(s.keyword == 'Given' for s in scenario.steps)
            has_when = any(s.keyword == 'When' for s in scenario.steps)
            has_then = any(s.keyword == 'Then' for s in scenario.steps)

            if not (has_given or has_when or has_then):
                self.errors.append(f"Scenario '{scenario.name}' has no Given/When/Then steps")

        if self.errors:
            for error in self.errors:
                self.logger.error(f"Validation error: {error}")
            return False

        return True
