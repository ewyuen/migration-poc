## ADDED Requirements

### Requirement: Extractor analyzes modernized code to identify domain logic

The extractor agent SHALL parse and analyze .NET 10 code to identify business logic, algorithms, and domain concepts.

#### Scenario: Extractor identifies business domain classes
- **WHEN** modernized code contains classes like "AuthenticationService", "PaymentProcessor"
- **THEN** extractor recognizes them as core domain logic and documents their responsibilities

#### Scenario: Extractor identifies algorithms and business rules
- **WHEN** code contains complex logic (e.g., discount calculation, pricing rules)
- **THEN** extractor isolates the algorithm, its inputs, and expected outputs

#### Scenario: Extractor identifies infrastructure vs. domain code
- **WHEN** code mixes database access, logging, and business logic
- **THEN** extractor separates concerns and classifies each: infrastructure (logging, DB), application (orchestration), domain (business rules)

### Requirement: Extractor produces structured business logic specifications

The extractor agent SHALL output domain logic in a structured, human-readable format.

#### Scenario: Output includes domain entities and their relationships
- **WHEN** extraction completes
- **THEN** specification documents: entity names, properties, relationships (1:1, 1:N), key constraints

#### Scenario: Output includes business rules in natural language
- **WHEN** code contains pricing or validation logic
- **THEN** specification translates it to readable rules (e.g., "Discount applies if customer age >= 65 AND total > $100")

#### Scenario: Output includes algorithms with inputs/outputs
- **WHEN** code contains algorithms
- **THEN** specification documents: algorithm name, inputs (types, constraints), outputs, complexity notes

### Requirement: Extractor maps dependencies between extracted concepts

The extractor agent SHALL document how extracted domain concepts depend on each other.

#### Scenario: Specification shows call hierarchy
- **WHEN** AuthenticationService calls PasswordValidator
- **THEN** extraction output documents this dependency: "AuthenticationService depends on PasswordValidator"

#### Scenario: Specification identifies external dependencies
- **WHEN** code depends on external libraries or services
- **THEN** extraction notes these as "External Dependency: {name}" for consideration during testing

### Requirement: Extractor generates artifacts for downstream use

The extractor agent SHALL produce specifications that serve as input for BDD generation.

#### Scenario: Extracted logic includes testable scenarios
- **WHEN** code contains conditional logic or state transitions
- **THEN** extraction notes potential test scenarios (e.g., "Success case: valid credentials", "Failure case: expired password")

#### Scenario: Specification is machine and human readable
- **WHEN** extraction completes
- **THEN** output is formatted as structured YAML/JSON with headers, lists, and narrative sections

### Requirement: Extractor validates extraction completeness

The extractor agent SHALL verify that all significant logic has been identified and documented.

#### Scenario: Coverage validation confirms logic identification
- **WHEN** extraction completes
- **THEN** extractor reports: "X classes analyzed, Y domain entities identified, Z algorithms extracted" with >90% coverage target

#### Scenario: Extractor flags unmapped code
- **WHEN** code exists that cannot be classified as domain logic (e.g., boilerplate)
- **THEN** extraction notes it separately as "Utility/Infrastructure Code: {description}"
