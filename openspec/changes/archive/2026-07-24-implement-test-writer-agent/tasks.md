## 1. Project Structure & Setup

- [x] 1.1 Create agents/test_writer/ module directory
- [x] 1.2 Create test_writer_agent.py (main entry point)
- [x] 1.3 Create skeleton_reader.py (read and parse C# skeleton files)
- [x] 1.4 Create gherkin_extractor.py (extract Given/When/Then from comments)
- [x] 1.5 Create service_introspector_csharp.py (C# reflection-based introspection)
- [x] 1.6 Create test_code_filler_csharp.py (C# test body filling)
- [x] 1.7 Add test_writer to agents/__init__.py exports

## 2. Skeleton File Reading

- [x] 2.1 Implement SkeletonReader.read_csharp_skeleton() to parse C# test files
- [x] 2.2 Implement SkeletonReader.extract_test_methods() to isolate individual test methods
- [x] 2.3 Implement SkeletonReader.extract_test_class_info() to get class name and base class
- [x] 2.4 Add unit tests for SkeletonReader

## 3. Gherkin Step Extraction

- [x] 3.1 Implement GherkinExtractor.extract_arrange_steps() from comments
- [x] 3.2 Implement GherkinExtractor.extract_act_steps() from comments
- [x] 3.3 Implement GherkinExtractor.extract_assert_steps() from comments
- [x] 3.4 Implement GherkinExtractor.extract_parameters() from Gherkin text
- [x] 3.5 Implement parameter type inference (numeric, string, currency, email, etc.)
- [x] 3.6 Add unit tests for GherkinExtractor

## 4. C# Service Code Introspection

- [x] 4.1 Create ServiceIntrospectorCSharp (reflection-based C# discovery)
- [x] 4.2 Implement ServiceIntrospectorCSharp.discover_classes() to find service classes
- [x] 4.3 Implement ServiceIntrospectorCSharp.discover_methods() with parameter types
- [x] 4.4 Implement ServiceIntrospectorCSharp.get_method_signature() with parameter/return types
- [x] 4.5 Implement ServiceIntrospectorCSharp.find_constructor() for dependency injection
- [x] 4.6 Add unit tests for service introspector

## 5. Gherkin-to-C# Code Mapping

- [x] 5.1 Create GherkinCodeMapper class
- [x] 5.2 Implement GherkinCodeMapper.match_step_to_method() using step registry
- [x] 5.3 Implement GherkinCodeMapper.extract_method_call() from step pattern and parameters
- [x] 5.4 Implement GherkinCodeMapper.match_assertion_to_code() for Then steps
- [x] 5.5 Add support for common C# assertion patterns (success/failure, field values, error messages)
- [x] 5.6 Add unit tests for GherkinCodeMapper

## 6. C# Test Code Filling

- [x] 6.1 Create TestCodeFillerCSharp class
- [x] 6.2 Implement TestCodeFillerCSharp.fill_arrange() for Given steps
- [x] 6.3 Implement TestCodeFillerCSharp.fill_act() for When steps
- [x] 6.4 Implement TestCodeFillerCSharp.fill_assert() for Then steps
- [x] 6.5 Implement proper C# type conversions (string, int, decimal, etc.)
- [x] 6.6 Implement C# variable naming conventions and formatting
- [x] 6.7 Generate proper TestFixture initialization for C#
- [x] 6.8 Add unit tests for C# test filling

## 7. C# FluentAssertions Integration

- [x] 7.1 Create AssertionBuilder class for FluentAssertions syntax
- [x] 7.2 Implement assertion methods: BeTrue(), BeNull(), Be(), Contain()
- [x] 7.3 Implement property access assertions (e.g., result.IsSuccess)
- [x] 7.4 Support assertion chaining (Should().And())
- [x] 7.5 Add mapping from Gherkin assertions to FluentAssertions
- [x] 7.6 Add unit tests for AssertionBuilder

## 8. Error Handling & Graceful Degradation

- [x] 8.1 Implement handling for unmapped Gherkin steps (generate TODO comments)
- [x] 8.2 Implement handling for missing service implementations
- [x] 8.3 Implement handling for ambiguous parameter extraction
- [x] 8.4 Implement handling for type mismatches (log warning, attempt conversion)
- [x] 8.5 Add comprehensive error logging with context
- [x] 8.6 Ensure tests remain syntactically valid even with TODOs
- [x] 8.7 Implement graceful fallback when service code cannot be introspected

## 9. Test Fixture Generation

- [x] 9.1 Implement FixtureGenerator.generate_csharp_fixture() 
- [x] 9.2 Implement dependency injection in CreateSystemUnderTest()
- [x] 9.3 Handle mock/test double creation for external dependencies
- [x] 9.4 Generate proper disposal/cleanup in fixture
- [x] 9.5 Add unit tests for fixture generation

## 10. Orchestrator Integration

- [x] 10.1 Create TestWriterStage class for orchestrator pipeline
- [x] 10.2 Implement TestWriterStage.execute() to process generated C# skeletons
- [x] 10.3 Add configuration support in speckit_config.yaml for test writer
- [x] 10.4 Update orchestrator_v2.py to include TestWriterStage after TestGenerationStage
- [x] 10.5 Implement result reporting (success/partial/failed)
- [x] 10.6 Add logging to track which tests were filled vs left as skeletons

## 11. End-to-End Testing

- [x] 11.1 Create integration test with sample C# service and skeleton test
- [x] 11.2 Verify C# test filling produces valid, compilable code
- [x] 11.3 Run generated tests against sample C# service
- [x] 11.4 Verify assertions pass/fail correctly based on service behavior
- [x] 11.5 Test full pipeline: BDD generator → SpecKit skeletons → test writer implementation

## 12. Documentation & Cleanup

- [x] 12.1 Update SPECKIT_TEST_GENERATION.md to document test writer phase
- [x] 12.2 Add test writer configuration guide to SPECKIT_TEST_GENERATION.md
- [x] 12.3 Document Gherkin best practices for test writer (how to write clear C# steps)
- [x] 12.4 Add troubleshooting section for C# test writer in SPECKIT_TEST_GENERATION.md
- [x] 12.5 Document FluentAssertions usage patterns in generated tests
- [x] 12.6 Update requirements.txt if any new dependencies are needed
- [x] 12.7 Update migration_config.yaml to enable C# test writer stage by default
- [x] 12.8 Clean up any temporary files or debug code
