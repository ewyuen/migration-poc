## Why

The current test generation pipeline creates monolithic test classes with inline step implementations, bypassing Reqnroll's proper step definition model. This prevents reusability, violates Reqnroll patterns, and creates tight coupling between scenarios and test code. By adopting Reqnroll's `[Binding]` + `StepDefinitions.cs` + `.feature` pattern, we gain a cleaner separation of concerns: Gherkin becomes the source of truth, step definitions bind steps to implementations, and the Reqnroll framework orchestrates execution.

## What Changes

- **Replace SpecFlow with Reqnroll**: Modern, community-driven BDD framework for .NET with standard step definition bindings.
- **Introduce Step Definitions Generation**: New agent generates `[Binding]` classes with step definition methods from extracted Gherkin steps.
- **LLM-Driven Step Enhancement**: LLM fills step implementations based on domain logic, modernized code, and scenario context. Uses template-first approach with placeholder TODOs.
- **Compile + Heal Loop**: Immediate C# compilation after enhancement; errors trigger LLM retries (up to 3 attempts) with error context for self-healing.
- **LangGraph Integration**: Two new orchestrator nodes between BDD generation and verification stages for step definitions generation and enhancement.
- **Reqnroll Type Patterns**: Leverage built-in `{int}`, `{string}`, `{float}` parameter patterns; LLM infers parameter mappings and `ScenarioContext` key naming from step intent.

## Capabilities

### New Capabilities
- `step-definitions-generation`: Extract Gherkin steps and generate skeleton `StepDefinitions.cs` with `[Binding]` class, method stubs with TODO placeholders, and Reqnroll-standard type patterns.
- `step-definitions-enhancement`: LLM fills step implementation TODOs based on modernized code, domain logic, previous steps in scenario, and business intent. Infers parameter mapping, context keys, and mock generation.
- `langgraph-step-definitions-node`: New LangGraph graph node for step definitions generation (between BDD and verification stages).
- `langgraph-step-enhancement-node`: New LangGraph graph node for LLM-driven enhancement + heal loop (between generation and verification).
- `reqnroll-test-orchestration`: Integration of Reqnroll test runner with existing verification stage; executes `.feature` files + `StepDefinitions.cs` bindings.

### Modified Capabilities
- `test-generation-orchestration`: Refactored to add two new nodes (step-definitions-generation, step-definitions-enhancement) into MigrationState graph; outputs now include `step_definitions_skeleton` and `step_definitions_enhanced` states.
- `bdd-test-generation`: Output remains Gherkin `.feature` files; now acts as input to step definitions generation instead of test code generation.

## Impact

- **New Files**: `StepDefinitions.cs` per feature file (in test output directory)
- **Modified Files**: `orchestrator_v3.py` (add two nodes), `MigrationState` type (new state fields), test verification stage (use Reqnroll runner)
- **Removed**: Old test code generation pipeline (replaced by step definitions + Reqnroll)
- **Dependencies**: Reqnroll NuGet package (already supported in .NET ecosystem)
- **Breaking**: Test structure changes from inline test classes to Reqnroll bindings; existing test runners must use Reqnroll CLI
