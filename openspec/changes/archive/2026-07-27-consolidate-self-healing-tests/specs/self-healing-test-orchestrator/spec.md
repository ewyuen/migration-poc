## ADDED Requirements

### Requirement: TestOrchestrator coordinates multi-attempt test generation
The system SHALL run a self-healing loop that attempts to generate compilable tests up to 4 times. Each attempt fills test skeletons with implementations and compiles them. If compilation fails, errors are captured and the next attempt uses those errors as feedback.

#### Scenario: Successful compilation on first attempt
- **WHEN** TestOrchestrator.execute() is called for a component with skeleton tests
- **THEN** TestWriterStage fills skeletons and TestRunner compiles successfully on the first attempt
- **AND** the orchestrator returns with status="success", compiled=True, attempts=1

#### Scenario: Recovery after compilation failure
- **WHEN** TestWriterStage.execute() is called with feedback_errors from a previous failed compilation
- **THEN** the test writer agent receives the error context and adjusts implementations accordingly
- **AND** TestRunner attempts to compile again with the adjusted code

#### Scenario: All 4 attempts exhaust without success
- **WHEN** compilation fails on all 4 attempts despite TestWriterStage adjustments
- **THEN** TestOrchestrator identifies failing test method names from compilation errors
- **AND** comments out those test methods with TODO markers explaining the failure
- **AND** performs one final compilation with commented tests
- **AND** returns with compiled=True (final state after commenting), commented_tests=[...], attempts=4

### Requirement: TestOrchestrator reports orchestration results transparently
The system SHALL return a result dictionary that clearly documents the orchestration attempt history and final state.

#### Scenario: Return value includes attempt metadata
- **WHEN** TestOrchestrator.execute() completes
- **THEN** the return dictionary includes:
  - attempts: integer count of attempts made
  - compiled: boolean indicating final compilation success
  - errors: list of final error messages (if any)
  - commented_tests: list of test method names that were commented out
  - tests_dir: path to the tests directory

#### Scenario: Verification stage can consume orchestration results
- **WHEN** orchestrator_v2.py Stage 6 (Verification) receives the orchestration result
- **THEN** it can distinguish between clean compilation (no commented tests) and recovered-with-comments
- **AND** it reports both cases transparently without failing the workflow

### Requirement: TestWriterStage accepts feedback from prior failures
The system SHALL modify TestWriterStage.execute() to accept an optional feedback_errors parameter.

#### Scenario: TestWriterStage without feedback (backward compatible)
- **WHEN** TestWriterStage.execute(component_name) is called without feedback_errors
- **THEN** the system behaves as before (no regression)

#### Scenario: TestWriterStage with feedback from compilation errors
- **WHEN** TestWriterStage.execute(component_name, feedback_errors=[...]) is called
- **THEN** feedback_errors are passed to the test writer agent as context
- **AND** the agent uses the context to adjust test implementations in the next iteration

### Requirement: Failing tests are gracefully commented out, not deleted
The system SHALL preserve test code by commenting it out rather than deleting it. Each commented test SHALL include a TODO marker.

#### Scenario: Failing test method is commented
- **WHEN** a test method fails to compile after all attempts
- **THEN** the method is wrapped in multi-line comments (/* ... */)
- **AND** a TODO comment is prepended explaining the failure reason
- **AND** the original test code remains readable in the comments

#### Scenario: Commented tests are visible in final output
- **WHEN** orchestrator_v2.py reads the final test file from disk after TestOrchestrator completes
- **THEN** the file contains both active tests and commented-out tests
- **AND** the count of commented tests is reported in state.artifacts["test_orchestration"]["commented_tests"]

### Requirement: Orchestration loop has configurable max attempts
The system SHALL support a configurable maximum number of attempts (default: 4).

#### Scenario: Max attempts is read from config
- **WHEN** TestOrchestrator is initialized with config parameter
- **THEN** it uses config.get("max_attempts", 4) to set the loop limit
- **AND** each attempt is logged with "Attempt N of M" messaging

#### Scenario: Hardcoded limit is used if config is not provided
- **WHEN** TestOrchestrator is called without a config or config lacks max_attempts
- **THEN** the system defaults to 4 attempts
