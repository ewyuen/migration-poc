# Reqnroll Step Definitions: Architecture & Patterns

This is the durable reference for the Reqnroll step-definitions pipeline. For a
point-in-time implementation status snapshot, see `REQNROLL_IMPLEMENTATION_STATUS.md`.
For hands-on testing steps, see `migration-poc/REQNROLL_TESTING_GUIDE.md`.

## What Reqnroll Replaced

The old pipeline (`SPECKIT_TEST_GENERATION.md`) generated NUnit/JUnit/pytest test
code directly from Gherkin step patterns via a static `StepRegistry`, with a
self-healing compile-retry loop in `TestOrchestrator`. That approach is retired
for components going through this pipeline. Reqnroll now binds Gherkin
`.feature` files to C# step methods directly, and step implementations are
filled by an LLM rather than pattern-matched.

## Pipeline (8 Stages)

```
validate → stage → explore → modernize → bdd_tests → step_defs_template → step_defs_enhance → verify → END
```

`bdd_tests` produces Gherkin only (no test code). The two new stages then:

1. **`step_defs_template`** — deterministic skeleton generation (no LLM)
2. **`step_defs_enhance`** — LLM fills the skeleton, then a single `dotnet build` check

## Modules

| Module | Responsibility |
|---|---|
| `migration-poc/agents/step_definitions_generator.py` | `GherkinStepExtractor`, `ParameterTypeInferencer`, `StepDefinitionSkeletonGenerator` — parses Gherkin, infers Cucumber Expression types, emits a `[Binding]` class with `// TODO` method bodies |
| `migration-poc/agents/step_definitions_enhancer.py` | `LLMContextBundleBuilder`, `StepDefinitionEnhancer` — builds LLM context (skeleton, Gherkin, modernized code, domain rules) and fills the TODOs in one LLM call |
| `migration-poc/agents/step_definitions_compiler.py` | `StepDefinitionsCompiler` — runs `dotnet build` against the generated `tests.csproj`, parses `CSxxxx` errors, writes an audit log |
| `migration-poc/agents/reqnroll_test_runner.py` | `ReqnrollTestRunner` — runs `dotnet test`, parses scenario pass/fail counts, step failures, and Cobertura coverage |
| `migration-poc/orchestrator_v3.py` | `_node_step_defs_template`, `_node_step_defs_enhance` — LangGraph nodes wiring the above into the pipeline with OTel spans |

## Key Patterns

- **Template-first, LLM-second**: the skeleton generator guarantees valid C#
  structure (attributes, method signatures, `ScenarioContext` injection); the
  LLM only fills method bodies. This avoids the LLM inventing invalid syntax.
- **Reqnroll standard type patterns**: `{string}`, `{int}`, `{float}` Cucumber
  Expressions — no custom regex. `ParameterTypeInferencer` picks the pattern
  from the Gherkin step text (quoted text → `{string}`, digits → `{int}`, etc).
- **`ScenarioContext` for state sharing**: constructor-injected, idiomatic
  Reqnroll pattern for passing state between steps in a scenario. The LLM
  infers semantic key names (e.g. `"CurrentUser"`, not `"var1"`).
- **Single compile check, no retry loop**: unlike `TestOrchestrator`'s
  multi-attempt heal loop, step definitions compile once. If it fails, the
  error is logged to the audit trail and the pipeline continues to
  verification — the Reqnroll test runner gives better step-binding
  diagnostics than another LLM retry would.
- **One `StepDefinitions.cs` per run**: `MigrationState.bdd_tests` holds a
  single Gherkin blob, so all extracted steps accumulate into one `[Binding]`
  class. Per-feature files are future (v2) work if BDD generation starts
  emitting multiple `.feature` files.
- **Inline mocks for missing services**: if a step references a
  service/method not present in the modernized code, the LLM generates a
  minimal mock class inline rather than failing generation.

## LLM Prompt & Inference Strategy

The enhancement prompt (`StepDefinitionEnhancer._build_prompt` /
`_build_system_prompt` in `step_definitions_enhancer.py`) gives the LLM:

- the skeleton (with `// TODO` placeholders and the exact method count to preserve)
- the full Gherkin spec (business intent)
- the modernized service code, truncated at 12,000 chars per file (large
  enough to avoid cutting off real methods — an earlier bug truncated at a
  smaller limit and caused the LLM to hallucinate mock methods instead of
  calling the real API)
- domain rules / compliance concerns from the exploration stage

Inference delegated entirely to the LLM (no heuristics in Python):

- **Parameter mapping** — which Gherkin capture maps to which method argument
- **`ScenarioContext` key naming** — semantic names, not positional/generic ones
- **Mock generation** — inline mock classes for services absent from modernized code
- **Method body implementation** — calling only methods/properties that
  literally appear in the modernized code shown (the prompt explicitly forbids
  inventing accessors, e.g. assuming a getter exists for a private field)
- **Weakest-true-assertion fallback** — if a Gherkin step needs to verify
  something with no corresponding public API, the LLM is instructed to assert
  the weakest true thing (e.g. "construction didn't throw") rather than invent
  a member to call

Output is post-processed by `_strip_markdown_blocks()`, which removes code
fences and truncates trailing LLM prose after the last valid C# line
(see the "Aggressive Markdown Stripping" fix in
`REQNROLL_IMPLEMENTATION_STATUS.md`).

## Dependency Notes (Python side)

Reqnroll itself is a .NET/NuGet dependency (`Reqnroll`, `Reqnroll.NUnit`,
`NUnit`, `NUnit3TestAdapter` — added to the test `.csproj` template in
`test_compiler.py`), not a Python package, so it does not appear in
`migration-poc/requirements.txt`.

`step_definitions_generator.py`'s Gherkin parsing is a small hand-rolled
line-based extractor (`GherkinStepExtractor`, using only `re`/`str` methods) —
it does not use the `gherkin-official` package already listed in
`requirements.txt`. That package remains there for other stages; no new
Python dependency was needed for step definitions.

## Error Message Reference

| Source | Format | Example |
|---|---|---|
| `step_definitions_compiler.py` `_parse_errors` | `{CS code} at {file}({line},{col}): {message}` | `CS0117 at StepDefinitions.cs(42,9): 'UserService' does not contain a definition for 'GetToken'` |
| `step_definitions_compiler.py` audit log | `migration-poc/audit/step-definitions-compilation-{run_id}.log` — status, error list, full build output | — |
| `reqnroll_test_runner.py` `_parse_step_failures` | Step binding / assertion failure lines, matched from `dotnet test` output, capped at 200 chars each | `Step binding not found for "the user is authenticated"` |

Both modules' catch-all exception handlers now prefix the underlying
exception with which operation failed (`dotnet build` vs `dotnet test`)
so a bare stack-trace string isn't the only signal in the audit log or
verification report.

## Known Limitations

See "Known Limitations (v1)" in `REQNROLL_IMPLEMENTATION_STATUS.md` — no step
reuse across scenarios, single Gherkin input, no interactive error
correction, basic mock generation, no reuse-conflict validation.
