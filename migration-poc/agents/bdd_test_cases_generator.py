"""BDD Test Agent: Generate Gherkin test scenarios"""
import re
from llm_client import call_llm


def _validate_gherkin_syntax(content: str) -> str:
    """Validate and fix invalid Gherkin keywords in step lines"""
    lines = content.split('\n')
    fixed_lines = []

    # Invalid keywords that LLM sometimes uses instead of Given/When/Then/And/But
    invalid_keywords = {
        'Without': 'And',
        'While': 'And',
        'However': 'And',
        'Therefore': 'Then',
        'If': 'And',
        'Unless': 'And',
        'Also': 'And',
        'Furthermore': 'And',
    }

    for line in lines:
        stripped = line.lstrip()
        # Check if line starts with an invalid keyword
        for invalid, replacement in invalid_keywords.items():
            if stripped.startswith(invalid + ' '):
                # Replace invalid keyword with valid one
                indent = line[:len(line) - len(stripped)]
                rest = stripped[len(invalid):].lstrip()
                line = f"{indent}{replacement} {rest}"
                break
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def _strip_markdown_blocks(content: str) -> str:
    """Remove markdown code block syntax and trailing prose from Gherkin content"""
    # Remove ```gherkin...``` or ```feature...``` blocks
    content = re.sub(r'```\s*(gherkin|feature)\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)
    content = re.sub(r'\n```\s*\n', '\n', content)

    lines = content.split('\n')

    # Remove leading prose before Feature: keyword
    feature_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('Feature:'):
            feature_idx = i
            break

    if feature_idx > 0:
        lines = lines[feature_idx:]

    # Find last valid Gherkin line and truncate after it
    # Valid Gherkin: keywords, table rows, comments, empty lines, or indented continuations
    last_valid_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_gherkin = (
            stripped.startswith(('Feature:', 'Background:', 'Scenario:', 'Scenario Outline:',
                                'Given ', 'When ', 'Then ', 'And ', 'But ', 'Examples:',
                                '|', '@', '#', '"""')) or
            stripped == '' or
            line.startswith((' ', '\t'))  # Indented lines (table cells, continuations)
        )
        if is_gherkin:
            last_valid_idx = i
        elif last_valid_idx >= 0 and stripped and not stripped.startswith(('Examples:', '|')):
            # Found non-Gherkin prose after valid content
            break

    if last_valid_idx >= 0:
        lines = lines[:last_valid_idx + 1]

    return '\n'.join(lines).strip()


def generate_bdd_tests(domain_logic: str, modernized_code: str, exploration: dict) -> str:
    """
    Generate Gherkin BDD test scenarios.

    Returns:
        Gherkin feature file content (plain text, no markdown blocks)
    """
    prompt = f"""
Write comprehensive Gherkin BDD test scenarios for this medical domain logic.

DOMAIN LOGIC:
```csharp
{domain_logic}
```

MODERNIZED SERVICE:
```csharp
{modernized_code}
```

STRICT GHERKIN SYNTAX RULES:
- ONLY use these step keywords: Given, When, Then, And, But, Background, Scenario, Scenario Outline, Examples, Feature
- NEVER use: Without, While, If, Unless, However, Therefore, or any other prose-like keywords
- Each step MUST start with Given/When/Then/And/But
- Multi-line steps use proper indentation and line continuation (not new keywords)
- Tables use | Field | Value | syntax with proper alignment

PARAMETER TYPES IN SCENARIO OUTLINES:
- VALID parameter types in Scenario Outline Examples: string, integer, decimal, boolean
- For Cucumber Expressions in step definitions: ONLY use {string}, {int}, {float}, {double}
- Boolean values must be passed as strings in Examples: | result | true | or | result | false |
- DO NOT use {bool}, {boolean}, or any other unsupported types
- NEVER put parameter types like {bool} directly in step text

Generate a .feature file that tests:
1. Happy path: Valid data recorded successfully
2. Validation failures: Each business rule enforcement
3. Edge cases: Boundary values, empty inputs
4. Compliance: CFR Part 11 audit trail recording
5. Error scenarios: What happens when validation fails?

Include:
- Feature description
- Scenario outline for parameterized tests
- Clear Given/When/Then steps with AND/BUT for continuation

CRITICAL: Only use valid Gherkin keywords. Never add prose explanations as new step lines.

Output format:
```gherkin
Feature: Medical Observation Recording
  As a lab technician
  I want to record patient observations
  So that they are tracked and compliant

  Background:
    Given the system is initialized
    And audit logging is enabled

  Scenario: Valid observation is recorded
    Given a patient with ID "PAT-001"
    And an observation with valid data
    When I record the observation
    Then the observation should be saved
    And an audit trail entry should be created

  Scenario Outline: Validation rules are enforced
    Given an observation with <field> value <value>
    When I try to record the observation
    Then the request should fail with error <error>
```
"""

    system = """You are a Gherkin/BDD expert specializing in medical software.

CRITICAL RULES:
1. Write ONLY valid Gherkin syntax - Given, When, Then, And, But keywords ONLY
2. Never use prose words like Without, While, However, Therefore as step starters
3. Each line must be a proper step or table row
4. Multi-line concepts use And/But continuation, never new keywords
5. Generate valid, parseable feature files

Cover compliance (21 CFR Part 11) concerns. Make scenarios specific to the domain."""

    print(f"📝 BDD Agent: Generating test scenarios...")
    result = call_llm(prompt, system, max_tokens=2500)
    result = _strip_markdown_blocks(result)
    result = _validate_gherkin_syntax(result)
    print(f"✅ BDD Agent: Test scenarios generated")
    return result
