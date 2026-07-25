"""Code Compiler Agent: Verifies modernized code compiles and extracts error diagnostics"""
import subprocess
import os
import re
from pathlib import Path
from typing import Tuple, List, Dict

def compile_modernized_code(code_content: str, component_name: str, base_output_dir: str = "migrated-output") -> Tuple[bool, List[Dict]]:
    """
    Compiles modernized C# code in isolation and extracts error diagnostics.

    Args:
        code_content: The modernized C# code to compile
        component_name: Name of the component being compiled
        base_output_dir: Base output directory for the component

    Returns:
        Tuple of (compiled: bool, errors: List[Dict])
        Each error dict contains: {file, line, column, error_code, message}
    """
    # Create temp directory for compilation
    temp_dir = os.path.join(base_output_dir, component_name, "temp_compile")
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    # Write code to temporary file
    temp_file = os.path.join(temp_dir, "ModernizedCode.cs")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code_content)
    except Exception as e:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "IO", "message": f"Failed to write code file: {str(e)}"}]

    # Attempt to compile using csc.exe
    try:
        result = subprocess.run(
            ["csc.exe", temp_file, "/nologo", "/out:" + os.path.join(temp_dir, "temp.exe")],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check if compilation succeeded
        if result.returncode == 0:
            return True, []

        # Parse compilation errors
        errors = _parse_csc_errors(result.stdout + "\n" + result.stderr)
        return False, errors

    except subprocess.TimeoutExpired:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "TIMEOUT", "message": "Compilation timed out after 30 seconds"}]
    except FileNotFoundError:
        # csc.exe not found, try dotnet
        return _compile_with_dotnet(code_content, component_name, temp_file, base_output_dir)
    except Exception as e:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "ERROR", "message": f"Compilation error: {str(e)}"}]

def _compile_with_dotnet(code_content: str, component_name: str, temp_file: str, base_output_dir: str) -> Tuple[bool, List[Dict]]:
    """
    Fallback: Compile using dotnet compiler if csc.exe not available.
    Creates a minimal .csproj file and compiles.
    """
    temp_dir = os.path.dirname(temp_file)
    csproj_path = os.path.join(temp_dir, "Compile.csproj")

    # Create minimal project file
    csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>"""

    try:
        with open(csproj_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)

        result = subprocess.run(
            ["dotnet", "build", csproj_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=temp_dir
        )

        if result.returncode == 0:
            return True, []

        errors = _parse_dotnet_errors(result.stdout + "\n" + result.stderr)
        return False, errors

    except subprocess.TimeoutExpired:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "TIMEOUT", "message": "Compilation timed out after 30 seconds"}]
    except Exception as e:
        return False, [{"file": "unknown", "line": 0, "column": 0, "error_code": "ERROR", "message": f"Dotnet compilation error: {str(e)}"}]

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
