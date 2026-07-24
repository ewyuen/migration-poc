"""Explorer Agent: Analyze legacy code and plan refactoring"""
from llm_client import call_llm_json
import json


def explore_code(legacy_code: str, component_name: str) -> dict:
    """
    Analyze legacy C# component.

    Returns:
        Dictionary with exploration results
    """
    prompt = f"""
Analyze this legacy C# medical component and provide a detailed refactoring plan.

COMPONENT: {component_name}

CODE:
```csharp
{legacy_code}
```

Provide analysis in JSON format with:
1. **current_state**: What does this code do?
2. **patterns_used**: What design patterns/anti-patterns?
3. **pain_points**: List of maintainability issues
4. **compliance_concerns**: CFR Part 11 related issues
5. **responsibilities**: List of distinct responsibilities
6. **refactoring_opportunities**: Specific improvements
7. **subtasks**: What should other agents do?

Format as valid JSON only (no markdown, no code blocks).
"""

    system = """You are an expert C# architect analyzing legacy medical software.
Identify code smells, maintainability issues, and compliance concerns.
Be specific and actionable.
Return only valid JSON."""

    print(f"🔍 Explorer: Analyzing {component_name}...")
    result = call_llm_json(prompt, system, max_tokens=2500)
    print(f"✅ Explorer: Analysis complete")
    return result
