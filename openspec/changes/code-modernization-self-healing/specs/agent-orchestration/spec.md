## MODIFIED Requirements

### Requirement: Orchestrator directs agents in correct sequence

The orchestrator SHALL manage the workflow progression: discovery → staging → exploration → extraction → modernization (with self-healing compilation loop) → (conditional) BDD → test writing → verification. Modernization with compilation verification MUST succeed before proceeding to BDD and test generation. If modernization fails after maximum attempts, test generation is skipped and orchestrator proceeds directly to verifier for failure reporting.

#### Scenario: Successful progression from discovery to staging
- **WHEN** explorer agent completes component identification
- **THEN** orchestrator directs staging agent to create branch and copy component to legacy-code folder

#### Scenario: Modernization with compilation verification precedes test generation
- **WHEN** extraction completes successfully
- **THEN** orchestrator runs the modernization loop with compilation verification
- **AND** if compilation succeeds, orchestrator proceeds to BDD generation
- **AND** if compilation fails after 3 attempts, orchestrator skips test generation and proceeds to verifier

#### Scenario: Workflow halts on modernization failure after max attempts
- **WHEN** modernization loop reports failure after 3 attempts (code still won't compile)
- **THEN** orchestrator halts test generation and test writing stages
- **AND** orchestrator proceeds directly to verifier with modernization failure report
- **AND** test generation and execution stages are skipped

### Requirement: Orchestrator validates prerequisites before delegating

The orchestrator SHALL check that prior stage outputs exist and are valid before invoking the next agent. For modernization, this includes verification that generated code compiles in isolation.

#### Scenario: Explorer output validation before modernization
- **WHEN** orchestrator prepares to invoke modernizer
- **THEN** orchestrator verifies that explorer's component inventory exists and contains the target component

#### Scenario: Modernization compilation validation before test generation
- **WHEN** modernization loop completes with claimed success
- **THEN** orchestrator verifies that generated code compiles without errors
- **AND** if compilation fails, orchestrator recognizes failure and does not proceed to test generation

#### Scenario: Skip test generation on modernization failure
- **WHEN** orchestrator detects modernization compilation failure
- **THEN** orchestrator does not invoke test generation, BDD, or test writing agents
- **AND** proceeds directly to verifier with failure report

### Requirement: Orchestrator handles conditional stage execution

The orchestrator SHALL implement conditional execution: test generation and test execution stages only run if modernization compilation succeeds. If modernization fails, verifier runs regardless to report the failure.

#### Scenario: Test generation only runs after successful modernization
- **WHEN** modernization loop reports success (code compiles)
- **THEN** orchestrator proceeds to BDD and test generation stages

#### Scenario: Test generation and execution skipped on modernization failure
- **WHEN** modernization loop reports failure (code won't compile after 3 attempts)
- **THEN** orchestrator skips BDD generation, test writing, and test execution stages
- **AND** proceeds directly to verifier with modernization error report

#### Scenario: Verifier reports success or failure consistently
- **WHEN** modernization succeeds: verifier reports test execution results
- **WHEN** modernization fails: verifier reports modernization failure
- **THEN** verifier serves as single source of truth for overall migration success/failure
