"""Code Compiler Agent: Verifies modernized code compiles and extracts error diagnostics"""
import subprocess
import os
import re
from pathlib import Path
from typing import Tuple, List, Dict

def compile_modernized_code(code_content: str, component_name: str, base_output_dir: str = "migrated-output") -> Tuple[bool, List[Dict]]:
    """
    Compiles modernized C# code using the generated csproj in the output directory.

    Args:
        code_content: The modernized C# code (not used directly - files already saved)
        component_name: Name of the component being compiled
        base_output_dir: Base output directory for the component

    Returns:
        Tuple of (compiled: bool, errors: List[Dict])
        Each error dict contains: {file, line, column, error_code, message}
    """
    # Get the component directory and csproj
    component_dir = os.path.abspath(os.path.join(base_output_dir, component_name))
    csproj_path = os.path.join(component_dir, f"{component_name}.csproj")

    # Verify csproj exists
    if not os.path.exists(csproj_path):
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "IO", "message": f"csproj not found: {csproj_path}"}]

    # Compile using dotnet build
    try:
        result = subprocess.run(
            ["dotnet", "build", csproj_path, "--nologo", "--verbosity", "minimal"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=component_dir
        )

        if result.returncode == 0:
            return True, []

        # Parse compilation errors from dotnet output
        errors = _parse_dotnet_errors(result.stdout + "\n" + result.stderr)
        return False, errors

    except subprocess.TimeoutExpired:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "TIMEOUT", "message": "Compilation timed out after 60 seconds"}]
    except Exception as e:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "ERROR", "message": f"Compilation error: {str(e)}"}]

def _parse_csc_errors(output: str) -> List[Dict]:
    """Parse errors from csc.exe output"""
    errors = []
    # Pattern: filename.cs(line,col): error CSxxxx: message
    pattern = r"([^:]+)\((\d+),(\d+)\):\s*error\s+(CS\d+):\s*(.*?)(?=\n|$)"

    for match in re.finditer(pattern, output):
        errors.append({
            "file": os.path.basename(match.group(1)),
            "line": int(match.group(2)),
            "column": int(match.group(3)),
            "error_code": match.group(4),
            "message": match.group(5).strip()
        })

    # If no structured errors found, return generic error
    if not errors and "error" in output.lower():
        errors.append({
            "file": "unknown",
            "line": 0,
            "column": 0,
            "error_code": "COMPILE",
            "message": output[:500] if len(output) > 500 else output
        })

    return errors

def _parse_dotnet_errors(output: str) -> List[Dict]:
    """Parse errors from dotnet build output"""
    errors = []
    # Pattern: /path/to/file.cs(line,col): error CSxxxx: message
    # Also handles: ModernizedCode.cs(10,5): error CS0103: ...
    pattern = r"([^:]+\.cs)\((\d+),(\d+)\):\s*error\s+(CS\d+):\s*(.*?)(?=\n|$)"

    for match in re.finditer(pattern, output):
        errors.append({
            "file": os.path.basename(match.group(1)),
            "line": int(match.group(2)),
            "column": int(match.group(3)),
            "error_code": match.group(4),
            "message": match.group(5).strip()
        })

    if not errors and "error" in output.lower():
        errors.append({
            "file": "unknown",
            "line": 0,
            "column": 0,
            "error_code": "BUILD",
            "message": output[:500] if len(output) > 500 else output
        })

    return errors

def format_errors_for_feedback(errors: List[Dict]) -> str:
    """
    Format compilation errors as human-readable feedback for the modernizer LLM.
    """
    if not errors:
        return "No compilation errors."

    lines = ["Compilation errors found:"]
    for error in errors:
        lines.append(f"- Line {error['line']}, Column {error['column']}: [{error['error_code']}] {error['message']}")

    return "\n".join(lines)
