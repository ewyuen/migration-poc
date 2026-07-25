"""Gherkin Extractor: Extract Given/When/Then steps from comments in C# test files"""
import re
from typing import Dict, List, Tuple, Any, Optional


class GherkinExtractor:
    """Parses C# method body comments to extract Gherkin steps and parameters"""

    def extract_steps_by_section(self, method_body: str) -> Dict[str, List[str]]:
        """
        Extract Given, When, and Then steps from method body comments
        
        Returns:
            Dict with keys: 'given', 'when', 'then' containing lists of step strings.
        """
        lines = method_body.split('\n')
        sections = {'given': [], 'when': [], 'then': []}
        current_section = None

        for line in lines:
            line_stripped = line.strip()
            
            # Check section headers
            if '// Arrange (Given)' in line_stripped or '// Arrange' in line_stripped:
                current_section = 'given'
                continue
            elif '// Act (When)' in line_stripped or '// Act' in line_stripped:
                current_section = 'when'
                continue
            elif '// Assert (Then)' in line_stripped or '// Assert' in line_stripped:
                current_section = 'then'
                continue
            
            # If we are in a section and find a comment line
            if current_section and line_stripped.startswith('//'):
                # Extract the comment text
                step_text = line_stripped.replace('//', '', 1).strip()
                # Skip secondary section labels if any
                if step_text.lower() in ['arrange (given)', 'arrange', 'act (when)', 'act', 'assert (then)', 'assert']:
                    continue
                if step_text:
                    sections[current_section].append(step_text)
                    
        return sections

    def extract_parameters(self, step_text: str) -> List[Dict[str, Any]]:
        """
        Extract parameter values and names/types from a Gherkin step text.
        For example:
          "a user with email 'doctor@clinic.com' and password 'SecurePass123'"
          -> [{'value': 'doctor@clinic.com', 'type': 'string'}, {'value': 'SecurePass123', 'type': 'string'}]
          
          "a patient age 70"
          -> [{'value': '70', 'type': 'int'}]
          
          "medication cost $100.00"
          -> [{'value': '100.00', 'type': 'decimal'}]
        """
        params = []
        
        # 1. Look for single or double quoted strings
        quoted_pattern = r'["\'“]([^"\'”]+)["\'”]'
        quoted_matches = re.finditer(quoted_pattern, step_text)
        for m in quoted_matches:
            val = m.group(1)
            params.append({
                "value": val,
                "type": self.infer_type(val),
                "raw": m.group(0),
                "span": m.span()
            })
            
        # 2. Look for currency values e.g. $100.00 or $50
        currency_pattern = r'\$(\d+(?:\.\d{2})?)\b'
        currency_matches = re.finditer(currency_pattern, step_text)
        for m in currency_matches:
            val = m.group(1)
            params.append({
                "value": val,
                "type": "decimal",
                "raw": m.group(0),
                "span": m.span()
            })
            
        # 3. Look for isolated numeric values (not matched by quoted/currency and not part of words)
        # Avoid matching numbers inside words or quotes
        # We'll filter out matches that overlap with existing parameters
        number_pattern = r'\b(\d+)\b'
        number_matches = re.finditer(number_pattern, step_text)
        for m in number_matches:
            # Check overlap
            start, end = m.span()
            overlap = False
            for p in params:
                p_start, p_end = p["span"]
                if not (end <= p_start or start >= p_end):
                    overlap = True
                    break
            if not overlap:
                val = m.group(1)
                params.append({
                    "value": val,
                    "type": "int",
                    "raw": m.group(0),
                    "span": m.span()
                })
                
        # Sort parameters by their position in the text
        params.sort(key=lambda x: x["span"][0])
        
        # Strip out the span and raw keys for return
        return [{"value": p["value"], "type": p["type"]} for p in params]

    def infer_type(self, val: str) -> str:
        """Infer type of a value string"""
        # Email pattern
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', val):
            return "string"
            
        # Decimal number
        if re.match(r'^\d+\.\d+$', val):
            return "decimal"
            
        # Integer number
        if re.match(r'^\d+$', val):
            return "int"
            
        # Boolean
        if val.lower() in ["true", "false"]:
            return "bool"
            
        return "string"

    def extract_template_variables(self, step_text: str) -> List[str]:
        """Extract template variables like <email> or <password> from step text"""
        return re.findall(r'<([\w-]+)>', step_text)
