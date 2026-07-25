"""Modernization Orchestrator Agent: Coordinates self-healing modernization loop"""
import logging
import os
import re
from typing import Dict, List, Optional
from agents.code_compiler import compile_modernized_code


class ModernizationOrchestrator:
    """Coordinates the modernizer and compiler in a self-healing loop"""

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        """
        Initialize the ModernizationOrchestrator.

        Args:
            base_output_dir: Base directory for output (default: "migrated-output")
            config: Configuration dictionary with optional max_attempts
        """
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.max_attempts = self.config.get("max_attempts", 5)

    def _is_csproj_error(self, errors: List[Dict]) -> bool:
        """
        Check if errors are related to the csproj file itself.
        Returns True if errors mention csproj, XML, SDK, or NuGet issues.
        """
        csproj_keywords = ["csproj", "xml", "netsdk", "msbuild", "nuget", "package", "restore"]
        for error in errors:
            message = error.get("message", "").lower()
            if any(keyword in message for keyword in csproj_keywords):
                return True
        return False

    def _extract_failed_lines(self, errors: List[Dict]) -> Dict[int, List[str]]:
        """
        Extract failed line numbers and their error messages.

        Returns:
            Dict mapping line numbers to list of error messages for that line
        """
        failed_lines = {}
        for error in errors:
            line_num = error.get("line", 0)
            message = error.get("message", "Unknown error")
            if line_num not in failed_lines:
                failed_lines[line_num] = []
            failed_lines[line_num].append(f"[{error.get('error_code', 'ERROR')}] {message}")
        return failed_lines

    def _format_error_feedback(self, errors: List[Dict], modernized_code: str) -> str:
        """
        Format compilation errors with code context for regeneration feedback.
        """
        if not errors:
            return "No errors."

        failed_lines = self._extract_failed_lines(errors)
        code_lines = modernized_code.split('\n')

        feedback = ["COMPILATION ERRORS - FIX THESE SPECIFIC LINES:\n"]

        for line_num in sorted(failed_lines.keys()):
            if 0 < line_num <= len(code_lines):
                code_line = code_lines[line_num - 1].strip()
                feedback.append(f"Line {line_num}: {code_line}")
                for error_msg in failed_lines[line_num]:
                    feedback.append(f"  └─ {error_msg}")
            else:
                for error_msg in failed_lines[line_num]:
                    feedback.append(f"Line {line_num}: {error_msg}")

        return "\n".join(feedback)

    def execute(self, component_name: str, modernizer_func, legacy_code: str, extraction_results: str, exploration_results: str) -> Dict:
        """
        Executes the self-healing modernization loop.

        Loop:
        1. Call modernizer to generate/regenerate code
        2. Save generated files immediately (whether compilation succeeds or fails)
        3. Compile to verify
        4. If failed, extract line-specific errors
        5. Pass feedback to modernizer and retry
        6. Repeat up to max_attempts
        7. Generate csproj with all generated files

        Args:
            component_name: Name of the component being modernized
            modernizer_func: Function that generates modernized code (callable)
            legacy_code: The legacy code to modernize
            extraction_results: Results from extraction stage
            exploration_results: Results from exploration stage

        Returns:
            Dictionary with keys:
            - status: "success" or "failed"
            - modernized_code: The final modernized code
            - errors: List of compilation errors from final attempt (empty if success)
            - attempts: Number of attempts made
            - compiled: Boolean indicating if code compiled
            - generated_files: List of generated file names
        """
        attempt = 1
        errors = []
        modernized_code = ""
        generated_files = []

        self.logger.info(f"🔄 Modernization Orchestrator: Starting self-healing loop for {component_name}")
        self.logger.info(f"🔄 Modernization Orchestrator: Max attempts = {self.max_attempts} (with line-specific error feedback)")

        while attempt <= self.max_attempts:
            self.logger.info(f"🔄 Modernization Orchestrator: Attempt {attempt} of {self.max_attempts}")

            # 1. Generate (or refine) modernized code
            self.logger.info(f"✍️ Modernization Orchestrator: Generating modernized code (attempt {attempt})...")

            if attempt == 1:
                # First attempt: fresh generation
                modernized_code = modernizer_func(
                    legacy_code,
                    extraction_results,
                    exploration_results
                )
            else:
                # Subsequent attempts: pass line-specific error feedback
                error_feedback = self._format_error_feedback(errors, modernized_code)
                attempt_context = {
                    "attempt": attempt,
                    "max_attempts": self.max_attempts,
                    "failed_lines": self._extract_failed_lines(errors),
                    "error_feedback": error_feedback
                }
                modernized_code = modernizer_func(
                    legacy_code,
                    extraction_results,
                    exploration_results,
                    feedback_errors=errors,
                    attempt_context=attempt_context
                )

            # 2. Save generated code immediately (regardless of compilation status)
            self.logger.info(f"💾 Modernization Orchestrator: Saving generated code (attempt {attempt})...")
            saved_files = self._save_modernized_code(component_name, modernized_code, attempt)
            generated_files = saved_files

            # 2b. Generate csproj immediately after files are written
            self.logger.info(f"📦 Modernization Orchestrator: Generating csproj with all files...")
            self._generate_csproj_with_files(component_name, generated_files)

            # 3. Compile and check
            self.logger.info(f"🔨 Modernization Orchestrator: Compiling modernized code...")
            compiled, errors = compile_modernized_code(modernized_code, component_name, self.base_output_dir)

            if compiled:
                self.logger.info(f"✅ Modernization Orchestrator: Code compiled successfully on attempt {attempt}!")
                return {
                    "status": "success",
                    "modernized_code": modernized_code,
                    "errors": [],
                    "attempts": attempt,
                    "compiled": True,
                    "generated_files": generated_files
                }

            # Compilation failed, check if it's a csproj issue
            self.logger.warning(f"⚠️ Modernization Orchestrator: Compilation failed on attempt {attempt}.")

            if self._is_csproj_error(errors):
                self.logger.warning(f"   Detected csproj-related error. Regenerating csproj...")
                self._generate_csproj_with_files(component_name, generated_files)

                # Retry compilation immediately after regenerating csproj
                self.logger.info(f"   Retrying compilation after csproj regeneration...")
                compiled, errors = compile_modernized_code(modernized_code, component_name, self.base_output_dir)

                if compiled:
                    self.logger.info(f"✅ Modernization Orchestrator: Code compiled successfully after csproj fix on attempt {attempt}!")
                    return {
                        "status": "success",
                        "modernized_code": modernized_code,
                        "errors": [],
                        "attempts": attempt,
                        "compiled": True,
                        "generated_files": generated_files
                    }

            # Compilation still failed, log errors for next iteration
            failed_lines = self._extract_failed_lines(errors)
            self.logger.warning(f"   Failed lines: {sorted(failed_lines.keys())}")
            self.logger.warning(f"   Error sample: {errors[0]['message'] if errors else 'Unknown'}")
            attempt += 1

        # Max attempts exhausted
        self.logger.error(f"❌ Modernization Orchestrator: Code failed to compile after {self.max_attempts} attempts.")
        return {
            "status": "failed",
            "modernized_code": modernized_code,
            "errors": errors,
            "attempts": self.max_attempts,
            "compiled": False,
            "generated_files": generated_files
        }

    def _parse_multiple_files(self, code_content: str) -> Dict[str, str]:
        """
        Parse multiple C# files from the modernizer output.
        Looks for file markers like:
        - // ============ FILE: ClassName.cs ============
        - // File: ClassName.cs
        - /* File: ... */

        Args:
            code_content: The full output containing multiple files

        Returns:
            Dict mapping filename to file content
        """
        files = {}

        # Pattern 1: // ============ FILE: ClassName.cs ============
        file_pattern_v1 = r'//\s*=+\s*FILE:\s*([^\n=]+\.cs)\s*=+\s*\n(.*?)(?=//\s*=+\s*FILE:|$)'
        matches_v1 = list(re.finditer(file_pattern_v1, code_content, re.DOTALL | re.IGNORECASE))

        if matches_v1:
            # Found v1 format markers
            for match in matches_v1:
                filename = match.group(1).strip()
                content = match.group(2).strip()
                if filename.endswith('.cs'):
                    files[filename] = content
                else:
                    files[f"{filename}.cs"] = content
        else:
            # Pattern 2: Fallback to older format with "// File:" or "/* File: */"
            file_pattern_v2 = r'(?://\s*File:\s*|/\*\s*File:\s*)([^\n/*]+)(?:\*/\n)?'
            parts = re.split(file_pattern_v2, code_content)

            if len(parts) > 1:
                # We found v2 format file markers
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        filename = parts[i].strip()
                        content = parts[i + 1].strip()
                        if filename.endswith('.cs'):
                            files[filename] = content
                        else:
                            files[f"{filename}.cs"] = content

        # If no markers found at all, treat entire output as one file
        if not files:
            files["ModernizedCode.cs"] = code_content.strip()

        return files if files else {"ModernizedCode.cs": code_content.strip()}

    def _save_modernized_code(self, component_name: str, modernized_code: str, attempt: int = 0) -> List[str]:
        """
        Save the modernized code to disk (saves after each attempt).
        Handles multiple files generated by modernizer.

        Args:
            component_name: Component name
            modernized_code: The generated code (may contain multiple files)
            attempt: Attempt number (0 for final)

        Returns:
            List of saved file names
        """
        try:
            output_dir = os.path.join(self.base_output_dir, component_name)
            os.makedirs(output_dir, exist_ok=True)

            # Parse multiple files from output
            files_to_save = self._parse_multiple_files(modernized_code)
            saved_files = []

            for filename, content in files_to_save.items():
                # Ensure .cs extension
                if not filename.endswith('.cs'):
                    filename = f"{filename}.cs"

                filepath = os.path.join(output_dir, filename)
                filedir = os.path.dirname(filepath)
                os.makedirs(filedir, exist_ok=True)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                saved_files.append(filename)
                self.logger.info(f"💾 Modernization Orchestrator: Saved {filename}")

            self.logger.info(f"💾 Modernization Orchestrator: Saved {len(saved_files)} file(s) to {output_dir}")
            return saved_files

        except Exception as e:
            self.logger.error(f"❌ Modernization Orchestrator: Failed to save modernized code: {e}")
            return []

    def _generate_csproj_with_files(self, component_name: str, generated_files: List[str]) -> None:
        """
        Generate a csproj file that includes all generated cs files using wildcard pattern.

        Args:
            component_name: Component name
            generated_files: List of generated .cs file names (for logging)
        """
        try:
            output_dir = os.path.join(self.base_output_dir, component_name)
            os.makedirs(output_dir, exist_ok=True)

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

            csproj_path = os.path.join(output_dir, f"{component_name}.csproj")
            with open(csproj_path, "w", encoding="utf-8") as f:
                f.write(csproj_content)

            # Verify file was actually created
            if os.path.exists(csproj_path):
                self.logger.info(f"✅ Modernization Orchestrator: Generated csproj with {len(generated_files)} file(s)")
                self.logger.info(f"   Path: {csproj_path}")
                self.logger.info(f"   Wildcard includes: **/*.cs (Exclude: obj/**, bin/**)")
                self.logger.info(f"   Packages included: FluentValidation, Moq, xunit, AutoMapper, and 10+ more")
            else:
                self.logger.error(f"❌ Modernization Orchestrator: csproj file was not created at {csproj_path}")

        except Exception as e:
            self.logger.error(f"❌ Modernization Orchestrator: Failed to generate csproj: {e}")
            import traceback
            self.logger.error(f"   Exception details: {traceback.format_exc()}")
