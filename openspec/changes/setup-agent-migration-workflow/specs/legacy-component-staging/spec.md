## ADDED Requirements

### Requirement: Staging agent creates feature branch for migration

The staging agent SHALL create an isolated git branch for each component migration.

#### Scenario: Branch created with timestamp
- **WHEN** component "LegacyAuthService" is identified for migration
- **THEN** staging agent creates branch "legacyauthservice-migration-20260724"

#### Scenario: Branch is based on current main
- **WHEN** branch is created
- **THEN** it contains the latest code from main branch and no additional changes

### Requirement: Staging agent copies component from legacy-src to legacy-code

The staging agent SHALL move the identified component(s) to the legacy-code directory within the feature branch.

#### Scenario: Component copied with full directory structure
- **WHEN** component exists at legacy-src/LegacyAuthService
- **THEN** staging agent copies it to legacy-code/LegacyAuthService preserving all files and folder structure

#### Scenario: Legacy-code directory is created if needed
- **WHEN** legacy-code directory does not exist
- **THEN** staging agent creates it at the repository root

#### Scenario: Copy preserves file permissions and encoding
- **WHEN** original component contains shell scripts or special files
- **THEN** staging agent preserves executable permissions and file encoding

### Requirement: Staging agent commits initial copy to feature branch

The staging agent SHALL create a baseline commit in the feature branch capturing the original component.

#### Scenario: Initial commit records component state
- **WHEN** component is copied to legacy-code
- **THEN** staging agent commits with message "Initial copy: {component} from legacy-src for migration"

#### Scenario: Commit includes metadata
- **WHEN** initial commit is created
- **THEN** commit message includes timestamp, component name, and component size (LOC)

### Requirement: Staging agent validates copy completeness

The staging agent SHALL verify that all files were copied successfully without data loss.

#### Scenario: Validation confirms file count matches
- **WHEN** copy completes
- **THEN** staging agent verifies: file count in legacy-code equals file count in legacy-src

#### Scenario: Validation confirms no corruption
- **WHEN** copy completes
- **THEN** staging agent computes and compares checksums of original and copied files

### Requirement: Staging agent records staging metadata

The staging agent SHALL create a metadata file documenting the staging operation.

#### Scenario: Metadata records component provenance
- **WHEN** component is staged
- **THEN** metadata file includes: source path, timestamp, branch name, component version/hash from legacy-src

#### Scenario: Metadata includes staging status
- **WHEN** staging completes
- **THEN** metadata marks status as "ready_for_modernization"
