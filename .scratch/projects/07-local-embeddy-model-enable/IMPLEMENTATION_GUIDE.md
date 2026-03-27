# Implementation Guide: remora-test Local Embeddy Primary Flow

Date: 2026-03-26  
Project: `07-local-embeddy-model-enable`  
Repository: `/home/andrew/Documents/Projects/remora-test`

## Objective

Implement the remaining `remora-test` work identified from project `07`:

1. Make real local embeddy setup the primary strict-search path (mock path becomes fallback only).
2. Improve search diagnostics so failures clearly differentiate:
   - embeddy backend unreachable
   - embeddy reachable but model/backend not ready (including "model not loaded")
3. Add an optional helper script to standardize local search stack startup.

This guide is written so an intern can execute it step by step with minimal ambiguity.

## Out of Scope

- Implementing embeddy local backend internals (belongs to embeddy upstream).
- remora-v2 runtime internals for search service behavior (belongs to remora-v2 upstream).
- Rewriting the full demo architecture.

## Current Baseline (Before Changes)

- Mock adapter is still explicitly documented in `README.md` for strict-search troubleshooting.
- `scripts/test_search.sh` has strict checks, but not a first-class preflight classification for backend unreachable vs backend not-ready/model-not-loaded.
- `scripts/start_search_local_stack.sh` does not exist.

## Files To Change

Required:

- `README.md`
- `DEMO_SCRIPT.md`
- `docs/architecture.md`
- `scripts/test_search.sh`
- `scripts/run_demo_checks.sh` (only if needed for messaging/flags consistency)
- `configs/embeddy.remote.yaml` (fallback retention only; do not delete unless explicitly requested)
- new `scripts/start_search_local_stack.sh`

Recommended new config:

- `configs/embeddy.local.yaml` (primary local model config template)

Project tracking updates after implementation:

- `.scratch/projects/07-local-embeddy-model-enable/PROGRESS.md` (create if needed or update)
- `.scratch/projects/07-local-embeddy-model-enable/DECISIONS.md` (create if needed or update)
- `.scratch/projects/07-local-embeddy-model-enable/ISSUES.md` (create if needed or update)

## Branch and Safety

1. Create implementation branch.

```bash
git checkout -b feat/local-embeddy-primary-flow
```

2. Capture baseline outputs for comparison.

```bash
mkdir -p .scratch/projects/07-local-embeddy-model-enable/artifacts

scripts/test_search.sh \
  > .scratch/projects/07-local-embeddy-model-enable/artifacts/test_search.before.out \
  2> .scratch/projects/07-local-embeddy-model-enable/artifacts/test_search.before.err || true

REQUIRE_SEARCH=1 scripts/test_search.sh \
  > .scratch/projects/07-local-embeddy-model-enable/artifacts/test_search.strict.before.out \
  2> .scratch/projects/07-local-embeddy-model-enable/artifacts/test_search.strict.before.err || true
```

3. Record current script/docs signatures.

```bash
rg -n "mock_embedder|embeddy.remote|REQUIRE_SEARCH|Search returns 500" README.md DEMO_SCRIPT.md scripts/test_search.sh \
  > .scratch/projects/07-local-embeddy-model-enable/artifacts/baseline_grep.txt
```

## Phase 1: Make Local Embeddy the Primary Strict Path

### 1.1 Add primary local embeddy config template

Create `configs/embeddy.local.yaml` with clearly real-model defaults (not mock):

Example template (adjust model/device based on environment reality):

```yaml
embedder:
  mode: local
  model_name: sentence-transformers/all-MiniLM-L6-v2
  embedding_dimension: 384
  device: cpu

pipeline:
  collection: code

server:
  host: 127.0.0.1
  port: 8585
```

Notes:

- Keep this file lightweight and realistic for CPU-capable development hosts.
- If chosen model requires `trust_remote_code`, document that explicitly instead of enabling silently.

### 1.2 Update README primary vs fallback ordering

In `README.md`:

1. In prerequisites, state real embeddy local model flow first.
2. Keep `scripts/mock_embedder_server.py` and `configs/embeddy.remote.yaml` as fallback only.
3. In troubleshooting:
   - add explicit section "Preferred strict-search setup (local embeddy model)".
   - move mock adapter instructions under "Fallback workaround".
4. Keep strict invocation examples:
   - `REQUIRE_SEARCH=1 scripts/run_demo_checks.sh`
   - `REQUIRE_SEARCH=1 MAX_INDEX_ERRORS=0 scripts/test_search.sh`

Required wording pattern:

- "Primary path: real local embeddy model"
- "Fallback path: mock adapter (temporary workaround)"

### 1.3 Update DEMO_SCRIPT and architecture docs

In `DEMO_SCRIPT.md`:

- Search section should point to local embeddy setup as canonical.
- Add one-liner fallback note for mock adapter.

In `docs/architecture.md`:

- Mention that semantic search contract assumes real embeddy backend.
- Mention mock adapter exists only for constrained/fallback environments.

### 1.4 Keep fallback assets but re-label

Do not remove:

- `scripts/mock_embedder_server.py`
- `configs/embeddy.remote.yaml`

Do:

- Ensure docs label them as fallback and non-primary.

## Phase 2: Improve `scripts/test_search.sh` Diagnostics

### 2.1 Add preflight classifier for embeddy backend state

Implement explicit preflight before `remora index`:

1. Determine embeddy base URL from `REMORA_EMBEDDY_URL` (already used by runtime config).
2. Probe `"$REMORA_EMBEDDY_URL/api/v1/health"` with bounded timeout.
3. Classify into one of:
   - `BACKEND_UNREACHABLE`: curl/connectivity failure
   - `BACKEND_READY`: health endpoint reachable and indicates ready
   - `BACKEND_NOT_READY`: endpoint reachable but signals unhealthy/not ready/model not loaded
   - `BACKEND_UNKNOWN`: endpoint reachable but payload unexpected

Implementation suggestion:

- Add helper function:
  - `search_preflight_status() -> prints enum + details`
- Parse JSON with `jq` defensively.
- Do not assume one strict health schema; accept common variants:
  - `.status == "ok"`
  - `.ready == true`
  - `.backend_ready == true`

### 2.2 Strict vs non-strict behavior rules

When `REQUIRE_SEARCH != 1`:

- `BACKEND_UNREACHABLE` -> skip with explicit reason.
- `BACKEND_NOT_READY` -> skip with explicit reason and health payload.

When `REQUIRE_SEARCH == 1`:

- `BACKEND_UNREACHABLE` -> fail immediately with actionable error.
- `BACKEND_NOT_READY` -> fail immediately with actionable error.

### 2.3 Model-not-loaded special-case messaging

Add explicit detection for known failure text patterns in health/search/index output:

- `Model not loaded`
- `call load() first`
- `not ready`

On match, print targeted remediation:

1. "embeddy is reachable but model is not loaded."
2. "Start embeddy with local config and verify readiness."
3. point to `scripts/start_search_local_stack.sh`.

### 2.4 Improve search error output context

When `/api/search` fails:

- Include:
  - HTTP code
  - first 1-2 key fields from JSON response when present
  - short branch-specific hint:
    - 503 -> backend unavailable
    - 500 + model-not-loaded text -> backend reachable, model not loaded
    - other -> unexpected backend/runtime failure

### 2.5 Preserve current index error threshold behavior

Keep:

- `MAX_INDEX_ERRORS` logic
- strict default `MAX_INDEX_ERRORS=0`
- top error-line extraction

Do not regress the parser behavior already added from project `08`.

## Phase 3: Add `scripts/start_search_local_stack.sh`

## Purpose

Standardize startup order and remove manual setup mistakes for local search demo.

### 3.1 Script behavior contract

Script should:

1. Validate required tools exist (`devenv`, `embeddy`, `curl`, `jq`).
2. Resolve config path (default: `configs/embeddy.local.yaml`, overridable with `EMBEDDY_CONFIG`).
3. Start embeddy in background.
4. Poll embeddy health/readiness until success or timeout.
5. Print export hint for runtime:
   - `export REMORA_EMBEDDY_URL=http://127.0.0.1:8585`
6. Optionally start remora runtime when `START_REMORA=1`.
7. Ensure clean shutdown of background embeddy on script exit if it started it.

### 3.2 Recommended flags/env

- `EMBEDDY_CONFIG` (default config path)
- `EMBEDDY_URL` (default `http://127.0.0.1:8585`)
- `TIMEOUT_S` (default `30`)
- `START_REMORA` (default `0`)
- `REMORA_PORT` (default `8080`)

### 3.3 Suggested script skeleton

```bash
#!/usr/bin/env bash
set -euo pipefail

EMBEDDY_CONFIG="${EMBEDDY_CONFIG:-configs/embeddy.local.yaml}"
EMBEDDY_URL="${EMBEDDY_URL:-http://127.0.0.1:8585}"
TIMEOUT_S="${TIMEOUT_S:-30}"
START_REMORA="${START_REMORA:-0}"
REMORA_PORT="${REMORA_PORT:-8080}"
```

Then:

- start embeddy in background (`devenv shell -- embeddy serve --config "$EMBEDDY_CONFIG"`),
- poll `"$EMBEDDY_URL/api/v1/health"` every 1s until timeout,
- print next-step commands,
- if `START_REMORA=1`, run `devenv shell -- remora start --project-root . --port "$REMORA_PORT" --log-events`.

### 3.4 Script validation commands

```bash
bash -n scripts/start_search_local_stack.sh
TIMEOUT_S=5 scripts/start_search_local_stack.sh || true
```

Expected:

- clear readiness success/failure message,
- no orphaned embeddy process when script exits unsuccessfully.

## Phase 4: Docs/Script Integration

### 4.1 README command block

Add canonical startup sequence:

```bash
scripts/start_search_local_stack.sh
export REMORA_EMBEDDY_URL=http://127.0.0.1:8585
REQUIRE_SEARCH=1 scripts/test_search.sh
```

Fallback block (explicitly secondary):

```bash
devenv shell -- python scripts/mock_embedder_server.py
devenv shell -- embeddy serve --config configs/embeddy.remote.yaml
```

### 4.2 DEMO_SCRIPT search section

Add:

- primary local setup reference (`scripts/start_search_local_stack.sh`),
- strict-mode command sample,
- fallback note in one short subsection.

### 4.3 Architecture doc update

Add one short paragraph under validation/search describing:

- primary local embeddy contract,
- fallback mock adapter contract.

## Phase 5: Validation Matrix (Must Pass)

Run these in order:

1. Lint/syntax checks

```bash
bash -n scripts/test_search.sh
bash -n scripts/start_search_local_stack.sh
```

2. Non-strict search script behavior with backend absent:

```bash
scripts/test_search.sh
```

Expected: skip with explicit classification message.

3. Strict mode behavior with backend absent:

```bash
REQUIRE_SEARCH=1 scripts/test_search.sh
```

Expected: immediate failure, classified as unreachable/not-ready (not generic failure).

4. Start local stack and retest strict mode:

```bash
scripts/start_search_local_stack.sh
# in another shell:
REMORA_EMBEDDY_URL=http://127.0.0.1:8585 REQUIRE_SEARCH=1 scripts/test_search.sh
```

Expected: pass (or fail with clearly actionable model-load reason).

5. Full runner strict path:

```bash
REMORA_EMBEDDY_URL=http://127.0.0.1:8585 REQUIRE_SEARCH=1 scripts/run_demo_checks.sh
```

Expected: search stage behaves deterministically and diagnostics remain clear.

## Definition of Done

All are required:

1. Docs present local embeddy as primary strict path and mock adapter as fallback only.
2. `scripts/test_search.sh` emits first-class error classification for:
   - backend unreachable
   - backend reachable but not-ready/model-not-loaded
3. `scripts/start_search_local_stack.sh` exists, is executable, and reliably boots/polls local embeddy.
4. Strict/non-strict behavior remains intentional:
   - non-strict can skip with explicit reason
   - strict fails fast with actionable diagnostics
5. Existing index-error threshold checks remain intact.

## Common Failure Modes and Fixes

1. Health probe returns non-JSON payload.
- Print raw body and classify as `BACKEND_UNKNOWN`.
- In strict mode: fail with remediation to verify embeddy config and version.

2. embeddy starts but never becomes ready.
- Timeout with diagnostic showing last health payload and config path used.
- Suggest trying a smaller local model in `configs/embeddy.local.yaml`.

3. Script leaves background process running.
- Ensure `trap` cleanup kills embeddy child PID.

4. Docs drift from actual commands.
- Re-run command blocks after docs edits and fix examples immediately.

## Suggested Commit Plan

1. `feat(search): add local embeddy startup helper and primary config template`
2. `fix(search): classify backend unreachable vs not-ready in test_search.sh`
3. `docs(search): switch primary path to local embeddy and demote mock fallback`

## Final Deliverables Checklist

- [ ] `configs/embeddy.local.yaml` added
- [ ] `scripts/start_search_local_stack.sh` added + executable
- [ ] `scripts/test_search.sh` diagnostics/classification improved
- [ ] `README.md` updated (primary local, fallback mock)
- [ ] `DEMO_SCRIPT.md` updated (same priority ordering)
- [ ] `docs/architecture.md` updated for search contract
- [ ] validation artifacts saved under `.scratch/projects/07-local-embeddy-model-enable/artifacts/`
- [ ] project `07` tracking docs updated with completion status and residual risks
