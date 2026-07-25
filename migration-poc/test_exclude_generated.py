"""Test that generated files are excluded from migration"""
import os
import tempfile
from pathlib import Path
from orchestrator_v2 import OrchestratorV2


def test_exclude_generated_files():
    """Verify that obj/, bin/, and generated files are excluded"""
    print("\n" + "="*70)
    print("TEST: Generated files excluded from migration")
    print("="*70)

    # Create a mock component directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        component_dir = os.path.join(tmpdir, "TestComponent")
        Path(component_dir).mkdir(parents=True, exist_ok=True)

        # Create source files (should be migrated)
        source_file = os.path.join(component_dir, "MyService.cs")
        with open(source_file, "w") as f:
            f.write("public class MyService { }")
        print(f"✓ Created source file: MyService.cs")

        # Create obj directory with generated files (should be skipped)
        obj_dir = os.path.join(component_dir, "obj", "Debug", "net472")
        Path(obj_dir).mkdir(parents=True, exist_ok=True)

        generated_files = [
            ".NETFramework,Version=v4.7.2.AssemblyAttributes.cs",
            "TestComponent.AssemblyInfo.cs",
            "TemporaryGeneratedFile_123.cs"
        ]

        for gen_file in generated_files:
            filepath = os.path.join(obj_dir, gen_file)
            with open(filepath, "w") as f:
                f.write("// Generated file - should be skipped")
            print(f"✓ Created generated file: {gen_file}")

        # Create bin directory (should be skipped)
        bin_dir = os.path.join(component_dir, "bin", "Debug")
        Path(bin_dir).mkdir(parents=True, exist_ok=True)
        bin_file = os.path.join(bin_dir, "Generated.cs")
        with open(bin_file, "w") as f:
            f.write("// Bin generated file")
        print(f"✓ Created bin file: Generated.cs")

        # Use orchestrator to read files
        orch = OrchestratorV2()
        files = orch._read_component_files(component_dir)

        print(f"\n📂 Files read from component:")
        print(f"   Total: {len(files)}")
        for filename in sorted(files.keys()):
            print(f"   ✓ {filename}")

        # Verify results
        assert "MyService.cs" in files, "Source file should be included"
        assert len(files) == 1, f"Should have 1 file, got {len(files)}"

        for gen_file in generated_files:
            assert gen_file not in files, f"Generated file {gen_file} should be excluded"

        assert "Generated.cs" not in files, "bin/ files should be excluded"

        print(f"\n✅ TEST PASSED:")
        print(f"   ✓ Source files included: {len(files)}")
        print(f"   ✓ Generated files excluded: {len(generated_files)}")
        print(f"   ✓ bin/ directory excluded")
        print(f"   ✓ obj/ directory excluded")
        return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("GENERATED FILE EXCLUSION TEST")
    print("="*70)
    print("\nVerifies that only source files are migrated")
    print("Generated files from obj/, bin/ are excluded\n")

    try:
        result = test_exclude_generated_files()
        if result:
            print("\n✅ All tests passed!")
            print("\nOnly real source files will be migrated:")
            print("  ✓ Component root .cs files")
            print("  ✗ obj/ generated files (excluded)")
            print("  ✗ bin/ compiled files (excluded)")
            print("  ✗ AssemblyAttributes.cs (excluded)")
            print("  ✗ AssemblyInfo.cs (excluded)")
            exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
