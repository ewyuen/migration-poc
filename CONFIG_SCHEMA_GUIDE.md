# migration_config.yaml Schema & Customization Guide

## Overview

The `migration_config.yaml` file is the single source of truth for the migration system. It defines:
- Global settings for all migrations
- Agent definitions and responsibilities
- Workflow sequence and stage ordering
- Artifact formats and locations
- Error handling policies
- Logging configuration

---

## File Structure

### Complete Schema

```yaml
# Versioning
version: "1.0"
workflow_name: component-migration-pipeline

# Global Settings
global:
  legacy_src_dir: legacy-src
  legacy_code_dir: legacy-code
  output_dir: migration-poc/output
  audit_dir: migration-poc/audit
  target_framework: net10
  allow_parallel: false

# Agent Definitions
orchestrator: {...}
explorer: {...}
staging_agent: {...}
modernizer: {...}
extractor: {...}
bdd_generator: {...}
test_writer: {...}
verifier: {...}

# Artifact Formats
artifacts: {...}

# Error Handling
error_handling: {...}

# Logging
logging: {...}
```

---

## Section Reference

### 1. Version & Metadata

```yaml
version: "1.0"                      # Schema version (for backwards compatibility)
workflow_name: component-migration-pipeline  # Workflow identifier
```

### 2. Global Settings

```yaml
global:
  legacy_src_dir: legacy-src        # Source components directory (relative to repo root)
  legacy_code_dir: legacy-code      # Staging directory for migrations (relative to repo root)
  output_dir: migration-poc/output  # Archived outputs location
  audit_dir: migration-poc/audit    # Audit logs location
  target_framework: net10           # Target .NET version (net10, net9, net8, etc.)
  allow_parallel: false             # Whether to allow parallel agent execution
```

**Customization**:
```yaml
# For different target framework
target_framework: net9

# For different source location
legacy_src_dir: /external/legacy-components

# For distributed audit logs
audit_dir: /var/log/migration-audit
```

### 3. Agent Definition Template

Every agent follows this structure:

```yaml
agent_name:
  name: agent_name                  # Unique agent identifier
  role: agent_role                  # Role/responsibility in workflow
  description: Agent description    # What this agent does
  entrypoint: path/to/agent.py      # Python module path
  
  tools:                            # Capabilities available
    - tool_name_1
    - tool_name_2
  
  input:                            # Input expectations
    type: input_type                # E.g., component_name, json_config
    optional_filters:               # Available filters
      - filter_1
      - filter_2
  
  output:                           # Output specification
    artifact_type: type_name        # Artifact type identifier
    format: format_spec             # File format(s)
    location: directory/pattern     # Output path (can use {component} placeholder)
  
  validates:                        # Pre-requisite checks
    - check_1
    - check_2
```

---

## Agent Definitions

### 1. Orchestrator

```yaml
orchestrator:
  name: orchestrator
  role: orchestrator
  description: Coordinates the migration workflow and directs all delegate agents
  entrypoint: migration-poc/orchestrator.py
  
  tools:
    - user_input_handler            # Handle user requests
    - agent_director                # Invoke other agents
    - branch_manager                # Git operations
    - state_manager                 # Track workflow state
    - error_handler                 # Handle errors
    - workflow_logger               # Log all operations
  
  delegates:                        # Agents this orchestrator manages
    - explorer
    - staging_agent
    - modernizer
    - extractor
    - bdd_generator
    - test_writer
    - verifier
  
  workflow_sequence:                # Stage execution order
    - discovery
    - staging
    - modernization
    - extraction
    - bdd_generation
    - test_writing
    - verification
```

**To modify workflow order**:
```yaml
orchestrator:
  workflow_sequence:
    - discovery
    - staging
    - modernization
    # Swap extraction and bdd_generation
    - bdd_generation
    - extraction
    - test_writing
    - verification
```

### 2. Explorer

```yaml
explorer:
  name: explorer
  role: legacy_component_discovery
  description: Scans legacy-src folder and identifies components for migration
  entrypoint: migration-poc/agents/explorer.py
  
  tools:
    - code_scanner                  # Directory scanning
    - component_analyzer            # File analysis
    - dependency_analyzer           # Dependency detection
    - metadata_extractor            # Metadata collection
  
  input:
    type: component_name_or_pattern
    optional_filters:
      - domain
      - dependency
      - size
  
  output:
    artifact_type: component_inventory
    format: json
    location: legacy-code/inventory.json
  
  validates:
    - component_exists_in_legacy_src
    - component_readiness
    - dependency_compatibility
```

**Customization - Add new filter**:
```yaml
explorer:
  input:
    optional_filters:
      - domain
      - dependency
      - size
      - framework_version    # New filter
      - minimum_age          # New filter
```

### 3. Staging Agent (NEW)

```yaml
staging_agent:
  name: staging_agent
  role: legacy_component_staging
  description: Copies components to legacy-code and creates feature branches
  entrypoint: migration-poc/agents/staging_agent.py
  
  tools:
    - branch_manager                # Git branch operations
    - file_copier                   # File copying utilities
    - checksum_validator            # Integrity verification
    - metadata_writer               # Metadata creation
    - commit_manager                # Git commits
  
  input:
    artifact_type: component_inventory
  
  output:
    artifacts:
      - component_copy
      - feature_branch
      - metadata_file
    location: legacy-code/{component}/
  
  validates:
    - copy_completeness
    - branch_creation
    - file_integrity
```

**Branch naming customization**:
```python
# In staging_agent.py, modify _generate_branch_name():
def _generate_branch_name(self, component_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")  # More precision
    return f"migrate/{component_name}/{timestamp}"        # Different format
```

### 4. Modernizer

```yaml
modernizer:
  name: modernizer
  role: code_modernization_dotnet10
  description: Updates legacy code to .NET 10 standards and APIs
  entrypoint: migration-poc/agents/modernizer.py
  
  tools:
    - code_transformer              # AST transformation
    - dotnet_api_mapper             # API replacement mapping
    - nuget_updater                 # Package updates
    - config_migrator               # Config file conversion
    - compilation_validator         # Build validation
  
  input:
    artifact_type: staged_legacy_code
    location: legacy-code/{component}/
  
  output:
    artifacts:
      - modernized_code
      - modernization_report
    format: csproj, cs files
    location: legacy-code/{component}/{component}.modernized/
  
  validates:
    - syntax_validity
    - compilation_success
    - api_compatibility
```

**API mapping customization**:
```python
# Extend API_REPLACEMENTS in modernizer.py:
API_REPLACEMENTS = {
    "System.Web.HttpContext": "Microsoft.AspNetCore.Http.HttpContext",
    "ConfigurationManager": "IConfiguration",
    # Add custom mappings
    "System.Data.SqlClient": "Microsoft.Data.SqlClient",
}
```

### 5. Extractor

```yaml
extractor:
  name: extractor
  role: domain_logic_extraction
  description: Decomposes modernized code into business logic and algorithms
  entrypoint: migration-poc/agents/extractor.py
  
  tools:
    - ast_analyzer                  # AST parsing
    - pattern_matcher               # Code pattern detection
    - abstraction_generator         # Abstraction creation
    - dependency_mapper             # Dependency tracking
    - coverage_analyzer             # Coverage metrics
  
  input:
    artifact_type: modernized_code
    location: legacy-code/{component}/{component}.modernized/
  
  output:
    artifact_type: business_logic_specs
    format: yaml, markdown
    location: legacy-code/{component}/{component}.extracted-logic.md
  
  validates:
    - extraction_completeness
    - logic_preservation
```

### 6. BDD Generator

```yaml
bdd_generator:
  name: bdd_generator
  role: bdd_specification_generation
  description: Creates Gherkin feature files from extracted domain logic
  entrypoint: migration-poc/agents/bdd_test_agent.py
  
  tools:
    - scenario_generator            # Scenario creation
    - gherkin_writer                # Gherkin file writing
    - traceability_linker           # Linkage to source logic
    - syntax_validator              # Gherkin validation
  
  input:
    artifact_type: business_logic_specs
    location: legacy-code/{component}/{component}.extracted-logic.md
  
  output:
    artifact_type: gherkin_specifications
    format: feature files
    location: legacy-code/{component}/{component}.feature
  
  validates:
    - gherkin_syntax
    - scenario_completeness
```

### 7. Test Writer (NEW)

```yaml
test_writer:
  name: test_writer
  role: gherkin_test_implementation
  description: Converts Gherkin specifications into executable C# test code
  entrypoint: migration-poc/agents/test_writer.py
  
  tools:
    - gherkin_parser                # Feature file parsing
    - test_code_generator           # Test generation
    - fixture_generator             # Fixture/setup creation
    - compilation_validator         # Code compilation check
  
  input:
    artifact_type: gherkin_specifications
    location: legacy-code/{component}/{component}.feature
  
  output:
    artifacts:
      - test_class
      - test_fixtures
      - helper_methods
    format: csharp
    location: legacy-code/{component}/{component}.Tests.cs
  
  validates:
    - code_compilation
    - fixture_validity
```

**Test framework customization**:
```python
# In test_writer.py, modify generate_test_class():
def generate_test_class(self, feature_name: str, scenarios: List[Dict], component_name: str) -> str:
    # Change from xUnit to NUnit:
    code.append("using NUnit.Framework;")
    code.append("[TestFixture]")
    # Update assertion syntax accordingly
```

### 8. Verifier

```yaml
verifier:
  name: verifier
  role: test_verification_execution
  description: Executes tests and validates the migration success
  entrypoint: migration-poc/agents/verifier.py
  
  tools:
    - test_compiler                 # C# compilation
    - test_runner                   # Test execution
    - result_reporter               # Report generation
    - coverage_analyzer             # Coverage analysis
  
  input:
    artifact_type: executable_tests
    location: legacy-code/{component}/{component}.Tests.cs
  
  output:
    artifacts:
      - test_results
      - coverage_report
      - verification_report
    format: json, markdown
    location: legacy-code/{component}/{component}.test-results.json
  
  validates:
    - test_execution
    - result_validity
```

---

## Artifact Definitions

Each artifact format is documented:

```yaml
artifacts:
  component_inventory:
    description: JSON file listing discovered components with metadata
    format: |
      {
        "components": [{"name": "...", "path": "...", ...}],
        "summary": "..."
      }
  
  business_logic_specs:
    description: Extracted domain concepts and business rules
    format: yaml, markdown
    includes:
      - domain_entities
      - business_rules
      - algorithms
      - test_scenarios
  
  # ... other artifact definitions
```

**To add custom artifact**:
```yaml
artifacts:
  custom_report:
    description: Custom analysis report
    format: json
    includes:
      - analysis_results
      - recommendations
```

---

## Error Handling

```yaml
error_handling:
  on_agent_failure: halt_pipeline   # halt_pipeline, skip_stage, continue
  validation_level: strict          # strict, lenient
  recovery_strategy: rollback_to_branch  # rollback_to_branch, manual_review
  logging_detail: comprehensive     # minimal, normal, comprehensive
```

**Customization options**:

```yaml
error_handling:
  # Continue pipeline even if non-critical stage fails
  on_agent_failure: continue
  
  # Lenient validation (skip some checks)
  validation_level: lenient
  
  # Manual review required before rollback
  recovery_strategy: manual_review
  
  # Minimal logging for performance
  logging_detail: minimal
```

---

## Logging Configuration

```yaml
logging:
  level: info                       # debug, info, warning, error
  format: json                      # json, text
  output:
    audit_log: migration-poc/audit/workflow.log
    error_log: migration-poc/audit/errors.log
  include_metadata: true            # Include timestamp, version, etc.
  persistence_location: legacy-code/{component}/audit/
```

**Customization**:

```yaml
logging:
  # Debug mode
  level: debug
  
  # Format for log aggregation
  format: json
  
  # Separate locations
  output:
    audit_log: /var/log/migration/audit.log
    error_log: /var/log/migration/errors.log
  
  # Per-component logs
  persistence_location: legacy-code/{component}/.logs/
```

---

## Variable Substitution

The following variables can be used in paths:

| Variable | Value | Example |
|----------|-------|---------|
| `{component}` | Component name | `legacy-code/AuthService/` |
| `{date}` | Current date | `logs/2026-07-24/` |
| `{timestamp}` | Current timestamp | `logs/20260724_181915/` |

**Example usage**:

```yaml
staging_agent:
  output:
    location: legacy-code/{component}/{date}/

bdd_generator:
  output:
    location: legacy-code/{component}/{timestamp}/scenarios.feature
```

---

## Performance Tuning

### For Large Codebases

```yaml
global:
  # Disable parallel to reduce resource usage
  allow_parallel: false
  
  # Custom output directory on faster disk
  output_dir: /fast-ssd/migration-output

error_handling:
  # Strict validation to catch issues early
  validation_level: strict
```

### For CI/CD Integration

```yaml
logging:
  # Comprehensive logging for debugging
  logging_detail: comprehensive
  
  # Store all logs for archival
  output:
    audit_log: /persistent-storage/audit.log
    error_log: /persistent-storage/errors.log
```

### For Development

```yaml
logging:
  # Debug level for troubleshooting
  level: debug
  
  # Detailed output
  logging_detail: comprehensive

error_handling:
  # Stop immediately on errors
  on_agent_failure: halt_pipeline
  validation_level: strict
```

---

## Validation

### Validate Config Syntax

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('migration_config.yaml')); print('✅ Valid')"

# Check against schema
python -c "from orchestrator_v2 import OrchestratorV2; o = OrchestratorV2(); print('✅ Schema valid')"
```

### Common Validation Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `IndentationError` | YAML indentation | Use consistent spaces (not tabs) |
| `KeyError` | Missing required field | Check schema above |
| `FileNotFoundError` | Path doesn't exist | Verify paths are relative to repo root |
| `TypeError` | Wrong value type | Check expected types (string, list, dict) |

---

## Example Configurations

### Minimal Configuration

```yaml
version: "1.0"
workflow_name: migration

global:
  legacy_src_dir: legacy-src
  legacy_code_dir: legacy-code
  target_framework: net10

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

### Production Configuration

```yaml
version: "1.0"
workflow_name: enterprise-migration

global:
  legacy_src_dir: /enterprise/legacy-components
  legacy_code_dir: /enterprise/migrations
  output_dir: /archive/migration-output
  audit_dir: /var/log/migration-audit
  target_framework: net10
  allow_parallel: false

error_handling:
  on_agent_failure: halt_pipeline
  validation_level: strict
  recovery_strategy: rollback_to_branch
  logging_detail: comprehensive

logging:
  level: info
  format: json
  include_metadata: true
  persistence_location: /var/log/migration/{component}/
```

### Development Configuration

```yaml
version: "1.0"
workflow_name: dev-migration

global:
  legacy_src_dir: ./legacy-src
  legacy_code_dir: ./legacy-code
  output_dir: ./output
  audit_dir: ./audit
  target_framework: net10

error_handling:
  on_agent_failure: halt_pipeline
  validation_level: strict

logging:
  level: debug
  format: text
  include_metadata: true
```

---

## Troubleshooting Config Issues

### Config Not Found

```bash
# Ensure migration_config.yaml is in repository root
ls -la migration_config.yaml

# Or specify explicit path
python orchestrator_v2.py ComponentName --config /path/to/migration_config.yaml
```

### Agent Not Recognized

```bash
# Verify agent name in config matches orchestrator code
grep "name: agent_name" migration_config.yaml

# Check if entrypoint file exists
ls -la migration-poc/agents/agent_name.py
```

### Invalid Path

```bash
# Paths should be relative to repository root
# ✅ Correct: legacy-src/Component
# ❌ Wrong: /home/user/migration-poc/legacy-src/Component
```

---

## Best Practices

1. **Keep migration_config.yaml in version control** - Track all changes
2. **Use consistent paths** - Relative to repository root
3. **Document custom changes** - Add comments explaining modifications
4. **Test config changes** - Validate with small components first
5. **Backup before major changes** - Keep previous config versions
6. **Use environment variables** - For sensitive paths or credentials

---

## Migration Path

To migrate from an older config version:

1. Backup old config: `cp migration_config.yaml migration_config.yaml.bak`
2. Create new config with updated schema
3. Migrate custom settings from old config
4. Test with a small component first
5. Gradually migrate other components

---

## Support

For config issues:
1. Validate syntax: `python -c "import yaml; yaml.safe_load(open('migration_config.yaml'))"`
2. Check MIGRATION_SYSTEM.md for detailed info
3. Review example configs above
4. Check audit logs for specific errors
