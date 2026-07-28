"""Step Definitions Generator: Creates Reqnroll step definition skeletons from Gherkin"""
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class GherkinStepExtractor:
    """Extract steps from Gherkin feature file content"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_steps(self, gherkin_content: str) -> List[Dict]:
        """
        Extract all Given/When/Then steps from Gherkin content.

        Returns list of dicts: {keyword, text, line_number}
        """
        steps = []
        lines = gherkin_content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Match Given, When, Then, And, But keywords
            match = re.match(r'^(Given|When|Then|And|But)\s+(.+)$', stripped)
            if match:
                keyword = match.group(1)
                text = match.group(2)
                steps.append({
                    'keyword': keyword,
                    'text': text,
                    'line_number': i,
                    'normalized_keyword': self._normalize_keyword(keyword)
                })

        return steps

    def _normalize_keyword(self, keyword: str) -> str:
        """Normalize And/But to Given/When/Then based on context"""
        # Simplified: just map to Given for now; full implementation would track state
        if keyword in ('And', 'But'):
            return 'Given'  # Conservative default
        return keyword


class ParameterTypeInferencer:
    """Infer Cucumber Expression types from step text"""

    def infer_types(self, step_text: str) -> List[Tuple[str, str]]:
        """
        Infer parameter types from step text.

        Returns list of (param_name, param_type) tuples.
        Types: 'string', 'int', 'float'
        """
        params = []

        # Find quoted strings -> {string}
        quoted_pattern = r'"([^"]*)"'
        for match in re.finditer(quoted_pattern, step_text):
            param_name = self._sanitize_param_name(match.group(1))
            if param_name:
                params.append((param_name, 'string'))

        # Find whole numbers -> {int}
        int_pattern = r'\b(\d+)\b'
        for match in re.finditer(int_pattern, step_text):
            # Avoid duplicates with string parameters
            if not any(str(match.group(0)) in p[0] for p in params):
                params.append((f"value{len(params)}", 'int'))

        return params

    def _sanitize_param_name(self, text: str) -> str:
        """Convert step text fragment to valid C# parameter name"""
        # Remove special chars, convert to camelCase
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', text)
        if not sanitized:
            return ''
        return sanitized[0].lower() + sanitized[1:]


class StepDefinitionSkeletonGenerator:
    """Generate Reqnroll step definition skeleton file"""

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.extractor = GherkinStepExtractor()
        self.inferencer = ParameterTypeInferencer()
        self.logger = logging.getLogger(__name__)

    def generate_skeleton(self, gherkin_content: str) -> str:
        """Generate StepDefinitions.cs skeleton from Gherkin"""
        steps = self.extractor.extract_steps(gherkin_content)

        # Build method stubs
        method_stubs = []
        for step in steps:
            method = self._generate_step_method(step)
            method_stubs.append(method)

        # Build complete file
        skeleton = self._build_file(method_stubs)
        return skeleton

    def _generate_step_method(self, step: Dict) -> str:
        """Generate a single step definition method with Cucumber Expression"""
        keyword = step['normalized_keyword']
        text = step['text']

        # Infer parameters
        params = self.inferencer.infer_types(text)

        # Build Cucumber Expression (replace quoted strings and numbers with {type})
        cucumber_expr = self._build_cucumber_expression(text, params)

        # Build C# method signature
        param_list = ', '.join(f"{ptype} {pname}" for pname, ptype in params)
        method_name = self._to_method_name(keyword, text)

        attr_mapping = {'Given': 'Given', 'When': 'When', 'Then': 'Then'}
        attribute = attr_mapping.get(keyword, 'Given')

        method = f'''
    [{attribute}("{cucumber_expr}")]
    public void {method_name}({param_list})
    {{
        // TODO: Implement {keyword} {text}
    }}'''
        return method

    def _build_cucumber_expression(self, text: str, params: List[Tuple[str, str]]) -> str:
        """Convert step text to Cucumber Expression with {type} placeholders"""
        result = text

        # Replace quoted strings with {string}
        result = re.sub(r'"([^"]*)"', '{string}', result)

        # Replace numbers with {int}
        result = re.sub(r'\b\d+\b', '{int}', result)

        return result

    def _to_method_name(self, keyword: str, text: str) -> str:
        """Convert step text to valid C# method name"""
        # Remove non-alphanumeric, split on spaces
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        words = [w.capitalize() for w in words if w]

        method_name = keyword + ''.join(words)
        return method_name or f"{keyword}Step"

    def _build_file(self, method_stubs: List[str]) -> str:
        """Build complete StepDefinitions.cs file"""
        # Use component name for namespaces
        tests_namespace = f"{self.component_name}.Tests"
        source_namespace = self.component_name

        file_content = f'''using Reqnroll;
using Xunit;
using System;
using System.Collections.Generic;
using {source_namespace};

namespace {tests_namespace}
{{
    [Binding]
    public class StepDefinitions
    {{
        private readonly ScenarioContext _context;

        public StepDefinitions(ScenarioContext context)
        {{
            _context = context;
        }}
{"".join(method_stubs)}
    }}
}}
'''
        return file_content
