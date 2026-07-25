"""Orchestrator Agent V2: Config-driven multi-agent extraction pipeline"""
import os
import json
import yaml
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from input_handler import InputHandler, MigrationRequest
from agents.staging_agent import StagingAgent
from agents.explorer import explore_code
from agents.modernizer import modernize_code
from agents.bdd_test_cases_generator import generate_bdd_tests
from agents.test_writer import TestWriter
from agents.test_writer_stage import TestWriterStage
from agents.verifier import run_tests_and_collect_coverage
from config import OUTPUT_DIR, TARGET_FRAMEWORK, COMPLIANCE_CONTEXT, DOMAIN


class WorkflowState:
    """Tracks workflow progress and state"""

    def __init__(self, request: MigrationRequest):
        self.request = request
        self.timestamp_start = datetime.now().isoformat()
        self.current_stage = "initialized"
        self.completed_stages = []
        self.failed_stage = None
        self.error_message = ""
        self.artifacts = {}

    def advance_stage(self, stage_name: str) -> None:
        """Move to next stage"""
        self.current_stage = stage_name
        print(f"\n{'='*70}")
        print(f"[STAGE {len(self.completed_stages) + 1}/6] {stage_name.upper()}")
        print(f"{'='*70}\n")

    def mark_stage_complete(self) -> None:
        """Mark current stage as complete"""
        self.completed_stages.append(self.current_stage)

    def mark_stage_failed(self, error: str) -> None:
        """Mark stage as failed"""
        self.failed_stage = self.current_stage
        self.error_message = error

    def to_dict(self) -> Dict:
        """Convert state to dictionary"""
        return {
            "request": self.request.to_dict(),
            "timestamp_start": self.timestamp_start,
            "timestamp_end": datetime.now().isoformat(),
            "current_stage": self.current_stage,
            "completed_stages": self.completed_stages,
            "failed_stage": self.failed_stage,
            "error_message": self.error_message,
            "status": "success" if not self.failed_stage else "failed"
        }


class OrchestratorV2:
    """Config-driven orchestrator for component migration workflow"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Try to find migration_config.yaml in parent directory or current directory
            if os.path.exists("../migration_config.yaml"):
                config_path = "../migration_config.yaml"
            else:
                config_path = "migration_config.yaml"

        self.config_path = config_path
        self.config = self._load_config()
        self.input_handler = InputHandler()
        self.staging_agent = StagingAgent()
        self.test_writer = TestWriter()
        self.test_writer_stage = TestWriterStage(config=self.config.get("test_writer"))
        self.audit_dir = self.config.get("global", {}).get("audit_dir", "migration-poc/audit")
        Path(self.audit_dir).mkdir(parents=True, exist_ok=True)

    def _cleanup_component_dirs(self, component_name: str) -> None:
        """Clean up legacy-code and migrated-output for component"""
        legacy_code_path = os.path.join("legacy-code", component_name)
        migrated_output_path = os.path.join("migrated-output", component_name)
        result_log_path = os.path.join("migrated-output", "result-log")

        for path in [legacy_code_path, migrated_output_path, result_log_path]:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    print(f"🧹 Cleaned up: {path}")
                except Exception as e:
                    print(f"⚠️  Failed to clean up {path}: {e}")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            print(f"✅ Config loaded: {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)

    def _log_workflow(self, state: WorkflowState) -> None:
        """Log workflow execution for audit trail"""
        log_file = os.path.join(self.audit_dir, "orchestrator.jsonl")

        log_entry = {
            **state.to_dict(),
            "artifacts": {k: str(v) for k, v in state.artifacts.items()}
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")

    def _extract_class_name(self, code_content: str) -> Optional[str]:
        """Extract the primary class name from C# code"""
        import re
        # Look for public class, interface, record, struct definitions
        patterns = [
            r'public\s+class\s+(\w+)',
            r'public\s+interface\s+I(\w+)',
            r'public\s+record\s+(\w+)',
            r'public\s+struct\s+(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, code_content)
            if match:
                return match.group(1)
        return None

    def _read_component_files(self, component_path: str) -> Dict[str, str]:
        """
        Read ONLY .cs source files (no other file types).
        Excludes: obj/, bin/, .vs/, packages/, and generated files.
        """
        files_content = {}
        try:
            # Exclude generated directories and files
            excluded_dirs = {"obj", "bin", ".vs", "packages"}
            excluded_patterns = {
                "AssemblyAttributes",
                "AssemblyInfo",
                ".AssemblyAttributes.",
                "TemporaryGeneratedFile"
            }

            for root, dirs, files in os.walk(component_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                # Only process files in root or first level (actual source files)
                # Skip nested directories from obj/, bin/, etc.
                if any(exc in root for exc in excluded_dirs):
                    continue

                for file in files:
                    # Skip generated files
                    if file.endswith(".cs"):
                        # Exclude generated/framework files
                        if any(pattern in file for pattern in excluded_patterns):
                            print(f"⊘ Skipping generated file: {file}")
                            continue

                        filepath = os.path.join(root, file)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            files_content[file] = f.read()
                            print(f"✓ Reading source file: {file}")

        except Exception as e:
            print(f"⚠️  Error reading component files: {e}")
        return files_content

    def _parse_modernized_files(self, modernized_code: str, original_files: list) -> Dict[str, str]:
        """
        Parse modernized code and organize into files.
        Try to preserve original filenames or use class names.
        """
        import re
        result = {}

        # Strip markdown wrappers first
        clean_code = self._strip_markdown_code_block(modernized_code)

        # Try to identify namespace blocks and classes
        namespace_pattern = r'namespace\s+[\w.]+\s*\{(.*?)(?=namespace|\Z)'
        class_pattern = r'(public\s+(?:class|interface|record|struct)\s+\w+.*?(?=\n\s*(?:public\s+(?:class|interface|record|struct)|namespace|\}\s*\Z|\Z)))'

        namespaces = list(re.finditer(namespace_pattern, clean_code, re.DOTALL))

        if len(namespaces) > 1 or len(original_files) > 1:
            # Multiple files - try to extract individual classes
            classes = re.finditer(class_pattern, clean_code, re.DOTALL | re.MULTILINE)
            file_index = 0
            for match in classes:
                code_section = match.group(1)
                class_name = self._extract_class_name(code_section)
                if class_name:
                    filename = f"{class_name}.cs"
                    result[filename] = code_section.strip()
                    file_index += 1

            # If we couldn't parse individual classes, use original filenames
            if not result and original_files:
                filename = list(original_files)[0] if isinstance(original_files, (list, tuple)) else "ModernizedCode.cs"
                result[filename] = clean_code
        else:
            # Single file - try to preserve original name or extract class name
            class_name = self._extract_class_name(clean_code)
            if class_name:
                filename = f"{class_name}.cs"
            elif original_files:
                filename = list(original_files)[0] if isinstance(original_files, (list, tuple)) else "ModernizedCode.cs"
            else:
                filename = "ModernizedCode.cs"
            result[filename] = clean_code

        return result if result else {"ModernizedCode.cs": clean_code}

    def _strip_markdown_code_block(self, content: str) -> str:
        """Remove markdown code block wrappers if present"""
        lines = content.split('\n')
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines)

    def _save_output(self, component_name: str, filename: str, content: str) -> str:
        """Save output to migrated-output directory"""
        # Determine if this is a source file or a log/report
        is_source_file = filename.endswith(('.cs', '.feature', '.csproj'))
        is_log_file = filename.endswith(('.md', '.json'))

        if is_log_file:
            output_dir = os.path.join("migrated-output", "result-log")
        else:
            output_dir = os.path.join("migrated-output", component_name, "src")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Strip markdown code blocks from source files
        if is_source_file:
            content = self._strip_markdown_code_block(content)

        filepath = os.path.join(output_dir, filename)
        # Ensure parent directories exist
        Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"💾 Saved: {filepath}")
        return filepath

    def orchestrate_migration(self, request: MigrationRequest) -> Dict:
        """
        Main orchestration: coordinate all agents sequentially

        Returns:
            Dictionary with all results
        """
        state = WorkflowState(request)

        print("\n" + "="*70)
        print(f"🎭 ORCHESTRATOR V2: Migration Workflow")
        print("="*70)
        print(f"Component: {request.component_name}")
        print(f"Request ID: {request.request_id}")
        print(f"Target Framework: {self.config['global']['target_framework']}")
        print("="*70)

        # Clean up previous runs
        print("\n🧹 Cleaning up previous output directories...")
        self._cleanup_component_dirs(request.component_name)

        # STAGE 1: VALIDATION
        state.advance_stage("validation")
        is_valid, error = self._validate_request(request)
        if not is_valid:
            state.mark_stage_failed(error)
            self._log_workflow(state)
            print(f"❌ Validation failed: {error}")
            return state.to_dict()
        state.mark_stage_complete()

        # STAGE 2: STAGING (NEW)
        state.advance_stage("staging")
        success, staging_results = self._stage_component(request.component_name)
        if not success:
            state.mark_stage_failed(f"Staging failed: {staging_results.get('error', 'Unknown error')}")
            self._log_workflow(state)
            return state.to_dict()
        state.artifacts["staging"] = staging_results
        state.mark_stage_complete()

        # STAGE 3: EXPLORATION
        state.advance_stage("exploration")
        success, exploration_results = self._explore_component(request.component_name)
        if not success:
            state.mark_stage_failed("Exploration failed")
            self._log_workflow(state)
            return state.to_dict()
        state.artifacts["exploration"] = exploration_results
        state.mark_stage_complete()

        # STAGE 4: MODERNIZATION (with self-healing compilation verification)
        state.advance_stage("modernization")
        legacy_code_path = os.path.join("legacy-code", request.component_name)
        output_src_dir = os.path.join("migrated-output", request.component_name, "src")
        failure_log_dir = os.path.join("migrated-output", "result-log")

        # IMPORTANT: Only process .cs and .csproj files
        # Read .cs source files only (exclude obj/, bin/, generated files)
        component_files = self._read_component_files(legacy_code_path)
        if not component_files:
            state.mark_stage_failed(f"No .cs files found in {legacy_code_path}")
            self._log_workflow(state)
            return state.to_dict()

        # Find .csproj file in legacy code (exactly one per component)
        csproj_path = None
        csproj_name = None
        for root, dirs, files in os.walk(legacy_code_path):
            for file in files:
                # Only process .csproj files
                if file.endswith(".csproj"):
                    csproj_path = os.path.join(root, file)
                    csproj_name = file
                    break
            if csproj_path:
                break

        if not csproj_path:
            # Fallback if no .csproj found
            csproj_name = f"{request.component_name}.csproj"
            csproj_path = os.path.join(legacy_code_path, csproj_name)

        # Extract assembly and namespace info from .csproj (simplified)
        assembly_name = request.component_name
        root_namespace = request.component_name

        try:
            # Use self-healing agent for each .cs file
            print(f"🔄 Modernizing {len(component_files)} file(s) with compilation verification...")
            all_modernized_code = {}

            for filename, legacy_code in component_files.items():
                print(f"\n📝 Processing: {filename}")
                modernized = modernize_code(
                    legacy_code=legacy_code,
                    domain_logic=exploration_results.get("domain_logic", ""),
                    exploration=exploration_results,
                    output_dir=output_src_dir,
                    csproj_name=csproj_name,
                    output_filename=filename,
                    target_framework=self.config["global"].get("target_framework", "net10.0"),
                    failure_log_dir=failure_log_dir
                )
                all_modernized_code[filename] = modernized
                state.artifacts[f"modernization_{filename}"] = modernized

            # Copy .csproj to output directory with updated target framework
            if os.path.exists(csproj_path):
                try:
                    with open(csproj_path, "r", encoding="utf-8") as f:
                        csproj_content = f.read()
                    # Update target framework
                    csproj_content = re.sub(
                        r"<TargetFramework>[^<]*</TargetFramework>",
                        f"<TargetFramework>{self.config['global'].get('target_framework', 'net10.0')}</TargetFramework>",
                        csproj_content
                    )
                    # Ensure Windows Compatibility Pack is included for .NET Framework migration
                    if "Microsoft.Windows.Compatibility" not in csproj_content:
                        # Add compatibility pack to ItemGroup or create one
                        if "<ItemGroup>" in csproj_content:
                            csproj_content = csproj_content.replace(
                                "<ItemGroup>",
                                '<ItemGroup>\n    <PackageReference Include="Microsoft.Windows.Compatibility" Version="10.0.0" />'
                            )
                        else:
                            # Add ItemGroup if missing
                            csproj_content = csproj_content.replace(
                                "</Project>",
                                '\n  <ItemGroup>\n    <PackageReference Include="Microsoft.Windows.Compatibility" Version="10.0.0" />\n  </ItemGroup>\n</Project>'
                            )
                        print(f"   ✓ Added Windows Compatibility Pack to .csproj")

                    output_csproj_path = os.path.join(output_src_dir, csproj_name)
                    Path(os.path.dirname(output_csproj_path)).mkdir(parents=True, exist_ok=True)
                    with open(output_csproj_path, "w", encoding="utf-8") as f:
                        f.write(csproj_content)
                    print(f"✅ Project file updated: {output_csproj_path}")
                except Exception as e:
                    print(f"⚠️  Failed to copy .csproj: {e}")

            # Save modernized files with original names
            for filename, content in all_modernized_code.items():
                self._save_output(request.component_name, filename, content)

            state.artifacts["modernization"] = all_modernized_code
            state.mark_stage_complete()

        except Exception as e:
            error_msg = f"Modernization failed: {str(e)}"
            state.mark_stage_failed(error_msg)
            self._log_workflow(state)
            print(f"❌ {error_msg}")
            return state.to_dict()

        # STAGE 5: BDD & TEST WRITING
        state.advance_stage("bdd_and_testing")
        bdd_tests = generate_bdd_tests(exploration_results, modernized_code, exploration_results)
        self._save_output(request.component_name, os.path.join("tests", "scenarios.feature"), bdd_tests)

        # Generate executable tests from Gherkin (NEW)
        success, error, test_code = self.test_writer.write_tests_from_gherkin(
            bdd_tests,
            request.component_name,
            self._save_output(request.component_name, os.path.join("tests", f"{request.component_name}.Tests.cs"), "")
        )

        if success:
            self._save_output(request.component_name, os.path.join("tests", f"{request.component_name}.Tests.cs"), test_code)
            # Run TestWriterStage to implement the skeleton test methods with real code
            print("🖋️ Running TestWriterStage to implement skeletons...")
            writer_stage_result = self.test_writer_stage.execute(request.component_name)
            if writer_stage_result["status"] == "success":
                print("✅ TestWriterStage successfully completed and filled all skeletons!")
                # Read the updated test code to save it in workflow state artifacts
                test_file_path = os.path.join("migrated-output", request.component_name, "tests", f"{request.component_name}.Tests.cs")
                if os.path.exists(test_file_path):
                    with open(test_file_path, "r", encoding="utf-8") as f:
                        test_code = f.read()
            else:
                print(f"⚠️ TestWriterStage completed with issues/errors: {writer_stage_result.get('errors', [])}")

        state.artifacts["bdd"] = bdd_tests
        state.artifacts["test_code"] = test_code if success else ""
        state.mark_stage_complete()

        # STAGE 6: VERIFICATION (Compilation, Test Execution & Coverage)
        state.advance_stage("verification")
        try:
            verification_results = run_tests_and_collect_coverage(request.component_name)
            state.artifacts["verification"] = verification_results
            if verification_results.get("status") == "PASS":
                state.mark_stage_complete()
            else:
                # Document fail state, but do not crash orchestrator process
                state.mark_stage_failed(f"Test verification failed. Status: {verification_results.get('status')}")
        except Exception as e:
            state.mark_stage_failed(f"Error executing verification stage: {str(e)}")

        self._log_workflow(state)
        self._print_summary(state)

        return state.to_dict()

    def _validate_request(self, request: MigrationRequest) -> Tuple[bool, str]:
        """Validate migration request"""
        print("Validating request...")

        # Check legacy-src directory
        is_valid, error = self.input_handler.validate_legacy_src_exists()
        if not is_valid:
            return False, error

        # Check component exists
        component_path = os.path.join("legacy-src", request.component_name)
        if not os.path.exists(component_path):
            return False, f"Component not found: {component_path}"

        print("✅ Validation passed")
        return True, ""

    def _stage_component(self, component_name: str) -> Tuple[bool, Dict]:
        """Stage component using staging agent"""
        print(f"Staging component: {component_name}...")

        results = self.staging_agent.stage_component(component_name)

        if results.get("status") == "success":
            print(f"✅ Staging complete")
            return True, results
        else:
            error = results.get("steps", {}).get("create_branch", {}).get("error", "Unknown error")
            return False, {"error": error}

    def _explore_component(self, component_name: str) -> Tuple[bool, Dict]:
        """Explore component using explorer agent"""
        print(f"Exploring component: {component_name}...")

        component_path = os.path.join("legacy-code", component_name)
        if not os.path.exists(component_path):
            return False, {}

        # Read component files
        try:
            file_contents = ""
            for root, dirs, files in os.walk(component_path):
                for file in files:
                    if file.endswith((".cs", ".csproj", ".sln")):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            file_contents += f.read() + "\n"

            exploration = explore_code(file_contents, component_name)
            print(f"✅ Exploration complete")
            return True, exploration

        except Exception as e:
            return False, {"error": str(e)}

    def _print_summary(self, state: WorkflowState) -> None:
        """Print workflow summary"""
        print("\n" + "="*70)
        print("✨ MIGRATION WORKFLOW COMPLETE")
        print("="*70)
        print(f"\nComponent: {state.request.component_name}")
        print(f"Status: {state.to_dict().get('status', 'unknown')}")
        print(f"Completed Stages: {len(state.completed_stages)}/6")
        print(f"Total Time: {state.to_dict().get('timestamp_end', 'Unknown')}")

        verification = state.artifacts.get("verification", {})
        if verification:
            print("\n🔬 Verification Details:")
            print(f"  Test Status: {verification.get('status', 'N/A')}")
            print(f"  Passed Tests: {verification.get('passed_tests', 0)} / {verification.get('total_tests', 0)}")
            print(f"  Line Coverage: {verification.get('line_coverage', 0.0):.2f}%")
            print(f"  Branch Coverage: {verification.get('branch_coverage', 0.0):.2f}%")
            if not verification.get("compiled") and verification.get("errors"):
                print("  Compilation Errors:")
                for err in verification.get("errors", [])[:5]:
                    print(f"    - {err}")
            elif verification.get("failed_tests", 0) > 0 and verification.get("failures"):
                print("  Failed Tests:")
                for fail in verification.get("failures", [])[:3]:
                    print(f"    - {fail['test_name']}: {fail['message']}")

        print(f"\n📁 Source files saved to: migrated-output/{state.request.component_name}/src/")
        print(f"📁 Logs and reports saved to: migrated-output/result-log/")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_v2.py <component_name> [filters_json]")
        print("Example: python orchestrator_v2.py MyComponent")
        sys.exit(1)

    # Change to repository root for consistent paths
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)

    component_name = sys.argv[1]
    filters_json = sys.argv[2] if len(sys.argv) > 2 else None

    # Create input handler and parse request
    input_handler = InputHandler(legacy_src_dir="legacy-src", audit_dir="migration-poc/audit")
    request, error = input_handler.parse_cli_args(component_name, filters_json)

    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)

    # Create orchestrator and run workflow
    orchestrator = OrchestratorV2()
    results = orchestrator.orchestrate_migration(request)

    # Exit with appropriate code
    sys.exit(0 if results.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
