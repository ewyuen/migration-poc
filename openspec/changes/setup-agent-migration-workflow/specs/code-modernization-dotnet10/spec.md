## ADDED Requirements

### Requirement: Modernizer transforms legacy code to .NET 10

The modernizer agent SHALL update legacy .NET Framework or .NET Core code to target .NET 10 APIs and patterns.

#### Scenario: Update target framework in project file
- **WHEN** legacy component has <TargetFramework>net472</TargetFramework>
- **THEN** modernizer updates to <TargetFramework>net10</TargetFramework>

#### Scenario: Replace deprecated APIs with .NET 10 equivalents
- **WHEN** code uses System.Web.HttpContext (ASP.NET Framework)
- **THEN** modernizer replaces with Microsoft.AspNetCore.Http.HttpContext

#### Scenario: Update package references for .NET 10
- **WHEN** component references outdated NuGet packages
- **THEN** modernizer updates to latest versions compatible with .NET 10

### Requirement: Modernizer handles common migration patterns

The modernizer agent SHALL recognize and transform common patterns from legacy .NET to .NET 10.

#### Scenario: Convert config file references to configuration system
- **WHEN** code reads from app.config or web.config
- **THEN** modernizer replaces with IConfiguration dependency injection pattern

#### Scenario: Update reflection-based registration to service collection
- **WHEN** code uses manual type scanning and reflection for plugin loading
- **THEN** modernizer replaces with ServiceCollection and dependency injection container

#### Scenario: Convert LINQ to XML (XDocument) from XmlDocument
- **WHEN** code uses legacy XmlDocument API
- **THEN** modernizer suggests migration to XDocument or System.Xml.Xsd

### Requirement: Modernizer validates modernized code compiles

The modernizer agent SHALL verify that transformed code compiles without errors.

#### Scenario: Build validation succeeds
- **WHEN** modernized component compiles
- **THEN** modernizer reports "Build successful" and proceeds

#### Scenario: Build validation fails with clear error
- **WHEN** transformed code has compilation errors (e.g., missing API on .NET 10)
- **THEN** modernizer reports the specific error, line number, and suggests a fix or manual review

### Requirement: Modernizer produces modernized source code

The modernizer agent SHALL output the transformed component as compilable .NET 10 source code.

#### Scenario: Modernized code is written to legacy-code directory
- **WHEN** modernization completes successfully
- **THEN** modernizer writes transformed .csproj and all source files to legacy-code/{component}/

#### Scenario: Modernizer creates a summary of changes
- **WHEN** modernization completes
- **THEN** modernizer generates a report listing: APIs changed, dependencies updated, patterns refactored, breaking changes identified

### Requirement: Modernizer preserves business logic

The modernizer agent SHALL transform code syntax and APIs while preserving the original business logic.

#### Scenario: Logic preservation verified through reflection
- **WHEN** modernization completes
- **THEN** modernizer compares method signatures and logic flow with original to ensure no functionality is lost

#### Scenario: Comments and documentation are preserved
- **WHEN** source code contains comments and XML documentation
- **THEN** modernizer preserves or updates them to reflect API changes
