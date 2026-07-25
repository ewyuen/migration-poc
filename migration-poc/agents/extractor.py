"""Extractor Agent: Extract business logic and domain algorithms"""
from llm_client import call_llm
import json


def extract_domain_logic(legacy_code: str, exploration: dict) -> str:
    """
    Extract pure domain logic from legacy code.

    Returns:
        Modern C# code with extracted domain logic
    """
    exploration_summary = json.dumps(exploration, indent=2)

    prompt = f"""
Extract the core domain logic and business algorithms from this legacy C# code.

LEGACY CODE:
```csharp
{legacy_code}
```

EXPLORATION ANALYSIS:
{exploration_summary}

Generate pure C# functions that:
1. Are FREE of side effects (no I/O, no state)
2. Express domain business rules clearly
3. Are testable and verifiable
4. Include XML documentation with invariants

Output ONLY C# code (no explanations, no markdown).
Use .NET 10 and C# 14 idioms where appropriate.

Example output format:
```csharp
namespace MedicalDomain.Logic
{{
    /// <summary>
    /// Pure domain logic for observation validation
    /// Invariant: Result depends only on inputs
    /// </summary>
    public static class ObservationDomainLogic
    {{
        public static ValidationResult ValidateObservationData(...)
        {{
            // Pure logic here
        }}
    }}
}}
```
"""

    system = """You are a domain-driven design expert.
Extract core business logic into pure, testable functions.
Preserve domain semantics completely.
Use modern C# 14 patterns."""

    print(f"🧬 Extractor: Extracting domain logic...")
    result = call_llm(prompt, system, max_tokens=2000)
    print(f"✅ Extractor: Domain logic extracted")
    return result
