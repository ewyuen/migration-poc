## 1. Prepare agents from manual-tests branch

- [x] 1.1 Copy test_orchestrator.py from feat/manual-tests to agents/ (ensures TestOrchestrator class with execute() method exists)
- [x] 1.2 Copy test_runner.py from feat/manual-tests to agents/ (ensures run_test_runner() function exists)
- [x] 1.3 Verify both files have correct imports and no hard dependencies on other manual-tests code
- [x] 1.4 Update agents/__init__.py if needed to export TestOrchestrator

## 2. Update TestWriterStage for feedback support

- [x] 2.1 Add `feedback_errors: Optional[List[str]] = None` parameter to TestWriterStage.execute() signature
- [x] 2.2 Pass feedback_errors to self.agent.write_tests() if provided (preserves backward compatibility)
- [x] 2.3 Verify TestWriterAgent can accept feedback_errors and uses it as context for LLM prompts
- [x] 2.4 Add logging to show feedback_errors being passed when present

## 3. Refactor orchestrator_v2.py Stage 5

- [x] 3.1 Import TestOrchestrator in orchestrator_v2.py: `from agents.test_orchestrator import TestOrchestrator`
- [x] 3.2 Initialize TestOrchestrator instance in __init__ with config parameter: `self.test_orchestrator = TestOrchestrator(config=self.config.get("test_orchestrator"))`
- [x] 3.3 In orchestrate_migration(), replace the direct TestWriterStage.execute() call with TestOrchestrator.execute(request.component_name)
- [x] 3.4 Capture orchestration result: `orchestrator_result = self.test_orchestrator.execute(request.component_name)`
- [x] 3.5 Update state.artifacts to include test orchestration result: `state.artifacts["test_orchestration"] = orchestrator_result`
- [x] 3.6 Keep BDD generation and skeleton generation as-is (before the TestOrchestrator call)
- [x] 3.7 Read final test code from disk after orchestrator completes (existing pattern at lines 444-447)
- [x] 3.8 Add TODO reporting: if orchestrator_result contains commented_tests, log and display them

## 4. Verify integration and error handling

- [x] 4.1 Ensure Stage 5 does NOT fail the workflow if TestOrchestrator returns compiled=True (even with commented tests)
- [x] 4.2 If TestOrchestrator returns compiled=False, mark Stage 5 as failed with clear error message
- [x] 4.3 Add logging to show each attempt number during orchestration (TestOrchestrator should log this)
- [x] 4.4 Verify commented test comments have TODO markers as per spec

## 5. Test the consolidated pipeline

- [x] 5.1 Run orchestrator on a test component and verify Stage 5 completes successfully
- [x] 5.2 Verify BDD gherkin is generated correctly
- [x] 5.3 Verify test skeleton is generated once (not on each attempt)
- [x] 5.4 Verify TestOrchestrator loop runs (check logs for "Attempt N of M")
- [x] 5.5 Verify if tests don't compile initially, they eventually compile (with or without commented tests)
- [x] 5.6 Verify final test file is readable and includes commented tests if any
- [x] 5.7 Verify Stage 6 (verification) runs and reports correctly

## 6. Update configuration and documentation

- [x] 6.1 Add test_orchestrator section to migration_config.yaml with max_attempts: 4 (or verify it exists)
- [x] 6.2 Update README or CLAUDE.md to document the 6-step pipeline with Stage 5 self-healing behavior
- [x] 6.3 Document what "commented tests" means and how to review them

## 7. Final validation

- [x] 7.1 Run a full orchestration end-to-end and verify all 6 stages complete
- [x] 7.2 Verify workflow state artifacts are logged correctly (audit trail)
- [x] 7.3 Verify no regressions in other stages (exploration, modernization, verification still work)
- [x] 7.4 Commit changes with clear message: "Consolidate self-healing test orchestrator into Stage 5"
