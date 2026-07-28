## Purpose

Define how an LLM fills the `// TODO` placeholders in a skeleton `StepDefinitions.cs` file into working C# implementations, using modernized code, domain logic, and scenario context, while preserving the skeleton's Reqnroll attributes and method signatures.

## Requirements

### Requirement: LLM fills skeleton implementations
The system SHALL use an LLM to fill TODO placeholders in the skeleton `StepDefinitions.cs` with actual C# implementations based on modernized code, domain logic, and scenario context.

#### Scenario: Basic step implementation
- **WHEN** skeleton has `[Given("user {string} exists")] public void GivenUserExists(string username) { // TODO }`
- **AND** modernized code provides `UserService.CreateUser(string name)`
- **THEN** LLM generates implementation like `var user = _userService.CreateUser(username);`

#### Scenario: State sharing via ScenarioContext
- **WHEN** step implementations need to share state between steps in a scenario
- **THEN** LLM stores intermediate results in `_context["key"]` with semantic key names
- **AND** subsequent steps retrieve values with `_context["key"]`

#### Scenario: Parameter mapping inference
- **WHEN** Gherkin step text is "user 'john' with age 25 exists"
- **THEN** LLM infers that 'john' maps to `{string}` username parameter and 25 maps to `{int}` age parameter

### Requirement: LLM has full context for inference
The system SHALL provide the LLM with modernized code, domain logic, previous steps in the scenario, and Gherkin intent to make informed implementation decisions.

#### Scenario: LLM sees modernized code methods
- **WHEN** LLM is generating step implementation
- **THEN** LLM prompt includes full modernized service code with all available methods and signatures
- **AND** LLM implementations call only methods present in the provided code

#### Scenario: LLM infers mock generation
- **WHEN** a step references a service (e.g., `UserService`) not found in modernized code
- **THEN** LLM generates a mock class definition in the same `StepDefinitions.cs` file
- **AND** mock includes methods inferred from how the step uses the service

#### Scenario: Scenario context chain awareness
- **WHEN** a step depends on prior steps in the same scenario
- **THEN** LLM prompt includes prior steps and what they store in `_context`
- **AND** current step retrieves values stored by prior steps

### Requirement: Preserve skeleton structure
The system SHALL ensure that skeleton Reqnroll attributes and method signatures remain unchanged; only method bodies are filled.

#### Scenario: Attributes untouched
- **WHEN** skeleton has `[Given(@"user ""{string}"" exists")]`
- **THEN** enhanced version preserves that exact attribute
- **AND** method body changed, but signature (parameters, return type) unchanged

### Requirement: Generate valid C# implementations
The system SHALL ensure all enhanced method bodies are syntactically valid C# code.

#### Scenario: Enhanced code is compilable
- **WHEN** LLM enhances a step definition
- **THEN** the resulting C# method body has valid syntax
- **AND** uses only types and methods available in scope (no undefined references)

### Requirement: Infer service initialization
The system SHALL infer whether services need mock generation and what methods should be included in mocks based on step implementation requirements.

#### Scenario: Mock with inferred methods
- **WHEN** a step calls a method on a mocked service
- **THEN** LLM generates the mock class with that method
- **AND** mock method returns appropriate test data (User object, bool success, etc.)

#### Scenario: Service from modernized code
- **WHEN** a service exists in modernized code
- **THEN** LLM instantiates it directly: `_userService = new UserService();`
- **AND** no mock generated

### Requirement: Infer ScenarioContext key names semantically
The system SHALL generate meaningful, semantic key names for ScenarioContext based on step intent and domain logic.

#### Scenario: Semantic key naming
- **WHEN** a step creates a user and stores it for later steps
- **THEN** LLM chooses key name `_context["CurrentUser"]` or `_context["User"]` (semantic, not `_context["var1"]`)
