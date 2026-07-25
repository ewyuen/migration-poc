"""Modernizer Agent: Translate legacy code to modern .NET 10"""
from llm_client import call_llm


def modernize_code(legacy_code: str, domain_logic: str, exploration: dict) -> str:
    """
    Translate legacy C# to modern .NET 10 architecture.

    Returns:
        Modern .NET 10 C# code
    """
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

Generate modern .NET 10 code that:
1. Uses extracted domain logic (don't rewrite it)
2. Follows SOLID principles
3. Uses dependency injection
4. Implements async/await patterns
5. Uses records for immutable DTOs
6. Includes proper error handling
7. Targets .NET 10 specifically

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
"""

    system = """You are a .NET 10 architect.
Modernize legacy code to cloud-native, containerized patterns.
Use latest C# 14 features and async-first design.
Ensure medical domain compliance is preserved."""

    print(f"🚀 Modernizer: Translating to .NET 10...")
    result = call_llm(prompt, system, max_tokens=3000)
    print(f"✅ Modernizer: Code modernized")
    return result
