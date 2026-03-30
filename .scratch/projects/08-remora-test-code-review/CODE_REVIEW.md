# remora-test Code Review

## Executive Summary
This repo is in a workable demo state, but there are several reliability and quality gaps that will cause false positives/false negatives in validation and make maintenance noisy.

### Severity Overview
- High: 1
- Medium: 3
- Low: 3

## Scope and Method
Reviewed:
- `src/**`
- `scripts/**`
- `tests/**`
- config and packaging (`pyproject.toml`, `remora*.yaml`, `.gitignore`)
- bundle/tool definitions under `bundles/**`

Executed checks:
1. `devenv shell -- uv sync --extra dev`
2. `devenv shell -- uv run pytest -q`
3. import sanity check for `pytest`, `pygls`, `embeddy`

Observed test result:
- `pytest` passed with heavy skipping and no meaningful source coverage.
- Coverage report: `src/main.py` only, 0% covered.

---

## Findings

## High

### H1: LSP bridge validation script is currently non-deterministic and likely to fail strict mode
**Impact:** High confidence strict checks for LSP event bridging are not trustworthy; likely false failures in CI/manual verification.

**Evidence:**
- [scripts/test_lsp_event_bridge.sh:168](/home/andrew/Documents/Projects/remora-test/scripts/test_lsp_event_bridge.sh#L168) proceeds even when no `initialize` response is received.
- [scripts/test_lsp_event_bridge.sh:233](/home/andrew/Documents/Projects/remora-test/scripts/test_lsp_event_bridge.sh#L233) requires `content_changed` event specifically.
- [scripts/test_lsp_event_bridge.sh:244](/home/andrew/Documents/Projects/remora-test/scripts/test_lsp_event_bridge.sh#L244) fails hard if that event is not observed.

**Why this is a problem:**
- If JSON-RPC handshake is not confirmed, subsequent notifications are not a reliable signal of bridge health.
- The script assumes one exact runtime event contract (`content_changed`), which may not match current runtime emission behavior.

**Recommendation:**
1. Treat missing `initialize` response as hard precondition failure in strict mode.
2. Validate against the actual current runtime event contract (or broaden accepted event shapes).
3. Capture and surface LSP stderr/stdout diagnostics in failure output to reduce triage time.

---

## Medium

### M1: Search validation can hide partial indexing failures
**Impact:** `test_search.sh` can pass while indexing has meaningful per-file failures, giving false confidence.

**Evidence:**
- [scripts/test_search.sh:33](/home/andrew/Documents/Projects/remora-test/scripts/test_search.sh#L33) only checks `remora index` process exit code.
- No parsing/guard on index summary errors before proceeding to search assertions.

**Why this is a problem:**
- `remora index` may return success while still reporting per-file indexing errors; script then validates only final search output.

**Recommendation:**
1. Parse `index_log` for reported error count and fail in strict mode when non-zero.
2. Add explicit threshold flag (e.g., `MAX_INDEX_ERRORS=0`) and enforce by default for strict runs.

---

### M2: Proposal scripts do not assert chat send status before waiting
**Impact:** Failures become delayed/ambiguous (timeout waiting for proposal) instead of failing immediately at the actual cause.

**Evidence:**
- [scripts/test_proposal_flow.sh:26](/home/andrew/Documents/Projects/remora-test/scripts/test_proposal_flow.sh#L26) sends `/api/chat` but does not assert `.status == "sent"`.
- [scripts/test_proposal_accept_flow.sh:56](/home/andrew/Documents/Projects/remora-test/scripts/test_proposal_accept_flow.sh#L56) same pattern.

**Recommendation:**
1. Capture chat response payload and assert `status=sent` before entering proposal polling loop.
2. Include full chat response in failure output.

---

### M3: Test suite provides minimal behavioral coverage of repo logic
**Impact:** Regressions in `src/**` and script contracts can ship undetected.

**Evidence:**
- [tests/smoke/test_placeholder.py:1](/home/andrew/Documents/Projects/remora-test/tests/smoke/test_placeholder.py#L1) placeholder-only smoke test.
- [tests/integration/test_demo_contract.py:7](/home/andrew/Documents/Projects/remora-test/tests/integration/test_demo_contract.py#L7) mostly path/executable existence assertions.
- [pyproject.toml:48](/home/andrew/Documents/Projects/remora-test/pyproject.toml#L48) coverage is configured, but execution showed no meaningful source coverage.

**Recommendation:**
1. Add unit tests for `src/services/*` business logic.
2. Add non-live integration tests that validate script parsing/decision branches.
3. Gate on a minimal coverage threshold for `src/**` (exclude only demo entrypoints if needed).

---

## Low

### L1: Runtime-generated `.grail/*/check.json` files are tracked and produce noisy dirty trees
**Impact:** Routine runtime usage dirties working tree, increasing accidental commit risk and review noise.

**Evidence:**
- [\.grail/query_agents/check.json:2](/home/andrew/Documents/Projects/remora-test/.grail/query_agents/check.json#L2) includes ephemeral `/run/user/...` absolute path.
- repeated modifications observed across many `.grail/*/check.json` files.

**Recommendation:**
1. Separate static tool specs from generated check outputs.
2. Ignore generated check artifacts in `.gitignore` or regenerate deterministically in CI only.

---

### L2: UI asset installer is not portable across GNU/BSD `sed`
**Impact:** Script can fail on macOS/BSD environments.

**Evidence:**
- [scripts/install_local_ui_assets.sh:23](/home/andrew/Documents/Projects/remora-test/scripts/install_local_ui_assets.sh#L23) uses `sed -i` GNU style with no BSD fallback.

**Recommendation:**
1. Use portable `sed` handling (OS switch) or write patched file via temp file move.

---

### L3: Demo trigger artifacts committed in source file
**Impact:** Minor code cleanliness issue; can confuse reviewers and automated diffs.

**Evidence:**
- [src/services/pricing.py:5](/home/andrew/Documents/Projects/remora-test/src/services/pricing.py#L5) and [src/services/pricing.py:6](/home/andrew/Documents/Projects/remora-test/src/services/pricing.py#L6) contain ad hoc trigger comments.

**Recommendation:**
1. Remove transient trigger comments from committed source.
2. Use dedicated trigger fixtures/files in tests instead of mutating source directly.

---

## Additional Observations
- Demo scripts are generally readable and fail fast with clear stderr messages.
- Bundle/tool wiring is coherent and organized.
- `remora.yaml` modern key usage is consistent with current runtime expectations.

## Suggested Remediation Order
1. Fix H1 (LSP bridge strict determinism).
2. Fix M1 and M2 (search/proposal script correctness).
3. Expand tests (M3) and establish minimum behavioral coverage.
4. Clean operational noise and portability issues (L1-L3).

## Reproduction Notes
Commands used during review:
- `devenv shell -- uv sync --extra dev`
- `devenv shell -- uv run pytest -q`
- `devenv shell -- python - <<'PY' ... import pytest, pygls, embeddy ... PY`
