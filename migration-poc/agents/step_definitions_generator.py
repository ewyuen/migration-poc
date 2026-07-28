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

        Tracks the effective step type per scenario block so that And/But steps
        inherit the type of the preceding Given/When/Then (as Reqnroll does at
        runtime), instead of defaulting everything to Given.

        Returns list of dicts: {keyword, text, line_number, normalized_keyword, examples}
        """
        steps = []
        lines = gherkin_content.split('\n')

        last_primary = None
        examples_header: Optional[List[str]] = None
        examples_rows: List[Dict[str, str]] = []
        in_examples = False
        block_steps: List[Dict] = []

        def flush_block():
            # Backfill all Examples rows (only known once we've reached the
            # Examples: table, which appears after the steps in source order).
            # All rows (not just the first) are kept so type inference can
            # account for a column mixing quoted/bare/numeric values.
            for s in block_steps:
                s['examples_rows'] = list(examples_rows)
            steps.extend(block_steps)

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Reset step-type tracking at the start of each scenario block
            if stripped.startswith(('Scenario:', 'Scenario Outline:', 'Background:')):
                flush_block()
                block_steps = []
                last_primary = None
                examples_rows = []
                examples_header = None
                in_examples = False
                continue

            if stripped.startswith('Examples:'):
                in_examples = True
                examples_header = None
                continue

            if in_examples and stripped.startswith('|'):
                cells = [c.strip() for c in stripped.strip('|').split('|')]
                if examples_header is None:
                    examples_header = cells
                else:
                    examples_rows.append(dict(zip(examples_header, cells)))
                continue

            # A table attached directly to a step (not under Examples:) is a
            # Gherkin DataTable. Reqnroll passes it as a `Table` argument to the
            # bound method, so the preceding step needs an extra parameter.
            if stripped.startswith('|') and block_steps:
                block_steps[-1]['has_table'] = True
                continue

            match = re.match(r'^(Given|When|Then|And|But)\s+(.+)$', stripped)
            if match:
                keyword = match.group(1)
                text = match.group(2)

                if keyword in ('Given', 'When', 'Then'):
                    last_primary = keyword
                    normalized = keyword
                else:
                    # And/But inherit the effective type of the preceding primary step
                    normalized = last_primary or 'Given'

                block_steps.append({
                    'keyword': keyword,
                    'text': text,
                    'line_number': i,
                    'normalized_keyword': normalized,
                    'examples_rows': [],
                    'has_table': False,
                })

        flush_block()
        return steps


class ParameterTypeInferencer:
    """Infer Cucumber Expression types from step text"""

    def infer_params(self, step_text: str, examples_rows: Optional[List[Dict[str, str]]] = None) -> List[Tuple[str, str, int]]:
        """
        Infer parameters from step text, in left-to-right order of appearance.

        Handles three token kinds:
        - Quoted strings -> {string}
        - Scenario Outline placeholders <name> -> type inferred from ALL Examples rows
          for that column (falls back to {word} if values mix quoted/bare/non-numeric
          forms, since {word} matches any non-whitespace token and {string} only
          matches text with literal surrounding quotes)
        - Bare numbers -> {int} / {float}

        Returns list of (param_name, param_type, start_pos) tuples, sorted by position.
        """
        examples_rows = examples_rows or []
        params = []

        for match in re.finditer(r'"([^"]*)"', step_text):
            name = self._sanitize_param_name(match.group(1)) or f"value{match.start()}"
            params.append((name, 'string', match.start()))

        for match in re.finditer(r'<(\w+)>', step_text):
            placeholder_name = match.group(1)
            column_values = [row[placeholder_name] for row in examples_rows if placeholder_name in row]
            param_type = self._infer_column_type(column_values)
            params.append((self._sanitize_param_name(placeholder_name), param_type, match.start()))

        for match in re.finditer(r'\b\d+(?:\.\d+)?\b', step_text):
            # Skip numbers that are inside quotes or placeholders already captured
            if any(start <= match.start() < start + len(str(name)) + 2 for name, _, start in params):
                continue
            param_type = 'float' if '.' in match.group(0) else 'int'
            params.append((f"value{len(params)}", param_type, match.start()))

        params.sort(key=lambda p: p[2])
        return params

    def _infer_column_type(self, values: List[str]) -> str:
        """
        Infer a Cucumber Expression type that safely matches every sample value
        in an Examples-table column.

        - All values quoted (e.g. "admin@test.com") -> string
        - All values integers -> int
        - All values integers/decimals -> float
        - Anything else (bare words like null/true/false, or a mix of quoted
          and bare values) -> word, since {word} matches any non-whitespace
          token while {string} requires literal surrounding quotes and would
          fail to match unquoted values.
        """
        if not values:
            return 'string'

        kinds = set()
        for raw in values:
            value = raw.strip()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                kinds.add('quoted')
            elif re.fullmatch(r'-?\d+', value):
                kinds.add('int')
            elif re.fullmatch(r'-?\d+\.\d+', value):
                kinds.add('float')
            else:
                kinds.add('bare')

        if kinds <= {'int'}:
            return 'int'
        if kinds <= {'int', 'float'}:
            return 'float'
        if kinds <= {'quoted'}:
            return 'string'
        return 'word'

    def _sanitize_param_name(self, text: str) -> str:
        """Convert step text fragment to valid C# parameter name"""
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

        # Dedupe identical (normalized_keyword, text) pairs across scenarios so we
        # don't emit the same binding method multiple times
        seen = set()
        method_stubs = []
        for step in steps:
            dedupe_key = (step['normalized_keyword'], step['text'])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            method_stubs.append(self._generate_step_method(step))

        skeleton = self._build_file(method_stubs)
        return skeleton

    # Cucumber Expression parameter type -> C# CLR type for method signatures.
    # {word} matches any non-whitespace token but resolves to a string value.
    CUCUMBER_TYPE_TO_CSHARP = {'string': 'string', 'int': 'int', 'float': 'float', 'word': 'string'}

    def _generate_step_method(self, step: Dict) -> str:
        """Generate a single step definition method with Cucumber Expression"""
        keyword = step['normalized_keyword']
        text = step['text']
        examples_rows = step.get('examples_rows', [])

        params = self.inferencer.infer_params(text, examples_rows)

        cucumber_expr = self._build_cucumber_expression(text, params)

        param_parts = [
            f"{self.CUCUMBER_TYPE_TO_CSHARP.get(ptype, 'string')} {pname}" for pname, ptype, _ in params
        ]
        if step.get('has_table'):
            # Reqnroll passes an attached Gherkin DataTable as a final Table argument
            param_parts.append('Table table')
        param_list = ', '.join(param_parts)
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

    def _build_cucumber_expression(self, text: str, params: List[Tuple[str, str, int]]) -> str:
        """Convert step text to Cucumber Expression with {type} placeholders"""
        result = text

        # Replace quoted strings with {string}
        result = re.sub(r'"([^"]*)"', '{string}', result)

        # Replace Scenario Outline placeholders <name> with their inferred type
        param_types_by_name = {}
        for pname, ptype, _ in params:
            param_types_by_name.setdefault(pname, ptype)

        def _replace_placeholder(match: 're.Match') -> str:
            placeholder_name = match.group(1)
            sanitized = re.sub(r'[^a-zA-Z0-9]', '', placeholder_name)
            sanitized = (sanitized[0].lower() + sanitized[1:]) if sanitized else ''
            ptype = param_types_by_name.get(sanitized, 'string')
            return '{' + ptype + '}'

        result = re.sub(r'<(\w+)>', _replace_placeholder, result)

        # Replace bare numbers with {int} or {float}
        result = re.sub(r'\b\d+\.\d+\b', '{float}', result)
        result = re.sub(r'\b\d+\b', '{int}', result)

        # Fix invalid Cucumber Expression types that LLM might generate
        result = re.sub(r'\{bool\}', '{string}', result, flags=re.IGNORECASE)
        invalid_types = [r'\{boolean\}', r'\{date\}', r'\{datetime\}', r'\{uuid\}']
        for invalid_type in invalid_types:
            result = re.sub(invalid_type, '{string}', result, flags=re.IGNORECASE)

        return result

    def _to_method_name(self, keyword: str, text: str) -> str:
        """Convert step text to valid C# method name"""
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        words = [w.capitalize() for w in words if w]

        method_name = keyword + ''.join(words)
        return method_name or f"{keyword}Step"

    def _build_file(self, method_stubs: List[str]) -> str:
        """Build complete StepDefinitions.cs file"""
        tests_namespace = f"{self.component_name}.Tests"
        source_namespace = self.component_name

        file_content = f'''using Reqnroll;
using Xunit;
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
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
