## Why

The current test generation pipeline is brittle — if generated tests don't compile, the entire workflow fails and halts. We need a resilient test generation phase that can self-heal by iteratively improving test implementations and, as a last resort, gracefully commenting out failing tests while allowing the verification phase to run and report. This enables the 6-step pipeline to stay operational and transparent about test quality.

## What Changes

- **Stage 5 (BDD & Test Writing)** now wraps test generation + compilation in a self-healing loop
- **TestOrchestrator** (from manual-tests) orchestrates up to 4 attempts to generate compilable tests
  - Each attempt: TestWriterStage fills test skeletons → TestRunner compiles & executes
  - If compilation fails, extract errors and retry with feedback
  - After 4 attempts: Comment out failing tests and do final compile
- **TestWriterStage.execute()** gains `feedback_errors` parameter to learn from previous failures
- **TestRunner** (dotnet test) integrated to validate compilability
- Tests that are commented out do NOT fail the workflow — verification stage reports them and proceeds
- All test artifacts remain transparent: original, skeleton, filled, and final versions

## Capabilities

### New Capabilities
- `self-healing-test-orchestrator`: Multi-attempt test generation with automatic error recovery. Maintains compilability through iterative refinement and graceful fallback (commenting failing tests).

### Modified Capabilities
- `bdd-test-generation`: Modified behavior in orchestration only (Stage 5 now calls TestOrchestrator instead of direct TestWriterStage). Core generation logic unchanged.

## Impact

- **Code changes**: orchestrator_v2.py (Stage 5 refactor), test_writer_stage.py (add feedback_errors), + test_orchestrator.py, test_runner.py (from manual-tests)
- **Pipeline behavior**: Stage 5 now resilient to test compilation failures. Tests may be commented out but workflow proceeds to Stage 6 verification.
- **Artifacts**: Test code files now include commented sections with TODO markers explaining why tests were disabled.
- **No breaking changes**: The 6-step pipeline structure unchanged. Verification stage still reports test status accurately.
