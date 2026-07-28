## 1. Staging agent: replace branch/commit with run_id

- [x] 1.1 In `staging_agent.py`, replace `_generate_branch_name()` with a `_generate_run_id(component_name)`. Implemented as `f"{sanitized_component_name}-{MMDDYY}-{HHMMSS}-{ms}"` (millisecond suffix added, not just `HHMMSS` as originally planned) — a smoke test (see task 4.3) showed two `stage_component()` calls in quick succession produced identical `run_id`s at second-level precision, and `copy_component()` silently `rmtree`s an existing destination before copying, so a collision would have caused silent data loss. Still no collision check against git/filesystem, consistent with the original "unique by construction" decision — the precision was just insufficient.
- [x] 1.2 Remove `create_feature_branch()` and its `git rev-parse --verify` / `git checkout -b` logic entirely.
- [x] 1.3 Remove `create_initial_commit()` and its `git add` / `git commit` logic entirely.
- [x] 1.4 Update `copy_component()` (and its callers) to copy into `legacy-code/<run_id>` instead of `legacy-code/<component_name>`.
- [x] 1.5 Update `create_metadata_file()` to accept and record `run_id` in place of `branch_name` in `.staging_metadata.json`.
- [x] 1.6 Update `stage_component()` to: generate `run_id`, copy component, validate, write metadata — no branch/commit steps — and return `run_id` in its results dict in place of `branch_name`.

## 2. Orchestrator: thread run_id through the pipeline

- [x] 2.1 In `orchestrator_v2.py`, update `orchestrate_migration()` to capture `run_id = staging_results["run_id"]` right after the staging stage completes.
- [x] 2.2 Update `orchestrate_migration()` so every subsequent stage (exploration, modernization, BDD generation, test writing, verification, output saving) receives and uses `run_id` for path construction, while continuing to pass `component_name` unchanged for anything codegen-related (assembly name, root namespace, `.csproj` filename, test class names). `_save_output()` and `_explore_component()` signatures updated to take `run_id`.
- [x] 2.3 Updated all `os.path.join("legacy-code", ...)` and `os.path.join("migrated-output", ...)` call sites (staging validation excluded — `legacy-src` stays component-name-scoped since it's the unmodified source) to use `run_id` instead of `request.component_name`.
- [x] 2.4 Removed `_cleanup_component_dirs()` and its call at the start of `orchestrate_migration()` (also dropped the now-unused `shutil` import).
- [x] 2.5 `_stage_component()`'s error path no longer references the removed `create_branch` step; it now scans `steps` for the first failed step's error. `_print_summary()` now reads `run_id` from `state.artifacts["staging"]` instead of printing a component-name-only path.

## 3. Downstream agent modules

- [x] 3.1 In `test_orchestrator.py`, add a `run_id` parameter to `execute()`, `_test_file_path()`, `_map_errors()`, and `_comment_out_blocks()`, replacing the bare `component_name` used for path construction; keep `component_name` for any codegen-facing logic. Also added `run_id` to `test_compiler.run_test_compiler()` (path-building helper not explicitly named in this task but required by the same chain) — `tests_dir` now uses `run_id`, while `generate_test_csproj()`'s `component_name` argument is untouched (it names the `.csproj` file/ProjectReference, not a path).
- [x] 3.2 In `verifier.py`, add a `run_id` parameter to `run_tests_and_collect_coverage()` for building `component_dir`. `_write_reports()`'s per-run `tests_md_path` now uses `run_id` (it lives inside the run-scoped tests directory); the shared `migrated-output/result-log/{component_name}_*` filenames are left unchanged (out of scope).
- [x] 3.3 In `test_writer_stage.py`, add a `run_id` parameter to `TestWriterStage.execute()` for building `component_dir`, replacing the bare `component_name` used there.

## 4. Verification

- [x] 4.1 (partial) Verified via a staging-only smoke test (synthetic component, no git repo present, no dotnet/LLM involved): `StagingAgent.stage_component()` copies into `legacy-code/<run_id>` with no git subprocess calls at all (the branch/commit code paths no longer exist). Full end-to-end pipeline run (modernization + test writing + verification stages, which call an LLM and `dotnet`) was **not** run — this repo currently has no `legacy-src/` component and no dotnet/LLM credentials available in this environment. Recommend the user run one real migration end-to-end to confirm stages 3-6 behave correctly with `run_id`-scoped paths.
- [ ] 4.2 Not independently run (depends on stage 4's LLM-generated output, see 4.1). Verified statically instead: `assembly_name`, `root_namespace`, and `csproj_name` in `orchestrator_v2.py` are all still derived from `request.component_name`, never `run_id` (confirmed by inspection of every edited call site). Recommend spot-checking actual generated code on a real run.
- [x] 4.3 Verified via the same smoke test: staging the same synthetic component twice in immediate succession (worst case for collision) produced two distinct `run_id`s and two independent `legacy-code/<run_id>` directories, with neither overwriting the other. This required fixing `_generate_run_id()` to include millisecond precision (see note on task 1.1) — second-level precision alone collided when called twice in a tight loop.
- [x] 4.4 Verified via the same smoke test: `.staging_metadata.json` contains `run_id` and has no `branch_name` key.
