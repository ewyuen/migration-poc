## 1. Create TestCompilationOrchestrator Class

- [ ] 1.1 Create `migration-poc/agents/test_orchestrator.py` with TestCompilationOrchestrator class
- [ ] 1.2 Implement `compile_tests(component_name: str) -> dict` method to run `dotnet build`
- [ ] 1.3 Implement error parsing to extract MSBuild error messages (error code, line number, message)
- [ ] 1.4 Implement method identification to find test methods from error line numbers
- [ ] 1.5 Implement test method commenting to replace method body with comment block
- [ ] 1.6 Implement compilation loop that retries up to max_iterations with error fixing
- [ ] 1.7 Implement result tracking to record which tests were commented and on which iteration
- [ ] 1.8 Implement `execute(component_name: str) -> dict` main entry point

## 2. Integrate into Orchestrator Workflow

- [ ] 2.1 Update `orchestrator_v2.py` to import TestCompilationOrchestrator
- [ ] 2.2 Instantiate TestCompilationOrchestrator in OrchestratorV2.__init__()
- [ ] 2.3 Add Stage 5A (Test Orchestration) between TestWriterStage (stage 5) and Verification (stage 6)
- [ ] 2.4 Call test_orchestrator.execute() at appropriate point in run() method
- [ ] 2.5 Update WorkflowState to track test orchestration results in artifacts
- [ ] 2.6 Update stage counter output to reflect new 7-stage workflow (currently shows "STAGE N/6")

## 3. Configuration Support

- [ ] 3.1 Add `test_orchestrator` section to config schema in YAML with properties: `enabled`, `max_iterations`, `comment_style`
- [ ] 3.2 Update TestCompilationOrchestrator to read config from OrchestratorV2.config
- [ ] 3.3 Add default config values: `enabled: true`, `max_iterations: 5`, `comment_style: "block"`
- [ ] 3.4 Implement config validation to ensure max_iterations >= 1

## 4. Update Verification Reports

- [ ] 4.1 Modify `verifier.py` _write_reports() to include commented tests section
- [ ] 4.2 Update markdown report template to show:
  - Total tests commented out
  - List of commented test names with error reasons
  - Iteration on which each was commented
- [ ] 4.3 Update JSON report to include `commented_tests` array with structure: `{name, error_code, error_message, iteration}`
- [ ] 4.4 Update summary statistics to show "Tests Commented: N" alongside pass/fail counts

## 5. Error Parsing Implementation Details

- [ ] 5.1 Create helper to parse MSBuild error format: `error CS<code>: <message> at <file>:<line>`
- [ ] 5.2 Create helper to find line in test file and identify containing method signature
- [ ] 5.3 Create helper to locate matching braces for method body (from opening brace to closing brace)
- [ ] 5.4 Handle edge cases: nested braces, string literals with braces, XML comments

## 6. Test and Validation

- [ ] 6.1 Run orchestrator on TestService component to verify compilation succeeds
- [ ] 6.2 Manually inject test errors and verify orchestrator correctly identifies and comments them
- [ ] 6.3 Verify report correctly lists commented tests with reasons
- [ ] 6.4 Test configuration option `enabled: false` to verify orchestrator can be disabled
- [ ] 6.5 Test max_iterations config to verify loop respects limit
- [ ] 6.6 Verify final verification report includes commented test statistics
- [ ] 6.7 Test end-to-end workflow with TestService to ensure all stages complete

## 7. Documentation Updates

- [ ] 7.1 Add test-compilation-orchestrator documentation to README or workflow guide
- [ ] 7.2 Document configuration options for test_orchestrator section
- [ ] 7.3 Update CLAUDE.md or architecture docs if applicable
- [ ] 7.4 Add comments explaining error parsing logic in test_orchestrator.py
