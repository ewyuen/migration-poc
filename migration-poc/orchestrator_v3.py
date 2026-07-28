"""OrchestratorV3: LangGraph-based multi-agent extraction pipeline with OpenTelemetry & Langfuse"""
import os
import json
import yaml
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, TypedDict, Tuple, Any
from dataclasses import dataclass

# Add parent directory to path so imports work from any location
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from input_handler import InputHandler, MigrationRequest
from agents.staging_agent import StagingAgent
from agents.explorer import explore_code
from agents.modernizer import modernize_code
from agents.bdd_test_cases_generator import generate_bdd_tests
from agents.test_writer import TestWriter
from agents.test_writer_stage import TestWriterStage
from agents.test_orchestrator import TestOrchestrator
from agents.verifier import run_tests_and_collect_coverage
from config import OUTPUT_DIR, TARGET_FRAMEWORK, COMPLIANCE_CONTEXT, DOMAIN

from langgraph.graph import StateGraph, START, END
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Try to import Langfuse integration; skip if not available
try:
    from langfuse.opentelemetry import LangfuseSpanProcessor
    HAS_LANGFUSE = True
except (ImportError, AttributeError):
    HAS_LANGFUSE = False
    LangfuseSpanProcessor = None


class MigrationState(TypedDict):
    """State schema for workflow orchestration"""
    request: MigrationRequest
    run_id: Optional[str]
    stage: str
    error: Optional[str]
    staging_results: Optional[Dict[str, Any]]
    exploration_results: Optional[Dict[str, Any]]
    modernized_code: Optional[Dict[str, str]]
    bdd_tests: Optional[str]
    test_code: Optional[str]
    step_definitions_skeleton: Optional[str]
    step_definitions_enhanced: Optional[str]
    verification_results: Optional[Dict[str, Any]]


class OrchestratorV3:
    """LangGraph-based orchestrator for component migration workflow.

    Coordinates a 6-stage migration pipeline using LangGraph StateGraph:
    1. Validation - check request validity
    2. Staging - copy component to run-scoped directory
    3. Exploration - LLM analyzes legacy code
    4. Modernization - LLM rewrites code with compilation verification
    5. BDD & Testing - generates and fills executable tests
    6. Verification - compile, run tests, collect coverage

    Each stage is a LangGraph node; edges route based on error state.
    Continues to verification even if intermediate stages fail (unlike V2's early exit).

    Instrumented with OpenTelemetry for full tracing; spans are exported to
    Langfuse via LangfuseSpanProcessor for observability.

    All existing agents (StagingAgent, explorer, modernizer, etc.) remain unchanged;
    this orchestrator simply calls them within LangGraph nodes.

    Entry point is orchestrate_migration(request), same as OrchestratorV2 for
    drop-in compatibility.
    """

    def __init__(self, config_path: str = None, tracer: Optional[trace.Tracer] = None):
        if config_path is None:
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
        self.test_orchestrator = TestOrchestrator(config=self.config.get("test_orchestrator"))
        self.audit_dir = self.config.get("global", {}).get("audit_dir", "migration-poc/audit")
        Path(self.audit_dir).mkdir(parents=True, exist_ok=True)

        self.tracer = tracer or self._setup_otel_tracer()
        self.graph = self._build_graph()

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

    def _setup_otel_tracer(self) -> trace.Tracer:
        """Initialize OpenTelemetry tracer with Langfuse exporter.

        Sets up OTLP gRPC exporter (default localhost:4317) and adds
        LangfuseSpanProcessor for trace ingestion to Langfuse SaaS (if available).

        Gracefully handles setup failures: if OTel init fails, logs warning
        but continues with no-op tracer (orchestration not blocked).

        Environment variables:
        - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default localhost:4317)
        - LANGFUSE_PUBLIC_KEY: Langfuse API key
        - LANGFUSE_SECRET_KEY: Langfuse secret
        - LANGFUSE_ENDPOINT: Langfuse endpoint (defaults to cloud)

        Returns:
            trace.Tracer: Initialized tracer instance
        """
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
            )
            tracer_provider = TracerProvider()
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

            if HAS_LANGFUSE and LangfuseSpanProcessor:
                try:
                    langfuse_processor = LangfuseSpanProcessor()
                    tracer_provider.add_span_processor(langfuse_processor)
                except Exception as e:
                    print(f"⚠️  Langfuse processor setup failed: {e}. Continuing with OTLP only.")

            trace.set_tracer_provider(tracer_provider)
            return trace.get_tracer(__name__)
        except Exception as e:
            print(f"⚠️  OpenTelemetry setup failed: {e}. Continuing without tracing.")
            return trace.get_tracer(__name__)

    def _build_graph(self) -> StateGraph:
        """Build LangGraph StateGraph with 8 nodes (refactored BDD + new step definitions nodes)"""
        builder = StateGraph(MigrationState)

        builder.add_node("validate", self._node_validate)
        builder.add_node("stage", self._node_stage)
        builder.add_node("explore", self._node_explore)
        builder.add_node("modernize", self._node_modernize)
        builder.add_node("bdd_tests", self._node_bdd_tests)
        builder.add_node("step_defs_template", self._node_step_defs_template)
        builder.add_node("step_defs_enhance", self._node_step_defs_enhance)
        builder.add_node("verify", self._node_verify)

        builder.add_edge(START, "validate")

        builder.add_conditional_edges(
            "validate",
            lambda state: "stage" if not state.get("error") else END,
        )

        builder.add_conditional_edges(
            "stage",
            lambda state: "explore" if not state.get("error") else "verify",
        )

        builder.add_conditional_edges(
            "explore",
            lambda state: "modernize" if not state.get("error") else "verify",
        )

        builder.add_conditional_edges(
            "modernize",
            lambda state: "bdd_tests" if not state.get("error") else "verify",
        )

        builder.add_conditional_edges(
            "bdd_tests",
            lambda state: "step_defs_template" if not state.get("error") else "verify",
        )

        builder.add_conditional_edges(
            "step_defs_template",
            lambda state: "step_defs_enhance" if not state.get("error") else "verify",
        )

        builder.add_edge("step_defs_enhance", "verify")
        builder.add_edge("verify", END)

        return builder.compile()

    def _node_validate(self, state: MigrationState) -> MigrationState:
        """Validate migration request (Stage 1).

        Checks that the legacy-src directory exists and component path is valid.
        Creates OTel span with status (success/failed) and error details.

        Args:
            state: MigrationState from prior node (or initial state)

        Returns:
            MigrationState with error set if validation fails, else error remains None
        """
        span = self.tracer.start_span("node_validate")
        try:
            span.set_attribute("stage_name", "validate")
            print(f"\n{'='*70}\n[STAGE 1/6] VALIDATION\n{'='*70}\n")

            is_valid, error = self._validate_request(state["request"])
            if not is_valid:
                state["error"] = error
                state["stage"] = "validate_failed"
                span.set_attribute("status", "failed")
                print(f"❌ Validation failed: {error}")
            else:
                state["stage"] = "validate"
                span.set_attribute("status", "success")
                print("✅ Validation passed")

            return state
        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "validate_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_stage(self, state: MigrationState) -> MigrationState:
        """Stage component (Stage 2).

        Calls StagingAgent.stage_component() to copy component to run-scoped
        legacy-code/<run_id> directory, generating manifest and metadata.

        Sets run_id in state (used for all downstream stages). Creates OTel
        span with run_id attribute for trace correlation.

        Args:
            state: MigrationState with request (run_id not yet available)

        Returns:
            MigrationState with run_id and staging_results if success,
            else error set and stage marked as stage_failed
        """
        span = self.tracer.start_span("node_stage")
        try:
            span.set_attribute("stage_name", "stage")
            print(f"\n{'='*70}\n[STAGE 2/6] STAGING\n{'='*70}\n")

            success, staging_results = self._stage_component(state["request"].component_name)
            if success:
                state["run_id"] = staging_results.get("run_id")
                state["staging_results"] = staging_results
                state["stage"] = "stage"
                span.set_attribute("status", "success")
                span.set_attribute("run_id", state["run_id"])
            else:
                state["error"] = staging_results.get("error", "Unknown staging error")
                state["stage"] = "stage_failed"
                span.set_attribute("status", "failed")
                print(f"❌ Staging failed: {state['error']}")

            return state
        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "stage_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_explore(self, state: MigrationState) -> MigrationState:
        """Explore component (Stage 3).

        Reads legacy code and calls explore_code() LLM agent to analyze
        code structure, pain points, compliance concerns, refactoring opportunities.

        Skips if prior stage failed (error already set in state). Creates OTel
        span for tracing.

        Args:
            state: MigrationState with run_id from stage node

        Returns:
            MigrationState with exploration_results containing LLM analysis
        """
        span = self.tracer.start_span("node_explore")
        try:
            span.set_attribute("stage_name", "explore")
            print(f"\n{'='*70}\n[STAGE 3/6] EXPLORATION\n{'='*70}\n")

            if state.get("error"):
                span.set_attribute("status", "skipped")
                return state

            success, exploration_results = self._explore_component(
                state["request"].component_name,
                state["run_id"]
            )
            if success:
                state["exploration_results"] = exploration_results
                state["stage"] = "explore"
                span.set_attribute("status", "success")
            else:
                state["error"] = "Exploration failed"
                state["stage"] = "explore_failed"
                span.set_attribute("status", "failed")

            return state
        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "explore_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_modernize(self, state: MigrationState) -> MigrationState:
        """Modernize component (Stage 4).

        For each .cs file, calls modernize_code() LLM agent with legacy code,
        exploration results, and target framework (net10.0). Agent performs
        self-healing: if compilation fails, retries with compiler errors as feedback.

        Stores all modernized files in modernized_code dict. Skips if prior
        error or no .cs files found. Creates OTel span.

        Args:
            state: MigrationState with run_id and exploration_results

        Returns:
            MigrationState with modernized_code dict mapping filename → modernized C# code
        """
        span = self.tracer.start_span("node_modernize")
        try:
            span.set_attribute("stage_name", "modernize")
            print(f"\n{'='*70}\n[STAGE 4/6] MODERNIZATION\n{'='*70}\n")

            if state.get("error"):
                span.set_attribute("status", "skipped")
                return state

            run_id = state.get("run_id")
            legacy_code_path = os.path.join("legacy-code", run_id)
            output_src_dir = os.path.join("migrated-output", run_id, "src")
            failure_log_dir = os.path.join("migrated-output", "result-log")

            component_files = self._read_component_files(legacy_code_path)
            if not component_files:
                state["error"] = f"No .cs files found in {legacy_code_path}"
                state["stage"] = "modernize_failed"
                span.set_attribute("status", "failed")
                return state

            csproj_path, csproj_name = self._find_csproj(legacy_code_path, state["request"].component_name)
            all_modernized_code = {}

            for filename, legacy_code in component_files.items():
                try:
                    modernized = modernize_code(
                        legacy_code=legacy_code,
                        domain_logic=state["exploration_results"].get("domain_logic", ""),
                        exploration=state["exploration_results"],
                        output_dir=output_src_dir,
                        csproj_name=csproj_name,
                        output_filename=filename,
                        target_framework=self.config["global"].get("target_framework", "net10.0"),
                        failure_log_dir=failure_log_dir
                    )
                    all_modernized_code[filename] = modernized
                    print(f"   ✅ {filename} modernized ({len(modernized)} bytes)")
                except Exception as file_error:
                    print(f"\n   ❌ ERROR processing {filename}: {str(file_error)}")
                    raise

            state["modernized_code"] = all_modernized_code
            state["stage"] = "modernize"
            span.set_attribute("status", "success")
            return state
        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "modernize_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_bdd_tests(self, state: MigrationState) -> MigrationState:
        """Generate BDD test scenarios (Gherkin only) (Stage 5).

        Calls generate_bdd_tests() to create Gherkin scenarios from modernized code.
        Old test code generation removed; step definitions now handled by separate nodes.

        Skips if prior error. Creates OTel span.

        Args:
            state: MigrationState with modernized_code

        Returns:
            MigrationState with bdd_tests (Gherkin feature content)
        """
        span = self.tracer.start_span("node_bdd_tests")
        try:
            span.set_attribute("stage_name", "bdd_tests")
            print(f"\n{'='*70}\n[STAGE 5/8] BDD TEST GENERATION\n{'='*70}\n")

            if state.get("error"):
                span.set_attribute("status", "skipped")
                return state

            modernized_code_str = "\n\n".join(state["modernized_code"].values())
            bdd_tests = generate_bdd_tests(modernized_code_str, modernized_code_str, state["exploration_results"])
            self._save_output(state["run_id"], "scenarios.feature", bdd_tests)

            state["bdd_tests"] = bdd_tests
            state["stage"] = "bdd_tests"
            span.set_attribute("status", "success")
            return state

        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "bdd_tests_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_step_defs_template(self, state: MigrationState) -> MigrationState:
        """Generate step definitions skeleton (Stage 6).

        Extracts steps from Gherkin and generates StepDefinitions.cs skeleton
        with [Binding] class, method stubs, and TODO placeholders.

        Skips if prior error. Creates OTel span.

        Args:
            state: MigrationState with bdd_tests (Gherkin content)

        Returns:
            MigrationState with step_definitions_skeleton
        """
        from agents.step_definitions_generator import StepDefinitionSkeletonGenerator

        span = self.tracer.start_span("node_step_defs_template")
        try:
            span.set_attribute("stage_name", "step_defs_template")
            print(f"\n{'='*70}\n[STAGE 6/8] STEP DEFINITIONS TEMPLATE\n{'='*70}\n")

            if state.get("error"):
                span.set_attribute("status", "skipped")
                return state

            generator = StepDefinitionSkeletonGenerator(state["request"].component_name)
            skeleton = generator.generate_skeleton(state["bdd_tests"])
            self._save_output(state["run_id"], "StepDefinitions.cs", skeleton)

            state["step_definitions_skeleton"] = skeleton
            state["stage"] = "step_defs_template"
            span.set_attribute("status", "success")
            return state

        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "step_defs_template_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_step_defs_enhance(self, state: MigrationState) -> MigrationState:
        """Enhance step definitions with LLM (Stage 7).

        Uses LLM to fill TODO implementations in step definitions skeleton.
        Validates via dotnet build. On compilation failure, logs to audit and continues
        (graceful degradation; Reqnroll runner provides diagnostics).

        Skips if prior error. Creates OTel span with compile_success attribute.

        Args:
            state: MigrationState with step_definitions_skeleton, modernized_code

        Returns:
            MigrationState with step_definitions_enhanced
        """
        from agents.step_definitions_enhancer import StepDefinitionEnhancer
        from agents.step_definitions_compiler import StepDefinitionsCompiler

        span = self.tracer.start_span("node_step_defs_enhance")
        try:
            span.set_attribute("stage_name", "step_defs_enhance")
            print(f"\n{'='*70}\n[STAGE 7/8] STEP DEFINITIONS ENHANCEMENT\n{'='*70}\n")

            if state.get("error"):
                span.set_attribute("status", "skipped")
                return state

            # LLM enhancement
            enhancer = StepDefinitionEnhancer()
            enhanced = enhancer.enhance(
                state["step_definitions_skeleton"],
                state["bdd_tests"],
                state["modernized_code"],
                state["exploration_results"]
            )
            self._save_output(state["run_id"], "StepDefinitions.cs", enhanced)

            # Single compilation check
            compiler = StepDefinitionsCompiler()
            compile_result = compiler.compile(state["request"].component_name, state["run_id"])
            compiler.save_to_audit(compile_result, state["run_id"], self.audit_dir)

            state["step_definitions_enhanced"] = enhanced
            state["stage"] = "step_defs_enhance"
            span.set_attribute("compile_success", compile_result["success"])

            if compile_result["success"]:
                span.set_attribute("status", "success")
            else:
                # Graceful failure: log but continue to verification
                span.set_attribute("status", "completed_with_errors")
                print(f"⚠️  Step definitions compilation had errors; continuing to verification...")

            return state

        except Exception as e:
            state["error"] = str(e)
            state["stage"] = "step_defs_enhance_failed"
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _node_verify(self, state: MigrationState) -> MigrationState:
        """Verify compilation and run tests (Stage 8).

        Calls run_tests_and_collect_coverage() to compile modernized code,
        execute tests, and collect coverage metrics.

        ALWAYS runs regardless of prior errors. Gracefully handles missing
        state (e.g., if staging failed, verification reports SKIPPED status).

        Creates OTel span. Final stage before workflow ends.

        Args:
            state: MigrationState (may have error set from prior stages)

        Returns:
            MigrationState with verification_results containing test status,
            pass/fail counts, coverage percentages
        """
        span = self.tracer.start_span("node_verify")
        try:
            span.set_attribute("stage_name", "verify")
            print(f"\n{'='*70}\n[STAGE 8/8] VERIFICATION\n{'='*70}\n")

            if state.get("run_id"):
                verification_results = run_tests_and_collect_coverage(
                    state["request"].component_name,
                    state["run_id"],
                    step_definitions_enhanced=state.get("step_definitions_enhanced")
                )
                state["verification_results"] = verification_results
                span.set_attribute("status", "success")
            else:
                state["verification_results"] = {"status": "SKIPPED", "compiled": False}
                span.set_attribute("status", "skipped")

            state["stage"] = "verify"
            return state
        except Exception as e:
            state["error"] = str(e)
            state["verification_results"] = {"status": "ERROR"}
            span.set_attribute("status", "error")
            span.record_exception(e)
            return state
        finally:
            span.end()

    def _validate_request(self, request: MigrationRequest) -> Tuple[bool, str]:
        """Validate migration request"""
        is_valid, error = self.input_handler.validate_legacy_src_exists()
        if not is_valid:
            return False, error

        component_path = os.path.join("legacy-src", request.component_name)
        if not os.path.exists(component_path):
            return False, f"Component not found: {component_path}"

        return True, ""

    def _stage_component(self, component_name: str) -> Tuple[bool, Dict]:
        """Stage component using staging agent"""
        results = self.staging_agent.stage_component(component_name)
        if results.get("status") == "success":
            return True, results
        else:
            error = "Unknown error"
            for step_result in results.get("steps", {}).values():
                if not step_result.get("success"):
                    error = step_result.get("error", "Unknown error")
                    break
            return False, {"error": error}

    def _explore_component(self, component_name: str, run_id: str) -> Tuple[bool, Dict]:
        """Explore component using explorer agent"""
        component_path = os.path.join("legacy-code", run_id)
        if not os.path.exists(component_path):
            return False, {}

        try:
            file_contents = ""
            for root, dirs, files in os.walk(component_path):
                for file in files:
                    if file.endswith((".cs", ".csproj", ".sln")):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            file_contents += f.read() + "\n"

            exploration = explore_code(file_contents, component_name)
            return True, exploration
        except Exception as e:
            return False, {"error": str(e)}

    def _read_component_files(self, component_path: str) -> Dict[str, str]:
        """Read .cs source files only"""
        files_content = {}
        excluded_dirs = {"obj", "bin", ".vs", "packages"}
        excluded_patterns = {"AssemblyAttributes", "AssemblyInfo", ".AssemblyAttributes.", "TemporaryGeneratedFile"}

        for root, dirs, files in os.walk(component_path):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            if any(exc in root for exc in excluded_dirs):
                continue

            for file in files:
                if file.endswith(".cs"):
                    if any(pattern in file for pattern in excluded_patterns):
                        continue
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        files_content[file] = f.read()

        return files_content

    def _find_csproj(self, legacy_code_path: str, component_name: str) -> Tuple[str, str]:
        """Find .csproj file in legacy code"""
        for root, dirs, files in os.walk(legacy_code_path):
            for file in files:
                if file.endswith(".csproj"):
                    return os.path.join(root, file), file

        csproj_name = f"{component_name}.csproj"
        return os.path.join(legacy_code_path, csproj_name), csproj_name

    def _save_output(self, run_id: str, filename: str, content: str) -> str:
        """Save output to migrated-output directory"""
        is_source_file = filename.endswith(('.cs', '.csproj'))
        is_feature_file = filename.endswith('.feature')
        is_test_file = filename.endswith('.Tests.cs') or "/tests/" in filename.replace("\\", "/")

        if is_test_file or is_feature_file:
            output_dir = os.path.join("migrated-output", run_id, "tests")
        else:
            output_dir = os.path.join("migrated-output", run_id, "src")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"💾 Saved: {filepath}")
        return filepath

    def _log_workflow(self, state: MigrationState, final_status: str) -> None:
        """Log workflow execution to audit trail"""
        log_file = os.path.join(self.audit_dir, "orchestrator.jsonl")

        log_entry = {
            "request": state["request"].to_dict() if hasattr(state["request"], "to_dict") else {"component_name": state["request"].component_name},
            "timestamp_start": datetime.now().isoformat(),
            "timestamp_end": datetime.now().isoformat(),
            "current_stage": state.get("stage", "unknown"),
            "run_id": state.get("run_id"),
            "status": final_status,
            "error": state.get("error"),
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")

    def orchestrate_migration(self, request: MigrationRequest) -> Dict:
        """Main orchestration: execute workflow and return results.

        Entry point for migration workflow. Creates root OTel span, initializes
        MigrationState, invokes LangGraph to execute all 6 stages, logs results
        to audit trail, and prints summary.

        Same interface as OrchestratorV2 for drop-in compatibility.

        Args:
            request: MigrationRequest with component_name, request_id, filters

        Returns:
            Dict with keys:
            - status: "success" | "failed"
            - run_id: Component run identifier (str or None if validation failed)
            - stage: Name of final stage reached
            - error: Error message if any (str or None)
            - artifacts: Dict of all intermediate outputs (staging, exploration,
                        modernization, bdd, test_code, verification)

        Raises:
            Exception: Unhandled exception in graph execution (logged to audit trail)
        """
        root_span = self.tracer.start_span("orchestrate_migration")
        root_span.set_attribute("request_id", request.request_id)
        root_span.set_attribute("component_name", request.component_name)

        try:
            print("\n" + "="*70)
            print(f"🎭 ORCHESTRATOR V3: LangGraph-based Migration Workflow")
            print("="*70)
            print(f"Component: {request.component_name}")
            print(f"Request ID: {request.request_id}")
            print("="*70)

            initial_state: MigrationState = {
                "request": request,
                "run_id": None,
                "stage": "initialized",
                "error": None,
                "staging_results": None,
                "exploration_results": None,
                "modernized_code": None,
                "bdd_tests": None,
                "test_code": None,
                "verification_results": None,
            }

            final_state = self.graph.invoke(initial_state)

            final_status = "success" if not final_state.get("error") else "failed"
            self._log_workflow(final_state, final_status)

            self._print_summary(final_state)

            return {
                "status": final_status,
                "run_id": final_state.get("run_id"),
                "stage": final_state.get("stage"),
                "error": final_state.get("error"),
                "artifacts": {
                    "staging": final_state.get("staging_results"),
                    "exploration": final_state.get("exploration_results"),
                    "modernization": final_state.get("modernized_code"),
                    "bdd": final_state.get("bdd_tests"),
                    "test_code": final_state.get("test_code"),
                    "verification": final_state.get("verification_results"),
                }
            }
        except Exception as e:
            root_span.record_exception(e)
            root_span.set_attribute("status", "error")
            self._log_workflow({"request": request, "error": str(e)}, "error")
            raise
        finally:
            root_span.end()

    def _print_summary(self, state: MigrationState) -> None:
        """Print workflow summary"""
        print("\n" + "="*70)
        print("✨ MIGRATION WORKFLOW COMPLETE")
        print("="*70)
        print(f"\nComponent: {state['request'].component_name}")
        print(f"Status: {'success' if not state.get('error') else 'failed'}")
        print(f"Final Stage: {state.get('stage', 'unknown')}")

        if state.get("verification_results"):
            verification = state["verification_results"]
            print("\n🔬 Verification Details:")
            print(f"  Test Status: {verification.get('status', 'N/A')}")
            print(f"  Passed Tests: {verification.get('passed_tests', 0)} / {verification.get('total_tests', 0)}")

        if state.get("run_id"):
            print(f"\n📁 Source files saved to: migrated-output/{state['run_id']}/src/")
        print(f"📁 Logs and reports saved to: migrated-output/result-log/")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_v3.py <component_name>")
        sys.exit(1)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)

    component_name = sys.argv[1]
    input_handler = InputHandler(legacy_src_dir="legacy-src", audit_dir="migration-poc/audit")
    request, error = input_handler.parse_cli_args(component_name)

    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)

    orchestrator = OrchestratorV3()
    results = orchestrator.orchestrate_migration(request)
    sys.exit(0 if results.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
