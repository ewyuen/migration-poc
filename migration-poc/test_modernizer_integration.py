"""Integration test: End-to-end modernization with real compilation verification"""
import os
import tempfile
import shutil
from pathlib import Path
from agents.modernizer import DotNetMigrationAgent


def stub_llm_modernize_auth_service(prompt: str) -> str:
    """Modernize AuthenticationService to .NET 10 with IConfiguration"""
    return """```csharp
using System;
using Microsoft.Extensions.Configuration;

namespace TestService
{
    /// <summary>
    /// Modernized authentication service using .NET 10 with dependency injection
    /// </summary>
    public class AuthenticationService
    {
        private readonly IConfiguration _configuration;

        public AuthenticationService(IConfiguration configuration)
        {
            _configuration = configuration ?? throw new ArgumentNullException(nameof(configuration));
        }

        /// <summary>
        /// Authenticate user with email and password
        /// </summary>
        public bool AuthenticateUser(string email, string password)
        {
            if (string.IsNullOrEmpty(email) || string.IsNullOrEmpty(password))
                return false;

            if (email == "admin@test.com" && password == "password123")
                return true;

            return ValidateUserInDatabase(email, password);
        }

        /// <summary>
        /// Check if user is senior citizen (age >= 65)
        /// </summary>
        public bool IsSeniorCitizen(int age) => age >= 65;

        /// <summary>
        /// Calculate discount for senior citizens
        /// </summary>
        public decimal CalculateDiscount(int age, decimal amount)
        {
            return age switch
            {
                >= 65 => amount * 0.15m,
                >= 21 and < 65 => amount * 0.05m,
                _ => 0m
            };
        }

        /// <summary>
        /// Validate user in database
        /// </summary>
        private bool ValidateUserInDatabase(string email, string password)
        {
            // Deferred: would use IDataService from DI
            return false;
        }

        /// <summary>
        /// Generate session token (modernized)
        /// </summary>
        public string GenerateSessionToken(string email)
        {
            if (string.IsNullOrEmpty(email))
                throw new ArgumentNullException(nameof(email));

            return Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes($"{email}:{DateTime.UtcNow.Ticks}")
            );
        }

        /// <summary>
        /// Validate session token (modernized)
        /// </summary>
        public bool ValidateSessionToken(string token)
        {
            if (string.IsNullOrEmpty(token))
                return false;

            try
            {
                var decoded = System.Text.Encoding.UTF8.GetString(
                    Convert.FromBase64String(token)
                );
                return !string.IsNullOrEmpty(decoded);
            }
            catch
            {
                return false;
            }
        }
    }
}
```"""


def test_end_to_end_modernization():
    """
    End-to-end test:
    1. Read real legacy code from legacy-src/TestService/AuthenticationService.cs
    2. Modernize it using DotNetMigrationAgent
    3. Verify dotnet build succeeds
    4. Verify file names are preserved
    5. Verify .csproj is created
    """
    print("\n" + "="*70)
    print("END-TO-END TEST: Real legacy code → Modernize → Compile")
    print("="*70)

    # Find legacy code (in parent directory)
    legacy_code_path = os.path.join(os.path.dirname(__file__), "..", "legacy-src", "TestService", "AuthenticationService.cs")
    if not os.path.exists(legacy_code_path):
        print(f"⚠️  Legacy code not found: {legacy_code_path}")
        print("   This test requires the legacy-src directory to be present")
        return False

    with open(legacy_code_path, "r", encoding="utf-8") as f:
        legacy_code = f.read()

    print(f"✓ Loaded legacy code: {legacy_code_path} ({len(legacy_code)} bytes)")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "modernized_output")

        print(f"\n📂 Output directory: {output_dir}")

        # Create agent
        agent = DotNetMigrationAgent(
            output_dir=output_dir,
            csproj_name="TestService.csproj",
            target_framework="net10.0",
            max_retries=4
        )

        # Generate .csproj
        agent.generate_csproj("TestService", "TestService")
        print(f"✓ Generated .csproj for TestService targeting net10.0")

        try:
            # Migrate the file
            result = agent.migrate_file(
                output_filename="AuthenticationService.cs",
                initial_code=legacy_code,
                llm_call_func=stub_llm_modernize_auth_service
            )

            # Verify: Output file exists with original name
            output_file = os.path.join(output_dir, "AuthenticationService.cs")
            assert os.path.exists(output_file), f"Output file not found: {output_file}"
            print(f"✓ Output file exists with original name: AuthenticationService.cs")

            # Verify: .csproj exists
            csproj_file = os.path.join(output_dir, "TestService.csproj")
            assert os.path.exists(csproj_file), f"Project file not found: {csproj_file}"
            print(f"✓ Project file created: TestService.csproj")

            # Verify: Code contains modern patterns
            assert "IConfiguration" in result, "Modernized code missing IConfiguration"
            assert "namespace TestService" in result, "Namespace lost"
            assert "class AuthenticationService" in result, "Class name lost"
            assert "switch" in result, "C# 8+ switch expressions not used"
            print(f"✓ Modernized code uses .NET 10 patterns:")
            print(f"   - IConfiguration DI")
            print(f"   - Switch expressions")
            print(f"   - Preserved namespace and class names")

            # Verify: Code compiles
            print(f"\n🔨 Verifying compilation...")
            success, errors, restore_error = agent.run_dotnet_build()
            if success:
                print(f"✅ BUILD SUCCEEDED")
            else:
                print(f"❌ Build failed with {len(errors)} error(s):")
                for err in errors[:5]:
                    print(f"   [{err.error_code}] Line {err.line}: {err.message}")
                return False

            print("\n" + "="*70)
            print("✅ END-TO-END TEST PASSED")
            print("="*70)
            print("\nSummary:")
            print(f"  ✓ Legacy code read: {len(legacy_code)} bytes")
            print(f"  ✓ Modernized with IConfiguration DI")
            print(f"  ✓ Preserved filename: AuthenticationService.cs")
            print(f"  ✓ Generated .csproj: TestService.csproj (net10.0)")
            print(f"  ✓ Compilation verified: dotnet build succeeded")
            print("\nReady for production use:")
            print(f"  Output: {output_dir}")
            return True

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MODERNIZER INTEGRATION TEST")
    print("="*70)
    print("\nThis test verifies:")
    print("  1. Real legacy code is read correctly")
    print("  2. LLM modernization creates valid .NET 10 C#")
    print("  3. Code compiles with dotnet build")
    print("  4. Original filenames are preserved")
    print("  5. Project file is generated with correct target framework")

    result = test_end_to_end_modernization()

    if result:
        print("\n✅ All checks passed! Ready to test with real LLM.")
        print("\nNext steps:")
        print("  1. Set OPENROUTER_API_KEY environment variable")
        print("  2. Run full orchestrator pipeline with real LLM")
        print("  3. Verify migrated-output/TestService/ compiles")
        exit(0)
    else:
        print("\n❌ Integration test failed")
        exit(1)
