## ADDED Requirements

### Requirement: Compile test project and detect errors
The system SHALL invoke `dotnet build` on the test project directory to detect compilation errors without executing tests.

#### Scenario: Successful compilation on first attempt
- **WHEN** the test project has no compilation errors
- **THEN** the orchestrator SHALL report success and proceed to verification stage

#### Scenario: Detect compiler errors in output
- **WHEN** `dotnet build` fails with compiler errors
- **THEN** the orchestrator SHALL parse the error output to extract error code (e.g., CS1061) and line number

### Requirement: Parse test methods from compilation errors
The system SHALL identify which test methods are causing compilation errors by parsing error line numbers and matching them to method signatures in the test file.

#### Scenario: Identify affected test method
- **WHEN** a compiler error reports line 42 within a test method
- **THEN** the orchestrator SHALL find the method containing line 42 (e.g., `Test_AuthenticateUser_Success`) and mark it for commenting

#### Scenario: Handle multiple errors in same method
- **WHEN** a test method has multiple compilation errors
- **THEN** the orchestrator SHALL comment out the entire method once (not multiple times)

### Requirement: Comment out problematic test methods
The system SHALL replace problematic test methods with comments that preserve the original code while removing it from compilation scope.

#### Scenario: Replace method body with comment
- **WHEN** a test method is identified as problematic
- **THEN** the orchestrator SHALL replace the entire method with a comment block containing the original code (commented out) and the error reason

#### Scenario: Preserve method signature documentation
- **WHEN** commenting out a method
- **THEN** the orchestrator SHALL preserve any XML documentation comments (///) above the method

### Requirement: Loop compilation until success
The system SHALL repeatedly attempt to compile the test project, comment out errors, and recompile until compilation succeeds or maximum iterations exceeded.

#### Scenario: Compile after first comment iteration
- **WHEN** tests are commented out and the file is saved
- **THEN** the orchestrator SHALL invoke `dotnet build` again to check if compilation now succeeds

#### Scenario: Continue looping on persistent errors
- **WHEN** compilation still fails after commenting out tests
- **THEN** the orchestrator SHALL parse new errors, comment out additional tests, and retry (up to configured max iterations)

#### Scenario: Exit after max iterations
- **WHEN** the maximum iteration limit is reached (default 5)
- **THEN** the orchestrator SHALL stop attempting to fix and report final status with commented tests listed

### Requirement: Report commented tests and reasons
The system SHALL produce a report documenting which tests were commented out, on which iteration, and for what reason.

#### Scenario: Generate commented test report
- **WHEN** the orchestration process completes
- **THEN** the orchestrator SHALL return a report containing:
  - List of commented test methods with original line numbers
  - Compiler error code and message for each (e.g., "CS1061: 'AuthService' does not define 'Login'")
  - Iteration number on which each test was commented
  - Total compilation attempts made

#### Scenario: Include commented tests in verification report
- **WHEN** verification stage runs after orchestration
- **THEN** the verification report SHALL include a section documenting commented tests and enable users to understand why tests were excluded

### Requirement: Support configuration
The system SHALL allow configuration of orchestrator behavior via YAML config file.

#### Scenario: Configure maximum iterations
- **WHEN** `config.test_orchestrator.max_iterations` is set to 3
- **THEN** the orchestrator SHALL stop attempting to fix errors after 3 iterations instead of the default 5

#### Scenario: Enable/disable orchestration
- **WHEN** `config.test_orchestrator.enabled` is set to false
- **THEN** the orchestrator stage SHALL be skipped entirely and control passed directly to verification

#### Scenario: Configure comment style
- **WHEN** `config.test_orchestrator.comment_style` is set to "line"
- **THEN** each line of the method SHALL be prefixed with `//` instead of wrapped in `/* */`
