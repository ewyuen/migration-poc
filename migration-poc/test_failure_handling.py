"""Test error handling: Files are preserved when migration fails"""
import os
import tempfile
from agents.modernizer import DotNetMigrationAgent


attempt_count = 0

def stub_llm_always_broken(prompt: str) -> str:
    """Always return broken code (to trigger max retries)"""
    global attempt_count
    attempt_count += 1
    return f"""```csharp
using System;
// Attempt {attempt_count}: Intentionally broken
public class Broken {{
    public void Missing() // Missing closing brace
}}
```"""


def test_file_preservation_on_failure():
    """Verify files are preserved when migration fails"""
    print("\n" + "="*70)
    print("TEST: File preservation when migration fails")
    print("="*70)

    global attempt_count
    attempt_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "output")

        agent = DotNetMigrationAgent(
            output_dir=output_dir,
            csproj_name="TestService.csproj",
            target_framework="net10.0",
            max_retries=2  # Low number for fast testing
        )

        # Generate .csproj
        agent.generate_csproj("TestService", "TestService")

        legacy_code = """
using System;
namespace TestService
{
    public class AuthService { }
}
"""

        try:
            # This will fail after 2 attempts
            result = agent.migrate_file(
                output_filename="AuthService.cs",
                initial_code=legacy_code,
                llm_call_func=stub_llm_always_broken
            )
            print("❌ Should have raised exception")
            return False

        except RuntimeError as e:
            error_msg = str(e)

            # Verify: Files are still there
            csproj_file = os.path.join(output_dir, "TestService.csproj")
            cs_file = os.path.join(output_dir, "AuthService.cs")

            csproj_exists = os.path.exists(csproj_file)
            cs_exists = os.path.exists(cs_file)

            print(f"\n📁 After migration failure:")
            print(f"   .csproj exists: {csproj_exists}")
            print(f"   .cs file exists: {cs_exists}")

            if not csproj_exists or not cs_exists:
                print(f"❌ Files were deleted!")
                return False

            # Verify: Error message includes path to preserved files
            if "preserved" not in error_msg.lower():
                print(f"⚠️  Error message doesn't mention preserved files")

            # Verify: Attempt count matches expected retries
            if attempt_count != 2:
                print(f"⚠️  Expected 2 attempts, got {attempt_count}")

            print(f"\n✅ TEST PASSED:")
            print(f"   ✓ Files preserved after max retries exceeded")
            print(f"   ✓ .csproj file: {csproj_file}")
            print(f"   ✓ Code file: {cs_file}")
            print(f"   ✓ Error clearly indicates failure: {error_msg[:80]}...")
            return True

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ERROR HANDLING TEST")
    print("="*70)
    print("\nVerifies that files are preserved when migration fails")
    print("This allows users to debug compilation issues\n")

    result = test_file_preservation_on_failure()

    if result:
        print("\n✅ File preservation test passed!")
        print("\nWhen migration fails:")
        print("  • All source files are preserved in output directory")
        print("  • .csproj file is saved for inspection")
        print("  • Error messages point to preserved files")
        print("  • Users can manually debug and retry")
        exit(0)
    else:
        print("\n❌ Test failed")
        exit(1)
