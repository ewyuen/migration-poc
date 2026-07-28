## ADDED Requirements

### Requirement: Extract Gherkin steps and generate skeleton
The system SHALL parse Gherkin `.feature` files, extract all steps (Given/When/Then) from all scenarios, and generate a skeleton `StepDefinitions.cs` file with `[Binding]` class and method stubs for each step.

#### Scenario: Single feature file with multiple scenarios
- **WHEN** input is a Gherkin feature with 3 scenarios each having 5 steps
- **THEN** output is one `StepDefinitions.cs` with 15 `[Given]`/`[When]`/`[Then]` method stubs (accumulated, not deduplicated)

#### Scenario: Method stubs use Cucumber Expression syntax
- **WHEN** a step contains text like "user 'john' with age 25 exists"
- **THEN** the generated `[Given]` attribute uses Cucumber Expressions: `[Given("user {string} with age {int} exists")]`
- **AND** the C# method signature includes typed parameters (e.g., `(string username, int age)`)

#### Scenario: TODO placeholders in method bodies
- **WHEN** a skeleton method is generated
- **THEN** the body contains `// TODO: Implement [step text]` placeholder comment

#### Scenario: Constructor receives ScenarioContext
- **WHEN** the `[Binding]` class is generated
- **THEN** constructor accepts `ScenarioContext context` parameter and stores it as field

### Requirement: Use standard Reqnroll attribute syntax
The system SHALL generate step definition attributes using Reqnroll's standard `[Given]`, `[When]`, `[Then]` attributes with parameter type patterns.

#### Scenario: Correct attribute format
- **WHEN** a step is "the user is authenticated"
- **THEN** the generated attribute is `[Then("the user is authenticated")]` (no type patterns if no parameters)

#### Scenario: Cucumber Expressions handle mixed parameter types
- **WHEN** a step contains mixed parameters like "user 'alice' logged in for 5 days"
- **THEN** the Cucumber Expression is `[Given("user {string} logged in for {int} days")]`
- **AND** method signature is `public void GivenUserLoggedInForDays(string username, int days)`

### Requirement: Generate valid C# structure
The system SHALL ensure generated `StepDefinitions.cs` is syntactically valid C# code that can be compiled without errors.

#### Scenario: File compiles without syntax errors
- **WHEN** skeleton is generated
- **THEN** compiling via `dotnet build` in the tests directory succeeds (with unimplemented TODO methods)
- **AND** references to Reqnroll types (`ScenarioContext`, `[Given]`, etc.) resolve correctly

#### Scenario: File includes proper namespaces and using statements
- **WHEN** skeleton is generated for component "UserService"
- **THEN** file includes appropriate `using` statements (e.g., `using Reqnroll;`)
- **AND** class is namespaced (e.g., `namespace MyService.Migration.Tests`)

### Requirement: Single StepDefinitions.cs file for all steps
The system SHALL generate one `StepDefinitions.cs` file per component/run, accumulating all extracted steps from the single Gherkin blob in one `[Binding]` class.

#### Scenario: All scenarios accumulate in one file
- **WHEN** input Gherkin contains multiple scenarios
- **THEN** output is one `StepDefinitions.cs` with all steps from all scenarios in one `[Binding]` class
- **AND** no per-scenario or per-feature file splitting

#### Scenario: Output file location
- **WHEN** skeleton is generated for component "UserService"
- **THEN** output is written to `migrated-output/{run_id}/tests/StepDefinitions.cs`
- **AND** file is co-located with compiled test assemblies and feature files
