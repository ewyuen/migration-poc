## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Orchestrator directs agents in correct sequence

The orchestrator SHALL manage the workflow progression: discovery → staging → modernization → extraction → BDD → test writing → verification. No subsequent stage begins until the prior stage completes successfully.

#### Scenario: Successful progression from discovery to staging
- **WHEN** explorer agent completes component identification
- **THEN** orchestrator directs staging agent to generate a run_id and copy the component into a run_id-scoped subdirectory of legacy-code, with no git branch created

#### Scenario: Workflow halts on agent failure
- **WHEN** modernizer agent reports failure (e.g., compilation error)
- **THEN** orchestrator halts the pipeline and reports the error without invoking subsequent agents

## REMOVED Requirements

### Requirement: Orchestrator creates and manages git branches
**Reason**: Isolation is now provided by run_id-scoped directories rather than git branches, removing the side effect of mutating the user's currently checked-out branch and eliminating the confusing collision-suffix naming behavior. See `legacy-component-staging`'s removed "Staging agent creates feature branch for migration" requirement.
**Migration**: Workflows that relied on a per-migration feature branch remaining available for review/merge should instead use the run_id-scoped directories under `legacy-code/` and `migrated-output/`, identified via `.staging_metadata.json`.
