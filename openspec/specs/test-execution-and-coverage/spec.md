## Purpose

Enable automated test execution and code coverage reporting within the modernized service pipeline.

## Requirements

### Requirement: Compile and run test suites
The system SHALL compile the modernized component code and the generated unit test files, then execute the tests using the appropriate test runner for the target platform (e.g., `dotnet test` for C#), outputting raw execution and coverage files (e.g. `.trx` and `coverage.cobertura.xml`) without performing verifier reporting analysis.

#### Scenario: Compile and execute C# tests
- **WHEN** the test runner is executed by the test orchestrator
- **THEN** the system compiles the C# codebase and runs the tests using `dotnet test`, outputting raw TRX and Cobertura XML files

### Requirement: Generate test execution report
The system SHALL capture the test results (number of passed, failed, and skipped tests) and generate a JSON/markdown report containing the execution status and diagnostics of any failures.

#### Scenario: Generate test execution report
- **WHEN** a test run completes
- **THEN** a test results file is saved under the `result-log/` or component's output directory

### Requirement: Generate code coverage report
The system SHALL perform code coverage analysis during test execution and generate a report showing line and branch coverage statistics.

#### Scenario: Generate C# code coverage report
- **WHEN** a C# test run is executed with coverage collection enabled
- **THEN** the system uses `coverlet` or `dotnet-coverage` to collect coverage data and writes a report under the `result-log/` or component's output directory

### Requirement: Integrate test runner stage in orchestrator pipeline
The system SHALL run the test runner stage as part of a self-healing test orchestration loop to validate that tests compile and execute, before handing off results to the verifier stage.

#### Scenario: Run verification stage in orchestrator
- **WHEN** the test writer stage completes successfully
- **THEN** the orchestrator runs the verification stage and prints a summary of the test results and coverage in the console and audit logs

#### Scenario: Run test runner in orchestration loop
- **WHEN** the test writer generates or updates test code
- **THEN** the orchestrator runs the test runner to determine if compilation is successful
