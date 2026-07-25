## Context

In our current modernized pipeline, unit tests are generated in Stage 6 and compiled/executed in Stage 7. If Gherkin step mapping introduces small syntax or parameter mismatch errors, the build fails and the pipeline terminates. This design separates the compilation/execution steps from results analysis and introduces a self-healing loop. The loop uses compiler error diagnostics as prompt context for the LLM to fix the generated tests automatically.

## Goals / Non-Goals

**Goals:**
- Separate compilation and execution (Test Runner) from result parsing and verification (Verifier).
- Implement a Test Orchestrator stage that runs the Test Writer and Test Runner in a loop.
- Feed compiler error outputs back to the Test Writer (LLM) to dynamically correct the C# test file.
- Support loop termination upon successful compilation or reaching maximum attempts (e.g., 3).

**Non-Goals:**
- Self-healing logical assertion failures (non-compilation failures).
- Modifying production component code to resolve test compilation issues.

## Decisions

### Decision 1: Create a Standalone Test Runner
- **Details**: Create a new module `migration-poc/agents/test_runner.py` dedicated to generating `tests.csproj`, executing `dotnet test`, and parsing raw stderr/stdout for compilation errors.
- **Alternative**: Keep compilation logic inside `verifier.py`.
- **Rationale**: Isolating compilation allows the Verifier to focus purely on test and coverage XML analysis, simplifying its logic and decoupling it from the build process.

### Decision 2: Implement a Test Orchestration Stage
- **Details**: Introduce `migration-poc/agents/test_orchestrator.py` to coordinate the Test Writer and Test Runner.
- **Alternative**: Code the loop directly inside `orchestrator_v2.py`.
- **Rationale**: Keeps the high-level orchestrator file clean and focused on general pipeline stages, while encapsulating testing retry loops in a domain-specific agent.

### Decision 3: Update Test Writer to Accept Compile Feedback
- **Details**: Modify the `TestWriter` client and prompts to support an optional list of compiler errors. When provided, the LLM will be instructed to refine and rewrite the existing test file to resolve those specific errors.
- **Alternative**: Re-run the BDD scenario generator from scratch.
- **Rationale**: Direct refinement of the existing test implementation is significantly faster and preserves correctly generated step definitions.

## Risks / Trade-offs

- **[Risk]** The LLM enters an infinite refinement loop or oscillates between different compiler errors.
  - **Mitigation** Limit the orchestration loop to a maximum of 3 attempts. If compilation still fails, exit the loop and pass compilation errors to the Verifier to log a FAIL status.
- **[Risk]** Context window overhead from passing full test files and build errors multiple times.
  - **Mitigation** Pass only the relevant compiler lines and the full test code, keeping prompts concise.
