## Why

The current OrchestratorV2 manually threads workflow state through 6 sequential stages using imperative control flow and hand-managed dictionaries. This makes the workflow topology implicit (hard to visualize), state contracts unclear (everything is a dict), and observability difficult (manual logging only). LangGraph makes the workflow explicit as a directed acyclic graph with clear state schemas and built-in callback hooks, enabling proper observability with OpenTelemetry and Langfuse. This change improves maintainability, debuggability, and monitoring without touching any existing agents.

## What Changes

- **New OrchestratorV3** (alongside V2, not replacing it) using LangGraph's StateGraph to coordinate the 6-stage migration pipeline
- **State schema** as TypedDict with only fields needed per-node (minimal coupling)
- **Workflow edges** with conditional logic: continue to verification even on failures, skip downstream stages on critical errors
- **OpenTelemetry instrumentation** at node level (each stage produces a span with duration, status, error details)
- **Langfuse integration** via OTel span processor to subscribe to and visualize the full workflow trace
- **Same entry point** as V2 (`orchestrate_migration(request)`) for drop-in compatibility
- **Audit trail** preserved to `orchestrator.jsonl` alongside OTel traces

## Capabilities

### New Capabilities
- `langgraph-orchestration`: LangGraph-based StateGraph orchestrating the 6-stage migration workflow with explicit nodes, edges, and conditional branching
- `opentelemetry-instrumentation`: Node-level OTel spans wrapping each orchestration stage with tracing metadata and error handling
- `langfuse-integration`: Langfuse subscription to OTel traces for end-to-end workflow observability and visualization

## Impact

- **No changes to existing agents**: StagingAgent, ExplorerAgent, ExtractorAgent, TestWriterAgent, modernizer, verifier all remain unchanged
- **New module**: `migration-poc/agents/orchestrator_v3.py` (can coexist with orchestrator_v2.py)
- **New dependencies**: `langgraph`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, `langfuse` (added to requirements.txt)
- **No breaking changes**: OrchestratorV3 is additive; existing code calling OrchestratorV2 continues to work
- **Observability improvement**: Full trace visibility via Langfuse dashboard
