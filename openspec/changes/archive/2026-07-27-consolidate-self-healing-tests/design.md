## Context

The current pipeline (feat/consolidate2) has 6 stages ending with BDD test generation and verification. The manual-tests branch introduces a `TestOrchestrator` that wraps test generation and compilation in a self-healing loop. The goal is to merge this orchestrator into the main pipeline so Stage 5 remains operational even when tests initially fail to compile.

Current state:
- orchestrator_v2.py Stage 5 calls TestWriterStage.execute() once, then saves results
- If tests don't compile, verification fails and halts
- No mechanism to recover from compilation failures

Desired state:
- Stage 5 wraps test generation + compilation in a 4-attempt loop
- Each attempt: generate test implementations → compile & run
- If failures persist after 4 attempts, comment out failing tests and proceed
- Verification stage always runs and reports status (no premature failure)

## Goals / Non-Goals

**Goals:**
- Integrate TestOrchestrator from manual-tests into orchestrator_v2.py Stage 5
- Enable self-healing loop that recovers from test compilation failures
- Keep Stage 5 isolated and composable (TestOrchestrator as separate class)
- Preserve Stage 6 (verification) as the final reporter; it always runs
- Support feedback_errors parameter in TestWriterStage for iterative refinement

**Non-Goals:**
- Merge code_compiler.py or modernization_orchestrator.py (out of scope)
- Change the 6-stage structure (only refactor Stage 5 internally)
- Modify existing agents (explorer, modernizer, bdd_test_cases_generator)
- Handle test runtime failures (only compilation failures)

## Decisions

**Decision 1: TestOrchestrator as separate, imported class**
- Rationale: Keeps orchestrator_v2.py focused on stage coordination; TestOrchestrator handles test-specific loop logic. Mirrors separation in manual-tests branch.
- Alternative considered: Inline the loop logic directly in orchestrator_v2.py Stage 5 → Would bloat the main orchestrator and mix concerns.

**Decision 2: Max 4 attempts (not configurable in initial version)**
- Rationale: User specified this limit; it's a pragmatic balance between giving LLM chances to fix vs. preventing infinite loops.
- Alternative considered: Make it configurable via config.yaml → Adds complexity; 4 is sufficient and predictable.

**Decision 3: Comment out failing tests instead of failing workflow**
- Rationale: Allows visibility into what's broken while keeping pipeline flowing. Verification stage reports the commented tests clearly.
- Alternative considered: Fail workflow if any tests commented → Too rigid; would require manual intervention for every test failure.

**Decision 4: TestWriterStage.feedback_errors parameter is optional**
- Rationale: Backward-compatible; existing callers don't need to pass it. New callers (TestOrchestrator) can pass errors from compilation failures.
- Alternative considered: Make it required → Breaking change; not necessary.

**Decision 5: Read final test code from disk, not from TestOrchestrator return value**
- Rationale: Test code already persisted by TestWriterStage; reading from disk ensures we capture the actual final state (with comments if any).
- Alternative considered: Return test code from TestOrchestrator → Unnecessary duplication; disk read is authoritative.

## Risks / Trade-offs

**[Risk] TestOrchestrator gets out of sync with TestWriterStage or TestRunner**
→ Mitigation: Keep TestOrchestrator minimal; it only orchestrates, doesn't implement. Both TestWriterStage and TestRunner are stable, imported modules.

**[Risk] 4 attempts may be too many (slow) or too few (doesn't recover)**
→ Mitigation: 4 attempts is empirically reasonable (each ~10-30s). Monitor actual behavior; adjust if needed post-merge.

**[Risk] Commented tests hide real issues**
→ Mitigation: Verification stage prominently reports commented test count and locations. Code review of final test file is mandatory.

**[Risk] TestWriterStage may not use feedback_errors effectively**
→ Mitigation: This is handled in implementation; we update TestWriterStage to pass feedback_errors to the test-writing agent.

## Migration Plan

1. **Pull from manual-tests**: Copy test_orchestrator.py and test_runner.py into agents/
2. **Update TestWriterStage**: Add feedback_errors parameter and pass to agent if provided
3. **Import in orchestrator_v2.py**: Add `from agents.test_orchestrator import TestOrchestrator`
4. **Refactor Stage 5**:
   - Keep: Generate gherkin, generate skeleton, read from disk
   - Replace: Direct TestWriterStage.execute() → TestOrchestrator.execute()
   - Capture: orchestration result (status, attempted, commented_tests)
5. **Test**: Run orchestrator on a component; verify self-healing loop works and commented tests appear with TODO markers
6. **No rollback needed**: feat/consolidate2 remains the fallback; this is additive

## Open Questions

- Should we log each attempt's error details to audit trail? (Recommendation: yes, capture in state.artifacts)
- Should the max_attempts be configurable via migration_config.yaml? (Recommendation: hardcode to 4 for now; can expose later if needed)
