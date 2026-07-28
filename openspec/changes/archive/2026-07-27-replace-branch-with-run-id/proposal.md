## Why

Today the staging agent isolates each migration by creating a git branch (`{component}-migration-{YYYYMMDD}`, with a `-{HHMMSS}` suffix appended on collision) and checking it out via `git checkout -b`. This mutates whatever branch the user currently has checked out, and the collision suffix is confusing when it silently appears. Replacing branch-based isolation with a per-run directory (`run_id`) removes both problems: the user's active checkout is never touched, and every run gets a predictable, always-unique name.

## What Changes

- **BREAKING**: Staging agent no longer creates a git branch or commits the legacy-code copy. `create_feature_branch()` and `create_initial_commit()` are removed from `staging_agent.py`.
- Staging agent generates a `run_id` (`{component}-{MMDDYY}-{HHMMSS}`) once per migration run, always timestamped (no conditional collision handling needed since it's unique by construction).
- `run_id` is threaded as a distinct parameter — never substituted for `component_name` — through every module that builds `legacy-code/` or `migrated-output/` paths: `staging_agent.py`, `orchestrator_v2.py`, `test_orchestrator.py`, `verifier.py`, `test_writer_stage.py`. `component_name` continues to drive codegen identifiers (assembly name, root namespace, `.csproj` filename, test class names) untouched.
- Component directories move from `legacy-code/<component>` and `migrated-output/<component>/...` to `legacy-code/<run_id>` and `migrated-output/<run_id>/...`.
- `.staging_metadata.json` records `run_id` in place of `branch_name`.
- `orchestrator_v2._cleanup_component_dirs()`, which wiped `legacy-code/<component>` and `migrated-output/<component>` at the start of every run to avoid path collisions, is removed — collisions are no longer possible once directories are run-scoped, so old run directories simply accumulate (cleanup/retention is explicitly out of scope for this change).
- `verifier.py`'s shared `migrated-output/result-log/{component_name}_*` report files are left as-is (not run-scoped) — out of scope for this change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `legacy-component-staging`: staging agent no longer creates a git branch or commits the copy; it generates a `run_id` and copies the component into a run-scoped subdirectory instead.
- `agent-orchestration`: orchestrator no longer creates or manages git branches for migrations; the staging directive and downstream stage sequencing use `run_id`-scoped paths instead of bare component-name paths.

## Impact

- Affected code: `migration-poc/agents/staging_agent.py`, `migration-poc/orchestrator_v2.py`, `migration-poc/agents/test_orchestrator.py`, `migration-poc/agents/verifier.py`, `migration-poc/agents/test_writer_stage.py`.
- Affected specs: `legacy-component-staging`, `agent-orchestration`.
- No downstream consumers depend on the git branch (no `git push` / PR automation exists in this codebase today), so removing it is functionally safe.
- Any external tooling or docs that assume `legacy-code/<component>` / `migrated-output/<component>` as fixed paths (rather than `run_id`-scoped) will need updating.
