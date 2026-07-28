## Purpose

Define how enhanced `StepDefinitions.cs` files are compiled and validated: a single `dotnet build` check after LLM enhancement (no retry loop), with results logged to the audit trail and graceful continuation to verification on failure.

## Requirements

### Requirement: Compilation via dotnet build after enhancement
The system SHALL compile the enhanced `StepDefinitions.cs` using `dotnet build` against the test project to validate C# syntax and assembly resolution.

#### Scenario: Successful compilation
- **WHEN** LLM enhancement is complete
- **THEN** system generates `tests.csproj` (or reuses existing) referencing the source project
- **AND** invokes `dotnet build` in the tests directory
- **AND** build succeeds (exit code 0)

#### Scenario: Build output includes warnings and errors
- **WHEN** compilation completes
- **THEN** system captures build output for logging
- **AND** extracts structured error messages (file, line, error code, description)

### Requirement: Single compilation check (No Retry Loop)
The system SHALL perform one compilation attempt after LLM enhancement. If compilation succeeds, proceed to verification. If it fails, log the error and continue to verification (graceful degradation).

#### Scenario: Compilation succeeds
- **WHEN** dotnet build runs and completes successfully
- **THEN** `MigrationState.step_definitions_enhanced` is populated
- **AND** `MigrationState.error` remains None
- **AND** verification stage receives valid step definitions

#### Scenario: Compilation fails
- **WHEN** dotnet build fails with compiler errors
- **THEN** system logs full build output to audit trail
- **AND** sets `MigrationState.step_definitions_enhanced` to partial/broken content
- **AND** continues to verification (does NOT retry; Reqnroll test runner provides better diagnostics)

### Requirement: Error logging to audit trail
The system SHALL log compilation errors (whether success or failure) to the audit directory for debugging and traceability.

#### Scenario: Error details logged
- **WHEN** compilation fails
- **THEN** error is logged to `migration-poc/audit/step-definitions-compilation-{run_id}.log`
- **AND** includes timestamp, full build output, and summary

#### Scenario: Success logged
- **WHEN** compilation succeeds
- **THEN** success status is logged to audit trail with build duration

### Requirement: Graceful pipeline continuation
The system SHALL continue to verification stage even if step definitions compilation fails.

#### Scenario: Verification notified of failure
- **WHEN** step definitions compilation fails
- **THEN** verification stage receives `step_definitions_enhanced` as None or partial
- **AND** verification gracefully handles missing/broken step definitions
- **AND** Reqnroll test runner will report "step not implemented" or binding errors
