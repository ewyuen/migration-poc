## ADDED Requirements

### Requirement: Orchestrator receives migration requests from user

The orchestrator SHALL accept structured migration requests specifying a component name to migrate and optional filters for identifying related components.

#### Scenario: User requests migration of single component
- **WHEN** user provides component name (e.g., "LegacyAuthService")
- **THEN** orchestrator logs the request and initiates the discovery phase

#### Scenario: User requests migration with related component filters
- **WHEN** user specifies component name and filters (e.g., domain="Authentication", dependency="SqlClient")
- **THEN** orchestrator passes both component name and filters to the explorer agent

### Requirement: Orchestrator generates and propagates a run_id for migration

The orchestrator SHALL obtain a `run_id` from the staging agent for each migration and use it, rather than the bare component name, to resolve `legacy-code/` and `migrated-output/` paths for every subsequent stage.

#### Scenario: run_id threaded to modernization stage
- **WHEN** staging completes and returns run_id "legacyauthservice-072726-143022"
- **THEN** orchestrator reads component source files from legacy-code/legacyauthservice-072726-143022 for the modernization stage

#### Scenario: run_id threaded to test writing and verification stages
- **WHEN** modernization completes for a given run_id
- **THEN** orchestrator directs the test writer and verifier agents to read and write under migrated-output/<run_id> for that same run_id

#### Scenario: component_name remains unchanged for generated code
- **WHEN** orchestrator derives assembly name, root namespace, or .csproj filename during modernization
- **THEN** these are derived from the original component_name, never from run_id

### Requirement: Orchestrator directs agents in correct sequence

The orchestrator SHALL manage the workflow progression: discovery → staging → modernization → extraction → BDD → test writing → verification. No subsequent stage begins until the prior stage completes successfully.

#### Scenario: Successful progression from discovery to staging
- **WHEN** explorer agent completes component identification
- **THEN** orchestrator directs staging agent to generate a run_id and copy the component into a run_id-scoped subdirectory of legacy-code, with no git branch created

#### Scenario: Workflow halts on agent failure
- **WHEN** modernizer agent reports failure (e.g., compilation error)
- **THEN** orchestrator halts the pipeline and reports the error without invoking subsequent agents

### Requirement: Orchestrator validates prerequisites before delegating

The orchestrator SHALL check that prior stage outputs exist and are valid before invoking the next agent.

#### Scenario: Explorer output validation before modernization
- **WHEN** orchestrator prepares to invoke modernizer
- **THEN** orchestrator verifies that explorer's component inventory exists and contains the target component

#### Scenario: Modernizer output validation before extraction
- **WHEN** orchestrator prepares to invoke extractor
- **THEN** orchestrator verifies that modernized code is syntactically valid .NET 10

### Requirement: Orchestrator logs workflow progress

The orchestrator SHALL record each stage's start, completion, and any errors in an audit trail.

#### Scenario: Audit trail records stage transitions
- **WHEN** each agent completes its work
- **THEN** orchestrator logs timestamp, agent name, status (success/failure), and output artifact path

#### Scenario: Workflow failure is logged with context
- **WHEN** an agent fails
- **THEN** orchestrator logs the failure reason, input that caused it, and which stage failed
