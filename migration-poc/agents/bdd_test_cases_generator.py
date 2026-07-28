"""BDD Test Agent: Generate Gherkin test scenarios"""
import re
from llm_client import call_llm


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

Generate a .feature file that tests:
1. Happy path: Valid data recorded successfully
2. Validation failures: Each business rule enforcement
3. Edge cases: Boundary values, empty inputs
4. Compliance: CFR Part 11 audit trail recording
5. Error scenarios: What happens when validation fails?

Include:
- Feature description
- Scenario outline for parameterized tests
- Clear Given/When/Then steps

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

    system = """You are a BDD/QA expert specializing in medical software.
Write clear, testable Gherkin scenarios.
Cover compliance (21 CFR Part 11) concerns.
Make scenarios specific to the domain."""

    print(f"📝 BDD Agent: Generating test scenarios...")
    result = call_llm(prompt, system, max_tokens=2500)
    result = _strip_markdown_blocks(result)
    print(f"✅ BDD Agent: Test scenarios generated")
    return result
