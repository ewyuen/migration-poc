## 1. Setup and Infrastructure

- [x] 1.1 Update MigrationState TypedDict in orchestrator_v3.py with step_definitions_skeleton and step_definitions_enhanced fields
- [x] 1.2 Add Reqnroll NuGet package to test .csproj template
- [ ] 1.3 Create utility module for C# compilation (csc.exe invocation, error parsing)
- [ ] 1.4 Create audit logging infrastructure for step definition generation errors

## 2. Step Definitions Skeleton Generation

- [x] 2.1 Implement Gherkin step extractor (parse .feature file, extract Given/When/Then steps)
- [x] 2.2 Implement parameter type inference from Gherkin step text (detect {string}, {int}, {float})
- [x] 2.3 Implement skeleton template generator (create [Binding] class, method stubs with TODO)
- [x] 2.4 Implement method signature generator (convert step text to regex pattern + C# method signature)
- [x] 2.5 Add ScenarioContext field initialization to generated skeleton
- [x] 2.6 Add using statements and namespace generation to skeleton
- [x] 2.7 Implement output writer (write skeleton to file)

## 3. LLM-Driven Step Enhancement

- [x] 3.1 Implement LLM context bundle builder (gather modernized code, scenario context, domain rules)
- [x] 3.2 Implement step enhancement prompt template (include skeleton, modernized code, scenario chain, domain intent)
- [x] 3.3 Implement LLM call wrapper for step enhancement (call LLM with context, parse response)
- [x] 3.4 Implement parameter mapping inference via LLM (infer parameter extraction from step text)
- [x] 3.5 Implement ScenarioContext key naming inference via LLM (semantic key names)
- [x] 3.6 Implement mock generation inference via LLM (detect missing services, generate mock stubs)

## 4. Compilation via dotnet build (Single Check, No Retry Loop)

- [x] 4.1 Reuse test_compiler.py pattern: generate tests.csproj referencing source project
- [x] 4.2 Implement dotnet build invocation in tests directory (not csc.exe single-file)
- [x] 4.3 Implement build output parsing (extract errors, warnings, structured messages)
- [x] 4.4 Implement audit logging for compilation results (success and failure cases)
- [x] 4.5 Implement graceful failure handling (log to audit, continue to verification on failure)

## 5. LangGraph Node Implementation (Refactor bdd_and_test, Add Step Defs Nodes)

- [x] 5.1 Refactor _node_bdd_and_test to _node_bdd_tests: remove old test code generation and TestOrchestrator call
- [x] 5.2 Implement _node_step_defs_template() method in OrchestratorV3 (skeleton generation)
- [x] 5.3 Implement _node_step_defs_enhance() method in OrchestratorV3 (LLM enhancement + single compile check)
- [x] 5.4 Update MigrationState TypedDict with step_definitions_skeleton and step_definitions_enhanced fields
- [x] 5.5 Add both new nodes to graph builder in _build_graph()
- [x] 5.6 Update graph edges: validate → stage → explore → modernize → bdd_tests → step_defs_template → step_defs_enhance → verify → END
- [x] 5.7 Implement error routing (step_defs_* nodes gracefully continue on error)
- [x] 5.8 Add OTel tracing to both nodes (span creation, status attributes, compile_success flag)

## 6. Verification Stage Integration

- [x] 6.1 Update verification stage to handle optional step_definitions_enhanced (graceful degradation)
- [x] 6.2 Integrate Reqnroll test runner into verification stage
- [x] 6.3 Implement .feature file and StepDefinitions.cs pairing logic
- [x] 6.4 Implement Reqnroll test execution (invoke test runner, capture results)
- [x] 6.5 Implement coverage collection from Reqnroll test run
- [x] 6.6 Implement result parsing and reporting (pass/fail, scenario counts, coverage %)
- [x] 6.7 Update verification_results output format to include step definitions status

## 7. Testing and Validation

- [ ] 7.1 Write unit tests for skeleton generation (Gherkin parsing, template rendering)
- [ ] 7.2 Write unit tests for parameter type inference
- [ ] 7.3 Write unit tests for error parser (compiler error extraction)
- [ ] 7.4 Write integration test: Gherkin → skeleton → enhancement → compilation (end-to-end single feature)
- [ ] 7.5 Write integration test: error case, heal loop retries and succeeds
- [ ] 7.6 Write integration test: max retries exhausted, graceful failure
- [ ] 7.7 Test with real modernized code sample (create test fixture)
- [ ] 7.8 Test Reqnroll test runner integration (execute generated StepDefinitions with .feature)

## 8. Documentation and Cleanup

- [ ] 8.1 Update SPECKIT_TEST_GENERATION.md to document new step definitions flow
- [ ] 8.2 Create REQNROLL_MIGRATION.md with Reqnroll architecture and patterns
- [ ] 8.3 Document LLM prompts and inference strategies
- [ ] 8.4 Add logging/debug output to step definitions nodes
- [ ] 8.5 Verify audit logging captures step definition generation status
- [ ] 8.6 Review and update requirements.txt for Reqnroll dependency
- [ ] 8.7 Test error messages for clarity and actionability

## 9. Deployment and Rollout

- [ ] 9.1 Create migration script (if needed) to handle existing test artifacts
- [ ] 9.2 Test end-to-end orchestrator flow with new nodes (validate + stage + explore + modernize + bdd + step_defs_template + step_defs_enhance + verify)
- [ ] 9.3 Verify backward compatibility (orchestrator entry point unchanged)
- [ ] 9.4 Performance testing (measure LLM call time, compilation time, total pipeline time)
- [ ] 9.5 Run full migration test on sample component
- [ ] 9.6 Generate audit trail review (check orchestrator.jsonl for new stages)
- [ ] 9.7 Document known issues and limitations
