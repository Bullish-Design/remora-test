# Scaffold Code Review — `scripts/democtl.py` + `scripts/_lib/`

## Table of Contents

1. [Architecture & Module Structure](#1-architecture--module-structure)
2. [manifest.py](#2-manifestpy)
3. [paths.py](#3-pathspy)
4. [http.py](#4-httpppy)
5. [runtime.py](#5-runtimepy)
6. [commands.py](#6-commandspy)
7. [democtl.py (entrypoint)](#7-democtlpy-entrypoint)
8. [Test Coverage](#8-test-coverage)
9. [Summary](#9-summary)

---

## 1. Architecture & Module Structure

**Files:**
```
scripts/
  democtl.py          (125 lines) — CLI entrypoint: argparse + dispatch
  _lib/
    __init__.py        (7 lines)  — re-exports DemoConfigError, load_manifest, REPO_ROOT, DEFAULT_DEMO_ID
    manifest.py        (116 lines) — YAML loading, validation, fallback parser
    paths.py           (92 lines)  — path resolution, delete safety, REPO_ROOT
    http.py            (42 lines)  — HTTP helpers, health polling, JSON printing
    runtime.py         (255 lines) — process management, search stack, command prefix
    commands.py        (306 lines) — all cmd_* functions
```

**Verdict: Good.** The split follows clear domain boundaries. Each module has a single responsibility. The entrypoint is thin. Import graph is acyclic: `manifest` <- `paths` <- `http`, `runtime` <- `commands`.

**Issues:**

### 1.1 `_lib` is a relative import but used as a package from `democtl.py`

`democtl.py` uses `from _lib.commands import ...` which only works if `scripts/` is on `sys.path` (i.e., running `python scripts/democtl.py` from repo root, or `python democtl.py` from `scripts/`). This works because Python adds the script's directory to `sys.path`, but it means `democtl.py` cannot be imported as a module from elsewhere. Not a bug, but limits reusability.

**Severity: Low.** The entrypoint is meant to be run directly, not imported.

### 1.2 `__init__.py` re-exports are incomplete

`__init__.py` exports `DemoConfigError`, `load_manifest`, `REPO_ROOT`, `DEFAULT_DEMO_ID`. But consumers also need `resolve_paths`, `ensure_path_safe_for_delete`, `http_json`, etc. The `__init__.py` only serves as a convenience surface — no module actually imports from `_lib` directly (they all import from `_lib.paths`, `_lib.commands`, etc.), so the re-exports are vestigial.

**Severity: Cosmetic.** Either expand to be a real facade or remove the re-exports to avoid false expectations.

---

## 2. manifest.py

### 2.1 Fallback parser handles nested maps — good

The `_parse_simple_yaml` function now correctly handles one level of nesting (`requires: { lsp: true, ... }`). The section-tracking logic on lines 25-34 correctly switches into child mode when a key has an empty value followed by indented children.

### 2.2 Bug: `_parse_simple_yaml` doesn't handle YAML lists

The manifest currently doesn't use list values, but the `discovery_languages` or `discovery_paths` fields in remora configs do. If a future manifest adds a list field like:

```yaml
tags:
  - demo
  - baseline
```

The parser would interpret `- demo` as a key-value pair with key `- demo` and empty value, producing garbage. This is fine for manifests (which don't use lists), but could bite if anyone tries to reuse the parser for config files.

**Severity: Low.** The parser is explicitly scoped to manifest files. Add a comment noting the limitation.

### 2.3 `_validate_manifest` makes `repo_dir` optional for local — good

The conditional `if not _is_local_repo(manifest): required.add("repo_dir")` correctly implements the design decision from project 11.

### 2.4 `load_manifest` accepts `repo_root` as a parameter — good

This makes it testable without touching the filesystem constant. Nice improvement over the original global-dependent version.

### 2.5 Minor: `_parse_scalar` edge case with empty strings

`_parse_scalar("")` returns `""` (falls through to the final `return value`). This is correct but worth noting — an empty YAML value like `key:` will be parsed as `""` by the fallback parser, while `yaml.safe_load` would produce `None`. This inconsistency could cause subtle differences. The current manifests don't trigger this because all keys have explicit values.

**Severity: Low.** Document or align behavior.

---

## 3. paths.py

### 3.1 Symlink safety — good

`ensure_path_safe_for_delete` now checks `candidate.is_symlink()` before resolving, rejecting symlinks outright. This is a clean, conservative approach.

### 3.2 `delete_if_exists` handles race conditions

Lines 76-91 handle the case where the path disappears between the existence check and the actual deletion (TOCTOU). Uses `missing_ok=True` for unlink and catches `FileNotFoundError` for `rmtree`. Good defensive coding.

### 3.3 `resolve_paths` generates a default `repo_dir` for local demos

Line 31: `raw_repo_dir = str(manifest.get("repo_dir", f"/tmp/remora-demo-{manifest['demo_id']}"))`. This means even local demos get a `/tmp/remora-demo-*` path as a fallback, which is never used but is present in the returned dict. Harmless but slightly misleading — the `wipe` command already skips repo_dir deletion for local demos (commands.py:180), so the path is truly dead.

**Severity: Cosmetic.** Could return `None` for local demos instead.

### 3.4 `resolve_paths` return type is `dict[str, Path | str | int]`

This union-typed dict means every consumer has to cast: `Path(str(paths["project_root"]))`. Commands.py does this repeatedly (lines 36-38, 48, 60, 77-78, 161, 175, 177, 243-244, 255). Consider returning a dataclass or TypedDict instead to avoid the casting ceremony.

**Severity: Medium (readability).** A `ResolvedPaths` dataclass with typed fields would eliminate ~20 casts across commands.py and runtime.py.

---

## 4. http.py

### 4.1 Clean and minimal — good

42 lines, pure stdlib, no state. `http_json`, `wait_for_health`, `wait_for_raw_json`, `print_json`. Each does one thing.

### 4.2 `http_json` doesn't handle non-200 status codes

`urllib.request.urlopen` raises `urllib.error.HTTPError` for 4xx/5xx responses. This means `http_json` will throw on any non-2xx response. Callers in `commands.py` (`cmd_status`, `cmd_queries`, the verify summary) assume success and would get an unhandled exception with a cryptic urllib traceback instead of a useful error.

**Severity: Medium.** Either catch `HTTPError` and raise `DemoConfigError` with context, or document that callers should handle it. The harness's `RemoraClient._request` handles this correctly (line 74-76 in `_harness.py`), so this is only an issue for the scaffold's direct HTTP calls.

### 4.3 `wait_for_health` and `wait_for_raw_json` have identical structure

These two functions differ only in their success predicate (one checks `status == "ok"`, the other checks `isinstance(dict)`). Could be unified with a predicate parameter. Very minor.

**Severity: Cosmetic.**

---

## 5. runtime.py

### 5.1 `build_command_prefix` auto-detection — good

Falls back from explicit prefix → devenv detection → bare command. Clean three-tier resolution.

### 5.2 `_resolve_url_template` is a limited env-var substitution

Lines 86-95 handle `${VAR:-default}` and `${VAR}` patterns from YAML config values. This is used to resolve `search.embeddy_url` from the remora config. Works for the current use case but would silently fail on more complex patterns like `${VAR:-${OTHER}}` or `http://${HOST}:${PORT}`.

**Severity: Low.** Scoped to a known set of configs. Add a comment noting the limitation.

### 5.3 `_build_embeddy_config` creates temp files in `/tmp/`

Line 155: `tempfile.mkstemp(prefix="democtl-embeddy-config-", suffix=".yaml", dir="/tmp")`. The temp file is returned and cleaned up in `commands.py:304-305` (`embeddy_temp_config.unlink(missing_ok=True)`). This is correct, but if `cmd_verify` crashes before reaching the `finally` block (e.g., a `SIGKILL`), the temp file leaks. Acceptable for a CLI tool.

### 5.4 `start_search_stack` file handle leak on error path

Lines 196-197 open two log file handles. If `embeddy_proc` starts but fails health check (line 208), the code calls `stop_process(embeddy_proc)` and `mock_handle.close()` — but `embeddy_handle` was already closed on line 206. However, if the `Popen` call on line 199 itself raises (e.g., `FileNotFoundError` because `embeddy` isn't installed), `embeddy_handle` is never closed and `mock_handle` is never closed. The file handles would be GC'd eventually, but it's a minor resource leak.

**Severity: Low.** Use `with` blocks or a try/finally for the file handles.

### 5.5 Typo: `embedy_cfg` (missing 'd')

Line 182: `embedy_cfg = _build_embeddy_config(...)`. Used consistently through the function and returned on line 239, so it works — but the variable name is misspelled. Also appears in `commands.py:233` as `embeddy_temp_config` (correctly spelled), so the mismatch is only internal to `runtime.py`.

**Severity: Cosmetic.** Rename to `embeddy_cfg`.

### 5.6 `stop_process` signal handling — good

The SIGINT → terminate → kill cascade with timeouts is correct and robust. Handles the already-exited case first.

---

## 6. commands.py

### 6.1 `_manifest_requires` helper — good

Clean extraction of nested `requires.key` with safe dict checking. Used consistently in `cmd_verify`.

### 6.2 `cmd_setup` prints `start_command` that may be stale

Line 68-71: `print("start_command=python scripts/democtl.py start ...")`. This hardcodes the command format and doesn't include `--command-prefix` or `--bind` or `--log-events` flags that the user might need. It's informational output, but could be misleading.

**Severity: Low.** Consider omitting or making it reflect the actual flags used.

### 6.3 `cmd_verify` strict mode logic — good

Lines 197-216 correctly implement the `--strict` flag semantics: strict mode auto-enables `require_*` flags based on the manifest's `requires:` block, while individual `--require-*` flags override. This is the design from project 11.

### 6.4 `cmd_verify` calls Python runner directly — good

Lines 255-281 build a command to invoke `checks/runner.py` with full flag passthrough. The runner is invoked as a subprocess (not imported), which provides clean process isolation. The flag rendering via `_bool_flag` is consistent.

### 6.5 `cmd_verify` redundant API calls after check runner

Lines 285-296 fetch `/api/health`, `/api/nodes`, `/api/edges` again after the check runner completes, just to print a summary. The check runner already validates these endpoints. These calls could fail if the runtime was stopped between the runner finishing and the summary fetch (unlikely but possible in edge cases).

**Severity: Low.** The summary is useful for automated agents. Could catch exceptions here and degrade gracefully.

### 6.6 `cmd_wipe` skips repo_dir for local demos — good

Line 180: `if repo_url != "local" and (repo_dir.exists() or repo_dir.is_symlink())`. Correctly avoids touching repo_dir for local demos. Matches the design decision from project 11.

### 6.7 Excessive Path casting throughout

As noted in 3.4, every `paths[...]` access is wrapped in `Path(str(...))`. This pattern appears ~20 times in commands.py. Example from line 36-38:
```python
demo_root = Path(str(paths["demo_root"]))
project_root = Path(str(paths["project_root"]))
config_path = Path(str(paths["config_path"]))
```

**Severity: Medium.** A `ResolvedPaths` dataclass would clean this up significantly.

---

## 7. democtl.py (entrypoint)

### 7.1 Clean dispatch — good

125 lines. Argparse definition + dispatch to `cmd_*` functions. The `DemoConfigError` catch in `__main__` provides user-friendly error messages.

### 7.2 `parser.error()` unreachable

Line 116: `parser.error(f"Unknown command: {args.command}")`. Since `command` uses `choices=`, argparse will reject unknown commands before reaching `main()`. This line can never execute.

**Severity: Cosmetic.** Defensive but dead code.

### 7.3 All args are global

Every argument is defined on the single parser, so every command sees every flag. `--run-guardrails` is only relevant to `verify`, `--clean-workspace` only to `setup`, `--log-events` only to `start`, etc. This means `democtl start --run-guardrails` silently accepts and ignores the flag.

**Severity: Low-Medium.** Consider subparsers (`parser.add_subparsers()`) to scope flags per command. This prevents confusing silent ignores and improves `--help` output per command.

---

## 8. Test Coverage

### 8.1 Contract tests are structural, not behavioral

`test_democtl_contracts.py` checks that string literals exist in source files (e.g., `'"setup"' in text`). These are fragile — any refactoring of string formatting would break them. They don't test actual behavior.

**Severity: Medium.** Add behavioral tests: call `main(["setup", "--demo", "00_repo_baseline"])` and assert the return code and output. The manifest loading and path resolution logic is rich enough to warrant proper unit tests with fixtures.

### 8.2 No unit tests for `_lib` modules directly

There are no tests for:
- `_parse_simple_yaml` (edge cases: nested maps, empty values, comments, special characters)
- `ensure_path_safe_for_delete` (symlinks, banned paths, edge cases)
- `resolve_paths` (profile selection, local vs remote, missing keys)
- `build_command_prefix` (devenv present/absent, explicit prefix)
- `_resolve_url_template` (env var substitution patterns)

These are all testable pure functions that would benefit from dedicated unit tests.

**Severity: Medium-High.** The safety-critical functions (path deletion, manifest validation) especially need tests.

### 8.3 Manifest/isolation tests are solid

`test_demo_manifests.py` and `test_demo_isolation_contracts.py` correctly validate manifest structure, uniqueness constraints, and safety invariants. These are well-designed contract tests.

---

## 9. Summary

### What's Good
- Clean module boundaries with single responsibilities
- Symlink safety and TOCTOU-aware deletion
- `--strict` mode correctly driven by manifest `requires:` block
- Auto-detection of devenv with fallback to bare commands
- Search stack config derived from remora config rather than hardcoded
- Proper process lifecycle management (SIGINT → terminate → kill)

### What Needs Attention

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 1 | `resolve_paths` returns untyped dict — causes ~20 casts in commands.py | Medium | 30 min |
| 2 | No unit tests for `_lib` module functions | Medium-High | 1-2 hr |
| 3 | `http_json` doesn't handle non-200 responses | Medium | 15 min |
| 4 | All CLI args are global (no subparsers) | Low-Med | 45 min |
| 5 | Contract tests are string-match based, not behavioral | Medium | 1 hr |
| 6 | File handle leak in `start_search_stack` error path | Low | 15 min |
| 7 | Typo: `embedy_cfg` → `embeddy_cfg` | Cosmetic | 1 min |
| 8 | Dead code: `parser.error()` unreachable | Cosmetic | 1 min |
