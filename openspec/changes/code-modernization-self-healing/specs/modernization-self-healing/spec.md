## Purpose

Coordinate code modernization with compilation verification in a self-healing loop that extracts errors and passes them back to the modernizer until code compiles or maximum attempts are reached.

## Requirements

### Requirement: Self-healing modernization loop
The system SHALL coordinate the modernizer LLM and code compiler in a loop, passing compilation errors back to the modernizer as feedback for refinement, until the modernized code compiles successfully or the maximum attempt count is reached.

#### Scenario: Compilation succeeds on first attempt
- **WHEN** the modernizer generates code and the compiler validates it without error on the first attempt
- **THEN** the loop terminates immediately with success, and test generation proceeds

#### Scenario: Compilation fails, heals on second attempt
- **WHEN** the first compilation attempt fails with syntax or type errors, and the second attempt (using compiler feedback) compiles successfully
- **THEN** the loop terminates with success, and test generation proceeds

#### Scenario: Compilation fails repeatedly, exits after maximum attempts
- **WHEN** compilation fails on all attempts up to the maximum attempt count (3 attempts)
- **THEN** the loop terminates with failure status, test generation is skipped, and orchestration exits to the verifier with error report

### Requirement: Extract and format compilation diagnostics
The system SHALL extract compilation diagnostics (file path, line number, error code, and error message) from the C# compiler output and format them as structured feedback for the modernizer.

#### Scenario: Parse and pass compiler errors to modernizer
- **WHEN** the compiler fails with exit code non-zero due to syntax or type errors
- **THEN** the system extracts line number, error code (e.g., CS0103), error message, and type information
- **AND** passes this structured error list to the modernizer for code correction

#### Scenario: Include context in error feedback
- **WHEN** compiler diagnostics are extracted
- **THEN** feedback includes: file name, line number, column (if available), error code, full error message, and context about what type or symbol was missing

### Requirement: Attempt-aware modernizer feedback
The system SHALL indicate to the modernizer the current attempt number and progress within the retry loop, enabling focused refinement strategy.

#### Scenario: Modernizer receives attempt context
- **WHEN** the modernizer is called on attempt 2 or later
- **THEN** feedback includes: current attempt number, total max attempts, and previous errors from prior attempts

#### Scenario: Modernizer uses feedback to refine strategy
- **WHEN** modernizer receives attempt count and previous errors
- **THEN** modernizer can adjust its approach, focusing on fixing specific errors rather than full regeneration

### Requirement: Fail fast on maximum attempts
The system SHALL terminate modernization and skip test generation if code fails to compile after the maximum number of attempts (3), returning a structured error report to the verifier.

#### Scenario: Exit after max attempts with failure report
- **WHEN** compilation fails on attempt 3
- **THEN** the orchestration exits the modernization loop without attempting test generation
- **AND** a failure report is generated containing all 3 attempts' errors and passed to the verifier

#### Scenario: Test generation is skipped on modernization failure
- **WHEN** modernization loop exits with failure status
- **THEN** stages for BDD generation and test writing are skipped entirely
- **AND** the verifier receives a report indicating modernization failed before reaching test generation
