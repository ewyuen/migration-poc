## ADDED Requirements

### Requirement: Execute Reqnroll tests in verification stage
The system SHALL integrate Reqnroll test execution into the verification stage, running `.feature` files with corresponding `StepDefinitions.cs` bindings.

#### Scenario: Test execution invokes Reqnroll runner
- **WHEN** verification stage runs
- **THEN** system invokes Reqnroll test runner (or Specrun, or dotnet test with Reqnroll)
- **AND** passes location of `.feature` files and `StepDefinitions.cs`

#### Scenario: Feature files are source of truth
- **WHEN** Reqnroll runner executes
- **THEN** it reads `.feature` files, matches steps to `[Given]`/`[When]`/`[Then]` methods
- **AND** executes bound step definitions in order

#### Scenario: Test results capture pass/fail status
- **WHEN** Reqnroll execution completes
- **THEN** results include pass/fail for each scenario
- **AND** failure details (assertion errors, step failures) are captured

### Requirement: Handle missing step definitions gracefully
The system SHALL report if a Gherkin step has no matching step definition binding.

#### Scenario: Unmapped step is reported
- **WHEN** a `.feature` file contains a step with no matching `[Given]`/`[When]`/`[Then]` method
- **THEN** test runner reports this as an error or pending step
- **AND** scenario fails or is marked as incomplete

### Requirement: Collect test coverage
The system SHALL collect code coverage metrics during Reqnroll test execution.

#### Scenario: Coverage data is recorded
- **WHEN** Reqnroll tests run
- **THEN** system instruments code to measure coverage
- **AND** collects line/branch coverage for modernized code

#### Scenario: Coverage report is generated
- **WHEN** test execution completes
- **THEN** verification results include coverage percentages
- **AND** coverage report is available for user review

### Requirement: Report test execution errors
The system SHALL capture and report any test execution failures, compilation errors, or missing dependencies.

#### Scenario: Test failure details reported
- **WHEN** a Reqnroll test fails
- **THEN** verification results include failure reason (assertion failed, exception thrown, etc.)
- **AND** error is traceable to specific step and line in `.feature` file

#### Scenario: Compilation error in step definitions
- **WHEN** `StepDefinitions.cs` cannot be compiled (e.g., mock class missing method)
- **THEN** verification stage reports compilation error
- **AND** indicates which step/scenario is affected

### Requirement: Integration with existing verification pipeline
The system SHALL incorporate Reqnroll test results into existing verification output format.

#### Scenario: Verification results structure
- **WHEN** verification stage completes
- **THEN** `verification_results` dict includes:
  - `test_runner`: "Reqnroll"
  - `status`: "passed" or "failed"
  - `scenarios_run`: count
  - `scenarios_passed`: count
  - `scenarios_failed`: count
  - `coverage`: percentage
  - `errors`: list of error messages

#### Scenario: Results propagate to orchestrator
- **WHEN** verification node completes
- **THEN** `MigrationState.verification_results` is updated
- **AND** workflow proceeds to completion or error handling based on test results
