## ADDED Requirements

### Requirement: Translate legacy .NET Framework code to .NET 10
The system SHALL translate legacy C# code targeting .NET Framework (4.8 or earlier) to modern .NET 10, employing current architectural patterns and language features.

#### Scenario: Modernizer produces .NET 10 compatible code
- **WHEN** Modernizer receives legacy .NET Framework code
- **THEN** output targets `<TargetFramework>net10.0</TargetFramework>` and uses async/await, IServiceProvider, modern C# syntax

#### Scenario: WCF service is translated to minimal API or gRPC
- **WHEN** legacy code uses WCF for communication
- **THEN** modernized code uses ASP.NET Core minimal APIs or gRPC patterns

#### Scenario: Manual object construction is replaced with dependency injection
- **WHEN** legacy code manually instantiates dependencies
- **THEN** modernized code uses constructor injection with IServiceProvider

### Requirement: Use C# 14 language features and modern patterns
The system SHALL leverage current C# 14 capabilities for clarity and conciseness (records, pattern matching, top-level statements where appropriate).

#### Scenario: Immutable data objects use records
- **WHEN** modernizing data transfer objects or domain entities
- **THEN** uses C# records instead of classes with hand-written equality

#### Scenario: Pattern matching replaces conditional logic
- **WHEN** code contains cascading if/else or switch statements
- **THEN** modernized code uses pattern matching for clarity

### Requirement: Implement async-first design
The system SHALL translate synchronous patterns to async/await, ensuring all I/O-bound operations are non-blocking.

#### Scenario: Blocking database calls are replaced with async
- **WHEN** legacy code calls `.Result` or synchronous database methods
- **THEN** modernized code uses async Task-based patterns, ConfigureAwait(false)

#### Scenario: Service methods are declared async
- **WHEN** service methods interact with external systems
- **THEN** modernized methods are `async Task<T>` with CancellationToken support

### Requirement: Reuse extracted domain logic
The system SHALL integrate previously extracted pure domain logic into the modernized service layer, composing it with framework concerns.

#### Scenario: Extracted validator is composed into service
- **WHEN** modernized service receives a request
- **THEN** it calls the extracted pure validator, then handles infrastructure concerns (logging, storage)
