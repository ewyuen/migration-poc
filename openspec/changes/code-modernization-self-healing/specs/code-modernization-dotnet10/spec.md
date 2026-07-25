## ADDED Requirements

### Requirement: Verify modernized code compiles
The system SHALL verify that generated modernized code compiles without syntax or type errors before proceeding to test generation. The modernizer SHALL accept compilation feedback in a loop and refine code to fix errors, with a maximum of 3 attempts. If code does not compile after 3 attempts, modernization SHALL fail and exit orchestration.

#### Scenario: Modernizer receives compilation errors and refines code
- **WHEN** generated code fails to compile with syntax or type errors
- **THEN** the modernizer receives structured error feedback (line number, error code, message, type information)
- **AND** regenerates/refines the code to address those specific errors

#### Scenario: Modernizer is loop-aware in prompt context
- **WHEN** modernizer is called on attempt 2 or 3
- **THEN** the prompt context includes current attempt number and max attempts (3)
- **AND** modernizer can adjust refinement strategy based on attempt progress

#### Scenario: Orchestration exits on persistent compilation failures
- **WHEN** modernized code fails to compile on all 3 attempts
- **THEN** modernization loop exits without proceeding to test generation
- **AND** orchestration reports failure to the verifier with all compilation errors

## MODIFIED Requirements

### Requirement: Translate legacy .NET Framework code to .NET 10
The system SHALL translate legacy C# code targeting .NET Framework (4.8 or earlier) to modern .NET 10, employing current architectural patterns and language features. The generated code MUST compile when verified in isolation.

#### Scenario: Modernizer produces .NET 10 compatible code
- **WHEN** Modernizer receives legacy .NET Framework code
- **THEN** output targets `<TargetFramework>net10.0</TargetFramework>` and uses async/await, IServiceProvider, modern C# syntax
- **AND** generated code compiles successfully when verified

#### Scenario: WCF service is translated to minimal API or gRPC
- **WHEN** legacy code uses WCF for communication
- **THEN** modernized code uses ASP.NET Core minimal APIs or gRPC patterns
- **AND** generated code compiles successfully when verified

#### Scenario: Manual object construction is replaced with dependency injection
- **WHEN** legacy code manually instantiates dependencies
- **THEN** modernized code uses constructor injection with IServiceProvider
- **AND** generated code compiles successfully when verified

### Requirement: Use C# 14 language features and modern patterns
The system SHALL leverage current C# 14 capabilities for clarity and conciseness (records, pattern matching, top-level statements where appropriate). All generated code MUST compile successfully.

#### Scenario: Immutable data objects use records
- **WHEN** modernizing data transfer objects or domain entities
- **THEN** uses C# records instead of classes with hand-written equality
- **AND** generated code compiles successfully when verified

#### Scenario: Pattern matching replaces conditional logic
- **WHEN** code contains cascading if/else or switch statements
- **THEN** modernized code uses pattern matching for clarity
- **AND** generated code compiles successfully when verified

### Requirement: Implement async-first design
The system SHALL translate synchronous patterns to async/await, ensuring all I/O-bound operations are non-blocking. All generated async code MUST compile successfully.

#### Scenario: Blocking database calls are replaced with async
- **WHEN** legacy code calls `.Result` or synchronous database methods
- **THEN** modernized code uses async Task-based patterns, ConfigureAwait(false)
- **AND** generated code compiles successfully when verified

#### Scenario: Service methods are declared async
- **WHEN** service methods interact with external systems
- **THEN** modernized methods are `async Task<T>` with CancellationToken support
- **AND** generated code compiles successfully when verified

### Requirement: Reuse extracted domain logic
The system SHALL integrate previously extracted pure domain logic into the modernized service layer, composing it with framework concerns. Composition MUST result in compilable code.

#### Scenario: Extracted validator is composed into service
- **WHEN** modernized service receives a request
- **THEN** it calls the extracted pure validator, then handles infrastructure concerns (logging, storage)
- **AND** generated code compiles successfully when verified
