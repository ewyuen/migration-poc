# Multi-Agent C# Extraction POC

Proof-of-concept for **Agentic C# Migration Pipeline** targeting **.NET 10**.

Uses DeepSeek via OpenRouter for cost-effective, sequential agent orchestration.

## Architecture

**6-Stage Migration Pipeline:**

```
Stage 1: VALIDATION
  └─ Verify component exists and is ready

Stage 2: STAGING
  └─ Copy component to legacy-code, create feature branch

Stage 3: EXPLORATION
  └─ Analyze code structure, extract domain logic

Stage 4: MODERNIZATION (with compilation verification)
  └─ Translate to .NET 10, generate .csproj

Stage 5: BDD & TEST WRITING (with self-healing loop)
  ├─ Generate Gherkin scenarios from modernized code
  ├─ Create test skeleton (.Tests.cs)
  └─ TestOrchestrator: Multi-attempt test generation
      ├─ Attempt 1-4: Fill test skeletons, compile
      ├─ Extract errors, retry with feedback
      └─ On failure after 4 attempts: Comment out failing tests
           (Tests are marked with TODO, not deleted)

Stage 6: VERIFICATION
  └─ Compile final tests, execute, collect coverage
      Reports: pass/fail counts, coverage %, commented tests
```

## Self-Healing Test Generation

**What are "commented tests"?**

When Stage 5 (Test Writing) encounters a test method that won't compile after 4 retry attempts, it gracefully "comments it out" rather than failing the pipeline. The test method is wrapped in `/* ... */` comments and preceded by a TODO marker:

```csharp
// TODO: Fix compilation error - test needs dependencies to be defined
/*
    [Fact]
    public void TestMethod_ShouldDoSomething()
    {
        // Test implementation that couldn't compile
    }
*/
```

**Why?** This keeps the pipeline flowing and allows verification to run and report. The commented tests are visible in the final test file for human review—nothing is hidden.

**How to review:**
1. Check the Test Orchestration report in `migrated-output/{component}/audit/`
2. Look for `commented_tests` in the workflow state
3. Open the final `.Tests.cs` file and search for `// TODO: Fix compilation` to find commented tests
4. Review the error messages and decide whether to:
   - Fix the test implementation manually
   - Skip that test for now
   - Investigate missing dependencies

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Configure OpenRouter API
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 2. Run Orchestration

```bash
python orchestrator.py
```

### 3. Review Outputs

Results are saved to `output/`:
- `1_exploration_report.json` - Component analysis
- `2_extracted_domain_logic.cs` - Pure business logic
- `3_modernized_code.cs` - .NET 10 implementation
- `4_bdd_test_scenarios.feature` - Gherkin test specs
- `5_verification_report.json` - Quality assurance report
- `0_complete_results.json` - Full pipeline results

## Key Features

✅ **6-Stage Pipeline** - Validation → Staging → Exploration → Modernization → Test Writing → Verification
✅ **Self-Healing Test Generation** - Up to 4 retry attempts with error feedback; gracefully comments out failing tests
✅ **Domain Logic Extraction** - Pure business logic separated from infrastructure
✅ **BDD Test Generation** - Gherkin scenarios for medical workflows
✅ **Compliance Verification** - 21 CFR Part 11 checks
✅ **Cost-Effective** - Uses DeepSeek via OpenRouter (~$0.27/1M tokens)
✅ **Resilient** - Pipeline continues even if some tests can't be fixed (commented out with TODO)
✅ **Transparent** - All agent outputs saved for review, audit trail recorded
✅ **.NET 10 Target** - Modern C# 14 patterns and async-first design

## For the Interview

When demonstrating to Babita Jain:

```
"I built this POC to show how we can use sequential AI agents 
to safely modernize legacy medical software. Each agent has a 
specific role:

1. Explorer analyzes the code and identifies refactoring needs
2. Extractor pulls out pure domain logic
3. Modernizer translates to .NET 10 with modern patterns
4. BDD Agent generates compliance-focused tests
5. Verifier ensures correctness and regulatory compliance

All outputs are transparent and auditable—exactly what you need 
for 21 CFR Part 11. The Human-in-the-Loop gate is the PR review 
where your QA team approves before deployment.

This is single-component. At Agilent scale, a Coordinator agent 
would decompose your entire OpenLab Suite into modules, workers 
would process them in parallel, and the Safe Outputs Gate ensures 
nothing ships without approval."
```

## Next Steps (Day 2)

- [ ] Wrap agents in GitHub Actions workflow
- [ ] Add manual approval gate (Pull Request step)
- [ ] Add CFR Part 11 audit trail recording
- [ ] Test end-to-end on different legacy components

## Model Selection

Using **DeepSeek-V3** via OpenRouter:
- Fast: ~10-30s per agent
- Cheap: $0.27 / 1M tokens
- Excellent at code analysis and generation
- Perfect for medical domain logic extraction

To use a different model, update `.env`:
```
MODEL=meta-llama/llama-3.1-405b-instruct  # For more power
MODEL=qwen/qwen-2.5-72b-instruct  # For better reasoning
```

## Architecture Decisions

### Sequential vs. Parallel
**Chosen: Sequential** - Simpler to debug, clearer orchestration logic, easier to demo

### Local vs. GitHub Workflow
**Day 1: Local Python** - Fast iteration, direct output review
**Day 2: GitHub Actions** - Production-ready, audit trail, approval gates

### Agent Communication
**Chosen: JSON + Direct Pass** - Each agent outputs JSON/text, next agent reads it directly

## CFR Part 11 Compliance

This POC demonstrates key Part 11 controls:
- ✅ Audit trail (who ran what, when)
- ✅ Change documentation (all outputs logged)
- ✅ Verification (verifier agent checks correctness)
- ✅ Human approval ready (PR approval gate in workflow)

## Questions?

For the Agilent interview, key talking points:
1. Why sequential agents? (Simpler, more debuggable, easier to audit)
2. Why DeepSeek? (Cost-effective, sufficient quality for code extraction)
3. Where's human-in-the-loop? (PR approval before deployment)
4. How does this scale? (Add Coordinator agent, parallelize workers, add Safe Outputs Gate)
5. How is compliance maintained? (Every step logged, verifier checks compliance)
