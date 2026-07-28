## 1. Setup & Dependencies

- [x] 1.1 Add LangGraph and OpenTelemetry dependencies to requirements.txt (langgraph, opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp, langfuse)
- [x] 1.2 Update venv and test dependency installation locally
- [x] 1.3 Create OrchestratorV3 module file at migration-poc/agents/orchestrator_v3.py (empty scaffold)

## 2. State Schema & Core Graph Setup

- [x] 2.1 Define MigrationState TypedDict with all required fields (request, run_id, stage, error, staging_results, exploration_results, modernized_code, bdd_tests, test_code, verification_results)
- [x] 2.2 Create StateGraph instance and register initial state schema
- [x] 2.3 Implement __init__() method to load config, initialize agents, and set up graph

## 3. LangGraph Nodes (Wrapping Existing Agents)

- [x] 3.1 Implement node_validate(): calls self._validate_request(), returns updated state
- [x] 3.2 Implement node_stage(): calls self.staging_agent.stage_component(), stores run_id, handles exceptions
- [x] 3.3 Implement node_explore(): calls explore_code(), stores exploration_results, handles exceptions
- [x] 3.4 Implement node_modernize(): calls modernize_code() for each file, stores modernized_code dict, handles exceptions
- [x] 3.5 Implement node_bdd_and_test(): calls generate_bdd_tests() and test orchestration, stores test_code, handles exceptions
- [x] 3.6 Implement node_verify(): calls run_tests_and_collect_coverage(), stores verification_results, always succeeds even if tests failed

## 4. Graph Edges & Conditional Routing

- [x] 4.1 Add edge: START → node_validate
- [x] 4.2 Add conditional edge: node_validate → (node_stage if valid, END if invalid)
- [x] 4.3 Add conditional edge: node_stage → (node_explore if success, node_verify if failed) [continue to verification on error]
- [x] 4.4 Add conditional edge: node_explore → (node_modernize if success, node_verify if failed)
- [x] 4.5 Add conditional edge: node_modernize → (node_bdd_and_test if success, node_verify if failed)
- [x] 4.6 Add conditional edge: node_bdd_and_test → node_verify (always)
- [x] 4.7 Add edge: node_verify → END

## 5. OpenTelemetry Instrumentation

- [x] 5.1 Create _setup_otel_tracer() method to initialize OTLP exporter and tracer provider
- [x] 5.2 Add TracerProvider setup with OTLPSpanExporter (default localhost:4317)
- [x] 5.3 Implement root span wrapping orchestrate_migration() method
- [x] 5.4 Wrap each node call with OTel span creation (span name = node name, attributes: stage_name, status, run_id)
- [x] 5.5 Add exception handling to mark spans as ERROR and record exception details
- [x] 5.6 Ensure span hierarchy: root > 6 node children

## 6. Langfuse Integration

- [x] 6.1 Add LangfuseSpanProcessor to tracer provider in _setup_otel_tracer()
- [x] 6.2 Load LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_ENDPOINT from environment variables
- [x] 6.3 Configure OTLP gRPC exporter to default endpoint (or env-configured)
- [x] 6.4 Add graceful error handling: if span export fails, log warning but continue orchestration
- [x] 6.5 Add trace metadata: request_id and component_name as root span attributes

## 7. Entry Point & API Compatibility

- [x] 7.1 Implement orchestrate_migration(request: MigrationRequest) → dict as public interface
- [x] 7.2 Ensure return dict structure matches V2: timestamp_start, timestamp_end, current_stage, completed_stages, status, artifacts, error_message
- [x] 7.3 Call graph.invoke(state) and capture final state
- [x] 7.4 Format and return results dict matching V2 structure

## 8. Audit Trail & Logging

- [x] 8.1 Implement _log_workflow(state) to write final state to orchestrator.jsonl (same format as V2)
- [x] 8.2 Call audit logging after graph.invoke() completes
- [x] 8.3 Ensure audit log captures both success and failure paths
- [x] 8.4 Preserve existing audit_dir configuration from config.yaml

## 9. Testing

- [x] 9.1 Create test_orchestrator_v3.py with unit tests for each node in isolation (mock agents)
- [x] 9.2 Test node_validate: valid request passes, invalid request fails
- [x] 9.3 Test node_stage: successful staging, staging failure, run_id generation
- [x] 9.4 Test node_explore: exploration success and failure paths
- [x] 9.5 Test node_modernize: modernization success and failure paths
- [x] 9.6 Test conditional edges: verify error state causes skip to verification
- [x] 9.7 Test orchestrate_migration() end-to-end with real agents on test component
- [x] 9.8 Test OpenTelemetry spans are created and attributes recorded
- [x] 9.9 Test Langfuse integration: spans are exported (optional: mock exporter)
- [x] 9.10 Test error handling: exceptions in agents do not crash orchestration

## 10. Documentation & Finalization

- [x] 10.1 Add docstrings to OrchestratorV3 class and all node functions
- [x] 10.2 Document MigrationState TypedDict fields and their purpose
- [x] 10.3 Add example usage: `orchestrator_v3 = OrchestratorV3(); results = orchestrator_v3.orchestrate_migration(request)`
- [x] 10.4 Create migration guide: "How to switch from OrchestratorV2 to OrchestratorV3" (no-op replacement)
- [x] 10.5 Document Langfuse setup: environment variables and dashboard access
- [x] 10.6 Test all 6 stages end-to-end and verify audit trail + Langfuse traces
- [x] 10.7 Verify V2 still works unchanged (no regressions)
