## Context

The current modernization stage (Stage 5 in orchestrator_v2.py) generates modernized code once without any compilation verification. Errors in the generated code are only discovered during test execution (Stage 7), after test generation work has already been invested. This wastes resources and makes it hard to distinguish modernization problems from test generation problems.

We have a proven pattern for this from the recent self-healing test orchestrator implementation: coordinate an agent (test writer) with a verification step (test runner), passing errors back to the agent for refinement up to a maximum attempt count.

## Goals / Non-Goals

**Goals:**
- Add a self-healing loop to the modernization stage that verifies generated code compiles
- Extract structured compilation errors (line number, error message, type info) from C# compiler output
- Pass errors back to the modernizer LLM for refinement (attempt-aware feedback)
- Fail fast: if code won't compile after 3 attempts, exit the entire orchestration
- Skip test generation when modernization fails (save effort)
- Unified reporting: modernization failures reported through the verifier agent

**Non-Goals:**
- Fixing compilation errors automatically (LLM-assisted only)
- Compiling code with external dependencies (verify modernized code in isolation only)
- Keeping intermediate modernization attempts (save only the final version)
- Adding new architectural components beyond the modernization orchestrator (reuse existing patterns)

## Decisions

### Decision 1: ModernizationOrchestrator Pattern
**Choice:** Create a new `ModernizationOrchestrator` class following the same structure as `TestOrchestrator`

**Rationale:**
- TestOrchestrator is proven and familiar
- Loop-based coordination is well-understood
- Consistent with existing patterns reduces cognitive load
- Encapsulates modernization orchestration separately from main orchestrator

**Alternatives Considered:**
- Inline the loop in orchestrator_v2.py → Reduces reusability, makes main orchestrator harder to follow
- Fold into existing modernizer code → Couples orchestration with LLM logic
- Custom orchestrator design → Wastes time, increases maintenance burden

### Decision 2: Compilation Target - Modernized Code Only
**Choice:** Compile just the modernized .cs files in isolation without resolving external dependencies

**Rationale:**
- Source code is assumed compilable, so modernized code SHOULD compile without external context
- Avoids complexity of mocking dependencies or building full project
- Fast feedback (no waiting for full build)
- Contract: if source compiles, modernized code MUST compile

**Alternatives Considered:**
- Full project build with dependencies → Adds complexity, slower feedback
- Type-checking only (no compilation) → Misses runtime errors, less reliable

### Decision 3: Error Extraction - Use C# Compiler Diagnostics
**Choice:** Use C# compiler error output directly, extracting line number, error code, and message

**Rationale:**
- C# compiler provides structured diagnostics with line #, error code, and clear messages
- No need to parse or normalize error output
- Type information is included in compiler messages
- Proven approach (C# tools ecosystem uses this)

**Alternatives Considered:**
- Custom error parser → Fragile, maintenance burden
- Roslyn API for semantic analysis → Overkill for syntax/type errors

### Decision 4: Feedback to Modernizer - Attempt-Aware
**Choice:** Pass attempt number and structured error list back to modernizer LLM in the prompt

**Rationale:**
- LLM can adjust strategy ("attempt 2 of 3, focus on X")
- Error context helps LLM understand what broke
- Explicit attempt count creates urgency for effective fixes

**Alternatives Considered:**
- Send errors without attempt number → Less focused refinement
- No feedback, generate fresh each time → Ignores previous errors, won't converge

### Decision 5: Max Attempts = 3
**Choice:** Hard limit of 3 attempts, then fail the entire orchestration

**Rationale:**
- Pattern proven in TestOrchestrator
- Balances giving modernizer multiple chances vs. failing fast
- Avoids infinite loops
- After 3 attempts, if still broken, likely a fundamental design issue (not fixable by iteration)

**Alternatives Considered:**
- 1 attempt → No chance to fix, too strict
- 5 attempts → Too much looping, waste of resources
- Configurable → Adds complexity without clear benefit

### Decision 6: Conditional Test Generation
**Choice:** Test generation and execution (Stages 6-7) only run if modernization succeeds

**Rationale:**
- No point generating tests for code that won't compile
- Saves effort on test generation if modernization fails
- Clear stage dependency (tests depend on compilable code)
- Simplifies verifier reporting (single responsibility: modernization succeeded or failed)

**Alternatives Considered:**
- Generate tests anyway → Wasted effort, tests won't run
- Generate tests in parallel → Over-complicates orchestration

### Decision 7: Unified Failure Reporting - Verifier Handles Both
**Choice:** Verifier agent reports both modernization failures and test execution failures

**Rationale:**
- Verifier already has the reporting infrastructure (markdown, JSON, audit logs)
- Single source of truth for "did this component migration succeed?"
- Simplifies orchestrator error handling

**Alternatives Considered:**
- ModernizationOrchestrator reports failure directly → Doesn't leverage verifier, inconsistent

## Risks / Trade-offs

**[Risk]** LLM may not converge on compilable code even with feedback
→ **Mitigation:** 3 attempts is a reasonable limit; if still broken, likely indicates fundamental modernization issue (not fixable by iteration). Fail gracefully with detailed error report.

**[Risk]** Error messages might not always be clear enough for LLM to fix
→ **Mitigation:** C# compiler provides context (line #, type info); pass full error context. If LLM can't understand standard compiler output, modernization approach needs review.

**[Risk]** Compilation check adds latency to orchestration
→ **Mitigation:** Compilation of isolated code is fast (seconds, not minutes). Worth the latency for fail-fast detection.

**[Risk]** Modernized code might compile in isolation but fail with dependencies
→ **Mitigation:** This is an implementation testing problem, not modernization problem. Tests will catch it; verifier will report.

## Migration Plan

1. Implement ModernizationOrchestrator class (parallel to TestOrchestrator)
2. Implement code compiler verification step
3. Update modernizer LLM prompt to handle attempt-aware feedback
4. Update orchestrator_v2.py to integrate ModernizationOrchestrator before test generation
5. Test the end-to-end flow on TestService component
6. Update main spec documentation for `code-modernization-dotnet10` and `agent-orchestration`

## Open Questions

- Should we save compilation error logs for each attempt (for debugging), or only final version? → *Decision: Save only final version, errors are logged to console and verifier report*
- How should we present modernization errors in verifier report differently from test errors? → *Keep separate sections in report (Modernization Failures vs. Test Failures)*
