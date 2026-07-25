## Why

Currently, the migration pipeline's TestWriterStage generates test implementations, but the subsequent Verification stage only attempts to compile tests once. When compilation fails due to generated test errors, the workflow simply reports the errors without attempting to fix them. This requires manual intervention to comment out problematic tests and re-run the pipeline. A test orchestrator that iteratively fixes compilation errors will enable the pipeline to reach a compilable state automatically, reducing manual intervention and improving migration reliability.

## What Changes

- Add a new Test Orchestration stage (Stage 5A) between TestWriterStage and Verification that iteratively compiles tests and fixes errors
- Parse dotnet test compilation errors to identify which test methods are problematic
- Automatically comment out tests that cannot be fixed by regeneration
- Loop compilation attempts up to a configurable maximum (default: 5 iterations)
- Track and report which tests were commented out and why
- Exit with success when the test project compiles successfully, or with partial success if only some tests needed commenting
- Integration with existing orchestrator workflow to report commented tests in verification reports

## Capabilities

### New Capabilities
- `test-compilation-orchestrator`: Iterative test compilation with automatic error fixing by commenting out problematic tests. Parses compilation errors, identifies affected methods, and loops until compilation succeeds or max retries reached.

### Modified Capabilities
- `verification-stage`: Modified to depend on test-compilation-orchestrator completing first. Verification now receives a pre-compiled test project and reports statistics on originally-commented vs compilation-fixed tests.

## Impact

- **Code affected**: `orchestrator_v2.py` (adds new stage 5A), new file `agents/test_orchestrator.py`
- **Workflow stages**: Inserts new stage between stage 5 (TestWriterStage) and stage 6 (Verification)
- **APIs**: Returns report with `commented_tests`, `compilation_attempts`, `errors_fixed` metadata
- **Behavior**: Test projects that previously failed to compile will now compile with degraded test coverage (some tests commented out) rather than full failure
