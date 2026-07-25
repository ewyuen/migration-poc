## Context

The modernized code components are generated in the `migrated-output/` folder. Currently, Gherkin features (`scenarios.feature`) and unit test code files (`*.Tests.cs`) are output to the root of the component directory, cluttering production files. The testing pipeline lacks compilation, execution, and coverage analysis verification.

## Goals / Non-Goals

**Goals:**
- Move all Gherkin specifications and generated C# tests into a `tests/` subdirectory under the component's output directory.
- Compile and run the generated tests automatically as part of the pipeline (Verification stage).
- Collect and report code coverage metrics (line and branch coverage).
- Format test results and coverage data into clean JSON and Markdown reports.

**Non-Goals:**
- Full implementation of multi-language test compilation (C# is the primary focus for compilation and execution, while Gherkin/test paths are restructured for all languages).

## Decisions

### Decision 1: C# Test Project Generation (.csproj)
To compile and run tests, a standard .NET 10 test project file (`tests.csproj`) must be generated under the `tests/` folder.
- **Approach**: The verification/test runner agent will dynamically generate a `tests.csproj` that:
  - Targets `net10.0`.
  - Includes package references for:
    - `Microsoft.NET.Test.Sdk`
    - `xunit`
    - `xunit.runner.visualstudio`
    - `FluentAssertions`
    - `coverlet.collector` (for coverage collection)
    - Any libraries required by the production code (e.g., `FluentValidation`).
  - Compiles the modernized source code files (from the parent folder) and the test code files (in the `tests/` folder).
- **Rationale**: A separate test project keeps dependencies clean and allows standard `dotnet test` execution.

### Decision 2: Test Execution & Coverage Collection
We will use the built-in dotnet CLI tools to run tests and collect coverage.
- **Approach**: Execute `dotnet test --collect:"XPlat Code Coverage" --logger:"trx;LogFileName=results.trx"` in the `tests/` folder.
- **Rationale**: This command uses the standard coverlet collector (pre-installed via NuGet in the test project) and creates:
  - A `.trx` file containing detailed XML test execution results.
  - A `coverage.cobertura.xml` file containing coverage data.
These standard formats are easily parsed by the agent.

### Decision 3: Results Parsing & Reporting
We will parse the outputs of the test runner to create user-facing reports.
- **Approach**:
  - The test runner agent will parse `results.trx` to extract passed/failed counts, total execution time, and details of any failed tests.
  - It will parse `coverage.cobertura.xml` using a simple XML parser to extract overall line and branch coverage percentages.
  - A unified markdown report (`verification_report.md`) and JSON log will be written to `migrated-output/result-log/`.

## Risks / Trade-offs

- **[Risk] Missing packages in production code** → Modernized code might reference packages not in the standard test template.
  - *Mitigation*: Define a robust set of common NuGet dependencies (FluentValidation, Microsoft.Extensions.DependencyInjection, System.Text.Json) in the generated `tests.csproj`.
- **[Risk] Test failures halting pipeline** → If a generated test fails, it might halt the whole orchestrator.
  - *Mitigation*: Ensure the test execution stage catches compilation or execution errors, logs them to the reports, and sets `overall_status = FAIL` without crashing the main orchestrator script.
