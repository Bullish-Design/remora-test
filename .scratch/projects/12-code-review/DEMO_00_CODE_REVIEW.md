# Demo 00 Code Review — `demo/00_repo_baseline/`

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [_harness.py](#2-harnesspy)
3. [runner.py](#3-runnerpy)
4. [Check Modules (Individual Reviews)](#4-check-modules)
5. [Config Files](#5-config-files)
6. [Bundle Configs](#6-bundle-configs)
7. [Support Scripts](#7-support-scripts)
8. [Manifest (demo.yaml)](#8-manifest)
9. [Test Coverage](#9-test-coverage)
10. [Summary](#10-summary)

---

## 1. Architecture Overview

**Structure:**
```
demo/00_repo_baseline/
  demo.yaml                    — manifest
  config/
    remora.yaml                — default profile (full features)
    remora.constrained.yaml    — constrained profile (python-only, fewer observers)
    remora.stress.yaml         — stress profile (overflow-inducing settings)
  bundles/
    demo-code-agent/           — tool-equipped agent (5 tools + self_reflect)
    demo-directory-agent/      — minimal directory agent
    demo-virtual-observer/     — no-tool reactive observer
  checks/
    __init__.py                — package marker
    _harness.py (275 lines)    — shared client, polling, result types
    runner.py (176 lines)      — orchestrator with CLI
    17 x check_*.py            — individual checks
  scripts/
    mock_embedder_server.py    — FastAPI mock for embeddy
    install_local_ui_assets.py — offline UI asset patching
    reconcile_demo.sh          — 5-line reminder script
  queries/
    README.md                  — placeholder for custom query overrides
```

**Verdict: Good.** Clean separation between checks (validation), scripts (utilities), bundles (agent config), and config (runtime profiles). The checks/ package is self-contained with its own harness and runner.

---

## 2. _harness.py

### 2.1 `RemoraClient` — well-designed

The client wraps `urllib.request` with proper error handling:
- Returns `(status, payload)` tuples for endpoints where the caller needs to handle non-200 responses (search, proposals, companion).
- Raises `CheckFailure` for endpoints where non-200 is always an error (health, nodes, edges, events, chat, cursor).
- URL-encodes node IDs for path parameters (line 145, 150, 153, 157).
- Handles `HTTPError` to extract status codes and body (lines 74-76).
- Falls back to `{"_raw": raw}` for non-JSON responses (line 85) — used correctly by the SSE method.

### 2.2 `RemoraClient._request` always returns tuple — inconsistency

The convenience methods (`.health()`, `.nodes()`, `.edges()`, `.events()`, `.chat()`, `.cursor()`) call `_request` and then raise on non-200, returning only the payload (not the tuple). But `.search()`, `.proposal_diff()`, `.proposal_accept()`, `.proposal_reject()`, `.companion()` return the raw `(status, payload)` tuple. This split API means callers have to know which methods return what.

**Severity: Low-Medium.** The split is intentional (some endpoints have meaningful non-200 responses like 503 for search), but it's a footgun. Consider making all methods return the same shape and providing separate `*_or_raise` variants, or documenting the convention clearly.

### 2.3 `poll_events` predicate signature is unusual

```python
predicate: Callable[[dict[str, Any], list[dict[str, Any]]], bool]
```

The predicate receives `(event, all_events)`, allowing checks that need context from the full event list. However, none of the current check modules use `poll_events` — they all implement their own polling loops manually. This function is defined but unused.

**Severity: Low.** Either integrate it into the checks or remove it. Dead code adds maintenance burden.

### 2.4 `find_node` has a sensible fallback

Falls back to the first function node if the specific file/name match fails. This prevents hard failures when the fixture code changes. Good defensive design.

### 2.5 `event_agent_id` checks both nested and top-level

Lines 263-269 check `payload.agent_id` first, then `event.agent_id` as fallback. This handles both remora event formats robustly.

### 2.6 `auto_command_prefix` reads from `DEMO_COMMAND_PREFIX` env var

This is set by `cmd_verify` in commands.py (line 226), creating a clean bridge between the scaffold and the checks. The fallback chain (env → devenv detection → bare) mirrors the scaffold's `build_command_prefix`.

### 2.7 `CheckContext` dataclass is clean

All fields are primitives or simple types. No mutable defaults. Good.

### 2.8 Missing: `RemoraClient` has no `close()` or context manager

urllib connections are closed per-request (via `with urlopen(...)`), so there's no resource leak. But a `__enter__`/`__exit__` would be more Pythonic for future connection pooling.

**Severity: Cosmetic.**

---

## 3. runner.py

### 3.1 Check registration via module-level dict — good

```python
CHECKS: dict[str, RunFn] = {
    "check_runtime": check_runtime.run,
    ...
}
```

Explicit registration is better than auto-discovery (no import magic, clear ordering, easy to add/remove).

### 3.2 `DEFAULT_ORDER` controls execution sequence

Separate from `CHECKS` dict keys, which is good — you can register a check without it running by default. `check_guardrails` and `check_smoke` are in `CHECKS` but only added to the run order conditionally.

### 3.3 Bug: `check_smoke` is in `CHECKS` but not in `DEFAULT_ORDER`

`check_smoke` (line 44) is registered in `CHECKS` but missing from `DEFAULT_ORDER` (lines 52-68). It's only reachable via `--filter check_smoke`. This may be intentional (it's a non-asserting dump) but it's not documented.

**Severity: Low.** Either add it to the default order or add a comment explaining why it's excluded.

### 3.4 Runner stops on first failure

Line 154: `break` on first failed check. This is appropriate for a sequential pipeline where later checks depend on earlier ones (e.g., check_runtime must pass before check_virtual_agents makes sense). But it means a single failure gives no information about subsequent checks.

**Severity: Low.** Consider a `--continue-on-failure` flag for debugging sessions where you want to see all failures at once.

### 3.5 `--json` output is printed after human-readable output

Lines 156-166 dump JSON after the per-check PASS/FAIL lines have already been printed. This means `--json` output is appended, not replacing. A consumer parsing JSON would need to skip the preceding text.

**Severity: Low-Medium.** Consider either suppressing human output when `--json` is set, or writing JSON to stderr while human output goes to stdout.

### 3.6 Import style: bare imports, not package-relative

Lines 10-27: `import check_cursor`, `from _harness import ...`. These work because `runner.py` is invoked as `python runner.py` from the `checks/` directory (Python adds the script's directory to `sys.path`). But it means the checks/ package can't be imported from outside its own directory.

**Severity: Low.** Consistent with the design (runner is a standalone CLI). Would need relative imports if ever moved to a proper package.

---

## 4. Check Modules

### 4.1 Common Pattern — Good

All 17 checks follow an identical structure:
```python
NAME = "check_foo"

def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    try:
        # ... check logic ...
        return CheckResult(name=NAME, passed=True, ...)
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, detail=str(exc), ...)
```

The blanket `except Exception` catch ensures the runner never crashes — every check returns a result, even on unexpected errors. This is the right pattern for a check harness.

### 4.2 `check_runtime.py` — Clean

Simple endpoint verification: health, nodes, edges, events, chat, virtual count. No polling needed. Good first check.

### 4.3 `check_virtual_agents.py` — Companion check now correlation-scoped

Lines 101-109 scope the companion check to the `probe_corr` correlation ID:
```python
if str(event.get("correlation_id", "")) != probe_corr:
    continue
if event_agent_id(event) == "demo-companion-observer" and ...:
    companion_ok = True
```

This fixes the non-deterministic companion check from the original shell script. Good.

However, `require_companion` is hardcoded to `False` (line 52). This means the companion check is never enforced in virtual agents — it's only enforced in `check_reflection.py` (line 26: `require_companion = True`). This seems intentional but is worth noting: the virtual agents check only validates the review observer, not the companion chain.

### 4.4 `check_reflection.py` — Full causal chain validation

Validates: primary → reflection → turn_digested → companion. All scoped to `probe_corr`. This is the most thorough pipeline check and correctly verifies the full lifecycle.

### 4.5 `check_subscriptions.py` — Imports remora internals

Line 25: `from remora.core.events import NodeChangedEvent, SubscriptionPattern`. This is the only check that imports remora library code directly. All others use only the HTTP API. This creates a hard dependency on remora being importable in the Python environment.

**Severity: Medium.** If remora isn't installed (or a different version is installed), this check crashes with an import error rather than a clean skip. Consider wrapping the import in try/except and returning a skipped result.

### 4.6 `check_proposal_reject.py` — Clean and focused

Triggers rewrite_to_magic, waits for proposal, fetches diff, rejects. Validates the reject response status. No file mutation — clean.

### 4.7 `check_proposal_accept.py` — File restoration in `finally` — good

Lines 151-155: The `finally` block restores the original file content and cleans up the proposal artifact. This fixes the file mutation issue from the original shell script.

Minor issue: `_cleanup_proposal_artifact` (lines 12-25) has the same `rmdir` loop pattern from the original shell script. However, it's now guarded by Python's `OSError` catch and the loop has a `str(parent) not in {".", "/"}` safety check, which is better than the original.

### 4.8 `check_sse.py` — Clean SSE replay/resume test

Uses `_extract_last_event_id` to parse SSE format. The 2-second sleeps between chat sends and SSE fetches are necessary for event propagation. Clean implementation.

### 4.9 `check_cursor.py` — Soft failure for cursor events

Line 61: `if not cursor_event_found and require_cursor_event`. With `require_cursor_event = False`, the check passes even if the cursor event is never observed — it only verifies the API response. This is a reasonable default since cursor events may not propagate in all runtime configurations.

### 4.10 `check_discovery.py` — Has preflight check

Lines 11-19: `_preflight` verifies that Python, Markdown, and TOML files exist in the expected directories before running discovery. This prevents cryptic failures when fixture files are missing. Good addition from project 11.

### 4.11 `check_discovery.py` — Swallows runtime health check errors

Lines 52-59: The virtual node count check is wrapped in a bare `except Exception: pass`. If the runtime is running but returns unexpected data, this silently passes. The intent is to make this check optional (discovery can work without a running runtime), but the blanket catch is too broad.

**Severity: Low.** Catch `CheckFailure` specifically, or catch `Exception` but log a warning.

### 4.12 `check_search.py` — Thorough schema validation

Validates: index command, error count threshold, HTTP status, required response keys, query/collection/mode echo, results array shape, total_results >= 1, first result shape. Comprehensive.

### 4.13 `check_lsp_startup.py` — Imports remora config directly

Line 18: `from remora.core.model.config import load_config`. Same issue as check_subscriptions (4.5). Would crash with an import error if remora isn't installed.

### 4.14 `check_lsp_bridge.py` — File restoration in `finally` — good

Lines 205-208: Restores `pricing.py` to original content in the `finally` block. This fixes the file mutation issue from the original `lsp_event_bridge_probe.py`.

The probe also handles the LSP process cleanup properly: `proc.terminate()` with a `proc.kill()` fallback in the nested `finally` (lines 164-171).

### 4.15 `check_lsp_bridge.py` — Double event type loop

Lines 45-46:
```python
for event_type in CHANGE_EVENT_TYPES:
    events = _fetch_events(client, event_type=event_type, limit=event_limit)
```

This makes two separate API calls per poll iteration (one for `content_changed`, one for `node_changed`). Could be a single call without the `event_type` filter, then filter client-side. Minor performance concern for a check that runs infrequently.

**Severity: Cosmetic.**

### 4.16 `check_guardrails.py` — Thread pool burst — good

Lines 43-44: Uses `ThreadPoolExecutor(max_workers=16)` to send 80 concurrent chat messages. This correctly exercises the overflow behavior that the stress config is designed to trigger. The thread pool is cleaner than the original shell script's `curl ... &` + `wait` pattern.

### 4.17 `check_ui_dependencies.py` — Informational only

Always passes. Reports whether the UI uses CDN scripts and whether unpkg is reachable. Good diagnostic check.

### 4.18 `check_ui_playwright.py` — Graceful skip when playwright unavailable

Line 66-75: If playwright screenshot fails and we're not in strict mode, returns a skipped result instead of failing. Good portability.

### 4.19 `check_ui_playwright.py` — Temp file leak

Line 47-48: Creates a temp file with `tempfile.mkstemp` but never cleans it up on success. The screenshot path is reported in the result data, which is useful for inspection, but the file persists indefinitely in `/tmp/`.

**Severity: Low.** The file is small (a PNG screenshot) and has a descriptive prefix. Could add an `atexit` cleanup, but it's not worth the complexity.

---

## 5. Config Files

### 5.1 `remora.yaml` (default profile)

Well-structured. Covers discovery (Python, Markdown, TOML), bundles, virtual agents (4 agents with subscriptions), search, and workspace isolation. All env vars use `${VAR:-default}` syntax correctly.

### 5.2 `remora.constrained.yaml` — Reduced scope

Drops `docs/` and `configs/` from discovery, drops the two path-filter observers. Retains the core demo-review-observer and demo-companion-observer. Search remains enabled — this is intentional (the constraint is about observer load, not search).

### 5.3 `remora.stress.yaml` — Overflow-inducing settings

`max_concurrency: 1`, `actor_inbox_max_items: 5`, `actor_inbox_overflow_policy: "drop_new"`, `send_message_rate_limit: 2`. These settings force observable overflow when burst messages are sent. The `check_guardrails` test depends on these exact settings.

### 5.4 All three configs share the same `workspace_root`

`.remora-00-repo-baseline` is used across all profiles. This means switching profiles doesn't require a wipe — the workspace is shared. Could cause issues if you switch from stress to default without a clean workspace (stale overflow metrics), but the demo workflow typically involves a wipe between profile switches.

### 5.5 `workspace_ignore_patterns` doesn't glob

The patterns are exact prefix matches: `.remora`, `.remora-00-repo-baseline`. If someone created `.remora-00-repo-baseline-backup`, it wouldn't be ignored. This is fine for the current setup but worth noting.

### 5.6 Constrained config still has Markdown/TOML in `language_map`

Lines 11-13 of `remora.constrained.yaml` include `.md` and `.toml` in `language_map` even though only `src/` is in `discovery_paths`. The language_map entries for `.md` and `.toml` are harmless (no files matching those extensions will be found under `src/`), but they're vestigial.

**Severity: Cosmetic.** Remove `.md` and `.toml` from the constrained config's `language_map` for clarity.

---

## 6. Bundle Configs

### 6.1 `demo-code-agent/bundle.yaml`

The system prompt extension uses a token-matching convention: "If message contains `rewrite_to_magic`, call the rewrite_to_magic tool exactly once." This creates a deterministic, testable trigger system — the check scripts send specific tokens and expect specific tool calls.

`self_reflect` is enabled with `model: "Qwen/Qwen3-4B-Instruct-2507-FP8"` and `max_turns: 2`. The reflection prompt instructs the model to use companion tools (summarize, reflect, link). This drives the `check_reflection.py` pipeline.

### 6.2 Bundle model references the model_default in the config

The bundle hardcodes `Qwen/Qwen3-4B-Instruct-2507-FP8` for self_reflect, while the remora config has `model_default: "${REMORA_MODEL:-Qwen/Qwen3-4B-Instruct-2507-FP8}"`. If someone overrides `REMORA_MODEL`, the primary model changes but the reflection model stays pinned. This may be intentional (reflection should be stable) but creates a subtle inconsistency.

**Severity: Low.** Consider using `${REMORA_MODEL:-...}` in the bundle as well, or document that the reflection model is intentionally pinned.

### 6.3 `demo-directory-agent/` and `demo-virtual-observer/` have empty tools

Both have `tools/.gitkeep` — no actual tool definitions. The directory agent uses built-in remora tools (`summarize_tree`, `list_children`), and the virtual observer is explicitly tool-free. This is correct — the bundles exist to define system prompts and behavioral constraints, not tools.

---

## 7. Support Scripts

### 7.1 `mock_embedder_server.py` — Clean and deterministic

SHA256-seeded unit vectors ensure reproducible embeddings for the same input text. The server is configurable via `MOCK_EMBED_DIM`, `MOCK_EMBED_MODEL`, `MOCK_EMBED_HOST`, `MOCK_EMBED_PORT` env vars. The `_stable_vector` function properly normalizes to unit length.

### 7.2 `mock_embedder_server.py` — FastAPI is an external dependency

This script imports `fastapi` and `pydantic`, which are not in `remora-test`'s direct dependencies. They're pulled transitively through remora (which depends on `uvicorn`, `fastapi`). If the transitive chain changes, this breaks silently.

**Severity: Low.** Consider adding `fastapi` and `uvicorn` to the project's dependencies, or document the implicit dependency.

### 7.3 `install_local_ui_assets.py` — Clean conversion

Properly uses `shutil.copy2` instead of `cp`, `str.replace` instead of `sed`, and `pathlib` throughout. Imports `_STATIC_DIR` from remora's web server module, which is a private name — could break on a remora update.

**Severity: Low.** Pin or document the remora version contract.

### 7.4 `reconcile_demo.sh` — 5-line reminder

Just prints instructions. Not worth converting. Fine as-is.

---

## 8. Manifest (demo.yaml)

### 8.1 `repo_dir` still present despite being optional for local demos

The manifest still has `repo_dir: /tmp/remora-demo-00-repo-baseline` even though validation no longer requires it for local demos. This is harmless (the field is just ignored) and may be useful as documentation of the convention.

**Severity: Cosmetic.** Could remove it or add a comment saying it's optional for local repos.

### 8.2 `requires` block correctly drives strict mode

```yaml
requires:
  lsp: true
  search: true
  web: true
```

This is consumed by `cmd_verify` → `_manifest_requires()` to auto-enable `--require-lsp-bridge`, `--require-search`, `--require-web` in strict mode. The contract is clean and well-integrated.

### 8.3 Missing `requires.guardrails`

The `--require-overflow` flag checks `_manifest_requires(manifest, "guardrails")`, but the manifest doesn't have `guardrails: true` in the `requires` block. This means `--strict` mode doesn't auto-enable overflow checking. The `check_guardrails` is only run when explicitly requested via `--run-guardrails`.

**Severity: Low.** This seems intentional — guardrails require the stress config, which isn't the default. But the manifest could be more explicit with `guardrails: false` to document the choice.

---

## 9. Test Coverage

### 9.1 `test_demo_contract.py` — Good structural coverage

Checks for all 17 check_*.py files, runner, harness, bundle configs, scripts, and tools. Also verifies legacy shell scripts are removed and config keys are modern.

### 9.2 `test_scripts_contracts.py` — Good behavioral coverage

Verifies that search checks enforce error thresholds, proposal checks assert chat status, runner exposes LSP bridge flags, and playwright check is registered. These test the contracts rather than just structure.

### 9.3 `test_demo_live_contract.py` — Requires live runtime

Skips unless `REMORA_LIVE_BASE_URL` is set. Good separation of live integration tests from unit tests.

### 9.4 No unit tests for `_harness.py`

`RemoraClient`, `poll_events`, `find_node`, `event_payload`, `event_agent_id`, `ensure_chat_sent` have no unit tests. These could be tested with mock HTTP responses.

**Severity: Medium.** The harness is the foundation of all checks. A bug here would be hard to diagnose.

### 9.5 No test for `runner.py` CLI argument parsing

The runner accepts `--strict`, `--filter`, `--json`, `--require-*`, `--run-*` flags. None of these are tested for correct parsing or interaction.

**Severity: Low-Medium.** At minimum, test that `--filter unknown_check` raises `SystemExit`.

---

## 10. Summary

### What's Good
- Consistent check pattern: every check returns `CheckResult`, never crashes the runner
- `_harness.py` provides a clean, reusable `RemoraClient` with proper error handling
- File mutation cleanup in `finally` blocks (proposal accept, LSP bridge)
- Correlation-scoped event validation (virtual agents, reflection pipeline)
- Preflight checks prevent cryptic failures (discovery)
- Graceful skips for optional dependencies (playwright, LSP, search)
- Config profiles provide clear behavioral variants (default, constrained, stress)
- Token-triggered tool system in bundles creates deterministic, testable agent behavior
- Mock embedder produces reproducible embeddings

### What Needs Attention

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 1 | `check_subscriptions` and `check_lsp_startup` import remora internals without try/except | Medium | 15 min |
| 2 | `poll_events` in harness is defined but unused | Low | 5 min |
| 3 | `RemoraClient` method return types are inconsistent (some return payload, some return tuple) | Low-Med | 30 min |
| 4 | No unit tests for `_harness.py` primitives | Medium | 1-2 hr |
| 5 | `runner.py --json` mixes with human-readable output | Low-Med | 20 min |
| 6 | `check_smoke` registered but not in DEFAULT_ORDER (undocumented) | Low | 5 min |
| 7 | `check_discovery` swallows all exceptions in optional runtime check | Low | 5 min |
| 8 | Bundle self_reflect model hardcoded independently of config model_default | Low | 5 min |
| 9 | Constrained config has vestigial language_map entries | Cosmetic | 2 min |
| 10 | `check_ui_playwright` temp file leak | Low | 10 min |
