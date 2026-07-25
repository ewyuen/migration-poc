## Why

During component modernization, generated unit test code often fails to compile on the first attempt due to minor syntax issues or mismatched dependencies. Integrating a self-healing orchestration loop between the test writer and the test runner ensures that compilation errors are resolved automatically using LLM feedback before the verifier performs final analysis. Additionally, separating the execution (Test Runner) from analysis (Verifier) makes the testing pipeline more modular, robust, and maintainable.

## What Changes

- **Separation of Test Runner and Verifier**: The test runner is isolated into a standalone component (`test_runner.py`) responsible only for project file setup, compilation, and execution. The verifier (`verifier.py`) is simplified to focus strictly on analyzing results and coverage and generating final reports.
- **Self-Healing Test Orchestration Loop**: Implemented a coordinator/orchestrator loop (`test_orchestration.py`) that feeds compiler diagnostics from failed test runs back into the test writer to heal and regenerate code until it compiles successfully (up to a maximum attempt limit).
- **Interface Updates**: Updated Stage 6 and Stage 7 in the main orchestrator to invoke this self-healing loop.

## Capabilities

### New Capabilities
- `self-healing-test-orchestration`: Defines the loop coordination requirements, feedback loops, attempt counters, and exit strategies for automated test healing.

### Modified Capabilities
- `test-execution-and-coverage`: Modify requirements to explicitly separate compilation and execution from result reporting, defining the boundary interface between the runner and the verifier.

## Impact

- **Affected Components**: `orchestrator_v2.py`, `agents/verifier.py`, `agents/test_writer.py`, and `agents/test_writer_stage.py`.
- **Handoff Files**: Introduces internal feedback structures for passing build errors back to the test writer.
