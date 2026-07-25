## Context

The migration POC currently lacks executable specifications. The orchestrator and LLM client execute migration logic, but there's no structured way to verify behavior matches requirements. SpecFlow enables behavior-driven development where feature files document "what" the system should do, and step definitions implement "how" to test it. This bridges business requirements and code.

Current state:
- `orchestrator.py` manages migration workflows
- `llm_client.py` handles LLM interactions
- `config.py` provides configuration
- No test suite currently exists

## Goals / Non-Goals

**Goals:**
- Create executable specifications for migration workflows using SpecFlow
- Enable stakeholders to understand migration logic through readable feature files
- Establish automated test infrastructure for CI/CD validation
- Document expected behaviors: source detection, schema validation, transformation, deployment
- Support test execution via CLI for pipeline integration

**Non-Goals:**
- Performance benchmarking or load testing
- Integration with live production systems
- Testing external LLM provider reliability
- Migrating existing Python tests to C# (this is new test infrastructure)

## Decisions

**1. Language & Framework: C# with SpecFlow**
- Rationale: SpecFlow provides Gherkin syntax (readable to non-technical stakeholders), tight .NET ecosystem integration, and strong tooling
- Alternatives considered: Cucumber (Python/JavaScript - adds cross-language complexity), BehaveJ (Java - not applicable to Python POC), pytest-bdd (Python - less mature than SpecFlow)
- Trade-off: Adds C# to project stack; requires .NET SDK

**2. Test Project Structure**
- Create `migration-poc/tests/Migration.Specs/` with standard .NET test project layout
- Feature files in `features/` directory organized by capability (e.g., `features/source-detection/`, `features/validation/`)
- Step definitions in `Steps/` directory with one file per feature area
- Hooks for setup/teardown in `Hooks/` directory
- Rationale: Standard SpecFlow project structure, easy to scale and maintain

**3. Execution Target: CLI/Python Subprocess**
- Step definitions execute migration tool via process invocation (`dotnet run` in orchestrator context or direct Python subprocess)
- Alternative: Direct C# implementation of migration logic - rejected (requires porting Python to C#, high effort)
- Trade-off: Subprocess overhead; requires careful environment setup and path management
- Benefit: Tests actual Python implementation, validates real behavior

**4. Test Data & Configuration**
- Use embedded test fixtures (JSON/YAML sample schemas)
- Create temporary workspace per test scenario for isolation
- Configuration via environment variables or fixture injection
- Rationale: Isolated tests, easy cleanup, reproducible

**5. Reporting & Integration**
- Use xUnit test runner for CLI execution (`dotnet test`)
- Generate XML reports for CI/CD tooling (Azure Pipelines, GitHub Actions)
- Rationale: Standard .NET practice, wide CI/CD support

## Risks / Trade-offs

[Python-C# Subprocess Overhead] → Run tests in groups during CI, don't run on every file save locally; subprocess calls are fast enough for validation but not for TDD tight loops

[Environment Setup Complexity] → Document required paths and environment variables; use .env.example for test configuration

[Test Maintenance as Logic Changes] → Establish code review practice: update feature files and steps whenever migration logic changes; document feature file syntax

[Slow First Test Run] → .NET compilation time; acceptable as tests run in CI, not per-commit locally

## Migration Plan

1. Create test project: `dotnet new xunit -n Migration.Specs`
2. Add SpecFlow NuGet packages: SpecFlow, SpecFlow.xUnit, FluentAssertions
3. Establish `features/` and `Steps/` directories
4. Create initial feature files for core scenarios
5. Implement step definitions (initially focused on orchestrator API)
6. Integrate test execution into CI/CD (`dotnet test`)
7. Document feature file syntax and running tests locally

Rollback: Delete `tests/Migration.Specs/` directory; remove test project from solution

## Open Questions

- Should step definitions call orchestrator functions directly or via subprocess? (Proposed: subprocess for isolation, real environment testing)
- How to handle async/await in SpecFlow steps given Python subprocess? (Proposed: wrap in Task<T>, use ConfigureAwait)
- Test data strategy: fixture files or generated? (Proposed: fixture files in `tests/Migration.Specs/fixtures/`)
