## Context

The migration pipeline (`orchestrator_v2.py`) runs one component per CLI invocation, always `os.chdir`'d to the repo root once at startup, with every subsequent stage resolving paths relative to that single working directory. Isolation between runs is currently provided by `staging_agent.py`'s `create_feature_branch()`, which does `git checkout -b {component}-migration-{YYYYMMDD}` (appending `-{HHMMSS}` if that branch already exists) and `create_initial_commit()`, which commits the legacy-code copy onto that branch.

This has two problems in practice:
1. `git checkout -b` mutates whichever branch the user has actively checked out in their working copy — there is no isolation from the user's own in-progress work.
2. The collision-suffix behavior (append current time only if the plain name already exists) produces branch names that are inconsistent run-to-run and confusing to read.

No other stage in the pipeline reads git branch state, diffs against a branch, or pushes/opens a PR — `git` usage is entirely confined to `staging_agent.py`. The branch today functions only as a container for one commit; nothing downstream depends on it.

## Goals / Non-Goals

**Goals:**
- Remove git branch creation and the checkout side effect from the staging stage.
- Give every migration run a unique, predictable identifier (`run_id`) used consistently for on-disk paths.
- Keep `component_name` pure for anything that ends up in generated code (assembly name, root namespace, `.csproj` filename, test class names) — `run_id` must never leak into codegen identifiers.

**Non-Goals:**
- Retention/cleanup policy for old run directories (explicitly deferred).
- Run-scoping `verifier.py`'s shared `migrated-output/result-log/{component_name}_*` report files (they remain last-run-wins).
- Enabling concurrent/parallel migration runs (`allow_parallel: false` in `migration_config.yaml` is unaffected by this change; run-scoped directories are a prerequisite for parallelism but this change does not turn parallelism on).
- Git worktrees (considered and rejected — see Decisions).

## Decisions

### Directory-per-run instead of git worktree

**Chosen:** Namespace `legacy-code/` and `migrated-output/` by a per-run `run_id`, with no git branch or worktree involved at all.

**Alternative considered — git worktree:** `git worktree add` would isolate each run's working directory without mutating the user's active checkout, while keeping git history per run. Rejected because it adds a second location (worktree path) that must also be unique and cleaned up, doesn't remove the branch-naming problem (a branch is still created, just checked out elsewhere), and requires the orchestrator to `chdir` into a directory outside the repo it currently assumes it's chdir'd into for the entire process — touching the same breadth of files as the chosen approach for strictly more mechanical complexity (worktree lifecycle, shared audit-log location decision, `git worktree remove` on cleanup). Directory namespacing achieves the same isolation with less machinery.

### Drop git branch and commit entirely, rather than keep a lightweight commit

**Chosen:** No git operations remain in staging. `create_feature_branch()` and `create_initial_commit()` are removed.

**Alternative considered — keep a lightweight commit, drop only the branch:** Committing the legacy-code copy without creating a branch would land that commit directly on whichever branch the user currently has checked out. Before this change, commits were "free" because they landed on a disposable branch; without a branch, every migration run would leave a permanent commit in the user's real branch history. Rejected — `.staging_metadata.json` (already written per run, recording manifest, checksums, and now `run_id`) serves as the audit record without forcing a git commit into existence.

### `run_id` as a distinct parameter, not a repurposed `component_name`

**Chosen:** Compute `run_id = f"{component_name}-{MMDDYY}-{HHMMSS}"` once per run and thread it as a new, separate parameter through every function that builds a `legacy-code/` or `migrated-output/` path. `component_name` is never reassigned or shadowed.

**Alternative considered — reuse `component_name`:** Simpler to thread (one fewer parameter per call site) but risks the timestamp leaking into codegen — `orchestrator_v2.py` currently derives `assembly_name`, `root_namespace`, and the `.csproj` filename directly from `component_name` (lines ~350-355). Reusing it for the directory name would require carefully re-deriving the "clean" component name at each of those call sites, reintroducing the exact class of bug (stray timestamp in generated identifiers) that a distinct parameter avoids by construction. Rejected in favor of the distinct parameter, which costs one extra argument per call site but eliminates the failure mode entirely.

### Always timestamp `run_id`; no conditional collision handling

**Chosen:** `run_id` always includes the full timestamp (`MMDDYY-HHMMSS`), generated unconditionally — no "check if it exists, append suffix only on collision" logic like today's branch naming.

**Rationale:** The conditional-suffix behavior is exactly what made the old branch names confusing (same component migrated twice in a day produces two differently-shaped names depending on timing). An unconditional, always-unique scheme is simpler to implement and reason about, and removes the `git rev-parse --verify` existence check entirely.

### Remove `_cleanup_component_dirs()`'s upfront wipe

**Chosen:** `orchestrator_v2._cleanup_component_dirs()` (which deletes `legacy-code/<component>` and `migrated-output/<component>` at the start of every run) is removed rather than adapted, since run-scoped directories can never collide with a prior run's directory.

## Risks / Trade-offs

- **[Risk] Losing git-level audit trail of what changed per run** → Mitigated by `.staging_metadata.json`, which already records source path, timestamp, manifest (file list + checksums), and now `run_id` in place of `branch_name`.
- **[Risk] Disk usage grows unbounded since old run directories are never cleaned up** → Accepted as explicitly out of scope; noted in proposal.md for a future change.
- **[Risk] `run_id` leaking into a codegen identifier if a future call site mixes it up with `component_name`** → Mitigated by keeping them as distinct, never-aliased parameters throughout; code review should watch for any new path-building call site that isn't handed `run_id` explicitly.
- **[Trade-off] `verifier.py`'s `result-log` reports remain shared/last-run-wins** → Acceptable for now since it's a pre-existing behavior (two runs of the same component already overwrote each other's reports before this change); revisit if run history for verification reports becomes valuable.

## Migration Plan

- Single-PR change; no data migration or rollout sequencing needed since this only affects local, ephemeral pipeline-run directories (not committed artifacts).
- Rollback is a straightforward revert — no persisted state format changes outside `.staging_metadata.json`'s field rename (`branch_name` → `run_id`), which is not read by any other stage.

## Open Questions

None outstanding — all decisions confirmed during exploration.
