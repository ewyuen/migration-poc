## Why

SpecKit generates test file skeletons from Gherkin scenarios with proper structure, test attributes, and scenario descriptions embedded as comments. However, the test bodies contain only placeholder implementations (generic `Execute()` calls and `Should().NotBeNull()` assertions). The test writer agent fills this gap by reading the skeleton structures and Gherkin comments, introspecting actual service implementations, and generating real test code that exercises top-level use cases with proper setup, method calls, and assertions.

## What Changes

- **New test writer agent for C#**: Post-processing component that reads SpecKit-generated C# test skeleton files and fills in their method bodies with real implementations
- **Service introspection (C#)**: Agent analyzes migrated C# service code to discover available classes, methods, and expected parameter types
- **Gherkin-to-code translation (C#)**: Converts Gherkin steps embedded in test comments (Given/When/Then) into proper C# setup, act, and assert code
- **Test fixture generation (C#)**: Creates proper C# test fixtures that initialize services with real dependencies (or mocks for external dependencies)
- **Assertion mapping (C#)**: Maps Gherkin assertions ("should succeed", "should contain X") to C# FluentAssertions idioms (`Should().BeTrue()`, `Should().Contain()`)
- **Focus on top-level use cases only**: Tests exercise main happy paths and critical edge cases; does not generate exhaustive coverage of every method or parameter combination

## Capabilities

### New Capabilities
- `test-writer-agent`: Post-processing agent that fills in test implementations after SpecKit generates C# test skeletons. Introspects C# service code, translates Gherkin steps to actual method calls and assertions, and generates working C# NUnit tests

### Modified Capabilities
- `gherkin-test-generation`: SpecKit now acts as skeleton generator only; test writer agent is the separate post-processing phase that completes the pipeline

## Impact

- **Pipeline integration**: Test generation now has two phases: skeleton generation (SpecKit) → implementation (test writer)
- **Service code requirement**: Test writer assumes service implementations exist and are discoverable in the migrated output structure
- **Test quality**: Generated tests transition from scaffolding to working code that can be executed and will fail/pass based on actual service behavior
- **Maintenance**: Tests become part of the migrated code and can be run as part of normal test suites
