## 1. Day 1: Local Agent Setup (Today)

### 1.1 Environment & Dependencies
- [ ] 1.1.1 Create Python virtual environment (`python -m venv venv`)
- [ ] 1.1.2 Install dependencies (`pip install -r requirements.txt`)
- [ ] 1.1.3 Set up `.env` file with OpenRouter API key
- [ ] 1.1.4 Verify OpenRouter API key is valid (test API call if needed)

### 1.2 Core LLM Integration
- [ ] 1.2.1 Implement `llm_client.py` with OpenRouter API integration
- [ ] 1.2.2 Create `config.py` with model settings and paths
- [ ] 1.2.3 Test LLM client: run single API call to verify connectivity
- [ ] 1.2.4 Verify response parsing (JSON and text extraction)

### 1.3 Explorer Agent
- [ ] 1.3.1 Implement `agents/explorer.py` to analyze legacy code
- [ ] 1.3.2 Test Explorer on sample legacy code (e.g., `legacy-code/Observation.cs`)
- [ ] 1.3.3 Verify output: exploration report includes current_state, pain_points, compliance_concerns
- [ ] 1.3.4 Save exploration report to `output/1_exploration_report.json`

### 1.4 Extractor Agent
- [ ] 1.4.1 Implement `agents/extractor.py` to extract domain logic
- [ ] 1.4.2 Test Extractor with output from Explorer
- [ ] 1.4.3 Verify output: extracted logic is pure C# functions without side effects
- [ ] 1.4.4 Confirm extracted logic reuses business rules from exploration analysis
- [ ] 1.4.5 Save extracted logic to `output/2_extracted_domain_logic.cs`

### 1.5 Modernizer Agent
- [ ] 1.5.1 Implement `agents/modernizer.py` to translate code to .NET 10
- [ ] 1.5.2 Test Modernizer with extracted domain logic and legacy code
- [ ] 1.5.3 Verify output: code targets `net10.0`, uses async/await, includes DI
- [ ] 1.5.4 Confirm reuse of extracted domain logic in modernized service
- [ ] 1.5.5 Check for C# 14 patterns (records, pattern matching)
- [ ] 1.5.6 Save modernized code to `output/3_modernized_code.cs`

### 1.6 BDD Test Agent
- [ ] 1.6.1 Implement `agents/bdd_test_cases_generator.py` to generate Gherkin scenarios
- [ ] 1.6.2 Test BDD Agent with domain logic and modernized code
- [ ] 1.6.3 Verify output: Gherkin feature file with valid syntax
- [ ] 1.6.4 Confirm coverage: happy path, validation failures, edge cases, compliance scenarios
- [ ] 1.6.5 Verify medical domain language used in scenarios
- [ ] 1.6.6 Save BDD test scenarios to `output/4_bdd_test_scenarios.feature`

### 1.7 Verifier Agent
- [ ] 1.7.1 Implement `agents/verifier.py` to validate modernization
- [ ] 1.7.2 Test Verifier with all outputs from previous agents
- [ ] 1.7.3 Verify output: JSON report with behavioral_equivalence, test_coverage, compliance_check, security_check status
- [ ] 1.7.4 Confirm report includes overall_status (PASS/FAIL/CAUTION), risks, recommendations
- [ ] 1.7.5 Check .NET 10 alignment verification is present
- [ ] 1.7.6 Save verification report to `output/5_verification_report.json`

### 1.8 Orchestrator Integration
- [ ] 1.8.1 Implement `orchestrator.py` to coordinate all agents sequentially
- [ ] 1.8.2 Create output directory structure
- [ ] 1.8.3 Run full orchestration: `python orchestrator.py`
- [ ] 1.8.4 Verify all 6 output files are created and contain expected content
- [ ] 1.8.5 Verify runtime is acceptable (<5 minutes total)
- [ ] 1.8.6 Save combined results to `output/0_complete_results.json`

### 1.9 Documentation & Review
- [ ] 1.9.1 Review each output file and note quality/completeness
- [ ] 1.9.2 Document any agent failures or suboptimal outputs
- [ ] 1.9.3 Create DAY1_GUIDE.md with setup and execution instructions
- [ ] 1.9.4 Create README.md explaining the POC, architecture, and interview use
- [ ] 1.9.5 Screenshot or document pipeline execution (for interview demo)
- [ ] 1.9.6 Commit all code and outputs to git: `git add -A && git commit -m "POC: Multi-agent extraction pipeline working locally"`

---

## 2. Day 2: GitHub Actions & Approval Gate (Tomorrow)

### 2.1 GitHub Actions Workflow Setup
- [ ] 2.1.1 Create `.github/workflows/multi-agent-extraction.yml`
- [ ] 2.1.2 Define trigger: `workflow_dispatch` (manual trigger)
- [ ] 2.1.3 Add orchestrator job: checkout → setup Python → run `python orchestrator.py`
- [ ] 2.1.4 Upload artifacts: exploration report, domain logic, modernized code, BDD tests, verification report
- [ ] 2.1.5 Test workflow: manually trigger and verify artifacts are produced
- [ ] 2.1.6 Commit workflow file to git

### 2.2 Manual Approval Gate (Pull Request)
- [ ] 2.2.1 Create GitHub Action job to open a Pull Request with agent outputs
- [ ] 2.2.2 Add PR comment with summary of outputs and verification status
- [ ] 2.2.3 Configure branch protection rule: require manual approval before merge
- [ ] 2.2.4 Test approval flow: trigger workflow → review PR → approve → merge
- [ ] 2.2.5 Verify merge only happens after approval (HITL gate functioning)

### 2.3 CFR Part 11 Audit Trail
- [ ] 2.3.1 Create audit trail JSON structure with: timestamp, action, initiator, approver, status
- [ ] 2.3.2 Add step to workflow that generates audit log entry
- [ ] 2.3.3 Store audit trail in `output/audit_trail.json`
- [ ] 2.3.4 Ensure audit log persists across workflow runs
- [ ] 2.3.5 Document audit trail schema in README

### 2.4 End-to-End Testing
- [ ] 2.4.1 Manually trigger workflow from GitHub UI
- [ ] 2.4.2 Verify orchestrator runs successfully in GitHub Actions
- [ ] 2.4.3 Review uploaded artifacts (no truncation or corruption)
- [ ] 2.4.4 Create pull request with artifacts
- [ ] 2.4.5 Perform manual approval/review
- [ ] 2.4.6 Verify merge succeeds only after approval
- [ ] 2.4.7 Confirm audit trail is recorded

### 2.5 Interview Preparation
- [ ] 2.5.1 Document the 2-day workflow narrative (for telling Babita the story)
- [ ] 2.5.2 Create a "Demo Script" showing how to run locally and via workflow
- [ ] 2.5.3 Prepare screenshots/screen recording of the pipeline in action
- [ ] 2.5.4 Draft 2-minute explanation of the POC, how it scales, how compliance is maintained
- [ ] 2.5.5 Practice demo on laptop (ensure it's reproducible and fast)
- [ ] 2.5.6 Prepare 5-minute deep dive talking points for each agent's role
- [ ] 2.5.7 Prepare response to "How would you scale this?" (Coordinator agent, parallel workers, etc.)

### 2.6 Documentation & Polish
- [ ] 2.6.1 Update README with GitHub Actions workflow instructions
- [ ] 2.6.2 Document how to run locally vs. via GitHub workflow
- [ ] 2.6.3 Document CFR Part 11 compliance story (audit trail, verification gates, human approval)
- [ ] 2.6.4 Add troubleshooting guide (common errors, solutions)
- [ ] 2.6.5 Add "Roadmap" section: future enhancements (parallel execution, Lean proofs, etc.)
- [ ] 2.6.6 Commit workflow and documentation: `git add -A && git commit -m "POC: GitHub Actions workflow with approval gates and audit trail"`

---

## 3. Validation & Acceptance Criteria

### Success Criteria for Day 1
- ✅ All 6 agent implementations are complete and tested
- ✅ `python orchestrator.py` runs to completion without errors
- ✅ 6 output files are produced with expected content
- ✅ Execution time is <5 minutes
- ✅ Code is readable, well-documented, and committed to git
- ✅ README and DAY1_GUIDE explain the setup and execution

### Success Criteria for Day 2
- ✅ GitHub Actions workflow successfully runs the orchestrator
- ✅ Artifacts are uploaded and available in GitHub
- ✅ Pull Request is created with agent outputs
- ✅ Manual approval gate works (can approve/reject PR)
- ✅ Audit trail is recorded in JSON format
- ✅ End-to-end workflow: trigger → execute → approve → merge functions correctly
- ✅ Interview demo can be run live on laptop (reproducible, <10 minute end-to-end execution)

### Definition of Done
- All tasks in sections 1-2 are checked off
- Code passes basic smoke tests (no runtime errors, outputs are well-formed)
- Git history shows clear progression (separate commits for agents, workflow, documentation)
- README and inline documentation are sufficient for someone to understand and run the POC
- POC successfully demonstrates multi-agent orchestration, compliance-first architecture, and human-in-the-loop verification to interview panel
