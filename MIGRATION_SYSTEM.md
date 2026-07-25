# Component Migration System - Complete Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Configuration Guide](#configuration-guide)
5. [Agent Responsibilities](#agent-responsibilities)
6. [Workflow Stages](#workflow-stages)
7. [Generated Artifacts](#generated-artifacts)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## System Overview

The **Component Migration System** is an AI-powered, multi-agent orchestration platform designed to automate the migration of legacy .NET components to .NET 10. It provides:

- **Config-driven agent management** - Define all agents and their responsibilities in migration_config.yaml
- **Sequential workflow pipeline** - 7-stage orchestrated process from discovery to verification
- **Automated code transformation** - Modernize legacy code with dependency injection and async patterns
- **BDD test generation** - Create Gherkin specs and convert them to executable xUnit tests
- **Git branch management** - Isolated feature branches for each migration
- **Comprehensive audit trail** - Full logging of all workflow steps

### Key Features

✅ **Orchestrator-Delegate Pattern** - Single entry point with specialized agent delegation
✅ **Component Discovery** - Find and analyze legacy components in legacy-src
✅ **Automated Staging** - Copy components with checksum validation and branch creation
✅ **Code Modernization** - Transform to .NET 10 APIs, patterns, and frameworks
✅ **Domain Logic Extraction** - Identify business rules and algorithms
✅ **BDD Test Generation** - Create Gherkin specifications from domain logic
✅ **Test Code Generation** - Convert Gherkin to C# xUnit tests (NEW)
✅ **Verification & Validation** - Comprehensive migration success validation

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR V2                         │
│         (Config-driven, sequential workflow engine)         │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴─────────────────────────────────┬──────────────┐
    │                                          │              │
    ▼                                          ▼              ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  ┌─────────┐
│   EXPLORER  │  │  STAGING     │  │   MODERNIZER     │  │EXTRACTOR│
│  Discovery  │  │  Branch & Copy   Async/DI Pattern  Domain Logic
└─────────────┘  └──────────────┘  └──────────────────┘  └─────────┘
    │
    ▼
┌────────────────┐     ┌──────────────┐     ┌───────────┐
│  BDD GENERATOR │────▶│  TEST WRITER │────▶│ VERIFIER  │
│   Gherkin      │     │  xUnit Tests │     │Validation │
└────────────────┘     └──────────────┘     └───────────┘
```

### Directory Structure

```
migration_poc/
├── migration_config.yaml                 # Agent definitions & workflow config
├── MIGRATION_SYSTEM.md        # This documentation
├── legacy-src/                # Original legacy components
│   ├── TestService/           # Example test component
│   │   ├── AuthenticationService.cs
│   │   └── TestService.csproj
│   └── [other components]
├── legacy-code/               # Staged components during migration
│   └── TestService/           # Migration artifacts for TestService
│       ├── .staging_metadata.json
│       ├── extracted_logic.md
│       ├── modernized_code.cs
│       ├── scenarios.feature
│       ├── TestService.Tests.cs
│       └── verification_report.json
├── migration-poc/             # Python orchestration system
│   ├── orchestrator_v2.py    # Main orchestrator (config-driven)
│   ├── input_handler.py      # User input & validation
│   ├── agents/
│   │   ├── explorer.py
│   │   ├── staging_agent.py  # NEW: Branch & copy management
│   │   ├── modernizer.py
│   │   ├── extractor.py
│   │   ├── bdd_test_agent.py
│   │   ├── test_writer.py    # NEW: Gherkin → xUnit conversion
│   │   └── verifier.py
│   ├── config.py             # Legacy configuration
│   └── audit/                # Workflow execution logs
└── openspec/                 # Specification documentation
    └── changes/
        └── setup-agent-migration-workflow/
```

---

## Quick Start

### 1. Prepare Your Component

Place legacy .NET components in `legacy-src/`:

```
legacy-src/
├── MyComponent/
│   ├── MyComponent.csproj
│   ├── Service.cs
│   └── Models.cs
```

### 2. Run the Migration

```bash
cd migration-poc
python orchestrator_v2.py MyComponent
```

### 3. Review Output

Check `legacy-code/MyComponent/` for:
- `extracted_logic.md` - Domain logic documentation
- `modernized_code.cs` - Transformed .NET 10 code
- `scenarios.feature` - BDD specifications
- `MyComponent.Tests.cs` - Generated xUnit tests
- `verification_report.json` - Migration validation results

### 4. Review & Merge

```bash
git checkout MyComponent-migration-20260724
# Review the changes
git checkout main
git merge MyComponent-migration-20260724
```

---

## Configuration Guide

### migration_config.yaml Structure

The system is entirely configured through `migration_config.yaml`. Key sections:

#### Global Settings

```yaml
global:
  legacy_src_dir: legacy-src          # Source component directory
  legacy_code_dir: legacy-code        # Staging directory
  target_framework: net10             # Target .NET version
  allow_parallel: false               # Sequential for POC
```

#### Agent Definition

Each agent is defined with:
- **role**: What the agent does (discovery, modernization, etc.)
- **tools**: Capabilities available to the agent
- **input**: Expected input artifact format
- **output**: Generated artifact type and location
- **validates**: Prerequisite checks before delegation

Example:

```yaml
explorer:
  name: explorer
  role: legacy_component_discovery
  tools:
    - code_scanner
    - component_analyzer
  input:
    type: component_name_or_pattern
  output:
    artifact_type: component_inventory
    format: json
```

#### Workflow Sequence

```yaml
orchestrator:
  workflow_sequence:
    - discovery
    - staging
    - modernization
    - extraction
    - bdd_generation
    - test_writing
    - verification
```

---

## Agent Responsibilities

### 1. Explorer (Discovery)
**Role**: Identify and analyze legacy components
- Scans legacy-src directory structure
- Detects .NET projects (.csproj, .sln files)
- Analyzes dependencies and component relationships
- Generates component inventory with metadata
- **Output**: `component_inventory.json`

### 2. Staging Agent (Component Preparation)
**Role**: Prepare component for migration
- Creates feature branch: `{component}-migration-{YYYYMMDD}`
- Copies component from legacy-src to legacy-code
- Validates copy completeness with checksums
- Creates initial commit with metadata
- **Output**: Staged component in legacy-code with git branch

### 3. Modernizer (Code Transformation)
**Role**: Transform code to .NET 10
- Updates target framework to net10
- Replaces deprecated APIs (System.Web → AspNetCore)
- Updates NuGet packages for .NET 10
- Converts config files to IConfiguration
- Adds dependency injection patterns
- **Output**: `modernized_code.cs`

### 4. Extractor (Domain Analysis)
**Role**: Identify business logic and algorithms
- Analyzes code structure and patterns
- Identifies domain entities and business rules
- Separates infrastructure vs. domain code
- Extracts algorithms with inputs/outputs
- **Output**: `extracted_logic.md` (YAML/Markdown)

### 5. BDD Generator (Test Specification)
**Role**: Create Gherkin test specifications
- Translates extracted logic to business language
- Creates Feature files with scenarios
- Supports Scenario Outlines for variations
- Includes boundary value and error cases
- **Output**: `scenarios.feature` (Gherkin)

### 6. Test Writer (Test Code Generation) [NEW]
**Role**: Convert Gherkin to executable C# tests
- Parses Gherkin feature files
- Generates xUnit test classes
- Creates [Fact] tests for single scenarios
- Creates [Theory] tests for Scenario Outlines
- Generates test fixtures and helper methods
- **Output**: `{component}.Tests.cs` (C# xUnit)

### 7. Verifier (Validation)
**Role**: Validate migration success
- Compiles generated test code
- Executes test suite
- Captures test results and coverage
- Identifies gaps and risks
- Generates final migration report
- **Output**: `verification_report.json`

---

## Workflow Stages

### Stage 1: Validation
**Purpose**: Verify prerequisites and request validity
- Checks legacy-src directory exists
- Validates component name and filters
- Confirms component is present in legacy-src
- **Exit on**: Missing component, invalid input
- **Next**: Staging if validation passes

### Stage 2: Staging
**Purpose**: Prepare component for migration
- Creates git feature branch
- Copies component with integrity checks
- Records component provenance
- Creates initial commit
- **Output**: Component in legacy-code with git branch
- **Next**: Exploration

### Stage 3: Exploration
**Purpose**: Analyze component structure
- Scans component files
- Builds component inventory
- Documents dependencies
- Identifies project type and size
- **Output**: Component analysis in exploration results
- **Next**: Extraction

### Stage 4: Extraction
**Purpose**: Extract domain logic
- Reads modernized component code
- Analyzes business logic
- Identifies domain concepts
- Documents algorithms and rules
- **Output**: `extracted_logic.md`
- **Next**: Modernization

### Stage 5: Modernization
**Purpose**: Transform to .NET 10
- Updates framework and NuGet packages
- Replaces deprecated APIs
- Adds async/await patterns
- Implements dependency injection
- **Output**: `modernized_code.cs`
- **Next**: BDD Generation

### Stage 6: BDD & Testing
**Purpose**: Create specs and test code
- Generates Gherkin specifications
- Parses Gherkin scenarios
- Generates xUnit test code
- Creates test fixtures
- **Output**: `scenarios.feature` + `{component}.Tests.cs`
- **Next**: Verification

### Stage 7: Verification
**Purpose**: Validate migration
- Compiles generated tests
- Executes test suite
- Analyzes coverage
- Generates final report
- **Output**: `verification_report.json`
- **Status**: Migration complete

---

## Generated Artifacts

### 1. Staging Metadata (.staging_metadata.json)

Records component provenance and migration start details:

```json
{
  "component_name": "TestService",
  "timestamp": "2026-07-24T18:20:00Z",
  "source_path": "legacy-src/TestService",
  "destination_path": "legacy-code/TestService",
  "branch_name": "testservice-migration-20260724",
  "status": "ready_for_modernization",
  "manifest": {
    "total_files": 13,
    "total_size_bytes": 38874
  }
}
```

### 2. Extracted Logic (extracted_logic.md)

Domain logic documentation in structured format:

```markdown
# Domain Logic: TestService

## Domain Entities
- AuthenticationService: User authentication and session management
- User: User credentials and profile

## Business Rules
- Senior citizens (age >= 65) get 15% discount
- Adults (21-64) get 5% discount
- Minors get no discount

## Algorithms
- AuthenticateUser(email, password) → bool
- CalculateDiscount(age, amount) → decimal
- GenerateSessionToken(email) → string
```

### 3. Modernized Code (modernized_code.cs)

.NET 10 compatible code with improvements:

```csharp
public class AuthenticationService
{
    private readonly IUserRepository _userRepository;

    public AuthenticationService(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<bool> AuthenticateUserAsync(UserCredentials credentials)
    {
        if (!AuthenticationLogic.ValidateInputs(credentials.Email, credentials.Password))
            return false;

        return await _userRepository.ValidateUserAsync(
            credentials.Email, 
            credentials.Password
        );
    }

    public decimal CalculateDiscount(DiscountRequest request) =>
        AuthenticationLogic.CalculateDiscount(request.Age, request.Amount);
}
```

### 4. Gherkin Specifications (scenarios.feature)

BDD test specifications:

```gherkin
Feature: User Authentication and Session Management
  As a system user
  I want to authenticate securely
  So that my data is protected

Scenario: Valid user authentication
  Given a user with email "user@test.com" and password "validPassword123"
  When I authenticate the user
  Then the authentication should succeed

Scenario Outline: Age-based discount calculation
  Given a user with age <age>
  When I calculate discount for amount <amount>
  Then the discount should be <discount>

  Examples:
    | age | amount | discount |
    | 65  | $100   | $15      |
    | 30  | $100   | $5       |
    | 15  | $100   | $0       |
```

### 5. Generated Test Code (TestService.Tests.cs)

Executable xUnit tests:

```csharp
using Xunit;
using FluentAssertions;

namespace TestService.Tests
{
    public class AuthenticationTests
    {
        [Fact]
        public void ValidUserAuthenticationSucceeds()
        {
            // Arrange
            var service = new AuthenticationService();
            
            // Act
            var result = service.AuthenticateUser("user@test.com", "password123");
            
            // Assert
            result.Should().BeTrue();
        }

        [Theory]
        [InlineData(65, 100, 15)]
        [InlineData(30, 100, 5)]
        [InlineData(15, 100, 0)]
        public void DiscountCalculationByAge(int age, decimal amount, decimal expected)
        {
            // Arrange
            var service = new AuthenticationService();
            
            // Act
            var discount = service.CalculateDiscount(age, amount);
            
            // Assert
            discount.Should().Be(expected);
        }
    }
}
```

### 6. Verification Report (verification_report.json)

Migration validation results:

```json
{
  "component": "TestService",
  "status": "CAUTION",
  "overall_status": "CAUTION",
  "test_results": {
    "total_tests": 14,
    "passed": 12,
    "failed": 2,
    "skipped": 0
  },
  "coverage": {
    "percentage": 87,
    "entities_tested": 5,
    "rules_tested": 8
  },
  "risks": [
    "Database validation logic needs real database",
    "Session token generation uses deprecated crypto",
    "Missing email validation"
  ],
  "recommendations": [
    "Implement IUserRepository for database access",
    "Update to modern cryptography for tokens",
    "Add email format validation"
  ]
}
```

---

## Usage Examples

### Example 1: Migrate a Single Component

```bash
cd migration-poc

# Run migration
python orchestrator_v2.py AuthService

# Expected output:
# ✅ All 7 stages complete
# Generated files in: legacy-code/AuthService/

# Review the changes
cd ../
git log --oneline | grep AuthService
git show AuthService-migration-20260724
```

### Example 2: Migrate with Filters

```bash
python orchestrator_v2.py PaymentService '{"domain": "Financial"}'
```

### Example 3: List Available Components

```bash
python orchestrator_v2.py --list-components
```

Output:
```
Available Components in legacy-src/:
 1. AuthService       (.csproj)    45 files
 2. PaymentService    (.csproj)    32 files
 3. ReportingService  (.sln)       78 files
```

### Example 4: Interactive Mode

```bash
python orchestrator_v2.py --interactive

# Prompts:
# Enter component name: AuthService
# Enter optional filters (JSON): {"domain": "Security"}
# Proceed? [Y/n]: Y
```

---

## Troubleshooting

### Issue: "Legacy source directory not found"

**Cause**: legacy-src directory doesn't exist or path is wrong

**Solution**:
```bash
# Verify directory exists
ls -la legacy-src/

# Run from correct directory
cd migration-poc
python orchestrator_v2.py ComponentName
```

### Issue: "Component not found in legacy-src"

**Cause**: Component directory doesn't exist or spelling is wrong

**Solution**:
```bash
# List available components
python orchestrator_v2.py --list-components

# Check correct spelling and case
ls legacy-src/ | grep -i component
```

### Issue: "Branch already exists"

**Cause**: Previous migration branch still exists

**Solution**:
```bash
# Clean up old branch
git branch -D component-migration-20260724

# Or use a different date/time in the branch name
```

### Issue: "Permission denied" errors

**Cause**: File or directory permissions issue

**Solution**:
```bash
# Check permissions
ls -la legacy-code/Component/

# Fix permissions if needed
chmod -R 755 legacy-code/Component/
```

### Issue: "Python module not found"

**Cause**: Missing dependencies (PyYAML, etc.)

**Solution**:
```bash
# Install requirements
pip install pyyaml

# Or use requirements.txt
pip install -r requirements.txt
```

### Issue: Workflow fails at a specific stage

**Cause**: Agent logic issue or invalid input

**Solution**:
1. Check audit logs: `cat migration-poc/audit/workflow.log`
2. Review the specific stage output in legacy-code/Component/
3. Check error message in verification report

---

## Advanced Topics

### Customizing Agents

To modify agent behavior, edit the corresponding file in `migration-poc/agents/`:

- `explorer.py` - Change discovery logic
- `staging_agent.py` - Modify branch/copy behavior
- `modernizer.py` - Update transformation rules
- `extractor.py` - Change domain logic extraction
- `bdd_test_agent.py` - Modify Gherkin generation
- `test_writer.py` - Customize test code generation
- `verifier.py` - Update validation logic

### Extending the Workflow

To add a new agent:

1. Create new agent file: `migration-poc/agents/my_agent.py`
2. Add to migration_config.yaml:
   ```yaml
   my_agent:
     name: my_agent
     role: my_role
     tools: [...]
     input: {...}
     output: {...}
   ```
3. Update orchestrator_v2.py to invoke the new agent
4. Update workflow_sequence to include new stage

### Integrating with CI/CD

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run migration
  run: |
    cd migration-poc
    python orchestrator_v2.py ${{ matrix.component }}

- name: Commit results
  run: |
    git add legacy-code/
    git commit -m "Migration: ${{ matrix.component }}"
    git push
```

### Monitoring and Reporting

Access workflow logs:

```bash
# Real-time workflow log
tail -f migration-poc/audit/workflow.log

# Component-specific audit trail
cat migration-poc/audit/migration_requests.jsonl | jq 'select(.component_name == "TestService")'

# Test results summary
jq '.test_results' legacy-code/TestService/verification_report.json
```

---

## Performance Considerations

- **Sequential Processing**: Current design processes stages sequentially (no parallelization)
- **File I/O**: Copying large components may take time; file checksums validate integrity
- **Memory**: All component code is loaded into memory for analysis
- **Network**: No external calls; fully self-contained

For large codebases (>100MB), consider:
- Splitting into smaller components
- Increasing timeout values
- Running during off-peak hours

---

## Support & Contributions

For issues, questions, or contributions:

1. Check this documentation first
2. Review the specification docs in `openspec/changes/setup-agent-migration-workflow/`
3. Check audit logs for detailed error context
4. File an issue with reproduction steps

---

## License & Attribution

This system is part of the Source Migration POC project.

**Generated**: 2026-07-24
**Last Updated**: 2026-07-24
**Status**: Production Ready (POC Phase)
