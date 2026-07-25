## 1. Test Artifact Output Restructuring

- [x] 1.1 Update `orchestrator_v2.py` file saving to place Gherkin scenarios under `tests/` subdirectory
- [x] 1.2 Update `orchestrator_v2.py` to output C# unit test files to `tests/` subdirectory
- [x] 1.3 Update test file paths in orchestrator state and variable lookups to point to `tests/` subdirectory
- [x] 1.4 Verify that `TestWriterStage` recursive file discovery correctly finds the skeleton files in `tests/`

## 2. Test Runner and Coverage Collection

- [x] 2.1 Implement `.csproj` project file generator in `verifier.py` to create test projects dynamically
- [x] 2.2 Implement subprocess execution in `verifier.py` to run `dotnet test` with coverage and logger flags
- [x] 2.3 Implement XML parsers for `results.trx` (test execution results) and `coverage.cobertura.xml` (code coverage metrics)
- [x] 2.4 Update `verifier.py` to generate markdown and JSON reports for both execution and coverage

## 3. Orchestration Integration

- [x] 3.1 Re-integrate the Verification stage (Stage 7) back into the `orchestrator_v2.py` execution sequence
- [x] 3.2 Add summary printing of test results and coverage percentage to the console output of the orchestrator
- [x] 3.3 Ensure verification failures are caught gracefully and documented in the workflow state without crashing
