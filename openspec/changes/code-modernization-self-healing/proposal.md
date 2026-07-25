## Why

Currently, the code modernizer generates modernized code once and proceeds directly to test generation without verifying that the generated code compiles. If the modernized code has syntax errors or type mismatches, these are not discovered until test execution, wasting effort on test generation for code that is fundamentally broken. By adding a self-healing loop to the modernization stage, we can fail fast and give the modernizer multiple chances to fix compilation errors before proceeding, or fail the entire orchestration if the code cannot be fixed.

## What Changes

- Add a **ModernizationOrchestrator** agent that wraps the modernization LLM call in a loop
- After each modernization attempt, compile the generated code to verify it compiles in isolation
- Extract compilation errors (line number, error message, type information) from the C# compiler output
- Pass compilation errors back to the modernizer as feedback for refinement (up to 3 attempts total)
- If modernized code still does not compile after 3 attempts, fail the entire orchestration and exit (do not attempt test generation)
- Update the main orchestrator to integrate the modernization self-healing loop, skip test generation on failure, and pass modernization failures to the verifier for reporting

## Capabilities

### New Capabilities
- `modernization-self-healing`: Self-healing loop for code modernization that verifies compilation, extracts errors, and passes feedback back to the modernizer until code compiles or max attempts exhausted

### Modified Capabilities
- `code-modernization-dotnet10`: Modernizer LLM will now be called in a loop with feedback from compilation errors; must handle attempt count and previous errors in prompt context
- `agent-orchestration`: Main orchestrator pipeline must integrate the modernization self-healing loop before test generation; must handle modernization failures and skip test generation if modernization fails

## Impact

- **Modernization stage becomes blocking** - Tests are not generated unless modernized code compiles
- **Faster fail detection** - Compilation errors are caught immediately, not during test execution
- **Reduced wasted work** - No time spent generating/running tests for code that won't compile
- **Clearer error reporting** - Modernization failures are explicitly reported by the verifier with detailed error context
- **Modified orchestration flow** - Stages 6 and 7 (test generation and execution) are now conditional on successful modernization
