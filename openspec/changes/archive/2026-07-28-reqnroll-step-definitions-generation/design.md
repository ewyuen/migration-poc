## Context

Current state: The migration pipeline generates Gherkin `.feature` files in Stage 5 (BDD generation), then transitions to verification. There is no step definition generation step. Test code generation bypasses Reqnroll's step binding model entirely.

Modernized code and domain logic are available from Stage 4. LangGraph V3 orchestrator (`orchestrator_v3.py`) provides the execution framework with OpenTelemetry tracing.

Reqnroll provides built-in type patterns (`{int}`, `{string}`, `{float}`) and `ScenarioContext` for state sharing, reducing the need for custom parsing logic.

## Goals / Non-Goals

**Goals:**
- Generate Reqnroll-compliant `StepDefinitions.cs` files with `[Binding]` classes
- Implement template-first approach: skeleton with TODOs, then LLM enhancement
- Add two new LangGraph nodes (step definitions generation and enhancement) into orchestrator pipeline
- Support compile + heal loop: immediate C# compilation with 3x retry on errors
- Use LLM to infer parameter mapping, ScenarioContext keys, and mock generation from step intent
- One `StepDefinitions.cs` file per feature file (accumulating steps from all scenarios in that feature)
- Leverage Reqnroll's standard type patterns; no custom regex inference

**Non-Goals:**
- Step reusability across features (v1 scope: each scenario gets its own step bindings)
- Custom step registry or pattern caching
- Integration with Visual Studio step definition IDE tools
- Support for non-Reqnroll frameworks
- Reqnroll configuration/infrastructure setup (assume `.csproj` and dependencies already present)

## Decisions

### 1. Template-First with LLM Enhancement
**Decision**: Generate skeleton `StepDefinitions.cs` with `[Binding]` class and method stubs containing `// TODO` placeholders. LLM fills these placeholders with implementations.

**Rationale**: 
- Skeleton provides structure and guarantees valid C# outline (correct attributes, method signatures)
- LLM enhancement based on full context (modernized code, domain logic, scenario chain) produces better implementations than unguided generation
- Clear phase separation: structure (template) vs. logic (LLM)

**Alternatives considered**:
- Full LLM generation without skeleton: Risk of invalid C# structure, harder to validate
- Template with zero placeholders, LLM only tweaks: Loses opportunity for semantic enhancement

### 2. LLM-Driven Inference for Parameters, Keys, and Mocks
**Decision**: All inference (parameter mapping, ScenarioContext key naming, mock method signatures) delegated to LLM based on natural language step intent, modernized code, and scenario context.

**Rationale**:
- LLM understands intent better than regex parsing or static analysis
- More flexible: LLM can make smart domain-aware decisions (e.g., "user" parameter → `_context["CurrentUser"]` not `_context["user"]`)
- Reduces custom parsing logic; cleaner codebase

**Alternatives considered**:
- Hardcoded pattern matching: Brittle, requires manual updates for new patterns
- Automatic type inference from Gherkin parameters: Limited to obvious cases (quoted text → string, digits → int)

### 3. Reqnroll Standard Type Patterns
**Decision**: Use Reqnroll's built-in `{int}`, `{string}`, `{float}` type patterns in step attributes. LLM infers which pattern applies per parameter.

**Rationale**:
- Official Reqnroll patterns: stable, well-documented, understood by framework
- No custom regex needed; Reqnroll handles parameter extraction automatically
- LLM already familiar with standard patterns

**Alternatives considered**:
- Custom regex patterns: Flexibility, but maintenance burden and risk of LLM hallucination

### 4. Compilation via dotnet build (Reuse Existing Pattern)
**Decision**: Reuse the `dotnet build` compilation approach from existing `test_compiler.py`. Generate a `tests.csproj` that references the source project, then invoke `dotnet build` in the tests directory. After LLM enhancement, compile once to validate. If compilation succeeds, proceed to verification. If compilation fails, log error and continue (graceful degradation; Reqnroll test runner will report missing/broken steps).

**Rationale**:
- Single-file `csc.exe` compilation fails on Reqnroll types, ScenarioContext, and modernized code type references (requires MSBuild + assembly resolution)
- Existing `test_compiler.py` (lines 61-131) proves the `dotnet build` + `.csproj` approach works and is already integrated
- Avoid duplicating the sophisticated heal loop in `TestOrchestrator` (test_orchestrator.py:138-200+), which is purpose-built for complex test code recovery
- Step definitions are simpler: validation is primarily syntax correctness; Reqnroll's test runner provides better feedback on step binding issues than an LLM retry loop

**Alternatives considered**:
- `csc.exe` single-file: Fails on type resolution; impossible for LLM to fix
- Multi-attempt heal loop: Adds complexity for diminishing returns; Reqnroll runner provides better diagnostics
- Adapt TestOrchestrator: Tight coupling; duplication of error-mapping logic already working elsewhere

### 5. ScenarioContext for State Sharing
**Decision**: Use Reqnroll's native `ScenarioContext` (key-value store) for sharing state between steps in a scenario.

**Rationale**:
- Standard Reqnroll pattern; framework-native
- Constructor injection of `ScenarioContext` is idiomatic
- LLM knows this pattern; straightforward to generate

**Alternatives considered**:
- Custom test context class: Adds abstraction; not Reqnroll-standard
- Static fields in step class: Not thread-safe; violates Reqnroll best practices

### 6. Single StepDefinitions.cs File (Not Per-Feature)
**Decision**: Generate a single `StepDefinitions.cs` file per component/run. `MigrationState.bdd_tests` contains Gherkin as a single string (not multiple `.feature` files), so all extracted steps accumulate into one `[Binding]` class.

**Rationale**:
- BDD generation outputs a single Gherkin blob in memory, not separate feature files
- One binding class for all steps simplifies Reqnroll configuration and discovery
- Accumulation in one file matches the single-feature Gherkin input model
- Future v2 can optimize for step reuse across multiple features if multi-feature Gherkin becomes input

**Alternatives considered**:
- Per-scenario files: Fragmented; Reqnroll discovery complex with multiple binding classes
- Per-feature files: Only viable if BDD stage changes to output multiple `.feature` files (future work)

### 7. LangGraph Node Integration (Split bdd_and_test, Remove Old Test Code Gen)
**Decision**: 
- Refactor existing `_node_bdd_and_test` to only generate Gherkin (rename to `_node_bdd_tests`), removing old test code generation and TestOrchestrator self-healing loop
- Add two new nodes: `step_defs_template` (skeleton generation) and `step_defs_enhance` (LLM enhancement + single compile check)
- New graph flow: `bdd_tests` → `step_defs_template` → `step_defs_enhance` → `verify`

**Rationale**:
- Reqnroll is the new test framework; old C# test code generation is replaced
- Avoid duplicating TestOrchestrator's sophisticated heal loop; let Reqnroll test runner provide step binding diagnostics
- Clear separation: BDD produces business specs, step definitions bind specs to implementation
- Maintains tracing/observability via LangGraph spans

**Alternatives considered**:
- Keep old test code generation in parallel: Diverges from Reqnroll adoption; wastes resources
- Single combined node: Harder to debug; LLM context mixing Gherkin extraction + enhancement
- Adapt TestOrchestrator for step definitions: Risk of regression; existing logic too complex for step-binding use case

### 8. Mock Generation Strategy
**Decision**: If a service/dependency referenced in a step does not exist in modernized code, generate a mock class inline in `StepDefinitions.cs`. LLM infers needed mock methods from step implementations.

**Rationale**:
- Self-contained: All step definition code in one file
- LLM can generate appropriate mock signatures
- Avoids external dependencies for testing

**Alternatives considered**:
- Fail and report missing dependencies: Breaks workflow
- Use Moq library: Adds complexity; LLM harder to coordinate

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| LLM hallucination (inventing method names) | LLM sees full modernized code; prompt emphasizes "use only methods shown in code" |
| Compilation failure on first attempt | Log error to audit trail; Reqnroll test runner will report missing/broken step bindings; user can manually refine |
| Parameter type inference ambiguity | Use Cucumber Expressions `{string}`, `{int}`, `{float}`; LLM sees type hints in modernized code signatures |
| Mock methods incomplete or incorrect | Reqnroll test runner provides clear error ("step not implemented"); v2 can refine mock inference |
| Reqnroll `ScenarioContext` key collisions | LLM infers unique, semantic keys (e.g., "CurrentUser", "AuthResult"); unlikely collision if naming discipline followed |
| Broken step bindings discovered at test time | Acceptable tradeoff; Reqnroll diagnostics are clearer than LLM retry loops; compilation validates C# syntax, not step binding correctness |

## Migration Plan

### Deployment
1. Implement two new LangGraph nodes in `orchestrator_v3.py`
2. Update `MigrationState` type with new fields (`step_definitions_skeleton`, `step_definitions_enhanced`)
3. Update graph routing to add nodes between `bdd_tests` and `verify`
4. Ensure Reqnroll NuGet package added to test `.csproj` templates
5. Test end-to-end: Gherkin → skeleton → enhancement → compilation → Reqnroll test run

### Rollback
- Remove the two new nodes from orchestrator; revert to direct `bdd_tests` → `verify` edge
- Old test code generation logic (if preserved) can be re-enabled
- No database or infrastructure changes; purely pipeline logic

## Open Questions

1. **Test output directory structure**: Where should generated `StepDefinitions.cs` be written?
   - Suggestion: `migrated-output/{run_id}/tests/StepDefinitions.cs` (co-located with `.feature` files)
   
2. **Reqnroll fixture/service injection**: How should test fixtures (e.g., `UserService` instances) be wired into step definitions?
   - Options: Constructor injection, factory method, static IoC container
   - Recommendation: Constructor injection (LLM-friendly, idiomatic)

3. **Feature file location**: Are `.feature` files already generated and persisted by BDD stage?
   - Confirmation needed: Are they in `migrated-output/{run_id}/tests/` or elsewhere?

4. **Error reporting to user**: If step definitions fail after 3 retries, what's the UX?
   - Log error and continue to verification (best-effort)?
   - Block verification and report?
   - Recommendation: Log error, store in audit, continue (matches existing orchestrator philosophy)
