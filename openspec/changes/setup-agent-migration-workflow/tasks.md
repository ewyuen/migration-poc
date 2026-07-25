## 1. Config.yaml Structure Setup

- [x] 1.1 Create config.yaml at repository root with agent definitions
- [x] 1.2 Define orchestrator agent with role, tools, and delegates
- [x] 1.3 Define explorer agent with discovery role and component_analyzer tools
- [x] 1.4 Define staging agent (part of orchestrator) with branch_manager and file_copier tools
- [x] 1.5 Define modernizer agent with code_transformer and dotnet_api_mapper tools
- [x] 1.6 Define extractor agent with ast_analyzer, pattern_matcher tools
- [x] 1.7 Define bdd_generator agent with scenario_generator and gherkin_writer tools
- [x] 1.8 Define test_writer agent with gherkin_parser and test_code_generator tools
- [x] 1.9 Define verifier agent with test_runner and result_reporter tools
- [x] 1.10 Add workflow sequence to config: discovery → staging → modernization → extraction → bdd → testing → verification
- [x] 1.11 Validate config.yaml schema against OpenSpec agent configuration requirements

## 2. User Input and Request Handling

- [x] 2.1 Create input handler module to accept user migration requests from CLI
- [x] 2.2 Implement component name parameter validation
- [x] 2.3 Implement optional filters parameter parsing (domain, dependency, size, etc.)
- [x] 2.4 Create request validation to ensure legacy-src directory exists
- [x] 2.5 Implement request logging for audit trail

## 3. Orchestrator Agent Implementation

- [x] 3.1 Create orchestrator agent entrypoint that accepts user requests
- [x] 3.2 Implement orchestrator delegation logic to invoke explorer agent
- [x] 3.3 Implement prerequisite validation before invoking each subsequent agent
- [x] 3.4 Add workflow state management (track current stage, completed stages, failures)
- [x] 3.5 Implement error handling to halt pipeline on agent failure
- [x] 3.6 Add comprehensive logging for each workflow transition
- [x] 3.7 Create workflow status reporting that shows current state to user
- [x] 3.8 Implement rollback mechanism (git commands to revert to main on user request)

## 4. Explorer Agent Enhancement

- [ ] 4.1 Update explorer agent to scan legacy-src directory structure
- [ ] 4.2 Implement component detection (.csproj, .sln file parsing)
- [ ] 4.3 Implement dependency analysis to identify related components
- [ ] 4.4 Add component metadata extraction (size in LOC, dependencies, last modified)
- [ ] 4.5 Implement filter logic: filter by domain, size, dependencies
- [ ] 4.6 Create component inventory JSON output format
- [ ] 4.7 Add validation for component readiness (no .NET Framework-only deps flagged)
- [ ] 4.8 Implement human-readable summary section in inventory

## 5. Staging Agent Implementation

- [x] 5.1 Create staging agent module for component copy operations
- [x] 5.2 Implement git branch creation with naming convention {component}-migration-{YYYYMMDD}
- [x] 5.3 Implement component copy from legacy-src to legacy-code with directory structure preservation
- [x] 5.4 Add file permission and encoding preservation during copy
- [x] 5.5 Create initial commit with component copy (message: "Initial copy: {component}")
- [x] 5.6 Implement checksum validation to confirm copy completeness
- [x] 5.7 Create metadata file documenting staging operation (provenance, timestamp, status)
- [x] 5.8 Add staging validation to confirm all files present in legacy-code

## 6. Modernizer Agent Enhancement

- [ ] 6.1 Update modernizer to update TargetFramework to net10
- [ ] 6.2 Implement .NET API replacement mapping (System.Web → AspNetCore, etc.)
- [ ] 6.3 Add NuGet package version updater for .NET 10 compatibility
- [ ] 6.4 Implement config file migration (app.config → IConfiguration)
- [ ] 6.5 Implement reflection-based registration conversion to ServiceCollection
- [ ] 6.6 Add compilation validation (dotnet build on modernized code)
- [ ] 6.7 Create modernization summary report (APIs changed, packages updated, patterns refactored)
- [ ] 6.8 Implement output to legacy-code/{component}/ for modernized code

## 7. Extractor Agent Enhancement

- [ ] 7.1 Update extractor to analyze modernized .NET 10 code
- [ ] 7.2 Implement domain entity identification and classification
- [ ] 7.3 Implement algorithm/business rule isolation and documentation
- [ ] 7.4 Add infrastructure vs. domain code separation logic
- [ ] 7.5 Create structured YAML/JSON output format for business logic specs
- [ ] 7.6 Implement dependency mapping between extracted concepts
- [ ] 7.7 Add testable scenario identification from conditional logic
- [ ] 7.8 Implement extraction coverage validation (>90% target)

## 8. BDD Generator Agent Enhancement

- [ ] 8.1 Update BDD generator to parse extracted domain logic specs
- [ ] 8.2 Implement Gherkin feature file generation from domain entities
- [ ] 8.3 Implement Gherkin scenario generation from business rules
- [ ] 8.4 Implement Scenario Outline generation with Examples for algorithm variations
- [ ] 8.5 Add feature descriptions explaining business value
- [ ] 8.6 Implement scenario naming (user/business perspective, not implementation)
- [ ] 8.7 Implement traceability comments linking scenarios to extracted logic
- [ ] 8.8 Add Gherkin syntax validation (parser check for all generated files)

## 9. Test Writer Agent Implementation (NEW)

- [x] 9.1 Create test writer agent module
- [x] 9.2 Implement Gherkin feature file parser (.feature file reading)
- [x] 9.3 Implement scenario extraction from feature files
- [x] 9.4 Implement Scenario Outline parameter handling and Example data expansion
- [x] 9.5 Implement C# test class generation corresponding to feature files
- [x] 9.6 Implement test method generation with Given-When-Then structure
- [x] 9.7 Implement xUnit test framework integration ([Fact] and [Theory] attributes)
- [x] 9.8 Implement step definition code generation (Given setup, When action, Then assertion)
- [x] 9.9 Implement test fixture setup/teardown generation
- [x] 9.10 Implement helper method generation for common operations
- [x] 9.11 Implement parameterized test generation from Examples
- [x] 9.12 Implement test code compilation validation (dotnet build on test project)
- [x] 9.13 Add generated test output to legacy-code/{component}/{component}.generated.cs

## 10. Verifier Agent Enhancement

- [ ] 10.1 Update verifier to compile generated test code
- [ ] 10.2 Implement test dependency resolution (NuGet packages)
- [ ] 10.3 Implement test execution using dotnet test command
- [ ] 10.4 Implement isolated test environment setup (clean state per test)
- [ ] 10.5 Implement parameterized test execution ([Theory] support)
- [ ] 10.6 Create test result capture (pass/fail counts, timing data)
- [ ] 10.7 Implement detailed failure reporting (stack traces, actual vs. expected)
- [ ] 10.8 Create human-readable test report generation
- [ ] 10.9 Implement test coverage analysis vs. extracted logic
- [ ] 10.10 Implement coverage gap identification
- [ ] 10.11 Add final migration status verdict (success/failure)
- [ ] 10.12 Generate recommendations based on test results

## 11. Artifact Format and Handoff

- [ ] 11.1 Define artifact file naming convention in design doc
- [ ] 11.2 Create {component}.modernized.csproj output format documentation
- [ ] 11.3 Create {component}.extracted-logic.md output format documentation
- [ ] 11.4 Create {component}.gherkin output format documentation
- [ ] 11.5 Create {component}.generated.cs output format documentation
- [ ] 11.6 Create {component}.test-results.json output format documentation
- [ ] 11.7 Implement metadata inclusion (timestamps, version info) in all artifacts
- [ ] 11.8 Create artifact validation utilities for each handoff point

## 12. Error Handling and Validation

- [ ] 12.1 Implement explorer validation: component exists in legacy-src
- [ ] 12.2 Implement staging validation: component copied successfully to legacy-code
- [ ] 12.3 Implement modernizer validation: code is syntactically valid .NET 10
- [ ] 12.4 Implement extractor validation: extraction completeness check
- [ ] 12.5 Implement BDD generator validation: Gherkin syntax check
- [ ] 12.6 Implement test writer validation: generated code compiles
- [ ] 12.7 Implement verifier validation: tests compile and execute
- [ ] 12.8 Create comprehensive error messages with mitigation suggestions

## 13. Logging and Audit Trail

- [ ] 13.1 Implement audit log creation at workflow start
- [ ] 13.2 Add timestamp logging for each stage transition
- [ ] 13.3 Implement agent name and status logging (success/failure)
- [ ] 13.4 Add output artifact path logging
- [ ] 13.5 Implement failure context logging (input, error details)
- [ ] 13.6 Create audit log output format (JSON or structured text)
- [ ] 13.7 Implement audit log persistence in legacy-code directory

## 14. End-to-End Testing and Documentation

- [x] 14.1 Create a small test component in legacy-src for POC validation
- [x] 14.2 Document CLI commands for invoking orchestrator
- [x] 14.3 Document config.yaml schema and agent definitions
- [x] 14.4 Create step-by-step workflow walkthrough guide
- [x] 14.5 Document artifact formats and handoff expectations
- [x] 14.6 Create troubleshooting guide for common failures
- [x] 14.7 Run end-to-end workflow test with test component
- [x] 14.8 Verify all agents invoke correctly in sequence
- [x] 14.9 Verify artifact handoff works correctly
- [x] 14.10 Collect metrics (total time, success rate, test coverage)

## 15. Integration with Agent SDK

- [ ] 15.1 Ensure all agents follow Agent SDK patterns from agent setup
- [ ] 15.2 Verify agents use consistent logging and error handling
- [ ] 15.3 Implement inter-agent communication using orchestrator delegation pattern
- [ ] 15.4 Ensure all agents respect config.yaml agent definitions
- [ ] 15.5 Test integration with existing agent infrastructure

## 16. Branch Management and Cleanup

- [ ] 16.1 Create branch cleanup script for completed migrations
- [ ] 16.2 Document branch merge process after verification
- [ ] 16.3 Document branch deletion criteria (after merge or explicit user request)
- [ ] 16.4 Implement git hooks for branch naming validation
