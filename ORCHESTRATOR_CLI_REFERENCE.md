# Orchestrator CLI Reference

## Quick Commands

### Run Migration

```bash
python orchestrator_v2.py <component_name> [filters_json]
```

### Examples

#### Basic Migration
```bash
python orchestrator_v2.py TestService
```

#### With Filters
```bash
python orchestrator_v2.py AuthService '{"domain": "Security"}'
python orchestrator_v2.py PaymentService '{"domain": "Financial", "size": "small"}'
```

---

## Command Structure

```
orchestrator_v2.py [OPTIONS] <component_name> [filters_json]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `component_name` | string | Yes | Name of component in legacy-src to migrate |
| `filters_json` | JSON | No | Optional filters for component discovery |

### Supported Filters

```json
{
  "domain": "string",        // Business domain (Security, Financial, etc.)
  "dependency": "string",    // Dependency name to search for
  "size": "small|medium|large", // Component size
  "language": "string",      // Programming language
  "namespace": "string"      // .NET namespace prefix
}
```

---

## Workflow Output

### Console Output

During execution, you'll see:

```
✅ Config loaded: config.yaml

======================================================================
🎭 ORCHESTRATOR V2: Migration Workflow
======================================================================
Component: TestService
Request ID: TestService-20260724-181915
Target Framework: net10
======================================================================

======================================================================
[STAGE 1/7] VALIDATION
======================================================================

Validating request...
✅ Validation passed

======================================================================
[STAGE 2/7] STAGING
======================================================================

[STAGING] Starting staging for TestService
------
✅ Branch created: testservice-migration-20260724
✅ Component copied: legacy-src\TestService → legacy-code\TestService
✅ Copy verified: 13 files, 38874 bytes
✅ Initial commit created for TestService
✅ Metadata file created: legacy-code\TestService\.staging_metadata.json

[...remaining stages...]

======================================================================
✨ MIGRATION WORKFLOW COMPLETE
======================================================================

Component: TestService
Status: CAUTION
Completed Stages: 7/7
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - all stages complete |
| 1 | Failure - workflow halted at some stage |

---

## Generated Files

### Output Location

```
legacy-code/<component_name>/
```

### File Reference

| File | Size | Stage | Purpose |
|------|------|-------|---------|
| `.staging_metadata.json` | ~3KB | Staging | Component provenance & branch info |
| `extracted_logic.md` | ~2KB | Extraction | Domain logic documentation |
| `modernized_code.cs` | ~2KB | Modernization | .NET 10 compatible code |
| `scenarios.feature` | ~3KB | BDD | Gherkin test specifications |
| `<component>.Tests.cs` | ~9KB | Test Writer | Generated xUnit test code |
| `verification_report.json` | ~2KB | Verification | Test results & validation |

### File Descriptions

#### .staging_metadata.json
Metadata about the component and migration start:
- Component name and paths
- Feature branch name created
- File manifest with checksums
- Migration start timestamp

#### extracted_logic.md
Domain logic extracted from the component:
- Domain entities and relationships
- Business rules and algorithms
- Test scenarios identified
- Dependencies documented

#### modernized_code.cs
Transformed legacy code for .NET 10:
- Updated target framework
- Async/await patterns added
- Dependency injection implemented
- Deprecated APIs replaced
- Modern C# patterns used

#### scenarios.feature
Gherkin specifications for testing:
- Feature descriptions
- Business scenarios
- Boundary value examples
- Error handling scenarios
- Compliance requirements

#### <component>.Tests.cs
Generated executable test code:
- xUnit test class
- [Fact] tests for single scenarios
- [Theory] tests for data-driven scenarios
- Test fixtures and helpers
- Integration-ready structure

#### verification_report.json
Migration validation results:
- Test execution summary
- Pass/fail counts
- Code coverage metrics
- Identified risks
- Recommendations

---

## Environment Setup

### Prerequisites

```bash
# Python 3.7+
python --version

# Required packages
pip install pyyaml
```

### Installation

```bash
cd migration-poc

# Install dependencies (if requirements.txt exists)
pip install -r requirements.txt

# Or install manually
pip install pyyaml
```

### Verification

```bash
# Test orchestrator
python orchestrator_v2.py --help

# Expected: Shows usage information
```

---

## Common Workflows

### Workflow 1: Migrate Single Component

```bash
# 1. Ensure component exists in legacy-src
ls legacy-src/MyComponent/

# 2. Run migration
python orchestrator_v2.py MyComponent

# 3. Review outputs
cd ../legacy-code/MyComponent/
ls -la

# 4. Review git changes
cd ../
git log --oneline | grep MyComponent

# 5. Review generated code
cat legacy-code/MyComponent/modernized_code.cs

# 6. Check test scenarios
cat legacy-code/MyComponent/scenarios.feature
```

### Workflow 2: Review Test Code

```bash
# 1. Run migration
python orchestrator_v2.py TestService

# 2. View generated tests
cat ../legacy-code/TestService/TestService.Tests.cs

# 3. Check test count
grep -c "public void\|public async Task" ../legacy-code/TestService/TestService.Tests.cs

# 4. Review fixture setup
grep -A 5 "TestFixture" ../legacy-code/TestService/TestService.Tests.cs
```

### Workflow 3: Batch Migration

```bash
# Migrate multiple components
for component in Component1 Component2 Component3; do
  echo "Migrating $component..."
  python orchestrator_v2.py $component
  echo "✅ $component complete"
done
```

### Workflow 4: Verify All Stages

```bash
# Run migration with verbose output
python orchestrator_v2.py ComponentName 2>&1 | tee migration.log

# Check each stage in log
grep "STAGE" migration.log

# Verify artifacts exist
for file in staging_metadata extracted_logic modernized_code scenarios TestService.Tests verification_report; do
  if [ -f "legacy-code/ComponentName/$file*" ]; then
    echo "✅ $file generated"
  else
    echo "❌ $file missing"
  fi
done
```

---

## Troubleshooting Commands

### Check Config Validity

```bash
# Validate config.yaml syntax
python -c "import yaml; yaml.safe_load(open('../config.yaml')); print('✅ Config valid')"
```

### List Components

```bash
# Find all components in legacy-src
ls -d legacy-src/*/ | xargs -I {} basename {}
```

### Check Audit Trail

```bash
# View workflow logs
tail -20 ../migration-poc/audit/workflow.log

# Search for errors
grep ERROR ../migration-poc/audit/workflow.log

# View component requests
cat ../migration-poc/audit/migration_requests.jsonl
```

### Verify Branch Created

```bash
# Check git branches
git branch -a | grep migration

# Get branch details
git log --graph --oneline --all | head -20
```

### Inspect Generated Artifacts

```bash
# View metadata
cat ../legacy-code/ComponentName/.staging_metadata.json | jq '.'

# Count lines of generated test code
wc -l ../legacy-code/ComponentName/ComponentName.Tests.cs

# View Gherkin syntax
grep "Scenario\|Given\|When\|Then" ../legacy-code/ComponentName/scenarios.feature
```

---

## Performance Tuning

### For Large Components

```bash
# Set Python to use more memory
set PYTHONHASHSEED=0
python orchestrator_v2.py LargeComponent

# Increase timeout for git operations
# (Modify in orchestrator_v2.py timeout parameter)
```

### For Multiple Migrations

```bash
# Create a migration script
cat > migrate_all.sh << 'EOF'
#!/bin/bash
for component in $(ls ../legacy-src/); do
  if [ -d "../legacy-src/$component" ]; then
    echo "Migrating $component..."
    python orchestrator_v2.py "$component" || echo "Failed: $component"
  fi
done
EOF

chmod +x migrate_all.sh
./migrate_all.sh
```

---

## Integration Examples

### GitHub Actions

```yaml
name: Component Migration
on: [push]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install pyyaml
      
      - name: Run migration
        run: |
          cd migration-poc
          python orchestrator_v2.py TestService
      
      - name: Commit results
        run: |
          git add legacy-code/
          git commit -m "Migration: TestService" || true
          git push
```

### Docker

```dockerfile
FROM python:3.9

WORKDIR /app
COPY . .

RUN pip install pyyaml

ENTRYPOINT ["python", "migration-poc/orchestrator_v2.py"]
```

```bash
# Usage
docker build -t migrator .
docker run migrator TestService
```

---

## Exit Scenarios

### Successful Completion (Exit 0)

```
✨ MIGRATION WORKFLOW COMPLETE
Component: TestService
Status: CAUTION / SUCCESS
Completed Stages: 7/7
```

### Validation Failure (Exit 1)

```
❌ Validation failed: Component not found in legacy-src
```

### Staging Failure (Exit 1)

```
❌ Branch creation failed: Repository is dirty
```

### Extraction Failure (Exit 1)

```
❌ Extraction failed: Unable to read component files
```

---

## Advanced Options

### Skip to Specific Stage

```python
# Modify orchestrator_v2.py to skip stages
# Example: Start from modernization
state.completed_stages = ["validation", "staging", "exploration", "extraction"]
```

### Custom Config Path

```python
# Modify orchestrator_v2.py
orchestrator = OrchestratorV2(config_path="custom-config.yaml")
```

### Enable Debug Logging

```python
# Add to orchestrator_v2.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-24 | Initial release with 7-stage pipeline |
| 1.1 | TBD | Enhanced error handling and logging |
| 1.2 | TBD | Parallel execution support |

---

## Need Help?

1. Check this CLI reference
2. Read MIGRATION_SYSTEM.md for detailed documentation
3. Review audit logs: `migration-poc/audit/workflow.log`
4. Check specification docs: `openspec/changes/setup-agent-migration-workflow/`
