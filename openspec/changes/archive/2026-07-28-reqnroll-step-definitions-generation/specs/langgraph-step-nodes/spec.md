## ADDED Requirements

### Requirement: New LangGraph node for step definitions template generation
The system SHALL add a `step_defs_template` node to the orchestrator LangGraph that generates skeleton `StepDefinitions.cs` from Gherkin features.

#### Scenario: Node executes after BDD generation
- **WHEN** BDD generation completes (Gherkin only; old test code generation is removed)
- **THEN** graph routes to `step_defs_template` node
- **AND** node receives `MigrationState` with `bdd_tests` field populated (single Gherkin string)

#### Scenario: Node produces state update
- **WHEN** template node executes
- **THEN** `MigrationState.step_definitions_skeleton` is populated with skeleton `StepDefinitions.cs` content
- **AND** state is passed to next node

#### Scenario: Node includes OpenTelemetry tracing
- **WHEN** template node executes
- **THEN** system creates OTel span with status (success/failed)
- **AND** span includes attributes like `status`, `feature_files_processed`, etc.

### Requirement: New LangGraph node for step definitions enhancement
The system SHALL add a `step_defs_enhance` node to the orchestrator LangGraph that runs LLM enhancement with single compilation check (no retry loop).

#### Scenario: Node receives skeleton and context
- **WHEN** enhancement node starts
- **THEN** it receives `MigrationState` with `step_definitions_skeleton`, `modernized_code`, `bdd_tests` fields
- **AND** builds full context bundle including modernized code, scenario intent, domain rules

#### Scenario: Node runs LLM enhancement (single pass)
- **WHEN** enhancement node runs
- **THEN** it calls LLM once with full context to fill skeleton implementations
- **AND** LLM infers parameter mapping, ScenarioContext keys, mock generation
- **AND** returns enhanced `StepDefinitions.cs` content

#### Scenario: Node compiles enhanced code (single check)
- **WHEN** LLM enhancement completes
- **THEN** node invokes `dotnet build` against test project
- **AND** captures build output (success or errors)

#### Scenario: Node produces output on successful compilation
- **WHEN** compilation succeeds
- **THEN** `MigrationState.step_definitions_enhanced` is populated
- **AND** `MigrationState.error` is null
- **AND** state passed to verification

#### Scenario: Node reports failure gracefully (no retry)
- **WHEN** compilation fails
- **THEN** `MigrationState.step_definitions_enhanced` is populated with LLM output (even if broken)
- **AND** error logged to audit trail
- **AND** graph continues to verification (Reqnroll runner provides diagnostic feedback)

#### Scenario: Node includes tracing
- **WHEN** enhancement node executes
- **THEN** OTel span includes attributes like `status`, `compile_success`, `error_summary` (if failed)
- **AND** no attempt counter (single pass, not retry loop)

### Requirement: Node routing in graph
The system SHALL integrate the two new nodes into the orchestrator graph between BDD generation and verification.

#### Scenario: Correct edge sequence
- **WHEN** orchestrator graph is built
- **THEN** edges flow: `bdd_tests` → `step_defs_template` → `step_defs_enhance` → `verify` → END
- **AND** conditional routing based on error state continues to work

#### Scenario: Error handling maintains graph integrity
- **WHEN** step_defs_template encounters error
- **THEN** graph can skip to `verify` (or continue with error state)
- **AND** verify node handles missing `step_definitions_enhanced` gracefully

### Requirement: MigrationState extensions
The system SHALL add fields to `MigrationState` TypedDict to carry skeleton and enhanced step definitions through the workflow.

#### Scenario: State includes skeleton field
- **WHEN** `MigrationState` is defined
- **THEN** it includes `step_definitions_skeleton: Optional[str]` field
- **AND** can be None or populated with generated skeleton

#### Scenario: State includes enhanced field
- **WHEN** `MigrationState` is defined
- **THEN** it includes `step_definitions_enhanced: Optional[str]` field
- **AND** can be None or populated with LLM-enhanced content
