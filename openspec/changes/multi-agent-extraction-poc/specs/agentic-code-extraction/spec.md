## ADDED Requirements

### Requirement: Analyze legacy code for refactoring opportunities
The system SHALL analyze a legacy C# component to identify current architecture, design patterns, pain points, and refactoring opportunities. The analysis SHALL produce a structured report identifying responsibilities, compliance concerns, and a breakdown of work items for specialized agents.

#### Scenario: Explorer analyzes WCF service component
- **WHEN** Explorer Agent receives a legacy WCF service class (e.g., Observation.cs)
- **THEN** it produces a JSON report containing: current_state, patterns_used, pain_points, compliance_concerns, responsibilities, refactoring_opportunities, and subtasks

#### Scenario: Identified pain points include infrastructure tangling
- **WHEN** Explorer analyzes code mixing business logic with I/O and framework concerns
- **THEN** it flags "Validation logic mixed with transformation", "No clear domain model", "Infrastructure dependencies obscure business logic"

#### Scenario: Compliance concerns are identified
- **WHEN** Explorer analyzes medical data handling code
- **THEN** it identifies CFR Part 11 related concerns: "Audit trail implicit, not enforced", "Access control missing", "Data versioning undefined"

### Requirement: Decompose work into subtasks for downstream agents
The system SHALL break down the identified refactoring into discrete subtasks suitable for delegation to specialized extraction, modernization, and verification agents.

#### Scenario: Refactoring plan includes multiple subtasks
- **WHEN** Explorer generates a refactoring plan
- **THEN** it includes subtasks for: Extract validation rules, Create domain entity, Write BDD scenarios, Modernize to .NET 10

### Requirement: Plan is human-readable and actionable
The system SHALL produce analysis that is comprehensible to human architects and suitable for discussion in code review or architecture sessions.

#### Scenario: Report uses domain language
- **WHEN** exploring medical software
- **THEN** uses terms like "observation", "patient", "validation", not generic "function", "parameter"
