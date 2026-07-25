## 1. Separate Test Runner Agent

- [x] 1.1 Create `migration-poc/agents/test_runner.py` as a standalone component
- [x] 1.2 Move `.csproj` project generation logic from `verifier.py` to `test_runner.py`
- [x] 1.3 Move `dotnet test` subprocess execution and environment setup to `test_runner.py`
- [x] 1.4 Implement output parser in `test_runner.py` to extract compiler diagnostics (errors like `CSxxxx`, file paths, and line/column numbers)
- [x] 1.5 Verify standalone test runner returns structured build compile results

## 2. Refactor Verifier Agent

- [x] 2.1 Remove compilation, runner execution, and project setup code from `verifier.py`
- [x] 2.2 Refactor `verifier.py` to accept paths to TRX and coverage XML files directly
- [x] 2.3 Ensure verifier focusing only on parsing outcomes and generating markdown/JSON reports works correctly

## 3. Implement Test Orchestrator Agent

- [x] 3.1 Create `migration-poc/agents/test_orchestrator.py`
- [x] 3.2 Implement coordination loop that executes `TestWriterStage` followed by `TestRunner`
- [x] 3.3 Set up attempt limits (maximum 3 attempts) and loop termination conditions
- [x] 3.4 Implement feedback formatter that passes runner compilation errors back to the Test Writer

## 4. Update Test Writer Feedback Integration

- [x] 4.1 Update `TestWriter` client and stage code to accept optional `feedback_errors` parameter
- [x] 4.2 Create refinement prompt template for LLM when compiler errors are provided, instructing it to fix compilation issues
- [x] 4.3 Verify Test Writer successfully rewrites test code based on compiler error context

## 5. Main Orchestrator Integration & Validation

- [x] 5.1 Modify `orchestrator_v2.py` to run the self-healing test orchestration loop in Stage 6 (BDD & Testing)
- [x] 5.2 Modify Stage 7 (Verification) in `orchestrator_v2.py` to run the simplified verifier on the final loop output
- [x] 5.3 Run full migration pipeline on `TestService` component and verify compilation errors are healed automatically
