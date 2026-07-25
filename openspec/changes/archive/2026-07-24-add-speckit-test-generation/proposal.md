## Why

The BDD test agent generates Gherkin feature files describing migrated service behavior, but these are specifications only—not executable tests. SpecKit provides an automated mechanism to convert Gherkin scenarios directly into runnable test code. This enables consistent, language-specific test generation and reduces manual test implementation effort.

## What Changes

- Add SpecKit integration to the migration orchestrator to read Gherkin feature files
- Create test code generator pipeline that uses SpecKit to produce executable test implementations
- Generate language-specific test code (C#, Java, Python) from Gherkin scenarios for each migrated service
- Establish step-to-code mapping to translate Gherkin Given/When/Then into service-specific API calls
- Integrate test code generation as a pipeline stage after code modernization

## Capabilities

### New Capabilities
- `gherkin-test-generation`: Automated generation of executable tests from Gherkin feature files using SpecKit

### Modified Capabilities

## Impact

- **Code**: Test files generated in each migrated service's test directory
- **Pipeline**: New stage in migration orchestrator for test generation
- **Dependencies**: SpecKit library and language-specific test framework integrations
- **Artifacts**: Generated test code in the orchestrator output structure
