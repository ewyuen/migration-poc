## ADDED Requirements

### Requirement: Explorer scans legacy-src folder for components

The explorer agent SHALL analyze the legacy-src directory structure to identify .NET components (projects, assemblies, namespaces).

#### Scenario: Explorer identifies a single component
- **WHEN** legacy-src contains a project folder "LegacyAuthService" with .csproj file
- **THEN** explorer recognizes it as a component and includes it in the component inventory

#### Scenario: Explorer identifies related components via dependency analysis
- **WHEN** user requests "LegacyAuthService" with filter "dependency:all"
- **THEN** explorer scans legacy-src and identifies all components that depend on or are depended upon by LegacyAuthService

### Requirement: Explorer validates component existence and readiness

The explorer agent SHALL verify that identified components are valid, accessible, and ready for migration.

#### Scenario: Component validation succeeds
- **WHEN** explorer identifies component "LegacyAuthService"
- **THEN** it verifies: directory exists, contains .csproj or .sln, has readable source files

#### Scenario: Component contains incompatible dependencies
- **WHEN** component references .NET Framework-only libraries (e.g., Enterprise Services)
- **THEN** explorer flags the component with warning "Contains .NET Framework-only dependencies" in the inventory

### Requirement: Explorer generates component inventory

The explorer agent SHALL produce a structured inventory of identified components with metadata.

#### Scenario: Inventory includes component metadata
- **WHEN** explorer completes discovery
- **THEN** inventory file contains: component name, file path, dependencies, estimated LOC, last modified date

#### Scenario: Inventory is machine-readable and human-readable
- **WHEN** inventory is generated
- **THEN** it is formatted as JSON (machine-readable) and includes a human-readable summary section

### Requirement: Explorer applies user-specified filters

The explorer agent SHALL honor optional filters to narrow or expand component discovery scope.

#### Scenario: Filter by domain
- **WHEN** user specifies filter "domain:Authentication"
- **THEN** explorer returns only components tagged with or documented as part of Authentication domain

#### Scenario: Filter by component size
- **WHEN** user specifies filter "size:small" (< 5 KLOC)
- **THEN** explorer returns components with estimated size less than 5,000 lines of code

#### Scenario: Multiple filters combine with AND logic
- **WHEN** user specifies filters "domain:Authentication" AND "size:small"
- **THEN** explorer returns components matching BOTH criteria
