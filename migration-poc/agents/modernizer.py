"""Modernizer Agent: Self-healing migration to .NET 10 with compilation verification"""
import os
import re
import json
import subprocess
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from pathlib import Path
from llm_client import call_llm


@dataclass
class CompilerError:
    file_path: str
    line: int
    column: int
    error_code: str
    message: str


MIGRATION_HINTS = {
    "CS0103": "ConfigurationManager is from System.Configuration. Replace with IConfiguration dependency injection pattern or add NuGet: System.Configuration.ConfigurationManager.",
    "CS0246": "Legacy System.Web types not available in .NET 10. Use ASP.NET Core equivalents (e.g., Microsoft.AspNetCore.Http).",
    "CS0117": "Configuration APIs changed. Use IConfiguration injected via DI instead of WebConfigurationManager.",
    "CS1061": "HttpContext API differs. In ASP.NET Core, use context.Request/Response properties directly.",
    "CS0234": "Missing namespace. Check if type moved to different NuGet package in modern .NET.",
    "CS0619": "API is obsolete. Use modern equivalent (check documentation).",
    "CS1503": "Parameter type mismatch. Verify method signatures match modern .NET APIs.",
    "CS0535": "Interface member not implemented. Add all required members.",
    "CS0436": "Type conflict (likely generated assembly attributes). Remove duplicate definitions.",
    "CS0649": "Field never assigned. Initialize in constructor or mark nullable.",
}


class DotNetMigrationAgent:
    def __init__(self, output_dir: str, csproj_name: str, target_framework: str = "net10.0", max_retries: int = 4):
        self.output_dir = output_dir
        self.csproj_name = csproj_name
        self.target_framework = target_framework
        self.max_retries = max_retries
        self.csproj_path = os.path.join(output_dir, csproj_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def generate_csproj(self, assembly_name: str, root_namespace: str) -> None:
        """Generate SDK-style .csproj for net10.0"""
        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>{self.target_framework}</TargetFramework>
    <AssemblyName>{assembly_name}</AssemblyName>
    <RootNamespace>{root_namespace}</RootNamespace>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Extensions.Configuration" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration.Abstractions" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="10.0.0" />
    <PackageReference Include="System.Configuration.ConfigurationManager" Version="8.0.1" />
  </ItemGroup>

</Project>
"""
        with open(self.csproj_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)
        print(f"📦 Generated: {self.csproj_path}")

    def run_dotnet_restore(self) -> bool:
        """Restore NuGet packages before building"""
        cmd = ["dotnet", "restore", self.csproj_path]
        print(f"   📦 Restoring NuGet packages...")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"   ✓ Packages restored")
                return True
            else:
                print(f"   ❌ Restore failed:")
                print(f"      {result.stderr[:300]}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ❌ Restore timeout (60s)")
            return False
        except Exception as e:
            print(f"   ❌ Restore error: {e}")
            return False

    def run_dotnet_build(self) -> tuple[bool, List[CompilerError]]:
        """Restore packages, then execute dotnet build and parse compiler errors"""
        # First: restore packages
        restore_ok = self.run_dotnet_restore()

        # Then: build
        cmd = ["dotnet", "build", self.csproj_path, "-c", "Debug"]
        print(f"   🔨 Building...")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, []

            # Parse errors
            errors = self._parse_compiler_errors(result.stdout + result.stderr)

            # Show raw output if no errors parsed (helps debug)
            if not errors and result.stderr:
                print(f"   ⚠️  Build failed but no CS errors parsed. Raw output:")
                print(f"      {result.stderr[:500]}")

            return False, errors
        except subprocess.TimeoutExpired:
            print(f"   ❌ Build timeout (60s)")
            return False, [CompilerError("", 0, 0, "TIMEOUT", "Build timeout after 60s")]
        except Exception as e:
            print(f"   ❌ Build error: {e}")
            return False, [CompilerError("", 0, 0, "ERROR", str(e))]

    def _parse_compiler_errors(self, build_output: str) -> List[CompilerError]:
        """Parse MSBuild error lines: path(line,col): error CSxxxx: message"""
        pattern = r"(.*?)\((\d+),(\d+)\):\s+error\s+(CS\d+):\s+(.*?)(?:\s*\[|$)"
        errors = []
        for line in build_output.splitlines():
            match = re.search(pattern, line)
            if match:
                file_path, line_num, col_num, code, msg = match.groups()
                errors.append(CompilerError(
                    file_path=file_path.strip(),
                    line=int(line_num),
                    column=int(col_num),
                    error_code=code.strip(),
                    message=msg.strip()
                ))
        return errors

    def generate_repair_prompt(self, file_content: str, errors: List[CompilerError]) -> str:
        """Format compiler errors with migration hints into LLM prompt"""
        error_context = ""
        for err in errors:
            hint = MIGRATION_HINTS.get(err.error_code, "Review .NET 10 API documentation.")
            error_context += (
                f"• Line {err.line}, Col {err.column} [{err.error_code}]: {err.message}\n"
                f"  Hint: {hint}\n"
            )

        prompt = f"""You are a .NET modernization expert. Fix ALL compilation errors in this .NET 10 C# code.

### COMPILATION ERRORS:
{error_context}

### CURRENT CODE:
```csharp
{file_content}
```

### INSTRUCTIONS:
1. Fix EVERY error listed above.
2. Preserve business logic and class names (do not rename).
3. Use modern .NET 10 patterns: IConfiguration DI, async/await, records.
4. Output ONLY valid C# code in a ```csharp block.
5. No explanations, just code.
"""
        return prompt

    def _extract_csharp_code(self, response: str) -> str:
        """Extract C# code from markdown response"""
        pattern = r"```csharp\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

    def migrate_file(
        self,
        output_filename: str,
        initial_code: str,
        llm_call_func: Callable[[str], str],
        failure_log_dir: Optional[str] = None
    ) -> str:
        """Self-healing migration loop: compile -> parse errors -> repair -> retry"""
        print(f"\n{'='*70}")
        print(f"🚀 Migrating: {output_filename}")
        print(f"{'='*70}")

        output_filepath = os.path.join(self.output_dir, output_filename)

        # Step 1: Initial migration
        initial_prompt = f"""Modernize this legacy .NET Framework C# code to .NET 10.

TARGET GOALS:
1. Replace System.Configuration with IConfiguration DI
2. Use async/await where applicable
3. Apply modern C# 14 patterns (records, file-scoped namespaces, etc.)
4. Preserve business logic and class names
5. Target .NET 10 (remove .NET Framework dependencies)

LEGACY CODE:
```csharp
{initial_code}
```

Output ONLY the modernized C# code in a ```csharp block."""

        print(f"📝 Calling LLM for initial migration...")
        response = llm_call_func(initial_prompt)
        current_code = self._extract_csharp_code(response)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(current_code)
        print(f"✓ Initial code written to {output_filepath}")

        # Step 2: Self-healing compilation loop
        for attempt in range(1, self.max_retries + 1):
            print(f"\n🔨 Compilation Attempt {attempt}/{self.max_retries}...")
            success, errors = self.run_dotnet_build()

            if success:
                print(f"✅ BUILD SUCCEEDED! {output_filename} is ready for .NET 10.")
                return current_code

            # Filter errors for this file
            file_errors = [e for e in errors if os.path.basename(e.file_path) == output_filename]
            if not file_errors:
                file_errors = errors  # Use all if file filtering didn't match

            print(f"❌ {len(file_errors)} error(s) found. Calling LLM to repair...")
            for err in file_errors[:3]:  # Show first 3 errors
                print(f"   [{err.error_code}] Line {err.line}: {err.message[:60]}")

            # Repair via LLM
            repair_prompt = self.generate_repair_prompt(current_code, file_errors)
            response = llm_call_func(repair_prompt)
            current_code = self._extract_csharp_code(response)

            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(current_code)
            print(f"   → Attempt {attempt} code updated. Retrying...")

        # Max retries exceeded - preserve files and log errors
        print(f"\n❌ Migration failed after {self.max_retries} attempts.")
        print(f"📁 Output files preserved in: {self.output_dir}")
        print(f"📝 Latest code in: {output_filepath}")

        if failure_log_dir:
            self._log_failure(output_filename, errors, failure_log_dir)
            print(f"📋 Error log saved")

        # Show final errors for debugging
        if errors:
            print(f"\nFinal compilation errors:")
            for err in errors[:5]:
                print(f"  [{err.error_code}] Line {err.line}: {err.message}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")

        raise RuntimeError(f"Migration failed for {output_filename} after {self.max_retries} retries. Files preserved in {self.output_dir}")

    def _log_failure(self, filename: str, errors: List[CompilerError], log_dir: str) -> None:
        """Log failure details for debugging"""
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(log_dir, "migration_failure.json")

        log_entry = {
            "filename": filename,
            "errors": [
                {
                    "code": e.error_code,
                    "line": e.line,
                    "message": e.message
                }
                for e in errors
            ],
            "timestamp": str(__import__("datetime").datetime.now().isoformat())
        }

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)
        print(f"📋 Failure log: {log_file}")


def modernize_code(
    legacy_code: str,
    domain_logic: str,
    exploration: dict,
    output_dir: Optional[str] = None,
    csproj_name: Optional[str] = None,
    output_filename: Optional[str] = None,
    target_framework: str = "net10.0",
    failure_log_dir: Optional[str] = None
) -> str:
    """
    Modernize legacy C# code to .NET 10.

    If output_dir and csproj_name provided, uses self-healing agent with compilation verification.
    Otherwise falls back to single-pass LLM modernization (legacy mode).

    Args:
        legacy_code: Original C# code to modernize
        domain_logic: Domain logic patterns (for context)
        exploration: Exploration results (for context)
        output_dir: Output directory for compiled project (enables self-healing)
        csproj_name: Name of .csproj file (e.g., "TestService.csproj")
        output_filename: Original filename to preserve (e.g., "AuthenticationService.cs")
        target_framework: Target .NET framework (default "net10.0")
        failure_log_dir: Directory to log failures
    """

    # Self-healing mode (with compilation)
    if output_dir and csproj_name:
        if not output_filename:
            output_filename = "ModernService.cs"

        agent = DotNetMigrationAgent(
            output_dir=output_dir,
            csproj_name=csproj_name,
            target_framework=target_framework,
            max_retries=4
        )
        agent.generate_csproj("ModernService", "ModernService")
        result = agent.migrate_file(
            output_filename=output_filename,
            initial_code=legacy_code,
            llm_call_func=lambda prompt: call_llm(prompt, "You are a .NET 10 modernization expert.", max_tokens=3000),
            failure_log_dir=failure_log_dir
        )
        return result

    # Legacy single-pass mode (backward compatibility)
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
"""

    system = """You are a .NET 10 architect.
Modernize legacy code to cloud-native, containerized patterns.
Use latest C# 14 features and async-first design.
Ensure medical domain compliance is preserved."""

    print(f"🚀 Modernizer: Translating to .NET 10...")
    result = call_llm(prompt, system, max_tokens=3000)
    print(f"✅ Modernizer: Code modernized")
    return result
