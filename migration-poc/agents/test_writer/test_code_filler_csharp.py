"""Test Code Filler C#: Replaces placeholder test bodies with mapped C# implementations"""
import re
from typing import Dict, List, Tuple, Any, Optional
from agents.test_writer.gherkin_extractor import GherkinExtractor
from agents.test_writer.gherkin_code_mapper import GherkinCodeMapper


class TestCodeFillerCSharp:
    """Fills the body of C# test methods with executable test code"""

    def __init__(self, mapper: GherkinCodeMapper):
        self.extractor = GherkinExtractor()
        self.mapper = mapper

    def fill_test_method(self, method_name: str, method_body: str, header: str) -> str:
        """
        Parses comments from the skeleton method body, maps them to C#,
        and returns the filled method body.
        """
        # Determine if it's a theory and get parameter names
        is_theory = "[Theory]" in header
        
        # Extract parameters from header signature e.g. public void MyTheory(string age, string amount)
        sig_match = re.search(r'public\s+void\s+\w+\s*\((.*?)\)', header, re.DOTALL)
        if not sig_match:
            sig_match = re.search(r'public\s+async\s+Task\s+\w+\s*\((.*?)\)', header, re.DOTALL)
            
        method_params = []
        if sig_match:
            params_str = sig_match.group(1).strip()
            if params_str:
                for p in params_str.split(','):
                    parts = p.strip().split()
                    if len(parts) >= 2:
                        method_params.append(parts[1].strip())

        # Extract steps grouped by section
        steps = self.extractor.extract_steps_by_section(method_body)
        
        # We need to determine the target method for assertion type mapping
        # Let's check which service operations are mentioned in the When steps
        target_method = ""
        for when_step in steps['when']:
            if "authenticate" in when_step.lower() or "log in" in when_step.lower():
                target_method = "AuthenticateUserAsync"
                break
            elif "discount" in when_step.lower() or "calculate" in when_step.lower():
                target_method = "CalculateDiscountAsync"
                break
            elif "validate" in when_step.lower():
                target_method = "ValidateSessionTokenAsync"
                break

        # Map steps to C# code lines
        arrange_code = []
        for step in steps['given']:
            arrange_code.extend(self.mapper.map_arrange_step(step, is_theory, method_params))
            
        act_code = []
        for step in steps['when']:
            act_code.extend(self.mapper.map_act_step(step, is_theory, method_params))
            
        assert_code = []
        for step in steps['then']:
            assert_code.extend(self.mapper.map_assert_step(step, is_theory, method_params, target_method))

        # Scan for required but undeclared variables to ensure compilability
        all_code_text = "\n".join(act_code + assert_code)
        
        # Check declarations in arrange_code
        declared_vars = set()
        for line in arrange_code:
            match = re.search(r'var\s+(\w+)\s*=', line)
            if match:
                declared_vars.add(match.group(1))
                
        # Also method params are declared
        for p in method_params:
            declared_vars.add(p)
            
        # Defaults to inject if used but not declared
        defaults = {
            "email": 'var email = "doctor@clinic.com";',
            "password": 'var password = "SecurePass123!";',
            "token": 'var token = "valid-token";',
            "age": 'var age = 30;',
            "amount": 'var amount = 100.00m;'
        }
        
        injected_arranges = []
        for var_name, decl in defaults.items():
            if re.search(r'\b' + var_name + r'\b', all_code_text):
                if var_name not in declared_vars:
                    injected_arranges.append(decl)
                    declared_vars.add(var_name)

        # Re-assemble the method body with indentation
        new_lines = []
        
        # 1. Arrange Section
        new_lines.append("            // Arrange (Given)")
        for step in steps['given']:
            new_lines.append(f"            // {step}")
            
        # Add injected default arrangements
        for line in injected_arranges:
            new_lines.append(f"            {line}")
            
        # Add generated arrange code
        for line in arrange_code:
            # Skip repeating comment lines
            if not line.strip().startswith("// Given:"):
                new_lines.append(f"            {line}")
                
        new_lines.append("            var systemUnderTest = _fixture.CreateSystemUnderTest();\n")

        # 2. Act Section
        new_lines.append("            // Act (When)")
        for step in steps['when']:
            new_lines.append(f"            // {step}")
            
        # Add generated act code
        for line in act_code:
            if not line.strip().startswith("// When:"):
                new_lines.append(f"            {line}")
        new_lines.append("")

        # 3. Assert Section
        new_lines.append("            // Assert (Then)")
        for step in steps['then']:
            new_lines.append(f"            // {step}")
            
        # Add generated assert code
        for line in assert_code:
            if not line.strip().startswith("// Then:") and not line.strip().startswith("// TODO: Assert:"):
                new_lines.append(f"            {line}")
            elif line.strip().startswith("// TODO:"):
                new_lines.append(f"            {line}")

        return "\n".join(new_lines)
