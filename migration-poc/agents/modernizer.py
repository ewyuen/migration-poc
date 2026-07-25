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
    # Compiler errors (CS*)
    "CS0103": "ConfigurationManager is from System.Configuration. Replace with IConfiguration dependency injection pattern or add NuGet: System.Configuration.ConfigurationManager.",
    "CS0246": "Legacy System.Web types not available in .NET 10. Use ASP.NET Core equivalents (e.g., Microsoft.AspNetCore.Http). The Windows Compatibility Pack (Microsoft.Windows.Compatibility) provides many .NET Framework APIs for migration.",
    "CS0117": "Configuration APIs changed. Use IConfiguration injected via DI instead of WebConfigurationManager.",
    "CS1061": "HttpContext API differs. In ASP.NET Core, use context.Request/Response properties directly.",
    "CS0234": "Missing namespace. Check if type moved to different NuGet package in modern .NET. Try adding Microsoft.Windows.Compatibility for .NET Framework compatibility.",
    "CS0619": "API is obsolete. Use modern equivalent (check documentation).",
    "CS1503": "Parameter type mismatch. Verify method signatures match modern .NET APIs.",
    "CS0535": "Interface member not implemented. Add all required members.",
    "CS0436": "Type conflict (likely generated assembly attributes). Remove duplicate definitions.",
    "CS0649": "Field never assigned. Initialize in constructor or mark nullable.",
    # NuGet errors (NU*)
    "NU1202": "Package version does not support the target framework. Update to a newer version that supports net10.0 or adjust .csproj TargetFramework.",
    "NU1605": "Downgrade warning - package requires a newer version. Update the package version to the latest that supports net10.0.",
    # Build failures that couldn't be parsed
    "BUILD_FAILED": "Build failed but specific errors couldn't be parsed. Check the raw error output above. Common issues: missing using statements, wrong API calls, or missing NuGet packages. Ensure all .NET Framework APIs are replaced with .NET 10 equivalents or covered by Microsoft.Windows.Compatibility.",
}


class DotNetMigrationAgent:
    """
    Self-healing .NET migration agent.

    ONLY processes:
    - .cs files (C# source code)
    - .csproj files (project configuration)

    Uses: dotnet build (standard .NET CLI)
    """
    def __init__(self, output_dir: str, csproj_name: str, target_framework: str = "net10.0", max_retries: int = 4):
        self.output_dir = output_dir
        self.csproj_name = csproj_name
        self.target_framework = target_framework
        self.max_retries = max_retries
        self.csproj_path = os.path.join(output_dir, csproj_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def generate_csproj(self, assembly_name: str, root_namespace: str) -> None:
        """Generate SDK-style .csproj for net10.0 with essential packages"""
        # Include packages commonly needed for .NET Framework migrations
        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>{self.target_framework}</TargetFramework>
    <AssemblyName>{assembly_name}</AssemblyName>
    <RootNamespace>{root_namespace}</RootNamespace>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <Deterministic>false</Deterministic>
  </PropertyGroup>

  <ItemGroup>
    <!-- Essential packages for .NET Framework → .NET 10 migration (net10.0 verified) -->
    <PackageReference Include="Microsoft.Windows.Compatibility" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration.Abstractions" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="10.0.0" />
  </ItemGroup>

</Project>
"""
        with open(self.csproj_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)
        print(f"📦 Generated .csproj: {self.csproj_path}")
        print(f"   ✓ Includes essential migration packages (all net10.0 verified)")

    def run_dotnet_build(self) -> tuple[bool, List[CompilerError], Optional[str]]:
        """Execute standard 'dotnet build' and parse ALL errors (restore + compilation)"""
        print(f"   🔨 Building (dotnet build)...")
        cmd = ["dotnet", "build"]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print(f"   ✅ Build succeeded!")
                return True, [], None

            # Capture full output for error analysis
            full_output = result.stdout + result.stderr

            # ALWAYS log the build output for debugging
            print(f"\n   📋 Build output (exit code {result.returncode}):")
            output_lines = full_output.split('\n')
            for line in output_lines[-20:]:  # Show last 20 lines
                if line.strip():
                    print(f"      {line}")

            # Parse errors (both restore and compilation)
            errors = self._parse_compiler_errors(full_output)

            # CRITICAL: If build failed but no errors were parsed, something is wrong with error parsing
            # Create a synthetic error to force LLM to see build failure
            if not errors:
                print(f"\n   ⚠️  Build failed (exit {result.returncode}) but no errors parsed!")
                print(f"   This means our regex patterns don't match the error format.")
                print(f"   Full build output saved below:")
                # Save full output for inspection
                error_snapshot = full_output[:800]
                print(f"\n   --- Full Output Start ---")
                for line in error_snapshot.split('\n'):
                    if line.strip():
                        print(f"   {line}")
                print(f"   --- Full Output End ---\n")

                errors = [CompilerError(
                    file_path="<build-system>",
                    line=0,
                    column=0,
                    error_code="BUILD_FAILED",
                    message=f"Build failed with exit code {result.returncode}. Check .csproj and ensure all package versions are compatible with net10.0. Raw error: {full_output[:400]}"
                )]

            # Check if this is a NuGet/restore error
            # (NuGet errors need .csproj fixes, not code fixes)
            nuget_errors = [e for e in errors if e.error_code.startswith("NU")]
            if nuget_errors:
                # Send NuGet error + .csproj to LLM for fixing
                error_msg = f"{len(nuget_errors)} NuGet error(s):\n"
                for err in nuget_errors:
                    error_msg += f"  [{err.error_code}] {err.message}\n"
                return False, [], error_msg

            # For other errors, return them for LLM to fix code
            return False, errors, None

        except subprocess.TimeoutExpired:
            print(f"   ❌ Build timeout (120s)")
            return False, [CompilerError("", 0, 0, "TIMEOUT", "Build timeout after 120s")], None
        except Exception as e:
            print(f"   ❌ Build error: {e}")
            return False, [CompilerError("", 0, 0, "ERROR", str(e))], None

    def _parse_compiler_errors(self, build_output: str) -> List[CompilerError]:
        """Parse errors: compiler (CSxxxx) and NuGet (NUxxxx) with fallback patterns"""
        errors = []
        seen_codes = set()  # Track which errors we've found to avoid duplicates

        # Pattern 1: Compiler errors - path(line,col): error CSxxxx: message [project]
        cs_pattern = r"(.*?)\((\d+),(\d+)\):\s+error\s+(CS\d+):\s+(.*?)(?:\s*\[|$)"
        # Pattern 2: NuGet errors - path : error NUxxxx: message
        nu_pattern = r"(.*?)\s+:\s+error\s+(NU\d+):\s+(.*?)$"
        # Pattern 3: Fallback - any error line with code pattern (DLxxxx, MSxxxx, etc.)
        fallback_pattern = r":\s+error\s+([A-Z]+\d+):\s+(.*?)$"

        for line in build_output.splitlines():
            # Try compiler error pattern first
            match = re.search(cs_pattern, line)
            if match:
                file_path, line_num, col_num, code, msg = match.groups()
                errors.append(CompilerError(
                    file_path=file_path.strip(),
                    line=int(line_num),
                    column=int(col_num),
                    error_code=code.strip(),
                    message=msg.strip()
                ))
                seen_codes.add(code.strip())
                continue

            # Try NuGet error pattern
            match = re.search(nu_pattern, line)
            if match:
                file_path, code, msg = match.groups()
                errors.append(CompilerError(
                    file_path=file_path.strip(),
                    line=0,  # NuGet errors don't have line numbers
                    column=0,
                    error_code=code.strip(),
                    message=msg.strip()
                ))
                seen_codes.add(code.strip())
                continue

            # Try fallback pattern for other error codes (DL, MS, etc.)
            if "error" in line.lower() and not any(skip in line for skip in ["warning", "info", "note"]):
                match = re.search(fallback_pattern, line)
                if match:
                    code, msg = match.groups()
                    if code not in seen_codes:  # Avoid duplicates
                        errors.append(CompilerError(
                            file_path="<unknown>",
                            line=0,
                            column=0,
                            error_code=code.strip(),
                            message=msg.strip()[:200]  # Truncate very long messages
                        ))
                        seen_codes.add(code)

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

        prompt = f"""You are a .NET 10 modernization expert. Fix ALL compilation errors in this C# code.
Target framework: .NET 10.0 (net10.0)

### COMPILATION ERRORS:
{error_context}

### CURRENT CODE:
```csharp
{file_content}
```

### INSTRUCTIONS:
1. Fix EVERY error listed above
2. Ensure all APIs and namespaces are available in .NET 10
3. For legacy .NET Framework types, replace with modern equivalents or use Microsoft.Windows.Compatibility
4. Preserve business logic and class names (do not rename)
5. Use modern .NET 10 patterns: IConfiguration DI, async/await, records, file-scoped namespaces
6. Output ONLY valid, compilable C# code in a ```csharp block
7. No explanations, just the fixed code
"""
        return prompt

    def generate_csproj_repair_prompt(self, csproj_content: str, restore_error: str) -> str:
        """Generate prompt for LLM to fix .csproj file"""
        prompt = f"""You are a .NET 10 project expert. Fix the .csproj file to resolve the NuGet restore/build error.

### ERROR MESSAGE:
{restore_error}

### CURRENT .CSPROJ:
```xml
{csproj_content}
```

### CRITICAL RULES:
1. Only use packages compatible with net10.0 target framework
2. Check package versions - they must support net10.0
3. Remove any packages that don't exist in modern .NET
4. For .NET Framework APIs, rely on Microsoft.Windows.Compatibility package
5. Never add packages with versions that only support .NET Framework (e.g., 4.x, 6.0 for ConfigurationManager)

### INSTRUCTIONS:
1. Analyze the error message and identify which package is causing the problem
2. Fix ONLY the problematic package(s) - update version to one compatible with net10.0
3. If package doesn't exist or isn't available for net10.0, remove it
4. Ensure TargetFramework is set to net10.0
5. Output ONLY the complete, valid .csproj XML in a ```xml block
6. Preserve all PropertyGroup settings
7. No explanations, just the corrected XML.
"""
        return prompt

    def _extract_xml(self, response: str) -> str:
        """Extract XML from markdown response"""
        pattern = r"```xml\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

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

CRITICAL: Include ALL required using statements:
- using System; (for DateTime, Convert, ArgumentException, etc.)
- using Microsoft.Extensions.Configuration; (for IConfiguration)
- using System.Threading.Tasks; (for async/await)
- Any other using statements the code needs

LEGACY CODE:
```csharp
{initial_code}
```

Output ONLY the complete, modernized C# code with ALL using statements in a ```csharp block."""

        print(f"📝 Calling LLM for initial migration...")
        try:
            response = llm_call_func(initial_prompt)
            print(f"   ✅ LLM responded ({len(response)} chars)")
        except Exception as llm_error:
            print(f"   ❌ LLM call failed: {llm_error}")
            raise
        current_code = self._extract_csharp_code(response)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(current_code)
        print(f"✓ Initial code written to {output_filepath}")

        # Step 2: Self-healing compilation loop
        for attempt in range(1, self.max_retries + 1):
            print(f"\n🔨 Compilation Attempt {attempt}/{self.max_retries}...")
            success, errors, restore_error = self.run_dotnet_build()

            if success:
                print(f"✅ BUILD SUCCEEDED! {output_filename} is ready for .NET 10.")
                return current_code

            # Handle restore errors by asking LLM to fix .csproj
            if restore_error:
                print(f"❌ Package restore error detected. Asking LLM to fix .csproj...")
                csproj_path = os.path.join(self.output_dir, self.csproj_name)
                with open(csproj_path, "r", encoding="utf-8") as f:
                    csproj_content = f.read()

                # Ask LLM to fix .csproj
                csproj_repair_prompt = self.generate_csproj_repair_prompt(csproj_content, restore_error)
                csproj_response = llm_call_func(csproj_repair_prompt)
                fixed_csproj = self._extract_xml(csproj_response)

                # Write fixed .csproj
                with open(csproj_path, "w", encoding="utf-8") as f:
                    f.write(fixed_csproj)
                print(f"   → .csproj updated by LLM. Retrying...")
                continue

            # Handle compilation errors by asking LLM to fix .cs file
            if not errors:
                print(f"❌ Build failed but no errors parsed. Full output:")
                print(f"   {restore_error if restore_error else 'Check console output above'}")
                continue

            # Show and repair compilation errors
            print(f"❌ {len(errors)} error(s) found. Calling LLM to repair code...")
            for err in errors[:5]:  # Show first 5 errors
                print(f"   [{err.error_code}] Line {err.line}: {err.message[:60]}")

            # Repair via LLM with ALL errors
            repair_prompt = self.generate_repair_prompt(current_code, errors)
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
            print(f"\n⚠️  Final compilation errors (showing up to 10):")
            for err in errors[:10]:
                if err.error_code == "BUILD_FAILED":
                    print(f"  [BUILD_FAILED] {err.message}")
                else:
                    print(f"  [{err.error_code}] Line {err.line}: {err.message}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        else:
            print(f"\n⚠️  Build failed but no errors could be parsed. Check the build output above.")

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
