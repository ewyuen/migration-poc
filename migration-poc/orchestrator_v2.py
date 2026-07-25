"""Orchestrator Agent V2: Config-driven multi-agent extraction pipeline"""
import os
import json
import yaml
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from input_handler import InputHandler, MigrationRequest
from agents.staging_agent import StagingAgent
from agents.explorer import explore_code
from agents.extractor import extract_domain_logic
from agents.modernizer import modernize_code
from agents.bdd_test_agent import generate_bdd_tests
from agents.test_writer import TestWriter
from agents.verifier import verify_modernization
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
        print(f"[STAGE {len(self.completed_stages) + 1}/7] {stage_name.upper()}")
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
            output_dir = os.path.join("migrated-output", component_name)

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Strip markdown code blocks from source files
        if is_source_file:
            content = self._strip_markdown_code_block(content)

        filepath = os.path.join(output_dir, filename)
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

        # STAGE 4: EXTRACTION
        state.advance_stage("extraction")
        legacy_code_path = os.path.join("legacy-code", request.component_name)

        # Read all .cs files from the component directory
        legacy_code = ""
        try:
            for root, dirs, files in os.walk(legacy_code_path):
                for file in files:
                    if file.endswith(".cs"):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            legacy_code += f.read() + "\n"
        except Exception as e:
            state.mark_stage_failed(f"Failed to read component files: {str(e)}")
            self._log_workflow(state)
            return state.to_dict()

        extraction = extract_domain_logic(legacy_code, exploration_results)
        self._save_output(request.component_name, "extracted_logic.md", extraction)
        state.artifacts["extraction"] = extraction
        state.mark_stage_complete()

        # STAGE 5: MODERNIZATION
        state.advance_stage("modernization")
        modernized_code = modernize_code(legacy_code, extraction, exploration_results)
        self._save_output(request.component_name, "modernized_code.cs", modernized_code)
        state.artifacts["modernization"] = modernized_code
        state.mark_stage_complete()

        # STAGE 6: BDD & TEST WRITING
        state.advance_stage("bdd_and_testing")
        bdd_tests = generate_bdd_tests(extraction, modernized_code, exploration_results)
        self._save_output(request.component_name, "scenarios.feature", bdd_tests)

        # Generate executable tests from Gherkin (NEW)
        success, error, test_code = self.test_writer.write_tests_from_gherkin(
            bdd_tests,
            request.component_name,
            self._save_output(request.component_name, f"{request.component_name}.Tests.cs", "")
        )

        if success:
            self._save_output(request.component_name, f"{request.component_name}.Tests.cs", test_code)

        state.artifacts["bdd"] = bdd_tests
        state.artifacts["test_code"] = test_code if success else ""
        state.mark_stage_complete()

        # STAGE 7: VERIFICATION
        state.advance_stage("verification")
        verification = verify_modernization(legacy_code, modernized_code, extraction, bdd_tests)
        self._save_output(request.component_name, "verification_report.json", json.dumps(verification, indent=2))
        state.artifacts["verification"] = verification
        state.mark_stage_complete()

        # Summary
        self._log_workflow(state)
        self._print_summary(state, verification)

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

    def _print_summary(self, state: WorkflowState, verification: Dict) -> None:
        """Print workflow summary"""
        print("\n" + "="*70)
        print("✨ MIGRATION WORKFLOW COMPLETE")
        print("="*70)
        print(f"\nComponent: {state.request.component_name}")
        print(f"Status: {verification.get('overall_status', 'UNKNOWN')}")
        print(f"Completed Stages: {len(state.completed_stages)}/7")
        print(f"Total Time: {state.to_dict().get('timestamp_end', 'Unknown')}")

        risks = verification.get("risks", [])
        if risks:
            print(f"\n⚠️  Risks Identified:")
            risk_list = risks if isinstance(risks, list) else [risks]
            for risk in risk_list[:5]:
                print(f"   - {risk}")

        print(f"\n📁 Source files saved to: migrated-output/{state.request.component_name}/")
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
