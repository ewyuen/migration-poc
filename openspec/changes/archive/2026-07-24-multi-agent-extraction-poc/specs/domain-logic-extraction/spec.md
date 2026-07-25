## ADDED Requirements

### Requirement: Extract pure domain logic from legacy code
The system SHALL extract core business logic and algorithms as pure C# functions, free from side effects (I/O, state mutations, framework dependencies). Extracted logic SHALL express business rules clearly and be independently testable.

#### Scenario: Validation rules are extracted as pure functions
- **WHEN** Extractor analyzes a component containing tangled validation logic
- **THEN** it produces pure functions like `ValidateObservationData(patient, obs) -> ValidationResult` with no I/O side effects

#### Scenario: Extracted functions are independently testable
- **WHEN** domain logic is extracted
- **THEN** each function can be unit-tested with simple input/output pairs (test vectors)

#### Scenario: Invariants are documented
- **WHEN** extracting domain logic
- **THEN** XML documentation includes invariants (e.g., "Result depends only on inputs, not system state")

### Requirement: Separate domain logic from infrastructure concerns
The system SHALL cleanly separate business rules from infrastructure dependencies (database, I/O, external services).

#### Scenario: Domain logic does not depend on repository
- **WHEN** extracting observation validation
- **THEN** the pure function doesn't reference IRepository, database calls, or persistence layer

#### Scenario: Infrastructure dependencies are identified but excluded
- **WHEN** legacy code contains mixed concerns
- **THEN** extracted logic includes a note about infrastructure to be handled separately (e.g., "Audit trail recording handled by service layer")

### Requirement: Support algorithmic and business rule extraction
The system SHALL extract both imperative algorithms (transformations, calculations) and declarative rules (constraints, validations).

#### Scenario: Medical algorithm extraction
- **WHEN** extracting blood pressure validation algorithm
- **THEN** produces testable function expressing the business rule (e.g., "BloodPressure must be between 80-120")

#### Scenario: Complex business rules are expressed clearly
- **WHEN** rules have dependencies or conditions
- **THEN** rules are structured for clarity (guard clauses, early returns, nested logic organized by precedence)
