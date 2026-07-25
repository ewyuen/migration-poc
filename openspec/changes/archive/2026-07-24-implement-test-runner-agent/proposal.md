## Why

Currently, the migration orchestrator pipeline only generates BDD test cases and implements skeleton tests, but does not run the tests or analyze code coverage. Additionally, generating all test-related files directly under the component output directory clutters the main application codebase structure, making it harder to distinguish production code from testing assets.

## What Changes

- **Test Execution**: Implement a new test runner capability (re-enabling/extending the Verification stage) that compiles and runs the C# test suite, producing structured test results.
- **Coverage Analysis**: Run code coverage analysis to generate reports on test coverage.
- **Output Reorganization**: Restructure the output directory layout such that Gherkin files (`scenarios.feature`) and unit test files (`*.Tests.cs`) are generated within a dedicated `tests/` subdirectory inside the migrated component output directory (e.g., `migrated-output/<component_name>/tests/`).
- **Test Writer Stage Update**: Update `TestWriterStage` to scan for and fill skeleton test files inside the `tests/` subfolder.

## Capabilities

### New Capabilities
- `test-execution-and-coverage`: Compiles, executes tests, and generates structured test results and code coverage reports.

### Modified Capabilities
- `gherkin-test-generation`: Restructures the output layout so Gherkin scenarios and test files are isolated within a dedicated `tests/` subdirectory.

## Impact

- `migration-poc/orchestrator_v2.py`: Integration of test execution stage and adjustment of Gherkin/test paths.
- `migration-poc/agents/test_writer_stage.py`: Location path scanning for skeleton files.
- `migration-poc/agents/verifier.py`: Invocation of dotnet test and coverage analysis tools.
