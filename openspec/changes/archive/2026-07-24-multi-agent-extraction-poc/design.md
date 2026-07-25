## Context

This POC prepares for a role of **Software Modernization Enablement Lead Engineer**, demonstrating practical mastery of multi-agent AI workflows for legacy code modernization in regulated (medical/21 CFR Part 11) environments. The starting point is a real legacy WPF/WCF medical application (`mti-wpf` codebase) that serves as both the proof-of-concept input and a realistic proxy for modernization challenges of device company.  The goal is to show a *working, auditable, scalable methodology* that can be demonstrated as a POC.

## Goals / Non-Goals

**Goals:**
- Build a working multi-agent pipeline that can run locally in 2 days
- Demonstrate sequential agent orchestration with transparent, auditable outputs
- Show practical understanding of code extraction, domain logic isolation, and modernization
- Generate realistic artifacts (modernized C# code, BDD tests, verification reports) for interview discussion
- Establish a foundation for scaling to GitHub Actions workflow (Day 2)
- Illustrate compliance-first architecture (CFR Part 11 audit trails, verification gates)

**Non-Goals:**
- Production-ready deployment (this is a POC, not a shipping service)
- Comprehensive formal verification (Lean proofs mentioned but not implemented in this phase)
- Parallel agent execution (sequential is simpler, clearer, more auditable for interview)
- Integrate with existing systems (reference architecture only)
- Support for languages other than C# (POC focuses on legacy C# → .NET 10)

## Decisions

### Decision 1: Sequential Agent Orchestration (vs. Parallel)
**Choice**: Sequential execution (Explorer → Extractor → Modernizer → BDD → Verifier)

**Rationale**:
- **Simpler to debug**: Each agent's output is explicit, reviewable, and serves as input for the next
- **More auditable**: Clear handoff trail, easier to understand what each agent did and why
- **Interview-friendly**: Can narrate each step and show intermediate outputs
- **Sufficient speed**: ~2-5 minutes total runtime for a single component
- **Easier error recovery**: If one agent fails, you know exactly where and can retry

**Alternative considered**: Parallel workers (Explorer plans 5 tasks, all run concurrently)
- Pro: Faster execution at scale
- Con: More complex coordination, harder to demo, requires shared state management
- **Decision**: Defer parallelization to Day 2 GitHub Actions (where orchestrator can spawn parallel jobs)

### Decision 2: OpenRouter + DeepSeek (vs. Claude API, other models)
**Choice**: DeepSeek-V3 via OpenRouter

**Rationale**:
- **Cost**: ~$0.27 per 1M tokens vs. Claude at $3-15 per 1M tokens (10-50x cheaper)
- **Code quality**: DeepSeek specializes in code analysis and generation, performs well on C# migration tasks
- **Availability**: User already has OpenRouter account, immediate access
- **Sufficient for POC**: No need for Opus-level reasoning for code extraction and modernization

**Alternatives considered**:
- Claude Opus: Better quality, but expensive; better for Day 2 when budget is clearer
- Llama 405B via OpenRouter: Slightly more capable than DeepSeek, 5x more expensive
- Local LLM (Ollama): Would avoid API cost, but adds infrastructure complexity and slower inference

**Decision**: DeepSeek for POC (fast iteration, cost-effective), can upgrade to Claude for production if needed.

### Decision 3: Local Python Scripts First, Then GitHub Actions
**Choice**: Day 1 = local Python orchestrator, Day 2 = wrap in GitHub workflow

**Rationale**:
- **Faster iteration**: Local scripts run instantly, no GitHub API latency, easier debugging
- **Transparent outputs**: Direct inspection of agent results without GitHub artifact download delays
- **Interview-ready**: Can run live demo on laptop during interview
- **Foundation for automation**: Day 2 wraps the same agents in workflow, adding CI/CD pipeline and approval gates

**Alternative considered**: Build GitHub Actions from day one
- Pro: Production-ready from start
- Con: Slower iteration (GitHub API calls, workflow triggering), harder to debug, needs secrets management

**Decision**: Build locally first (known, fast, controllable), package into workflow second (production-ready, auditable).

### Decision 4: Transparent Agent Outputs (JSON + Code + Feature Files)
**Choice**: Each agent writes to `output/` directory with clearly named files

**Files produced**:
1. `1_exploration_report.json` - Agent #1 analysis output
2. `2_extracted_domain_logic.cs` - Agent #2 domain logic code
3. `3_modernized_code.cs` - Agent #3 .NET 10 implementation
4. `4_bdd_test_scenarios.feature` - Agent #4 Gherkin test specs
5. `5_verification_report.json` - Agent #5 verification results
6. `0_complete_results.json` - Full pipeline results in one file

**Rationale**:
- **Auditability**: Every step is logged and can be reviewed
- **Human-in-the-Loop ready**: Clear approval gates (PR review before merge)
- **CFR Part 11 compliance**: Full chain of custody for code changes, who ran what, when

### Decision 5: .NET 10 Target (vs. .NET 8 or .NET Core 7)
**Choice**: .NET 10 (latest stable)

**Rationale**:
- **Forward-looking**: Shows understanding of platform roadmap
- **C# 14 features**: Modern syntax and patterns (records, pattern matching, IAsyncEnumerable)
- **Interview positioning**: Demonstrates cutting-edge thinking, matches latest modernization goals
- **Performance & Cloud-native**: .NET 10 optimizations for containerized, Kubernetes deployments

### Decision 6: Single Component POC (vs. Multiple Components)
**Choice**: Focus on one legacy component (`Observation.cs`) to completion

**Rationale**:
- **Demonstrate depth**: Full workflow from analysis to verification on one realistic component
- **Time constraint**: 2 days; better to finish one component completely than start many
- **Scalability narrative**: Can explain "this shows single-component; at scale, Coordinator decomposes into 20+ components, all run in parallel via GitHub Actions workers"

**Alternative**: Multiple components to show breadth
- Pro: Demonstrates variety
- Con: Incomplete outputs, harder to explain each step

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **DeepSeek API slowness** (first agent ~30s) | Document expected runtime; emphasize that this is acceptable for async CI/CD pipelines. Day 2 GitHub Actions can trigger overnight. |
| **Agent hallucination** (LLM generates incorrect C# code) | Verifier Agent catches semantic errors; human review before merge (HITL gate) catches remaining issues. Not a blocker for POC. |
| **Limited error handling** (what if DeepSeek returns malformed JSON?) | POC accepts "good enough" outputs; production would need retry logic, timeout handling, graceful degradation. Add to Day 2 roadmap. |
| **Test coverage** (generated BDD tests may not be exhaustive) | Acceptable for POC; interviewer will understand this is a starting point, not production-ready test suite. |
| **CFR Part 11 audit trail incomplete** (Day 2 only) | Acknowledged: this POC demonstrates the *structure* of an audit trail (who, what, when, why). Full compliance requires signature/timestamp infrastructure (deferred to production). |
| **No parallel execution** (sequential is slower than possible) | Trade-off for clarity and auditability. Parallelization is a Day 2 feature. |
| **Tight 2-day timeline** | Risk: If LLM API is slow or agent logic needs debugging, completion may slip. Mitigation: Clear priority (complete 5 agents by end of Day 1; GitHub workflow second priority on Day 2). |

## Migration Plan

### Day 1: Local Execution
1. **Setup** (30 min): Environment, OpenRouter key, requirements.txt
2. **Run orchestrator.py** (30 min): Execute all 6 agents sequentially
3. **Review outputs** (30 min): Examine generated files, verify quality
4. **Document results** (30 min): Create README, screenshot demo

**Deliverable**: Working local pipeline with 6 output files, ready to discuss with interviewer

### Day 2: GitHub Actions Workflow
1. **Create workflow file** (1 hour): `.github/workflows/multi-agent-extraction.yml`
   - Trigger: `workflow_dispatch` (manual) or PR label
   - Jobs: Orchestrator job runs Python orchestrator.py
   - Outputs: Artifacts uploaded for review

2. **Add approval gate** (1 hour):
   - PR created with agent outputs as comments
   - Manual approval required before merge
   - CFR Part 11 audit trail recorded (JSON with timestamp, approver, rationale)

3. **Test end-to-end** (1 hour): Manually trigger workflow, review PR, approve, merge

**Deliverable**: Production-ready GitHub workflow demonstrating CI/CD + HITL gate + audit trail

### Rollback Strategy
- This is exploratory code; no production systems affected
- If workflow fails, simply delete the PR and re-run (no data loss risk)
- Local scripts can always be re-run offline for debugging

## Open Questions

1. **Should we add formal verification (Lean proofs) in Day 2?**
   - Feasible but time-consuming; current plan defers to "future work"
   - Could add optional Lean proof for critical domain logic (e.g., validation rules)

2. **How deep should the CFR Part 11 audit trail be?**
   - Current plan: JSON log with who/what/when/why
   - Production would need: digital signatures, immutable records, role-based access control
   - For POC: structured audit trail is sufficient

3. **Should BDD tests be generated as runnable SpecFlow code?**
   - Current plan: Gherkin feature files (human-readable, framework-agnostic)
   - Could add: Step definitions (C#) for immediate test execution
   - Decision: Feature files are sufficient for POC; step definitions can follow

4. **What if the generated code has bugs?**
   - Expected: Verifier Agent will flag issues in verification report
   - HITL gate (human PR review) will catch remaining issues
   - Acceptable for POC: this demonstrates the *safety net* of human oversight

---

**Next Steps**: Implement tasks.md to define concrete work items for Day 1 and Day 2.
