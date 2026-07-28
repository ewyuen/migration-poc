## ADDED Requirements

### Requirement: Configure Langfuse span processor
OrchestratorV3 SHALL add LangfuseSpanProcessor to the OpenTelemetry tracer provider to subscribe to all spans.

#### Scenario: LangfuseSpanProcessor initialized
- **WHEN** OrchestratorV3 initializes OpenTelemetry
- **THEN** LangfuseSpanProcessor is created and added to tracer provider

#### Scenario: Langfuse API credentials loaded from environment
- **WHEN** LangfuseSpanProcessor initializes
- **THEN** LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are read from environment (or use Langfuse defaults)

#### Scenario: Spans exported to Langfuse
- **WHEN** root span ends
- **THEN** entire span tree (root + 6 node children) is exported to Langfuse via OTLP gRPC

### Requirement: Full trace visible in Langfuse dashboard
Langfuse SHALL receive the complete workflow trace and display it as a waterfall with timing and status.

#### Scenario: Workflow trace appears in Langfuse
- **WHEN** orchestrate_migration() completes
- **THEN** full trace tree is visible in Langfuse UI under Traces section

#### Scenario: Trace shows node names and durations
- **WHEN** user views trace in Langfuse
- **THEN** each node (validate, stage, explore, modernize, bdd_and_test, verify) is shown as a span with its duration

#### Scenario: Failed nodes marked as errors in trace
- **WHEN** a node fails
- **THEN** that node's span shows error status and exception details in Langfuse

#### Scenario: Trace correlates to run_id
- **WHEN** trace is recorded
- **THEN** run_id is included as an attribute, allowing user to correlate trace with migration run

### Requirement: No local file overhead from Langfuse exporter
Langfuse integration SHALL not create additional local log files; traces flow directly to Langfuse service.

#### Scenario: Trace exported via network only
- **WHEN** orchestration completes
- **THEN** span data is sent to Langfuse (no local JSON/protobuf files saved as side-effect)

### Requirement: Environment variables for Langfuse configuration
Langfuse credentials and endpoint SHALL be configurable via environment variables.

#### Scenario: Public key from LANGFUSE_PUBLIC_KEY env var
- **WHEN** OrchestratorV3 initializes
- **THEN** LANGFUSE_PUBLIC_KEY is read; if missing, default Langfuse endpoint is used

#### Scenario: Secret key from LANGFUSE_SECRET_KEY env var
- **WHEN** OrchestratorV3 initializes
- **THEN** LANGFUSE_SECRET_KEY is read; if missing, defaults or initialization fails gracefully

#### Scenario: Custom endpoint via LANGFUSE_ENDPOINT env var (optional)
- **WHEN** LANGFUSE_ENDPOINT is set
- **THEN** OTLP exporter uses that endpoint instead of default

### Requirement: Langfuse integration does not block orchestration
Failures in span export to Langfuse SHALL not crash the migration workflow.

#### Scenario: Network error to Langfuse does not crash orchestration
- **WHEN** Langfuse service is unreachable during export
- **THEN** exporter logs warning but orchestration completes normally; span data is dropped (not queued)

#### Scenario: Malformed Langfuse config does not block startup
- **WHEN** LANGFUSE_PUBLIC_KEY is malformed or empty
- **THEN** OrchestratorV3 still starts; traces are not exported but orchestration proceeds

### Requirement: Trace linked to migration request
Traces SHALL include metadata linking back to the original migration request for context.

#### Scenario: Request ID in trace
- **WHEN** orchestrate_migration() runs
- **THEN** root span includes request_id attribute (from MigrationRequest.request_id)

#### Scenario: Component name in trace
- **WHEN** orchestrate_migration() runs
- **THEN** root span includes component_name attribute (from MigrationRequest.component_name)

### Requirement: Integration with LangGraph callbacks (optional)
If LangGraph callbacks are used, they SHALL integrate with OTel tracing, not duplicate it.

#### Scenario: LangGraph and OTel do not double-instrument
- **WHEN** LangGraph callbacks and OTel instrumentation are both enabled
- **THEN** spans are emitted exactly once (no duplication in Langfuse)
