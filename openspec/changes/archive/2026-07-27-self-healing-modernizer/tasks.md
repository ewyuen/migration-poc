## 1. Create Compiler Helpers Module

- [x] 1.1 Create `agents/compiler_helpers.py` with `CompilerError` dataclass
- [x] 1.2 Implement `parse_compiler_errors(build_output: str) -> List[CompilerError]` using regex pattern for MSBuild errors
- [x] 1.3 Implement `enrich_errors_with_hints(errors: List[CompilerError], hints_dict: dict) -> str` to format errors for LLM prompt
- [x] 1.4 Add unit tests for error parsing (test valid/invalid error lines, edge cases like missing brackets)
- [x] 1.5 Test regex against real `dotnet build` output from sample .csproj files

## 2. Create Migration Hints Configuration

- [x] 2.1 Create `migration_hints.json` in project root with initial CSxxxx error codes and hints
- [x] 2.2 Include hints for common errors: CS0103, CS0246, CS0117, CS1061 (from prototype)
- [x] 2.3 Add at least 5 additional hints based on .NET Framework → .NET 10 migration patterns
- [x] 2.4 Create function in `compiler_helpers.py` to load hints from JSON and provide fallback for unknown codes

## 3. Refactor Modernizer Agent

- [x] 3.1 Rename current `modernize_code()` function to `_legacy_modernize_code()` (internal)
- [x] 3.2 Create `DotNetMigrationAgent` class with `__init__(project_dir, csproj_path, max_retries=4)`
- [x] 3.3 Implement `run_dotnet_build() -> Tuple[bool, List[CompilerError]]` method
- [x] 3.4 Implement `generate_repair_prompt(file_content: str, errors: List[CompilerError]) -> str` method
- [x] 3.5 Implement `migrate_file(target_file_path, initial_code, llm_call_func) -> bool` with full retry loop
- [x] 3.6 Add git revert logic when max retries exceeded (revert file via `git checkout`)
- [x] 3.7 Add structured logging of each retry attempt (attempt #, errors, result) to stdout and/or log file
- [x] 3.8 Update signature of `modernize_code()` wrapper to accept `legacy_code, domain_logic, exploration, project_dir, csproj_path`

## 4. Update Orchestrator

- [x] 4.1 Update `orchestrator.py` to pass `project_dir` and `csproj_path` to `modernize_code()` call
- [x] 4.2 Add error handling around modernizer step: catch exceptions from failed migrations
- [x] 4.3 Log modernizer failures with context (file path, attempts made, compiler errors)
- [x] 4.4 Decide orchestrator behavior on modernizer failure: skip file, retry, or abort pipeline
- [x] 4.5 Update step label from "[STEP 3/6] MODERNIZER AGENT" to include build time estimate

## 5. Integration Testing

- [x] 5.1 Test with legacy .cs file from `legacy-code/TestService/` (if available)
- [x] 5.2 Verify retry loop: manually create code with an intentional error, confirm agent fixes it
- [x] 5.3 Test max retries exceeded: create code that cannot compile, confirm git revert and exception
- [x] 5.4 Measure build time per file and verify acceptable performance (<30 seconds per file)
- [x] 5.5 Test with multi-file project: ensure file errors are correctly attributed
- [x] 5.6 Test hint enrichment: verify hints appear in LLM prompts and help resolve errors

## 6. Documentation & Polish

- [x] 6.1 Add docstrings to all new functions and classes (follow existing style)
- [x] 6.2 Document `migration_hints.json` format and how to extend it
- [x] 6.3 Update `README.md` or project docs: note that modernizer step now includes compilation verification
- [x] 6.4 Add comments in modernizer explaining key decisions (e.g., why regex over Roslyn, retry limit logic)
- [x] 6.5 Create or update `IMPLEMENTATION_LOG.md` with details of first run (errors encountered, hints added, success rate)

## 7. Validation & Handoff

- [x] 7.1 Run full orchestrator pipeline on test case and verify modernizer output compiles
- [x] 7.2 Verify orchestrator gracefully handles modernizer exceptions
- [x] 7.3 Check git history: no uncommitted changes from failed migration attempts (all reverted cleanly)
- [x] 7.4 Confirm all specs are satisfied (review each scenario in compile-verification, error-enrichment, self-healing-migration)
