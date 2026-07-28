## Purpose

Instrument OrchestratorV3 with OpenTelemetry so the `orchestrate_migration()` call and each of the 6 workflow nodes produce a parent/child span tree with timing, status, and error attributes, without exporter failures ever crashing the migration workflow.

## Requirements

### Requirement: Initialize OpenTelemetry tracer and provider
OrchestratorV3 SHALL initialize OpenTelemetry SDK with a tracer provider and global tracer instance on startup.

#### Scenario: Create OTLP exporter
- **WHEN** OrchestratorV3 initializes
- **THEN** OTLPSpanExporter is created targeting OTLP gRPC endpoint (default localhost:4317 or env-configured)

#### Scenario: Add span processor
- **WHEN** OrchestratorV3 initializes
- **THEN** span processor(s) are added to tracer provider (LangfuseSpanProcessor and/or other exporters)

### Requirement: Instrument orchestrate_migration as root span
The `orchestrate_migration()` method SHALL be wrapped in a root OTel span.

#### Scenario: Root span created
- **WHEN** orchestrate_migration() is called
- **THEN** root span "orchestrate_migration" is created with span context

#### Scenario: Root span closed on completion
- **WHEN** orchestrate_migration() completes (success or exception)
- **THEN** root span is ended with final status (UNSET, OK, or ERROR)

### Requirement: Each graph node produces a span
Each of the 6 workflow nodes (validate, stage, explore, modernize, bdd_and_test, verify) SHALL produce its own child span under the root.

#### Scenario: Span for validation node
- **WHEN** node_validate runs
- **THEN** child span "node_validate" is created and attributes recorded

#### Scenario: Span for staging node
- **WHEN** node_stage runs
- **THEN** child span "node_stage" is created with run_id and component_name as attributes

#### Scenario: Span for exploration node
- **WHEN** node_explore runs
- **THEN** child span "node_explore" is created

#### Scenario: Span for modernization node
- **WHEN** node_modernize runs
- **THEN** child span "node_modernize" is created

#### Scenario: Span for BDD and test node
- **WHEN** node_bdd_and_test runs
- **THEN** child span "node_bdd_and_test" is created

#### Scenario: Span for verification node
- **WHEN** node_verify runs
- **THEN** child span "node_verify" is created

### Requirement: Span attributes capture metadata
Each span SHALL include attributes for debugging and monitoring.

#### Scenario: Node span includes stage name and status
- **WHEN** node completes
- **THEN** span includes attributes: stage_name, status (success/failed), node_type

#### Scenario: Span includes error details on failure
- **WHEN** node fails with exception
- **THEN** span status is set to ERROR and exception details are recorded (message, stack trace)

#### Scenario: Span includes timing
- **WHEN** span ends
- **THEN** span duration (end_time - start_time) is available to exporter

#### Scenario: Span includes run_id when available
- **WHEN** state.run_id is populated (after staging)
- **THEN** downstream nodes record run_id as span attribute for correlation

### Requirement: Span hierarchy is parent-child
Spans SHALL form a tree: root contains 6 node spans, each node span is a direct child of root.

#### Scenario: Span hierarchy recorded
- **WHEN** all nodes complete
- **THEN** exported traces show orchestrate_migration as parent with 6 child spans

### Requirement: Exceptions do not break tracing
If a node raises an exception, tracing SHALL continue and record the error without crashing.

#### Scenario: Exception in node is caught and traced
- **WHEN** node_modernize raises Exception
- **THEN** exception is caught, span is marked ERROR, and orchestration continues to next node

#### Scenario: Span exporter errors do not break orchestration
- **WHEN** span exporter fails (e.g., network unreachable)
- **THEN** orchestration continues; exporter error is logged but does not crash workflow

### Requirement: Tracer instance passed to orchestrator
OrchestratorV3 SHALL accept an optional tracer instance or create one if not provided.

#### Scenario: Use injected tracer
- **WHEN** caller passes `tracer=my_tracer` to OrchestratorV3 constructor
- **THEN** OrchestratorV3 uses that tracer for all spans

#### Scenario: Create default tracer if not provided
- **WHEN** no tracer is passed
- **THEN** OrchestratorV3 creates a tracer via `trace.get_tracer(__name__)`
