"""BDD Test Agent: Generate Gherkin test scenarios"""
from llm_client import call_llm


def generate_bdd_tests(domain_logic: str, modernized_code: str, exploration: dict) -> str:
    """
    Generate Gherkin BDD test scenarios.

    Returns:
        Gherkin feature file content
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
    print(f"✅ BDD Agent: Test scenarios generated")
    return result
