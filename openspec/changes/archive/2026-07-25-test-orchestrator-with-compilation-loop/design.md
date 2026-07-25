## Context

The current migration workflow has 6 stages, with stage 5 (TestWriterStage) generating test implementations from Gherkin. Stage 6 (Verification) then attempts to compile and run these tests. When LLM-generated tests have errors (missing methods, incorrect signatures, type mismatches), the compilation fails entirely and the workflow stalls. 

Currently, errors are simply reported to the user who must manually fix tests. A test orchestrator stage can automatically comment out problematic tests to achieve compilability, allowing the pipeline to produce valuable partial results (90% of tests working) rather than failing completely (0% of tests working).

## Goals / Non-Goals

**Goals:**
- Automatically comment out test methods that cause compilation errors
- Loop compilation attempts up to a maximum configured number (default: 5 retries)
- Exit when compilation succeeds (preferred) or max retries exceeded (fallback)
- Report which tests were commented out, why, and on which iteration
- Preserve all test code (commented, not deleted) so users can later review and fix

**Non-Goals:**
- Automatically fix test logic errors (only handle compilation errors)
- Regenerate test code or call TestWriterAgent again
- Modify source code under tests/src/
- Change Gherkin scenarios or BDD coverage
- Handle warnings or code analysis issues (only errors block compilation)

## Decisions

**Decision 1: Use `dotnet build` instead of `dotnet test` for compilation checks**
- *Rationale*: `dotnet build` is faster and focuses only on compilation errors, avoiding timeout issues from test execution
- *Alternative considered*: Use `dotnet test --no-run` (similar benefit but build is more direct)

**Decision 2: Parse MSBuild error output to identify affected methods**
- *Rationale*: Enables surgical removal of only the problematic method, leaving working tests intact
- *Alternative considered*: Comment out entire test classes (too aggressive, loses more tests than necessary)

**Decision 3: Insert as new stage 5A (TestCompilationOrchestrator) between TestWriterStage and Verification**
- *Rationale*: Keeps concerns separated; Verification stage receives pre-compiled code
- *Alternative considered*: Embed in TestWriterStage (would couple concerns); Embed in Verification (makes verification step unclear)

**Decision 4: Loop up to 5 times by default (configurable)**
- *Rationale*: Most compilation errors are fixed after 1-2 loops; 5 provides safety margin without excessive retries
- *Alternative considered*: Loop until clean (risk of infinite loop on persistent issues)

**Decision 5: Comment out by method**
- Implementation: Find method signature from error line number, replace entire method body with `// Commented out: <reason>`
- *Rationale*: Preserves structure, allows review, minimal code change
- *Alternative considered*: Delete method entirely (loses code for review)

**Decision 6: Configuration via config YAML (test_orchestrator section)**
- *Rationale*: Consistent with existing TestWriterStage configuration pattern
- Properties: `enabled`, `max_iterations`, `comment_style` (line vs block)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Incorrect error parsing may comment out working tests | Test error parsing with sample MSBuild output before release; fallback: comment conservatively |
| Infinite loops on persistent errors | Max iteration limit (default 5) ensures termination |
| User loses sight of what tests were removed | Report commented tests with reasons in verification report and workflow artifacts |
| Compilation succeeds but test count drops unexpectedly | Document in migration report which tests were commented and why; helps user understand coverage gaps |

## Migration Plan

**Deployment:**
1. Create new TestCompilationOrchestrator class in `agents/test_orchestrator.py`
2. Integrate into orchestrator_v2.py as stage 5A (inject between test_writer_stage and verification)
3. Update workflow state to track test orchestration results
4. Modify verification report to include commented test statistics

**Rollback:**
- Set `test_orchestrator.enabled: false` in config to skip stage 5A
- Existing test projects that previously compiled will continue to work

## Open Questions

1. Should we attempt to fix certain classes of errors automatically (e.g., adding missing `await` to async calls)?
   - Current decision: No, only comment out. Future enhancement if needed.

2. Should commented tests be reported as "failures" or "skipped" in the verification report?
   - Current decision: New category "commented" distinct from pass/fail/skip.

3. What error message should we include in the comment for each commented-out test?
   - Current decision: Include compiler error number and message (e.g., `// CS1061: 'AuthService' does not contain a definition for 'Login'`)
