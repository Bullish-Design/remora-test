# Demo Improvements — Audit Findings and Action Items

Full audit of remora-test repo (concept, scaffold, demo 00) with cross-reference against remora-v2.

## Table of Contents

1. [Concept Issues (DEMO_OVERVIEW.md)](#1-concept-issues) — plan-vs-reality drift, dead fields, unpinned dep, missing --strict
2. [Scaffold Issues (democtl.py)](#2-scaffold-issues) — monolith refactor, YAML fallback, devenv coupling, search stack hardcoding, symlink safety
3. [Demo 00 Issues (00_repo_baseline)](#3-demo-00-issues) — shell-to-Python conversion, tool deps, file mutation, cleanup gaps, missing CLAUDE.md
4. [Prioritized Action Items](#4-prioritized-action-items) — ranked table with effort estimates
5. [Items NOT Worth Fixing](#5-items-not-worth-fixing) — acknowledged but intentionally deferred

---

## 1. Concept Issues

Issues with the design plan in `DEMO_OVERVIEW.md` vs. what was actually built.

### 1.1 `repo_dir` is vestigial for local demos

**Severity: Medium (confusing for new demo authors)**

Demo 00 uses `repo_url: local` and `project_root: .` — no clone happens. Yet `repo_dir: /tmp/remora-demo-00-repo-baseline` is a required manifest field. For local demos this field is dead weight. Future demo authors will wonder what to put here and whether it matters.

**Action:** Make `repo_dir` optional when `repo_url: local`. Skip the `/tmp/remora-demo-*` path validation for local demos. Update manifest validation in `democtl.py` accordingly.

### 1.2 No pinned remora-v2 revision

**Severity: High (silent breakage risk)**

The overview explicitly calls for "pinning `remora-v2` revision for the demo cycle." The actual `pyproject.toml` uses:

```toml
remora = { git = "https://github.com/Bullish-Design/remora-v2.git", rev = "main" }
```

Any breaking change on `main` silently breaks all demos with no way to bisect.

**Action:** Pin `rev` to a specific commit SHA or tag. Document the pinning policy (e.g., "update after each demo cycle, not continuously").

### 1.3 `verify --strict` not implemented as designed

**Severity: Medium (operator confusion)**

The overview specifies a single `--strict` flag where "no skips allowed for scoped capabilities." The actual implementation uses individual flags (`--require-search`, `--require-lsp-bridge`, `--require-overflow`) plus corresponding env vars. There is no unified `--strict` mode.

**Action:** Add a `--strict` flag that sets all `--require-*` flags based on the manifest's `requires:` block. Keep individual flags for granular control.

---

## 2. Scaffold Issues

Issues with `scripts/democtl.py` — the shared control plane.

### 2.1 Refactor `democtl.py` into `scripts/_lib/` modules

**Severity: Medium (maintainability, reuse)**

The overview proposed four library modules under `scripts/_lib/`. The actual implementation is a single 620-line `democtl.py`. This should be refactored now rather than waiting for organic growth — the logical seams are already clear and splitting now makes each module independently testable.

**Proposed layout:**

```
scripts/
  democtl.py                  # CLI entrypoint only (argparse + dispatch)
  _lib/
    __init__.py
    manifest.py               # _load_manifest, _parse_simple_yaml, _parse_scalar, DemoConfigError
    paths.py                  # _resolve_paths, _ensure_path_safe_for_delete, REPO_ROOT
    http.py                   # _http_json, _wait_for_health, _wait_for_raw_json, _print_json
    runtime.py                # _start_runtime_process, _start_search_stack, _stop_process
    commands.py               # cmd_setup, cmd_start, cmd_status, cmd_queries, cmd_cleanup, cmd_wipe, cmd_verify
```

**Mapping from current code:**

| Current location | Target module | Functions |
|---|---|---|
| `democtl.py:33-114` | `_lib/manifest.py` | `_load_manifest`, `_parse_simple_yaml`, `_parse_scalar`, `DemoConfigError` |
| `democtl.py:117-199` | `_lib/paths.py` | `_resolve_paths`, `_ensure_path_safe_for_delete`, `REPO_ROOT`, `DEFAULT_DEMO_ID` |
| `democtl.py:147-180` | `_lib/http.py` | `_http_json`, `_wait_for_health`, `_wait_for_raw_json`, `_print_json` |
| `democtl.py:365-485` | `_lib/runtime.py` | `_start_runtime_process`, `_start_search_stack`, `_stop_process` |
| `democtl.py:202-361,488-561` | `_lib/commands.py` | All `cmd_*` functions |
| `democtl.py:563-620` | `democtl.py` | `_build_parser`, `main` (thin entrypoint) |

**Benefits:**
- Each module can be tested in isolation (manifest parsing, path safety, HTTP helpers).
- Future demos or tools can import `_lib.manifest` or `_lib.http` without importing the entire CLI.
- Matches the overview's original design intent.

**Action:** Extract functions into `scripts/_lib/` modules following the mapping above. Update imports in `democtl.py` to re-export from `_lib`. Update existing unit tests (`test_democtl_contracts.py`) to reflect the new structure.

### 2.2 YAML fallback parser can't handle nested maps

**Severity: High (broken fallback path)**

`_parse_simple_yaml()` is a regex-based line parser that handles flat `key: value` pairs. Demo 00's manifest includes a nested `requires:` block:

```yaml
requires:
  lsp: true
  search: true
  web: true
```

If `pyyaml` isn't installed (it's not in `remora-test`'s direct deps — only pulled transitively via remora), the fallback parser will either skip this block or produce garbage. Since `requires` drives `verify --strict` behavior, this is a real functional risk.

**Action:** Either (a) add `pyyaml` to `remora-test`'s direct dependencies, or (b) extend `_parse_simple_yaml()` to handle one level of nesting. Option (a) is simpler and more reliable.

### 2.3 `start` command hardcodes `devenv shell --`

**Severity: Medium (portability blocker)**

The `start` command builds the subprocess command as `["devenv", "shell", "--", "remora", "start", ...]`. Anyone using a plain venv, pip install, or container can't use `democtl start` without modification.

**Action:** Detect whether `devenv` is available. If not, fall back to bare `remora start`. Alternatively, accept a `--command-prefix` flag (e.g., `--command-prefix "devenv shell --"`) with auto-detection as default.

### 2.4 Search stack ports/paths are hardcoded

**Severity: Low-Medium**

`_start_search_stack()` hardcodes port 8585 (embeddy) and 8586 (mock embedder), and constructs paths to `mock_embedder_server.py` and the `embeddy` binary from fixed locations. If a demo needs different ports (e.g., two demos running simultaneously), this breaks.

**Action:** Pull search stack ports from the manifest's config (the `search.embeddy_url` field already has the port). Add `mock_embedder_port` to the manifest schema if needed.

### 2.5 Symlink safety gap in `_ensure_path_safe_for_delete()`

**Severity: Medium (data loss vector)**

The safety check validates that the path starts with `/tmp/remora-demo-*` or is a known workspace subpath. But it doesn't resolve symlinks first. A symlink at `/tmp/remora-demo-foo/data -> /home/user/important` would pass the prefix check, and `shutil.rmtree` follows symlinks by default.

**Action:** Add `Path.resolve()` before the prefix check. Alternatively, use `shutil.rmtree` with `follow_symlinks=False` (Python 3.12+) or check `os.path.islink()` on each entry.

---

## 3. Demo 00 Issues

Issues specific to the `demo/00_repo_baseline/` demo.

### 3.1 Convert shell scripts to Python check modules

**Severity: High (maintainability, consistency, portability)**

There are 18 shell scripts under `demo/00_repo_baseline/scripts/`, totaling ~1400 lines of bash. They share significant boilerplate (health checks, event polling, JSON parsing via `curl | jq`, temp dir management, cleanup traps) and have external tool dependencies (`curl`, `jq`, `rg`) that aren't declared. Converting to Python eliminates these problems.

**Current scripts and their patterns:**

| Script | Lines | External deps | Core pattern |
|---|---|---|---|
| `run_demo_checks.sh` | 56 | curl | Orchestrator: sequential test runner with health gates |
| `test_demo_runtime.sh` | 50 | curl, jq | API contract: GET endpoints + POST /api/chat |
| `test_virtual_agents.sh` | 168 | curl, jq | Event polling: before/after count comparison |
| `test_reflection_pipeline.sh` | 110 | curl, jq | Event polling: correlation-scoped causal chain |
| `test_subscription_filters.sh` | 47 | curl, jq, devenv, python | Hybrid: Python unit test wrapped in bash |
| `test_proposal_flow.sh` | 59 | curl, jq, python | API + event polling: trigger -> wait -> reject |
| `test_proposal_accept_flow.sh` | 162 | curl, jq, python | API + event polling + file mutation: trigger -> wait -> accept -> verify |
| `test_sse_contract.sh` | 69 | curl, jq, rg | SSE: replay + resume with token matching |
| `test_cursor_focus.sh` | 64 | curl, jq | API + event polling: POST /api/cursor -> verify event |
| `test_relationship_tools.sh` | 56 | curl, jq | Event polling: tool execution evidence |
| `test_multilang_discovery.sh` | 46 | curl, jq, rg, devenv | CLI: `remora discover` output parsing |
| `test_search.sh` | 171 | curl, jq, rg, devenv | CLI + API: `remora index` -> POST /api/search |
| `test_lsp_startup.sh` | 70 | rg, devenv, python | CLI: `remora lsp` with timeout and log parsing |
| `test_lsp_event_bridge.sh` | 30 | devenv, python | Wrapper: delegates to `lsp_event_bridge_probe.py` |
| `test_runtime_guardrails.sh` | 51 | curl, jq | Burst: concurrent /api/chat + overflow metrics |
| `test_remora.sh` | 30 | curl, jq | Informational smoke dump (no assertions) |
| `test_ui_dependencies.sh` | 23 | curl, rg | Diagnostic: CDN reachability check |
| `install_local_ui_assets.sh` | 42 | python, sed | Utility: patch CDN URLs to local vendor |

**Proposed Python structure:**

```
demo/00_repo_baseline/
  checks/
    __init__.py
    _harness.py               # shared: RemoraClient, event polling, health wait, check result types
    check_runtime.py           # health, nodes, edges, events, chat, virtual count
    check_virtual_agents.py    # observer activation via before/after event counts
    check_reflection.py        # primary -> reflection -> turn_digested -> companion chain
    check_subscriptions.py     # path_glob matching semantics (already partly Python)
    check_proposal_reject.py   # trigger rewrite -> wait for proposal -> reject
    check_proposal_accept.py   # trigger rewrite -> wait -> accept -> verify file + events
    check_sse.py               # SSE replay + resume with token matching
    check_cursor.py            # POST /api/cursor -> verify mapping + event
    check_relationships.py     # tool execution evidence (show_dependencies)
    check_discovery.py         # remora discover output parsing
    check_search.py            # remora index -> /api/search contract
    check_lsp_startup.py       # remora lsp with timeout
    check_lsp_bridge.py        # absorb lsp_event_bridge_probe.py
    check_guardrails.py        # burst chat + overflow metrics
    runner.py                  # orchestrator: discover + run checks in sequence
  scripts/
    mock_embedder_server.py    # keep as-is (FastAPI server, not a check)
    install_local_ui_assets.py # convert from .sh
    lsp_event_bridge_probe.py  # keep as-is OR absorb into check_lsp_bridge.py
```

**Shared harness (`_harness.py`) consolidates all the repeated boilerplate:**

```python
# Core primitives every check currently reimplements in bash:
class RemoraClient:
    """HTTP client wrapping urllib for the remora API."""
    def __init__(self, base_url: str, timeout: float = 5.0): ...
    def health(self) -> dict: ...
    def nodes(self) -> list[dict]: ...
    def edges(self) -> list[dict]: ...
    def events(self, limit: int = 500, event_type: str | None = None) -> list[dict]: ...
    def chat(self, node_id: str, message: str) -> dict: ...
    def cursor(self, file_path: str, line: int, character: int = 0) -> dict: ...
    def search(self, query: str, collection: str = "code", top_k: int = 5, mode: str = "hybrid") -> dict: ...
    def proposals(self) -> list[dict]: ...
    def proposal_diff(self, node_id: str) -> dict: ...
    def proposal_accept(self, node_id: str) -> dict: ...
    def proposal_reject(self, node_id: str, feedback: str = "") -> dict: ...
    def sse(self, replay: int | None = None, once: bool = False, last_event_id: str | None = None) -> str: ...

def wait_for_health(client: RemoraClient, timeout_s: float = 30.0) -> bool: ...

def poll_events(client: RemoraClient, predicate: Callable, timeout_s: float = 20.0, poll_interval_s: float = 1.0) -> dict | None:
    """Poll /api/events until predicate(event) returns True or timeout."""
    ...

def find_node(client: RemoraClient, file_suffix: str, name: str) -> dict | None:
    """Resolve a target node by file path suffix and name. Falls back to first function node."""
    ...

@dataclass
class CheckResult:
    name: str
    passed: bool
    skipped: bool = False
    skip_reason: str = ""
    detail: str = ""
    duration_s: float = 0.0
```

**Benefits:**
- **Eliminates 6 external tool deps** (`curl`, `jq`, `rg`, `sed`, `awk`, `timeout`) — pure stdlib Python.
- **Removes ~400 lines of duplicated boilerplate** (health checks, event polling, JSON parsing, temp dir traps).
- **Testable**: check modules can be unit-tested with a mock `RemoraClient`.
- **Structured output**: `CheckResult` replaces ad-hoc `echo` + exit codes with machine-readable results.
- **Portable**: works anywhere Python runs — no `devenv`, `rg`, or GNU coreutils required.
- **Fixable**: the `rg` dependency (3.1), file mutation cleanup (3.2), orphan directory cleanup (3.4), and non-deterministic companion check (3.5) all get fixed as part of the conversion.

**Runner (`runner.py`) replaces `run_demo_checks.sh`:**

```python
# Discovers check_*.py modules, runs them in order, prints structured results.
# Supports: --strict (no skips), --filter (run subset), --json (machine output).
# Integrates with democtl.py verify command (replaces the bash subprocess call).
```

**Migration strategy:**
1. Build `_harness.py` with `RemoraClient` and shared primitives.
2. Convert checks one at a time, keeping the bash version alongside until the Python version passes.
3. Update `runner.py` to call Python checks directly.
4. Update `democtl.py verify` to call `runner.main()` instead of shelling out to `run_demo_checks.sh`.
5. Delete the bash scripts once all checks pass in Python.

**Scripts to keep as shell:**
- `reconcile_demo.sh` (5 lines, just prints instructions — not worth converting)

**Scripts to keep as Python but relocate:**
- `mock_embedder_server.py` → stays in `scripts/` (it's a server, not a check)
- `lsp_event_bridge_probe.py` → absorb into `checks/check_lsp_bridge.py`

### 3.2 `lsp_event_bridge_probe.py` mutates fixture files without cleanup

**Severity: Medium (dirty working tree)**

The probe appends `\n# remora lsp bridge probe\n` to `src/services/pricing.py` via LSP `didChange`/`didSave` notifications. If the probe crashes, the LSP server writes the change to disk, or the runtime propagates it, the fixture file is permanently modified. There is no `try/finally` or `atexit` handler to restore it.

**Action:** Add a `try/finally` block that reads the original content before modification and restores it on exit (success or failure). This will be addressed as part of the Python check conversion (3.1).

### 3.3 `discovery_paths` references potentially empty directories

**Severity: Low**

The config lists `docs/` and `configs/` as discovery paths. `docs/architecture.md` exists but `configs/` only has fixture files. If either directory is removed, discovery still works (empty scan) but `test_multilang_discovery.sh` will fail for markdown/toml assertions without a clear error message pointing to the missing directory.

**Action:** Add a pre-flight check in the converted Python check that verifies discovery source directories contain expected file types before running assertions.

### 3.4 `test_virtual_agents.sh` has a non-deterministic companion check

**Severity: Low-Medium**

The `companion_ok` check looks at global turn counts rather than correlation-scoped events. In a high-activity environment, a companion event from a different concurrent turn could satisfy the check, making the test pass for the wrong reason.

**Action:** Scope the companion check to the `probe_corr` correlation ID (already extracted), so it validates the specific causal chain (probe -> reflection -> companion). This will be addressed as part of the Python check conversion (3.1).

### 3.5 No `CLAUDE.md` in repository root

**Severity: Medium (LLM agent usability)**

For a repo whose stated goal includes LLM agent verification (`democtl verify`), there is no `CLAUDE.md` with project conventions, key file locations, or operational guidance. Any agent working in this repo has to discover everything from scratch.

**Action:** Create a `CLAUDE.md` covering: repo purpose, how to run demos, key paths (`scripts/democtl.py`, `demo/*/demo.yaml`), testing conventions, and the no-cross-contamination invariant.

### 3.6 No CI pipeline

**Severity: Medium (regression risk)**

There are no GitHub Actions workflows or any CI configuration. All testing is manual via `run_demo_checks.sh`. The DEMO_OVERVIEW.md Phase 3 calls for "CI smoke target for `setup` + `wipe` on at least one demo" but this was never implemented.

**Action:** Add a minimal GitHub Actions workflow that runs: (a) `pytest tests/unit/` (no runtime needed), (b) manifest validation, (c) `democtl setup --demo 00_repo_baseline` + `democtl wipe --demo 00_repo_baseline --force` as a smoke test.

---

## 4. Prioritized Action Items

| # | Item | Severity | Effort | Section |
|---|------|----------|--------|---------|
| 1 | Refactor `democtl.py` into `scripts/_lib/` modules | Medium | 1-2 hr | 2.1 |
| 2 | Convert shell scripts to Python check modules | High | 4-6 hr | 3.1 |
| 3 | Pin remora-v2 to specific commit/tag | High | 1 min | 1.2 |
| 4 | Add `pyyaml` to direct deps (or fix fallback parser) | High | 5 min | 2.2 |
| 5 | Add `--strict` flag to `verify` (manifest-aware) | Medium | 30 min | 1.3 |
| 6 | Fix symlink safety in delete check | Medium | 15 min | 2.5 |
| 7 | Decouple `start` from `devenv shell --` | Medium | 30 min | 2.3 |
| 8 | Make `repo_dir` optional for local demos | Medium | 20 min | 1.1 |
| 9 | Create `CLAUDE.md` | Medium | 30 min | 3.5 |
| 10 | Add CI workflow | Medium | 45 min | 3.6 |
| 11 | Pull search stack ports from manifest | Low-Med | 20 min | 2.4 |
| 12 | Add discovery path pre-flight to check | Low | 10 min | 3.3 |

Items 1 and 2 are the structural refactors — do these first since many other fixes (ripgrep dep, file mutation cleanup, non-deterministic companion check, orphan directory cleanup) get resolved as side effects of the Python conversion.

Items 3-4 are one-minute fixes that should be done immediately regardless.

---

## 5. Items NOT Worth Fixing

These were considered and intentionally deferred:

- **`workspace_ignore_patterns` multi-profile coverage**: All three profiles currently use the same `workspace_root`. Only becomes an issue if someone adds a profile with a different workspace root, at which point the fix is one line in the config.
- **`test_ui_dependencies.sh` temp file cleanup**: These are tiny files in `/tmp/` that get overwritten on each run. Not worth adding trap logic for. (This script becomes a trivial Python diagnostic in the conversion.)
- **`rewrite_to_magic.pym` relative path**: The `source/<node_id>` path is intentional — it's the proposal staging convention in remora-v2's Cairn workspace system. Not a bug.
- **`reconcile_demo.sh`**: 5 lines that just print instructions. Not worth converting to Python.
