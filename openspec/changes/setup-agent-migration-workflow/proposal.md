## Why

This POC demonstrates how an orchestrated multi-agent system can automate the migration of legacy .NET components to .NET 10. Currently, component modernization requires manual coordination across multiple analysis and refactoring steps. By defining a clear agent-driven workflow in config.yaml, we establish a repeatable, auditable process where each agent handles a specific responsibility in the pipeline.

## What Changes

- Define agent roles and responsibilities in config.yaml for the migration workflow
- Establish the orchestrator as the central coordinator that directs explorer, modernizer, extractor, BDD generator, test writer, and verifier agents
- Create a user-facing input mechanism allowing users to specify which legacy components to explore and migrate
- Implement the component identification pipeline: user input → explorer agent → legacy-code folder staging
- Implement the modernization pipeline: legacy component → modernizer agent → .NET 10 code
- Implement the decomposition pipeline: modernized code → extractor agent → business logic/algorithms
- Implement the BDD pipeline: decomposed code → BDD generator → gherkin specifications
- Implement the test writing pipeline: gherkin specifications → test writer agent → executable test code
- Implement the verification pipeline: test code → verifier agent → test execution and validation

## Capabilities

### New Capabilities

- `agent-orchestration`: Orchestrator agent that coordinates the workflow and directs all other agents based on user requests
- `legacy-component-discovery`: Explorer agent that analyzes legacy-src folder and identifies components or related component sets for migration
- `legacy-component-staging`: Process for moving identified components to legacy-code folder and creating migration branches
- `code-modernization-dotnet10`: Modernizer agent that updates legacy code to .NET 10 standards and APIs
- `domain-logic-extraction`: Extractor agent that decomposes modernized code into business logic and algorithms
- `bdd-specification-generation`: BDD generator agent that creates Gherkin specifications from decomposed business logic
- `gherkin-test-implementation`: Test writer agent that converts Gherkin specifications into executable test code
- `test-verification-execution`: Verifier agent that executes test suites and reports results

### Modified Capabilities

<!-- No existing capabilities are having requirement changes in this POC phase -->

## Impact

- **config.yaml structure**: Defines agent roles, their tools, and orchestration directives
- **Component organization**: Introduces legacy-src (source), legacy-code (staging), and migration branch workflow
- **Agent system architecture**: Establishes orchestrator-delegate pattern where the orchestrator controls workflow progression
- **User interaction**: Requires a user-facing interface for specifying which components to explore
- **Output artifacts**: Generates modernized .NET 10 code, extracted business logic specs, Gherkin files, and executable tests
