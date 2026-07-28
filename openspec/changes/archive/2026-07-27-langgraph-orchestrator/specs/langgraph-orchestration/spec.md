## ADDED Requirements

### Requirement: OrchestratorV3 with LangGraph StateGraph
OrchestratorV3 SHALL use LangGraph's StateGraph to define and execute a 6-stage migration workflow. The workflow topology SHALL be explicit as a directed graph with nodes (stages) and edges (transitions), making it visualizable and debuggable.

#### Scenario: Create OrchestratorV3 instance
- **WHEN** caller instantiates `OrchestratorV3(config_path=...)`
- **THEN** OrchestratorV3 initializes LangGraph StateGraph with 6 nodes and conditional edges

#### Scenario: Execute migration workflow
- **WHEN** caller invokes `orchestrator.orchestrate_migration(request: MigrationRequest)`
- **THEN** graph executes all 6 stages in order, managing state transitions automatically

#### Scenario: Graph continues to verification despite stage failures
- **WHEN** stage N fails (error set in state)
- **THEN** graph continues to stage N+1 (e.g., if modernization fails, still run verification)

### Requirement: State schema as TypedDict
MigrationState SHALL be a TypedDict defining exactly which fields flow between nodes, with type hints for clarity.

#### Scenario: State contains only required fields per-node
- **WHEN** a node completes
- **THEN** state includes only fields needed by the next node (minimal coupling)

#### Scenario: State passed automatically between nodes
- **WHEN** graph transitions from node A to node B
- **THEN** state is passed as dict; node B receives it as-is, no manual threading

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

### Requirement: Audit trail logging preserved
After graph completes, orchestrator SHALL write workflow state to `orchestrator.jsonl` with same format as OrchestratorV2.

#### Scenario: Write to audit log after success
- **WHEN** graph execution completes successfully
- **THEN** final state dict is appended to `migration-poc/audit/orchestrator.jsonl`

#### Scenario: Write to audit log after failure
- **WHEN** graph execution fails
- **THEN** error state is appended to audit log with failed_stage and error_message
