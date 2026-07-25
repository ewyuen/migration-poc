# Day 1: Get the POC Running (Today)

Your goal: **Run the multi-agent pipeline end-to-end and collect outputs.**

## Step 1: OpenRouter Setup (5 min)

1. Go to https://openrouter.ai/keys
2. Create an API key (free tier available)
3. Keep the key safe

## Step 2: Local Setup (5-10 min)

```bash
# Open PowerShell in migration-poc directory
cd migration-poc

# Copy env template
cp .env.example .env

# Edit .env with your API key
notepad .env
# Set: OPENROUTER_API_KEY=sk_your_key_here

# Run quick start
.\run.ps1
```

Or on macOS/Linux:
```bash
cd migration-poc
cp .env.example .env
nano .env  # Add your API key
bash run.sh
```

## Step 3: What to Expect

The orchestrator will run 6 steps sequentially:

```
[STEP 1/6] EXPLORER AGENT
🔍 Analyzing Observation.cs...
✅ Analysis complete

[STEP 2/6] EXTRACTOR AGENT
🧬 Extracting domain logic...
✅ Domain logic extracted

[STEP 3/6] MODERNIZER AGENT
🚀 Translating to .NET 10...
✅ Code modernized

[STEP 4/6] BDD TEST AGENT
📝 Generating test scenarios...
✅ Test scenarios generated

[STEP 5/6] VERIFIER AGENT
✔️ Validating modernization...
✅ Verification complete

[STEP 6/6] COMPILE RESULTS
✅ All results saved

📊 Summary:
  Component: Observation
  Status: PASS/FAIL/CAUTION
  Verification Risks: [...]

📁 All outputs saved to: output/
```

Runtime: **~2-5 minutes** (depends on OpenRouter response times)

## Step 4: Review Outputs

Open `output/` directory and review:

1. **1_exploration_report.json**
   - What the legacy code does
   - Pain points identified
   - Refactoring opportunities
   - Subtasks for other agents

2. **2_extracted_domain_logic.cs**
   - Pure business logic extracted
   - No I/O, no side effects
   - Ready to reuse in new code

3. **3_modernized_code.cs**
   - Modern .NET 10 implementation
   - Uses extracted domain logic
   - Async-first, DI-ready
   - C# 14 patterns

4. **4_bdd_test_scenarios.feature**
   - Gherkin BDD test specs
   - Medical domain scenarios
   - Compliance-focused (CFR Part 11)

5. **5_verification_report.json**
   - Behavioral equivalence check
   - Test coverage analysis
   - Compliance verification
   - Security scan results
   - Overall status (PASS/FAIL/CAUTION)

6. **0_complete_results.json**
   - Full pipeline results in one file
   - All agent outputs combined
   - Ready for commit/review

## Step 5: Troubleshooting

**Issue: "OPENROUTER_API_KEY not found"**
- Solution: Make sure `.env` file exists and has correct key format

**Issue: "ConnectionError" from LLM**
- Solution: Check internet connection and API key validity

**Issue: "Model not found"**
- Solution: Verify MODEL in .env is correct (default: deepseek/deepseek-chat)

**Issue: Slow responses**
- Solution: Normal for DeepSeek. First agent takes longest (~30s). Subsequent agents are faster.

## Step 6: Create Proof for Interview

After the pipeline completes:

```bash
# Create a summary screenshot/document
cd output
ls -la
# OR on Windows:
# dir
```

**Screenshot idea for interview:**
1. Show the command running
2. Show the 6 agent steps executing
3. Show the output directory with all generated files
4. Open one of the generated files (modernized_code.cs)

## Next: Day 2 Plan

Tomorrow you'll:
- [ ] Wrap this in GitHub Actions workflow
- [ ] Add manual approval gate (Pull Request)
- [ ] Add CFR Part 11 audit trail recording
- [ ] Create demo narrative for Babita

## Quick Checklist

- [ ] OpenRouter API key obtained
- [ ] .env configured
- [ ] `pip install -r requirements.txt` complete
- [ ] `python orchestrator.py` runs successfully
- [ ] `output/` directory has 6 files
- [ ] Review outputs and understand each agent's contribution
- [ ] Screenshot/document results for interview
- [ ] Commit to git with message: "POC: Multi-agent extraction pipeline working locally"
