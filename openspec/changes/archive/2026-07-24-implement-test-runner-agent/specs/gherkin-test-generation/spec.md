## MODIFIED Requirements

### Requirement: Output tests in service-appropriate directory structure
The system SHALL place generated Gherkin feature files and unit test files in a dedicated `tests` subfolder under the modernized output directory of each service.

#### Scenario: Output C# tests to tests subfolder
- **WHEN** test generation completes for a C# service
- **THEN** both the Gherkin feature file and the test file are written to `<ServiceRoot>/tests/`

#### Scenario: Output Java tests to tests subfolder
- **WHEN** test generation completes for a Java service
- **THEN** both the Gherkin feature file and the test file are written to `<ServiceRoot>/tests/`

#### Scenario: Output Python tests to tests subfolder
- **WHEN** test generation completes for a Python service
- **THEN** both the Gherkin feature file and the test file are written to `<ServiceRoot>/tests/`
