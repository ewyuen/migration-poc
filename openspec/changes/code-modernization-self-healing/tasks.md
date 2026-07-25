## 1. Create Code Compiler Module

- [x] 1.1 Create `migration-poc/agents/code_compiler.py` with functions for compiling C# code in isolation
- [x] 1.2 Implement `compile_modernized_code(code_content: str) -> tuple(bool, List[str])` that runs C# compiler on generated code
- [x] 1.3 Extract structured error diagnostics: line number, error code, error message, type information from compiler output
- [x] 1.4 Return structured error list with fields: (file, line, column, error_code, message)
- [x] 1.5 Handle compiler timeout (set reasonable timeout like 30 seconds)
- [x] 1.6 Test code_compiler with sample broken and valid C# code

## 2. Create ModernizationOrchestrator Class

- [x] 2.1 Create `migration-poc/agents/modernization_orchestrator.py` following TestOrchestrator pattern
- [x] 2.2 Implement `ModernizationOrchestrator` class with `__init__(base_output_dir, config)`
- [x] 2.3 Set max_attempts = 3 (configurable via config)
- [x] 2.4 Implement `execute(component_name: str) -> Dict` method that:
  - [x] 2.4a Runs modernizer on attempt 1
  - [x] 2.4b Compiles result
  - [x] 2.4c If success, return with status="success"
  - [x] 2.4d If failure, extract errors and retry up to 3 times
  - [x] 2.4e On final failure after 3 attempts, return status="failed" with all errors
- [x] 2.5 Implement feedback mechanism to pass attempt number and previous errors to modernizer
- [x] 2.6 Save only the final version of modernized code (overwrite file on each attempt)
- [x] 2.7 Log each attempt with timestamp and result

## 3. Update Modernizer LLM Integration

- [x] 3.1 Modify modernizer prompt to accept optional `feedback_errors` parameter
- [x] 3.2 Create refinement prompt template that includes:
  - [x] 3.2a Current attempt number (e.g., "attempt 2 of 3")
  - [x] 3.2b List of compilation errors from previous attempt
  - [x] 3.2c Instruction to focus on fixing those specific errors
- [x] 3.3 Update `modernize_code()` function to handle `feedback_errors` parameter
- [x] 3.3 If feedback_errors provided, use refinement prompt instead of fresh generation
- [x] 3.4 Ensure modernizer prompt emphasizes that code MUST compile in isolation

## 4. Integrate ModernizationOrchestrator into orchestrator_v2.py

- [x] 4.1 Import ModernizationOrchestrator in orchestrator_v2.py
- [x] 4.2 Add to OrchestratorV2.__init__: `self.modernization_orchestrator = ModernizationOrchestrator(...)`
- [x] 4.3 Replace Stage 5 (MODERNIZATION) logic:
  - [x] 4.3a Remove direct modernize_code() call
  - [x] 4.3b Call `self.modernization_orchestrator.execute(component_name)` instead
  - [x] 4.3c Handle return: extract status, errors, and final modernized code
- [x] 4.4 Add conditional logic:
  - [x] 4.4a If modernization succeeds: save code and continue to Stage 6
  - [x] 4.4b If modernization fails: skip Stages 6-7 (BDD & testing), proceed to Stage 8 (verification)
- [x] 4.5 Pass modernization result to verifier (either success or failure report)
- [x] 4.6 Update stage completion logic to mark modernization complete only on success

## 5. Update Verifier Agent

- [x] 5.1 Modify `verify_test_results()` to accept modernization failure reports
- [x] 5.2 Add to report structure: `modernization_status` and `modernization_errors`
- [x] 5.3 Update `_write_reports()` to include "Modernization Failures" section when applicable
- [x] 5.4 Format modernization errors in markdown report with line numbers and error codes
- [x] 5.5 Update JSON report to include modernization_status and full error list
- [x] 5.6 Update summary section to clearly indicate if failure is modernization vs. test-related

## 6. End-to-End Testing

- [x] 6.1 Test ModernizationOrchestrator in isolation with sample legacy code
- [x] 6.2 Test full pipeline on TestService component:
  - [x] 6.2a Verify modernization succeeds with compilable code
  - [x] 6.2b Verify tests are generated and run
  - [x] 6.2c Verify verifier reports success
- [x] 6.3 Test failure scenario: introduce deliberate error in modernizer and verify:
  - [x] 6.3a Modernization loop attempts up to 3 times
  - [x] 6.3b Test generation is skipped after 3 failed attempts
  - [x] 6.3c Verifier reports modernization failure
  - [x] 6.3d Error report includes line numbers and error codes
- [x] 6.4 Verify logs show all 3 attempts with timestamps and errors
- [x] 6.5 Test configurable max_attempts (ensure 3 is default)

## 7. Documentation and Cleanup

- [x] 7.1 Add docstrings to ModernizationOrchestrator methods
- [x] 7.2 Add docstrings to code_compiler functions
- [x] 7.3 Update main orchestrator docstring to document new modernization verification stage
- [x] 7.4 Add comments explaining conditional test generation logic
- [x] 7.5 Verify all imports are correct (no circular dependencies)
- [x] 7.6 Run full test suite to ensure no regressions
