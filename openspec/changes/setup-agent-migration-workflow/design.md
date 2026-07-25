## Context

The migration POC requires a coordinated, sequential workflow where multiple specialized agents collaborate to modernize legacy .NET components. Currently, we have agents for individual responsibilities (exploration, modernization, extraction, BDD generation) but lack a central orchestration mechanism and clearly defined config structure. The system must support:

1. **User input**: Specify which components to explore and migrate
2. **Component discovery**: Explorer agent identifies components in legacy-src
3. **Sequential pipeline**: Each stage must complete before the next begins
4. **Artifact tracking**: Output from each agent feeds into the next
5. **Reversibility**: Branch creation allows rollback if needed

## Goals / Non-Goals

**Goals:**
- Define config.yaml structure that specifies agent roles and orchestration flow
- Establish orchestrator as the single entry point for migration requests
- Create a sequential pipeline: discovery → staging → modernization → extraction → BDD → test writing → verification
- Enable user specification of target components for exploration
- Ensure each agent's output becomes the input for the next stage
- Support component identification (single component or related sets)
- Create git branches for each migration to isolate changes

**Non-Goals:**
- Parallel execution of pipeline stages (sequential only for this POC)
- Automatic rollback (manual git operations for now)
- GUI for component selection (command-line input in this phase)
- Performance optimization across large codebases

## Decisions

### 1. Orchestrator-Delegate Architecture

**Decision:** Implement a hierarchical agent model where the Orchestrator agent is the sole dispatcher.

**Rationale:** This centralizes control, simplifies error handling, and creates a clear audit trail. Users interact with one entry point (the orchestrator) rather than invoking individual agents.

**Alternatives Considered:**
- Flat agent model where any agent can call any other: Creates circular dependencies and makes sequencing implicit/fragile
- Event-driven pipeline: Good for scale, but adds complexity for a POC that needs clear sequential behavior

### 2. Config.yaml Structure

**Decision:** Define agents as named configurations under `agents:` key with explicit dependencies and tool capabilities.

**Rationale:** YAML is human-readable, supports validation, and integrates with existing infrastructure.

**Structure:**
```
orchestrator:
  role: orchestrator
  tools: [user_input_handler, agent_director, branch_manager]
  delegates: [explorer, modernizer, extractor, bdd_generator, test_writer, verifier]
  workflow: discovery → staging → modernization → extraction → bdd → testing → verification

explorer:
  role: discovery
  input: component_name_or_pattern
  tools: [code_scanner, component_analyzer]
  output: component_inventory

modernizer:
  role: modernization
  input: staged_legacy_code
  tools: [code_transformer, dotnet_api_mapper]
  output: modernized_dotnet10_code

extractor:
  role: domain_logic_extraction
  input: modernized_code
  tools: [ast_analyzer, pattern_matcher, abstraction_generator]
  output: business_logic_specs

bdd_generator:
  role: test_specification
  input: business_logic_specs
  tools: [scenario_generator, gherkin_writer]
  output: gherkin_specifications

test_writer:
  role: test_implementation
  input: gherkin_specifications
  tools: [gherkin_parser, test_code_generator]
  output: executable_tests

verifier:
  role: test_execution
  input: executable_tests
  tools: [test_runner, result_reporter]
  output: test_results
```

**Rationale:** This structure makes dependencies explicit and allows the orchestrator to validate pre-conditions before delegating work.

### 3. Component Staging Workflow

**Decision:** Use three directories with explicit state progression:
- `legacy-src/`: Original source (read-only reference)
- `legacy-code/`: Staging directory for identified components under migration
- `{component}-migration-{date}`: Git branch name for isolated work

**Rationale:** Separates concerns, enables parallel exploration of different components, and provides git-based rollback.

**Workflow:**
1. User specifies component name to explorer
2. Explorer scans legacy-src, validates component exists
3. Orchestrator copies component from legacy-src → legacy-code
4. Orchestrator creates feature branch: `component-migration-YYYYMMDD`
5. Subsequent agents work on legacy-code version in the feature branch

### 4. Agent-to-Agent Communication

**Decision:** Each agent's output is written to a structured artifact file in the legacy-code directory.

**Rationale:** Filesystem-based handoff is simple, auditable, and doesn't require shared state management.

**Artifact Format:**
- `{component}.modernized.csproj`: Modernizer output
- `{component}.extracted-logic.md`: Extractor output
- `{component}.gherkin`: BDD Generator output
- `{component}.generated.cs`: Test Writer output
- `{component}.test-results.json`: Verifier output

### 5. User Input Mechanism

**Decision:** Orchestrator accepts structured input specifying component name and optional filters.

**Rationale:** CLI-friendly, scriptable, supports both interactive and batch workflows.

**Input Format:**
```
orchestrate:
  action: migrate
  component: ComponentName
  filters: [dependency, domain]  # Optional - for identifying related component sets
```

### 6. Error Handling and Sequencing

**Decision:** Orchestrator validates prerequisites before delegating to next agent.

**Rationale:** Prevents cascading failures and gives clear feedback on where workflows fail.

**Validation:**
- Explorer: Verify component exists in legacy-src
- Modernizer: Verify explorer output exists, code is syntactically valid
- Extractor: Verify modernizer output is valid .NET 10 code
- BDD Generator: Verify extractor output is complete
- Test Writer: Verify gherkin is parseable
- Verifier: Verify tests compile and execute

## Risks / Trade-offs

**[Risk] Sequential execution becomes a bottleneck for large codebases**
→ Mitigation: POC accepts this for clarity; future versions can parallelize independent components

**[Risk] Orchestrator becomes a single point of failure**
→ Mitigation: Keep orchestrator logic simple and deterministic; add detailed logging for debugging

**[Risk] Artifact passing via filesystem could lose context**
→ Mitigation: Include metadata (timestamps, version info) in all artifacts; document artifact formats clearly

**[Risk] Git branch explosion if many components are migrated simultaneously**
→ Mitigation: Implement cleanup script to merge/archive completed migration branches

**[Trade-off] Config.yaml becomes the schema for agent behavior**
→ Pro: Centralized, auditable, human-readable
→ Con: Any schema change requires config update; not ideal for rapid experimentation

**[Trade-off] Test Writer is new; functionality unclear from legacy code alone**
→ Mitigation: Gherkin files from BDD Generator provide explicit test intent; Test Writer follows that contract

## Open Questions

1. Should component identification happen automatically (scan and suggest) or explicitly (user provides name)?
2. What should happen if modernization fails partway through? Continue or halt?
3. Should each agent generate a report/summary, or just the final verifier?
4. How deeply should the extractor decompose code (module-level, function-level, algorithm-level)?
