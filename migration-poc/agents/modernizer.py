"""Modernizer Agent: Translate legacy code to modern .NET 10"""
from typing import Optional, Dict, List
from llm_client import call_llm


def modernize_code(
    legacy_code: str,
    domain_logic: str,
    exploration: dict,
    feedback_errors: Optional[List[Dict]] = None,
    attempt_context: Optional[Dict] = None
) -> str:
    """
    Translate legacy C# to modern .NET 10 architecture.

    Args:
        legacy_code: The legacy code to modernize
        domain_logic: Extracted domain logic to reuse
        exploration: Exploration results
        feedback_errors: Optional compilation errors from previous attempt (for self-healing)
        attempt_context: Optional context about attempt number and max attempts

    Returns:
        Modern .NET 10 C# code
    """
    # Build prompt with optional feedback
    prompt = f"""
Translate this legacy C# code to modern .NET 10 architecture.

LEGACY CODE:
```csharp
{legacy_code}
```

EXTRACTED DOMAIN LOGIC (reuse this):
```csharp
{domain_logic}
```
"""

    # Add attempt context if provided
    if attempt_context:
        attempt = attempt_context.get("attempt", 1)
        max_attempts = attempt_context.get("max_attempts", 3)
        prompt += f"""
COMPILATION FEEDBACK - ATTEMPT {attempt} OF {max_attempts}:
The previous attempt had compilation errors. Fix these specific issues:
{attempt_context.get("previous_errors", "No specific errors")}

Focus on fixing only the compilation errors listed above.
"""

    prompt += """

Generate modern .NET 10 code that:
1. Uses extracted domain logic (don't rewrite it)
2. Follows SOLID principles
3. Uses dependency injection
4. Implements async/await patterns
5. Uses records for immutable DTOs
6. Includes proper error handling
7. Targets .NET 10 specifically
8. MUST compile successfully when verified in isolation

Output ONLY C# code (no explanations).

Structure:
1. Domain entity (record type)
2. Service class (with DI)
3. Repository interface
4. Validators (FluentValidation style)

Example:
```csharp
namespace MedicalApp.Services.Observations
{{
    public record ObservationDto(
        string Id,
        string PatientId,
        ObservationData Data,
        DateTime RecordedAt);

    public class ObservationService
    {{
        public ObservationService(IObservationRepository repo, IValidator<ObservationData> validator)
        {{
            // DI
        }}

        public async Task<Result<ObservationDto>> RecordObservationAsync(...)
        {{
            // Modern async implementation
        }}
    }}
}}
```

CRITICAL: The generated code MUST compile without errors.
"""

    system = """You are a .NET 10 architect.
Modernize legacy code to cloud-native, containerized patterns.
Use latest C# 14 features and async-first design.
Ensure medical domain compliance is preserved.
Most importantly: ensure generated code compiles in isolation."""

    attempt_num = attempt_context.get("attempt", 1) if attempt_context else 1
    print(f"🚀 Modernizer: Translating to .NET 10 (attempt {attempt_num})...")
    result = call_llm(prompt, system, max_tokens=3000)
    print(f"✅ Modernizer: Code modernized")
    return result
