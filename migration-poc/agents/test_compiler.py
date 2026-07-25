"""Test Compiler Agent: Creates and compiles test projects"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

def generate_test_csproj(tests_dir: str, component_name: str = None) -> None:
    """Generate a tests.csproj file that references the source project from Step 4"""
    # Determine the source project name and path
    if component_name is None:
        # Extract component name from tests_dir path: .../TestService/tests -> TestService
        component_name = os.path.basename(os.path.dirname(tests_dir))

    src_csproj_path = f"..\\src\\{component_name}.csproj"

    csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
    <IsTestProject>true</IsTestProject>
  </PropertyGroup>

  <!-- Reference the source project from Step 4 -->
  <ItemGroup>
    <ProjectReference Include="{src_csproj_path}" />
  </ItemGroup>

  <!-- Include test files from this directory -->
  <ItemGroup>
    <Compile Include="*.Tests.cs" />
    <Compile Include="*.cs" Exclude="*.Tests.cs" />
  </ItemGroup>

  <ItemGroup>
    <Using Include="FluentValidation" />
    <Using Include="Microsoft.Extensions.Options" />
    <Using Include="System.Text" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.1" />
    <PackageReference Include="xunit" Version="2.9.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.8.2">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="coverlet.collector" Version="6.0.2">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
    <PackageReference Include="FluentValidation" Version="11.9.0" />
    <PackageReference Include="Microsoft.Extensions.Options" Version="8.0.2" />
  </ItemGroup>
</Project>
"""
    csproj_path = os.path.join(tests_dir, "tests.csproj")
    with open(csproj_path, "w", encoding="utf-8") as f:
        f.write(csproj_content)
    print(f"🛠️ Generated test project file: {csproj_path}")
    print(f"   References: {src_csproj_path}")

def run_test_compiler(component_name: str, base_output_dir: str = "migrated-output") -> Dict:
    """
    Creates tests.csproj and compiles the test project, collecting raw outputs.

    Returns:
        Dict detailing build status, compilation errors, and directory paths.
    """
    tests_dir = os.path.join(base_output_dir, component_name, "tests")
    report = {
        "compiled": False,
        "errors": [],
        "tests_dir": tests_dir
    }

    if not os.path.exists(tests_dir):
        msg = f"Tests directory not found: {tests_dir}"
        report["errors"].append(msg)
        print(f"❌ {msg}")
        return report

    # 1. Generate tests.csproj (references source project from Step 4)
    generate_test_csproj(tests_dir, component_name)

    # 2. Run dotnet test
    print(f"🏃 Running dotnet test with coverage collection in {tests_dir}...")
    cmd = ["dotnet", "test", "--collect:XPlat Code Coverage", "--logger:trx;LogFileName=results.trx"]
    try:
        # Run with UTF-8 environment variable
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            cmd,
            cwd=tests_dir,
            capture_output=True,
            text=True,
            env=env,
            timeout=180 # 3 minute timeout
        )

        trx_search = os.path.join(tests_dir, "TestResults", "results.trx")
        if os.path.exists(trx_search):
            report["compiled"] = True
            print("✅ Compilation and test run completed successfully.")
        else:
            # Did not compile or no test results produced
            report["compiled"] = False

            # Extract compilation errors from output
            build_errors = []
            for line in (result.stdout + "\n" + result.stderr).split('\n'):
                if "error CS" in line or "Build FAILED" in line or "error NETSDK" in line:
                    build_errors.append(line.strip())
            report["errors"] = build_errors or [result.stdout[:2000]]
            print("❌ Compilation or project build failed.")

    except subprocess.TimeoutExpired:
        report["errors"].append("dotnet test execution timed out after 180 seconds.")
        print("❌ dotnet test execution timed out.")
    except Exception as e:
        report["errors"].append(f"Unexpected error running tests: {str(e)}")
        print(f"❌ Unexpected error: {e}")

    return report
