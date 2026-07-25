## Context

The BDD test agent generates Gherkin feature files (`.feature` files) that describe the behavior of migrated services. These specification files contain scenarios but are not executable tests. SpecKit is a framework that reads Gherkin files and generates language-specific test code (C#, Java, Python, etc.) with proper framework integration (NUnit, JUnit, pytest).

The orchestrator needs a test code generation stage that uses SpecKit to convert Gherkin scenarios into runnable tests in each service's target language.

## Goals / Non-Goals

**Goals:**
- Integrate SpecKit into the orchestrator to automate test generation from Gherkin files
- Generate language-specific test code (C#, Java, Python) matching each service's target platform
- Place generated tests in the appropriate test directory structure for each service
- Ensure generated tests reference the correct service implementations
- Enable validation that migrated services behave as specified in Gherkin scenarios

**Non-Goals:**
- Test execution infrastructure (CI/CD integration deferred)
- Test reporting or metrics collection
- Automatic test assertion generation beyond Gherkin step mapping
- Support for all Gherkin features (focus on core Given/When/Then)
- Backfill tests for non-migrated services

## Decisions

**1. Use SpecKit directly for test code generation**
- Decision: Use SpecKit library to generate test code from Gherkin files, not an LLM agent
- Rationale: SpecKit is deterministic, language-aware, and ensures consistent, valid test syntax; avoids unpredictability of LLM-generated test code; Gherkin scenarios already exist from BDD test agent
- Alternative: Use an LLM agent to generate tests (non-deterministic, requires validation, may generate invalid code)

**2. SpecKit Integration Point**
- Decision: Add test generation as a pipeline stage in the orchestrator after code modernization completes
- Rationale: Tests should reflect the final migrated code; generate after modernization ensures accuracy
- Alternative: Generate tests during migration phase (coupling risk, harder to iterate)

**3. Test Structure and Output**
- Decision: Generate tests in service-specific test directories following language conventions (e.g., `Tests/`, `test/`, `__tests__/`)
- Rationale: Maintains consistency with existing project structure, enables standard IDE test discovery
- Alternative: Central test directory (harder to navigate, violates co-location principle)

**3. Language Support**
- Decision: Start with C# and Java using NUnit and JUnit respectively; Python uses pytest
- Rationale: Aligns with observed migrated service distribution; can extend incrementally
- Alternative: Support all languages upfront (higher implementation effort, uncertain ROI)

**4. Gherkin-to-Code Mapping**
- Decision: Use SpecKit's built-in step definitions with service-specific glue code generation
- Rationale: Reduces boilerplate, SpecKit handles common patterns; glue code bridges to service APIs
- Alternative: Full custom DSL (higher complexity, limited reuse)

**5. Configuration**
- Decision: Store mapping of Gherkin files to test generation parameters in orchestrator configuration
- Rationale: Centralizes test generation logic, enables per-service customization without code changes
- Alternative: Infer from file structure (fragile, lacks flexibility)

## Risks / Trade-offs

**Risk: Gherkin Quality Variance**
- Mitigation: Establish Gherkin writing guidelines; validate syntax before test generation; fail gracefully on malformed files

**Risk: SpecKit Dependency Coupling**
- Mitigation: Abstract SpecKit behind a service interface; allows future replacement or extension

**Risk: Language-Specific Test Framework Differences**
- Mitigation: Create language-specific code generators; test each generator independently; document framework assumptions

**Risk: Maintenance Burden**
- Mitigation: Keep glue code minimal; prioritize template-based generation; invest in tooling for debugging generated code

**Trade-off: Flexibility vs. Convention**
- Accepting convention-over-configuration for common cases; explicit configuration for edge cases

## Migration Plan

1. **Phase 1**: Implement C# test generator using SpecKit, test with sample Gherkin files
2. **Phase 2**: Add Java and Python generators; integrate into orchestrator pipeline
3. **Phase 3**: Run full migration, validate generated tests on sample services
4. **Rollback**: Disable test generation stage in orchestrator configuration; existing Gherkin files remain unchanged
