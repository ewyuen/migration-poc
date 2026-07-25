## ADDED Requirements

### Requirement: Self-healing test execution loop
The system SHALL coordinate the test writer and test runner stages in a loop, passing compiler errors back to the test writer as feedback for regeneration, until the code compiles successfully or the maximum attempt count is reached.

#### Scenario: Compilation succeeds on first attempt
- **WHEN** the test writer generates code and the test runner compiles it without error on the first attempt
- **THEN** the loop terminates immediately with success, and the verifier is run

#### Scenario: Compilation fails, heals on second attempt
- **WHEN** the first compile attempt fails with syntax errors, and the second attempt (using compiler feedback) compiles successfully
- **THEN** the loop terminates with success, and the verifier is run

#### Scenario: Compilation fails repeatedly, exits after maximum attempts
- **WHEN** the compilation fails on all attempts up to the maximum attempt count (e.g., 3 attempts)
- **THEN** the loop terminates with a fail status, and the verifier is run on the last attempt's results

### Requirement: Error diagnostics feedback to test writer
The system SHALL extract compilation diagnostics (file path, line/column number, error code, and error message) from the failed test runner output and format them as feedback for the test writer.

#### Scenario: Parse and pass compiler errors
- **WHEN** the test runner fails with exit code 1 due to compilation errors
- **THEN** the system parses the error output and provides the list of error messages to the test writer for code correction
