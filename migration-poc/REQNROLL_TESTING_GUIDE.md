# Reqnroll Step Definitions Implementation - Testing Guide

## Overview

This guide walks through end-to-end testing of the new Reqnroll step definitions orchestration pipeline (Stages 1-8).

## What's Implemented

✅ **Complete 8-stage orchestrator pipeline:**
1. Validate - request validation
2. Stage - component staging
3. Explore - LLM code analysis
4. Modernize - code migration
5. BDD Tests - Gherkin generation (refactored, test code generation removed)
6. Step Defs Template - skeleton generation with Cucumber Expressions
7. Step Defs Enhance - LLM implementation filling + dotnet build validation
8. Verify - Reqnroll BDD test execution + coverage collection

## Pre-Test Checklist

- [ ] Reqnroll NuGet packages added to test .csproj
- [ ] Python dependencies: `pip install langchain langsmith opentelemetry-api opentelemetry-sdk langgraph`
- [ ] C# 10 SDK available (`dotnet --version`)
- [ ] Sample component available in `legacy-src/` directory

## Testing Steps

### 1. Quick Smoke Test

Run a minimal migration to verify the pipeline doesn't crash:

```bash
cd migration-poc
python -c "
from orchestrator_v3 import OrchestratorV3
from input_handler import MigrationRequest

orchestrator = OrchestratorV3()
request = MigrationRequest(
    component_name='TestService',
    target_framework='net10.0'
)
result = orchestrator.orchestrate_migration(request)
print('Pipeline completed:', result.get('current_stage'))
"
```

**Expected output**: `Pipeline completed: verify` or similar end stage

### 2. Verify Step Definitions Generation

Check that skeleton and enhanced files are created:

```bash
# After running migration with run_id = <run_id>
ls -la migrated-output/<run_id>/tests/StepDefinitions.cs
cat migrated-output/<run_id>/tests/StepDefinitions.cs
```

**Expected**: `StepDefinitions.cs` file with:
- `[Binding]` class attribute
- `[Given]`, `[When]`, `[Then]` method attributes
- Cucumber Expression syntax: `{string}`, `{int}`, `{float}`
- ScenarioContext constructor injection
- TODO placeholders for LLM enhancement

### 3. Verify LLM Enhancement

Check that TODO placeholders are filled:

```bash
# Open StepDefinitions.cs
# Verify no "// TODO" comments remain
# Verify method bodies have real C# code (not just comments)
```

**Expected**: 
- All method implementations filled (not TODO)
- Proper C# syntax
- ScenarioContext usage for state sharing

### 4. Verify Compilation

Check compilation output:

```bash
# During orchestrator run, watch for compilation status
# Check audit log:
cat migration-poc/audit/step-definitions-compilation-<run_id>.log
```

**Expected**:
- Status: SUCCESS or FAILED (with detailed error messages)
- No "csc.exe" errors (using dotnet build)
- Build output captured for diagnostics

### 5. Verify Reqnroll Test Execution

Check that BDD tests run:

```bash
# Verification stage runs automatically
# Check verification results:
cat migrated-output/result-log/<component_name>_verification_report.md

# Look for:
# - reqnroll_scenarios: N
# - reqnroll_scenarios_passed: N
# - step_failures: (should be empty if all passed)
```

**Expected**:
- Reqnroll scenarios executed
- Coverage metrics collected
- Step bindings found (no "step not implemented" errors)

### 6. Manual Feature File + Step Definitions Test

Create a standalone test to verify Reqnroll execution:

```bash
cd migrated-output/<run_id>/tests

# Run Reqnroll tests directly
dotnet test

# Or with more verbosity:
dotnet test --verbosity=detailed --logger=console
```

**Expected**:
- Tests compile successfully
- Scenarios execute
- Pass/fail results shown

## Troubleshooting

### Issue: "Step binding not found"
- Check StepDefinitions.cs has `[Binding]` class
- Verify `[Given]`, `[When]`, `[Then]` attribute syntax
- Ensure Cucumber Expressions match Gherkin step text

### Issue: Compilation fails
- Check audit log: `migration-poc/audit/step-definitions-compilation-<run_id>.log`
- Common issues:
  - Missing modernized code types (LLM hallucinated method names)
  - Mock class incomplete
  - Reqnroll namespace not imported

### Issue: LLM filled implementations are broken
- Check LLM prompt in `step_definitions_enhancer.py`
- Verify modernized code is being passed to LLM
- Try regenerating with different LLM model

### Issue: dotnet test hangs or times out
- Check tests directory has proper .csproj
- Verify Reqnroll/NUnit packages installed
- Check for deadlock in ScenarioContext usage

## Key Files to Inspect

| File | Purpose |
|------|---------|
| `migration-poc/agents/step_definitions_generator.py` | Skeleton generation from Gherkin |
| `migration-poc/agents/step_definitions_enhancer.py` | LLM enhancement logic |
| `migration-poc/agents/step_definitions_compiler.py` | Compilation via dotnet build |
| `migration-poc/agents/reqnroll_test_runner.py` | BDD test execution |
| `migration-poc/orchestrator_v3.py` | Main pipeline orchestration |
| `migration-poc/agents/verifier.py` | Test verification with Reqnroll integration |

## Test Assertions

**Pipeline should:**
- [ ] Generate valid Gherkin from modernized code
- [ ] Extract all Given/When/Then steps from Gherkin
- [ ] Create StepDefinitions.cs with correct Cucumber Expression syntax
- [ ] Compile skeleton without errors (dotnet build)
- [ ] LLM fill implementation methods (no more TODOs)
- [ ] Compilation of enhanced file succeeds
- [ ] Reqnroll test runner executes scenarios
- [ ] Coverage metrics collected
- [ ] All artifacts saved to correct directories

## Next Steps After Testing

If pipeline passes smoke tests:
1. ✅ Mark remaining 21 tasks (testing, docs, deployment) for future sessions
2. ✅ Archive this OpenSpec change
3. ✅ Start next phase: unit tests + integration tests

If pipeline has issues:
1. Check audit logs for specific failures
2. Review error messages in step_definitions_compiler output
3. Inspect generated StepDefinitions.cs for malformed Cucumber Expressions
4. Verify LLM is producing valid C# syntax
5. Check Reqnroll installation in test .csproj

## Performance Expectations

- Skeleton generation: <100ms
- LLM enhancement: 5-15 seconds (depends on step count)
- Compilation: 10-30 seconds
- Reqnroll test execution: 10-60 seconds (depends on scenario count)
- **Total pipeline**: 2-3 minutes for typical component

## Success Metrics

✅ **Core pipeline working**: All 8 stages complete without crashing
✅ **Reqnroll integration**: BDD scenarios execute and provide feedback
✅ **LLM enhancement**: Implementations are reasonable C# code
✅ **Compilation success**: No structural C# errors in generated code
✅ **Coverage collection**: Metrics reported in verification results
