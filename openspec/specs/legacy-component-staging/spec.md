## ADDED Requirements

### Requirement: Staging agent generates a run_id for migration

The staging agent SHALL generate a unique `run_id` for each migration run instead of creating or checking out a git branch.

#### Scenario: run_id combines component name, date, and time
- **WHEN** component "LegacyAuthService" is staged
- **THEN** staging agent generates run_id "legacyauthservice-072726-143022" combining the sanitized component name with the current date (MMDDYY) and time (HHMMSS)

#### Scenario: run_id is unique by construction
- **WHEN** the same component is staged multiple times
- **THEN** each staging run produces a distinct run_id (differing by timestamp) without checking git or the filesystem for an existing name first

#### Scenario: Staging does not alter git state
- **WHEN** staging agent generates a run_id and copies the component
- **THEN** the user's currently checked-out git branch is unchanged, and no new git branch or commit is created

### Requirement: Staging agent copies component from legacy-src to legacy-code

The staging agent SHALL move the identified component(s) to a run_id-scoped subdirectory of the legacy-code directory.

#### Scenario: Component copied with full directory structure
- **WHEN** component "LegacyAuthService" exists at legacy-src/LegacyAuthService and run_id "legacyauthservice-072726-143022" has been generated
- **THEN** staging agent copies it to legacy-code/legacyauthservice-072726-143022 preserving all files and folder structure

#### Scenario: Legacy-code directory is created if needed
- **WHEN** legacy-code directory does not exist
- **THEN** staging agent creates it at the repository root

#### Scenario: Copy preserves file permissions and encoding
- **WHEN** original component contains shell scripts or special files
- **THEN** staging agent preserves executable permissions and file encoding

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
- **THEN** metadata file includes: source path, timestamp, run_id, component version/hash from legacy-src

#### Scenario: Metadata includes staging status
- **WHEN** staging completes
- **THEN** metadata marks status as "ready_for_modernization"
