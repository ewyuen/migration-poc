## Purpose

Define OrchestratorV3, a LangGraph-based reimplementation of the migration orchestrator that models the migration workflow as an explicit `StateGraph` (nodes, edges, and a typed state schema) while wrapping the existing agents unchanged and preserving the OrchestratorV2 entry point and audit trail behavior. The workflow is an 8-stage pipeline (the original 6 stages plus two Reqnroll step definitions stages) that generates business-readable Gherkin, binds it to C# step definitions, and executes BDD tests as part of verification.

## Requirements

### Requirement: OrchestratorV3 with LangGraph StateGraph - Extended with Step Definitions
OrchestratorV3 SHALL use LangGraph's StateGraph to define an 8-stage migration workflow (original 6 stages + 2 new step definitions stages). The workflow topology SHALL be explicit as a directed graph with nodes and edges, including new nodes `step_defs_template` and `step_defs_enhance`.

#### Scenario: Create OrchestratorV3 instance with refactored stages
- **WHEN** caller instantiates `OrchestratorV3(config_path=...)`
- **THEN** OrchestratorV3 initializes LangGraph StateGraph with 8 nodes and conditional edges
- **AND** graph includes original 5 stages + refactored BDD (Gherkin only) + 2 new step definitions stages

#### Scenario: Execute migration workflow with step definitions stages
- **WHEN** caller invokes `orchestrator.orchestrate_migration(request: MigrationRequest)`
- **THEN** graph executes stages in order: validate → stage → explore → modernize → bdd_tests → step_defs_template → step_defs_enhance → verify → END

#### Scenario: Graph continues to verification despite stage failures
- **WHEN** stage N fails (error set in state)
- **THEN** graph continues to stage N+1 (e.g., if modernization fails, still run verification)

#### Scenario: Step definitions stages route to verification on error
- **WHEN** `step_defs_template` or `step_defs_enhance` fails (error set in state)
- **THEN** graph continues to `verify` node (best-effort; verification handles missing step definitions)

### Requirement: State schema as TypedDict
MigrationState SHALL be a TypedDict defining exactly which fields flow between nodes, with type hints for clarity.

#### Scenario: State contains only required fields per-node
- **WHEN** a node completes
- **THEN** state includes only fields needed by the next node (minimal coupling)

#### Scenario: State passed automatically between nodes
- **WHEN** graph transitions from node A to node B
- **THEN** state is passed as dict; node B receives it as-is, no manual threading

### Requirement: Extended state schema with step definitions fields
MigrationState SHALL include two new fields for step definitions: `step_definitions_skeleton` and `step_definitions_enhanced`.

#### Scenario: State includes skeleton field
- **WHEN** `step_defs_template` node completes
- **THEN** state includes `step_definitions_skeleton: Optional[str]` with generated skeleton

#### Scenario: State includes enhanced field
- **WHEN** `step_defs_enhance` node completes
- **THEN** state includes `step_definitions_enhanced: Optional[str]` with LLM-filled implementations

#### Scenario: State carries skeleton through enhancement
- **WHEN** `step_defs_enhance` node receives state from `step_defs_template`
- **THEN** `step_definitions_skeleton` is available in the state

### Requirement: Nodes wrap existing agents unchanged
Each of the 6 stages SHALL be a LangGraph node that calls the corresponding agent/function without modification.

#### Scenario: Node calls existing StagingAgent
- **WHEN** node_stage() runs
- **THEN** it calls `self.staging_agent.stage_component()` exactly as OrchestratorV2 does

#### Scenario: Node calls existing explorer function
- **WHEN** node_explore() runs
- **THEN** it calls `explore_code(...)` exactly as OrchestratorV2 does

#### Scenario: Node handles agent exceptions gracefully
- **WHEN** an agent raises an exception
- **THEN** node catches it, sets error in state, and returns state for graph to continue

### Requirement: Step definitions template node wraps generator
The `step_defs_template` LangGraph node SHALL call step definitions generation logic without modification.

#### Scenario: Node calls skeleton generator
- **WHEN** `node_step_defs_template()` runs
- **THEN** it calls generator function with Gherkin from `bdd_tests` state
- **AND** updates state with `step_definitions_skeleton`

#### Scenario: Node handles generator exceptions
- **WHEN** skeleton generation raises an exception
- **THEN** node catches it, sets error in state, returns state for graph to continue

#### Scenario: Node includes OpenTelemetry tracing
- **WHEN** node executes
- **THEN** creates OTel span with attributes like status, features_processed

### Requirement: Step definitions enhancement node (single compile check)
The `step_defs_enhance` LangGraph node SHALL run LLM enhancement with single compilation validation.

#### Scenario: Node runs LLM enhancement (single pass)
- **WHEN** `node_step_defs_enhance()` runs
- **THEN** it calls LLM once with full context (modernized code, Gherkin, domain intent)
- **AND** LLM generates enhanced implementations
- **AND** continues to compilation

#### Scenario: Node compiles and validates (single check)
- **WHEN** enhancement completes
- **THEN** node invokes `dotnet build` against test project
- **AND** captures output

#### Scenario: Node handles compilation failure gracefully
- **WHEN** compilation fails
- **THEN** node logs error to audit trail
- **AND** sets `step_definitions_enhanced` to LLM output (even if broken)
- **AND** graph continues to verification (Reqnroll test runner provides diagnostics)

#### Scenario: Node includes status in tracing
- **WHEN** node completes
- **THEN** OTel span includes attribute `compile_success: true/false`
- **AND** no retry counter (single pass)

### Requirement: Same entry point interface as OrchestratorV2
OrchestratorV3 SHALL provide the same public method signature as OrchestratorV2 for drop-in compatibility.

#### Scenario: Entry point: orchestrate_migration(request)
- **WHEN** caller invokes `orchestrator_v3.orchestrate_migration(request)`
- **THEN** method accepts MigrationRequest and returns dict with status, artifacts, stages

#### Scenario: Return dict structure matches V2
- **WHEN** orchestration completes
- **THEN** returned dict includes: timestamp_start, timestamp_end, current_stage, completed_stages, status, artifacts

### Requirement: Conditional edges for error handling
Graph edges SHALL use conditional functions to route based on error state.

#### Scenario: Skip modernization if exploration failed
- **WHEN** node_explore sets error in state
- **THEN** conditional edge skips node_modernize and jumps to verification

#### Scenario: Always route to verification
- **WHEN** any stage completes (success or failure)
- **THEN** verification node is always reached (no early exits except critical config errors)

### Requirement: Graph edge sequence
Graph edges SHALL route through all 8 nodes in sequence, with conditional routing for errors.

#### Scenario: Happy path edge sequence
- **WHEN** all stages succeed
- **THEN** edges flow: START → validate → stage → explore → modernize → bdd_tests → step_defs_template → step_defs_enhance → verify → END

#### Scenario: Error routing skips intermediate stage
- **WHEN** `step_defs_template` sets error in state
- **THEN** conditional edge routes to `verify` (skips `step_defs_enhance`)

### Requirement: Verify node handles optional step definitions
The verification node SHALL handle cases where `step_definitions_enhanced` is None or contains errors.

#### Scenario: Verify proceeds with or without step definitions
- **WHEN** verification node runs
- **THEN** if `step_definitions_enhanced` is present, use it
- **AND** if None, report as unavailable and continue with best-effort verification

### Requirement: Audit trail logging preserved
After graph completes, orchestrator SHALL write workflow state to `orchestrator.jsonl` with same format as OrchestratorV2.

#### Scenario: Write to audit log after success
- **WHEN** graph execution completes successfully
- **THEN** final state dict is appended to `migration-poc/audit/orchestrator.jsonl`

#### Scenario: Write to audit log after failure
- **WHEN** graph execution fails
- **THEN** error state is appended to audit log with failed_stage and error_message
