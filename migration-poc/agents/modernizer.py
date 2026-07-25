"""Modernizer Agent: Translate legacy code to modern .NET 10"""
from typing import Optional, Dict, List
from llm_client import call_llm


def generate_csproj(component_name: str) -> str:
    """
    Generate a .NET 10 csproj file for the modernized component with comprehensive NuGet packages.

    Args:
        component_name: Name of the component

    Returns:
        Generated csproj content as string
    """
    csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <RootNamespace>{component_name}</RootNamespace>
    <AssemblyName>{component_name}</AssemblyName>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
  </PropertyGroup>

  <ItemGroup>
    <!-- Dependency Injection and Configuration -->
    <PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.DependencyInjection.Abstractions" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Options" Version="8.0.2" />
    <PackageReference Include="Microsoft.Extensions.Logging" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Abstractions" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration.Abstractions" Version="8.0.0" />

    <!-- Validation -->
    <PackageReference Include="FluentValidation" Version="11.9.0" />

    <!-- Data Access -->
    <PackageReference Include="System.Data.SqlClient" Version="4.8.6" />

    <!-- Testing and Mocking -->
    <PackageReference Include="Moq" Version="4.20.70" />
    <PackageReference Include="xunit" Version="2.9.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.8.2">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="FluentAssertions" Version="6.12.0" />

    <!-- Mapping (Optional - uncomment if needed) -->
    <!-- <PackageReference Include="AutoMapper" Version="12.0.1" /> -->
  </ItemGroup>
</Project>"""
    return csproj_content


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

    # Add attempt context if provided (structured feedback with line info)
    if attempt_context:
        attempt = attempt_context.get("attempt", 1)
        max_attempts = attempt_context.get("max_attempts", 3)
        error_feedback = attempt_context.get("error_feedback", "No specific errors")
        prompt += f"""
ATTEMPT {attempt} OF {max_attempts} - REGENERATE TO FIX THESE LINES:

{error_feedback}

INSTRUCTIONS FOR THIS REGENERATION:
1. Review the failed lines above
2. Regenerate the ENTIRE code, but focus on fixing those specific lines
3. Preserve the overall structure and logic
4. Do NOT add new logic - only fix the compilation errors
5. The regenerated code MUST compile successfully

When regenerating, think about:
- Missing imports for types used on failed lines
- Incorrect namespace references
- Missing method definitions or parameters
- Type mismatches or casting issues
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
9. Generate MOCK/STUB implementations for any missing interfaces or dependencies

CRITICAL - MULTIPLE FILES FORMAT:
You MUST generate MULTIPLE separate files. Mark each file with this exact format:
```
// ============ FILE: ClassName.cs ============
[C# code for ClassName]
```

IMPORTANT - Mock Missing Dependencies:
- If code references interfaces that don't exist, GENERATE mock implementations
- Mark mocks with "// TODO: Implement proper <InterfaceName>" comments
- Mock implementations should have simple implementations that compile
- Example: mock repositories return empty lists or default values
- Example: mock validators accept all input or validate specific fields
- Example: mock loggers do nothing (Console.WriteLine is acceptable)
- ALL mocked interfaces must have at least a basic working implementation

Output ONLY C# code (no explanations or markdown).

FILE STRUCTURE (generate all of these):
1. // ============ FILE: Models.cs ============
   - Domain entities (records/classes)
2. // ============ FILE: Interfaces.cs ============
   - Repository, Service, and other interfaces
3. // ============ FILE: Services.cs ============
   - Service implementations with DI
4. // ============ FILE: Repositories.cs ============
   - Repository implementations (mock if original not provided)
5. // ============ FILE: Validators.cs ============
   - FluentValidation validators (if needed)
6. // ============ FILE: MockImplementations.cs ============
   - Any other mock/stub implementations for missing dependencies

CRITICAL REQUIREMENTS:
- Generate EXACTLY this many separate files (one FILE: marker per logical unit)
- ALL referenced interfaces MUST be defined (either in Interfaces.cs or as mocks)
- ALL referenced classes MUST be defined or available
- The generated code MUST compile without errors
- All files must be syntactically correct C# 14 code
- Every dependency the code uses must be available in the csproj packages
"""

    system = """You are a .NET 10 architect expert in generating complete, compilable code.
Modernize legacy code to cloud-native, containerized patterns.
Use latest C# 14 features and async-first design.
Ensure medical domain compliance is preserved.

CRITICAL - MOCK GENERATION RULES:
- If code references an interface/class that is NOT defined -> GENERATE a mock
- Every mock must have at least a minimal working implementation
- Mark all mocks with "// TODO: Implement proper <Name>" above the class
- Examples of valid mocks:
  * Repository that returns empty List<T>() or default values
  * Service that does minimal work (Console.WriteLine, return null)
  * Validator that always returns ValidationResult.Success
  * Logger that does nothing (mock ILogger)
- Without these mocks, the code WILL NOT COMPILE

CRITICAL - FILE GENERATION:
- Generate EXACTLY 6 files using this marker format:
  // ============ FILE: Models.cs ============
  // ============ FILE: Interfaces.cs ============
  // ============ FILE: Services.cs ============
  // ============ FILE: Repositories.cs ============
  // ============ FILE: Validators.cs ============
  // ============ FILE: MockImplementations.cs ============
- Each file must have a namespace: namespace <ComponentName> { ... }
- Use /// XML comments for public members

CRITICAL - COMPILATION:
- Every generated file must be syntactically correct C# 14
- Every reference must be defined (if not in extracted logic, mock it)
- Use only classes/interfaces from System.* or packages in csproj
- DO NOT use undefined types
- Ensure ALL code you generate compiles without errors"""

    attempt_num = attempt_context.get("attempt", 1) if attempt_context else 1
    print(f"🚀 Modernizer: Translating to .NET 10 (attempt {attempt_num})...")
    result = call_llm(prompt, system, max_tokens=3000)
    print(f"✅ Modernizer: Code modernized")
    return result
