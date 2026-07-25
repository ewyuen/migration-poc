"""Verifier Agent: Validate modernization quality and compliance"""
from llm_client import call_llm_json
import json


def verify_modernization(
    legacy_code: str,
    modernized_code: str,
    domain_logic: str,
    bdd_tests: str
) -> dict:
    """
    Verify that modernized code is correct and compliant.

    Returns:
        Verification report as dictionary
    """
    prompt = f"""
Verify this code modernization for correctness and compliance.

ORIGINAL LEGACY CODE:
```csharp
{legacy_code}
```

EXTRACTED DOMAIN LOGIC:
```csharp
{domain_logic}
```

MODERNIZED CODE:
```csharp
{modernized_code}
```

BDD TEST SCENARIOS:
```gherkin
{bdd_tests}
```

Provide a verification report in JSON with:
1. **behavioral_equivalence**: Does modern code do what legacy code did?
2. **test_coverage**: Are all scenarios covered?
3. **compliance_check**: Is CFR Part 11 preserved?
4. **security_check**: No credentials/PII hardcoded?
5. **performance_analysis**: Any major regressions?
6. **net10_alignment**: Uses .NET 10 features properly?
7. **risks**: Any concerns?
8. **recommendations**: Improvements?
9. **overall_status**: PASS/FAIL/CAUTION

Return only valid JSON.
"""

    system = """You are a code verification expert for medical software.
Carefully check behavioral equivalence, compliance, and security.
Be thorough but fair in assessment."""

    print(f"✔️ Verifier: Validating modernization...")
    result = call_llm_json(prompt, system, max_tokens=2500)
    print(f"✅ Verifier: Verification complete")
    return result
