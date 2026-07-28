"""Step Definitions Compiler: Compile and validate StepDefinitions.cs"""
import os
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple


class StepDefinitionsCompiler:
    """Compile step definitions file via dotnet build"""

    def __init__(self, base_output_dir: str = "migrated-output"):
        self.base_output_dir = base_output_dir
        self.logger = logging.getLogger(__name__)

    def compile(self, component_name: str, run_id: str) -> Dict:
        """
        Compile step definitions via dotnet build.

        Returns dict with:
        - success: bool
        - errors: List[str] (structured error messages)
        - raw_output: str (full build output)
        """
        tests_dir = os.path.join(self.base_output_dir, run_id, "tests")

        if not os.path.exists(tests_dir):
            return {
                "success": False,
                "errors": [f"Tests directory not found: {tests_dir}"],
                "raw_output": ""
            }

        self.logger.info(f"🏗️ Compiler: Compiling step definitions in {tests_dir}")

        try:
            result = subprocess.run(
                ["dotnet", "build"],
                cwd=tests_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info("✅ Compiler: Build succeeded")
                return {
                    "success": True,
                    "errors": [],
                    "raw_output": result.stdout
                }
            else:
                errors = self._parse_errors(result.stdout, result.stderr)
                self.logger.warning(f"⚠️ Compiler: Build failed with {len(errors)} error(s)")
                return {
                    "success": False,
                    "errors": errors,
                    "raw_output": result.stdout + "\n" + result.stderr
                }

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Compiler: Build timed out after 60 seconds")
            return {
                "success": False,
                "errors": ["Build timed out after 60 seconds"],
                "raw_output": ""
            }
        except Exception as e:
            self.logger.error(f"❌ Compiler: Unexpected error: {e}")
            return {
                "success": False,
                "errors": [f"Unexpected error: {str(e)}"],
                "raw_output": ""
            }

    def _parse_errors(self, stdout: str, stderr: str) -> List[str]:
        """Extract structured error messages from build output"""
        output = stdout + "\n" + stderr
        errors = []

        # Parse CSxxxx errors
        error_pattern = re.compile(r'(.+?)\((\d+),(\d+)\):\s+error\s+(CS\d+):\s+(.+?)(?:\n|$)')
        for match in error_pattern.finditer(output):
            file_path, line, col, code, message = match.groups()
            errors.append(f"{code} at {os.path.basename(file_path)}({line},{col}): {message.strip()}")

        # Also capture general error lines
        for line in output.split('\n'):
            if 'error' in line.lower() and 'CS' in line:
                errors.append(line.strip())

        return errors[:10]  # Limit to first 10 errors

    def save_to_audit(self, compile_result: Dict, run_id: str, audit_dir: str) -> None:
        """Save compilation result to audit trail"""
        audit_file = os.path.join(audit_dir, f"step-definitions-compilation-{run_id}.log")
        Path(audit_dir).mkdir(parents=True, exist_ok=True)

        with open(audit_file, "w", encoding="utf-8") as f:
            f.write(f"Step Definitions Compilation Result\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Status: {'SUCCESS' if compile_result['success'] else 'FAILED'}\n\n")

            if compile_result["errors"]:
                f.write("Errors:\n")
                for error in compile_result["errors"]:
                    f.write(f"  - {error}\n")
                f.write("\n")

            f.write("Full Build Output:\n")
            f.write(compile_result["raw_output"])

        self.logger.info(f"📝 Compiler: Audit logged to {audit_file}")
