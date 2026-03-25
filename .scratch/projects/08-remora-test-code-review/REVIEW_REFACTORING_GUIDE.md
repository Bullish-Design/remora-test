# Review Refactoring Guide

## Status Update (2026-03-25)
- [x] Phase 1 completed: LSP bridge strict-path determinism and diagnostics were refactored into a dedicated probe (`scripts/lsp_event_bridge_probe.py`) and wrapper script update.
- [x] Phase 2 completed: script reliability fixes landed for:
  - index error accounting/threshold handling in `scripts/test_search.sh`
  - chat send-status assertions in `scripts/test_proposal_flow.sh` and `scripts/test_proposal_accept_flow.sh`
- [ ] Phase 3 pending
- [ ] Phase 4 pending
- [ ] Phase 5 pending

## Objective
Implement all actionable issues identified in `CODE_REVIEW.md` with a phased, low-risk rollout that improves:
- validation correctness (less false pass/fail),
- test signal quality,
- operational hygiene and portability.

This guide is implementation-focused and scoped to this repo unless noted.

## Source Findings Covered
From [CODE_REVIEW.md](/home/andrew/Documents/Projects/remora-test/.scratch/projects/08-remora-test-code-review/CODE_REVIEW.md):
- H1: LSP bridge strict check non-determinism
- M1: Search check can hide indexing errors
- M2: Proposal scripts do not assert chat send success
- M3: Minimal behavior coverage
- L1: `.grail/*/check.json` noisy tracked artifacts
- L2: non-portable `sed -i`
- L3: trigger comments in source

## Implementation Phases

## Phase 0: Safety and Baseline
Goal: lock in baseline behavior before edits.

### Tasks
1. Create branch for refactor work.
2. Capture baseline outputs for:
   - `scripts/run_demo_checks.sh`
   - `RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh` (expected failure currently)
   - `devenv shell -- uv run pytest -q`
3. Save logs under `.scratch/projects/08-remora-test-code-review/baseline/`.

### Acceptance
- Reproducible baseline logs exist.

---

## Phase 1: Fix High Severity (H1)
Goal: make LSP bridge strict test deterministic and diagnostic.

### Files
- [scripts/test_lsp_event_bridge.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_lsp_event_bridge.sh)

### Required Changes
1. Enforce JSON-RPC handshake precondition:
   - In strict mode (`REQUIRE_LSP_BRIDGE=1`), fail immediately if initialize response is not observed.
2. Improve event contract handling:
   - Either:
     - align expected event type with actual runtime emissions, or
     - accept a set of valid change events (e.g. `content_changed` plus compatible alternatives) while keeping strict path deterministic.
3. Improve diagnostics:
   - Include LSP stderr tail on failure.
   - Include a summarized event-type histogram from `/api/events` on failure.
4. Prevent false writes:
   - Keep probe text in-memory only (already done); do not mutate repo files directly.

### Validation
1. `devenv shell -- env REQUIRE_LSP=1 scripts/test_lsp_startup.sh`
2. `devenv shell -- env REQUIRE_LSP_BRIDGE=1 scripts/test_lsp_event_bridge.sh`
3. If runtime contract mismatch persists, update expected contract and document exact event fields in README troubleshooting.

### Acceptance
- Strict bridge check either passes reliably or fails with explicit actionable reason (no ambiguous timeout-only failure).

---

## Phase 2: Fix Medium Severity Script Reliability (M1, M2)
Goal: tighten script correctness and early failure behavior.

### M1: Search script error accounting
#### Files
- [scripts/test_search.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_search.sh)

#### Changes
1. Parse indexing output for non-zero error count (e.g. `Done: X files, Y chunks, Z errors`).
2. Add `MAX_INDEX_ERRORS` (default `0` in strict mode).
3. In strict mode:
   - fail if `index` exit code non-zero, or
   - fail if parsed error count exceeds threshold.
4. Improve failure output:
   - show parsed counts and top N indexing errors.

#### Validation
- Run with intentionally broken search backend and verify strict failure is immediate and explicit.

### M2: Proposal scripts assert `/api/chat` success
#### Files
- [scripts/test_proposal_flow.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_proposal_flow.sh)
- [scripts/test_proposal_accept_flow.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_proposal_accept_flow.sh)

#### Changes
1. Capture chat response payload before polling.
2. Assert `.status == "sent"`.
3. On failure, print full payload and exit early.

#### Validation
- Force an invalid target node and confirm immediate clear failure at send step.

### Acceptance
- Search/proposal script failures point to root cause directly (not secondary timeout symptoms).

---

## Phase 3: Improve Test Signal Quality (M3)
Goal: increase behavior coverage for local repo logic and script contracts.

### Files (new)
- `tests/unit/test_services_pricing.py`
- `tests/unit/test_services_discounts.py`
- `tests/unit/test_services_tax.py`
- `tests/unit/test_services_fraud.py`
- `tests/unit/test_utils_money.py`
- `tests/unit/test_scripts_contracts.py` (string/regex-based verification for critical script checks)

### Files (existing)
- [tests/smoke/test_placeholder.py](/home/andrew/Documents/Projects/remora-test/tests/smoke/test_placeholder.py)

### Changes
1. Replace placeholder-only smoke test with meaningful lightweight checks.
2. Add unit tests for current deterministic business logic in `src/services/*` and `src/utils/money.py`.
3. Add script contract tests that verify critical assertions are present:
   - chat status assertion in proposal scripts,
   - index error handling in search script,
   - strict bridge precondition logic.
4. Add a minimal coverage threshold for `src/**` (example: 60% to start, then raise).

### Validation
- `devenv shell -- uv run pytest -q`
- Confirm coverage report reflects real `src/**` testing.

### Acceptance
- Coverage no longer reports effectively zero meaningful source coverage.

---

## Phase 4: Low Severity Hygiene and Portability (L1, L2, L3)
Goal: reduce repo noise and environment-specific failures.

### L1: `.grail` generated artifacts policy
#### Files
- [.gitignore](/home/andrew/Documents/Projects/remora-test/.gitignore)
- `.grail/**` policy docs (README section)

#### Changes
1. Decide and enforce one model:
   - Keep only stable `.pym` sources tracked, ignore generated `check.json`, or
   - Keep generated files but normalize/strip ephemeral fields before write.
2. If ignore model chosen, add targeted ignore pattern for generated check outputs.

### L2: Portable `sed` in UI installer
#### Files
- [scripts/install_local_ui_assets.sh](/home/andrew/Documents/Projects/remora-test/scripts/install_local_ui_assets.sh)

#### Changes
1. Add GNU/BSD-safe in-place edit helper.
2. Keep script behavior identical while ensuring macOS compatibility.

### L3: Remove trigger artifacts from source
#### Files
- [src/services/pricing.py](/home/andrew/Documents/Projects/remora-test/src/services/pricing.py)

#### Changes
1. Remove committed trigger comments.
2. Keep trigger generation in tests/scripts only.

### Validation
- `git status` after normal runtime usage is cleaner.
- `install_local_ui_assets.sh` works on Linux + macOS.

### Acceptance
- No accidental dirtying from routine runs, and no ad hoc trigger residue in source files.

---

## Phase 5: Documentation and Operations Update
Goal: ensure maintainers can run/understand updated checks.

### Files
- [README.md](/home/andrew/Documents/Projects/remora-test/README.md)
- [DEMO_SCRIPT.md](/home/andrew/Documents/Projects/remora-test/DEMO_SCRIPT.md)

### Changes
1. Document strict-mode behavior for:
   - search check (index error threshold)
   - lsp bridge check preconditions and expected events
2. Add a short troubleshooting matrix mapping common failures to exact remediation.
3. Document any `.grail` artifact policy changes.

### Acceptance
- New contributors can run checks and interpret failures without source spelunking.

---

## Suggested Work Breakdown (PR Plan)
1. PR-1: `scripts/test_lsp_event_bridge.sh` deterministic strict behavior + diagnostics.
2. PR-2: `scripts/test_search.sh` strict indexing error accounting + proposal script chat assertions.
3. PR-3: unit tests + smoke replacement + coverage threshold.
4. PR-4: `.grail` artifact policy + portable `install_local_ui_assets.sh` + pricing cleanup.
5. PR-5: README/DEMO docs update.

Each PR should include:
- before/after command outputs,
- explicit risk notes,
- rollback note.

## Verification Matrix (Final)
Run in this order:
1. `devenv shell -- uv run pytest -q`
2. `scripts/test_demo_runtime.sh`
3. `scripts/test_virtual_agents.sh`
4. `scripts/test_reflection_pipeline.sh`
5. `scripts/test_search.sh`
6. `scripts/test_lsp_startup.sh`
7. `RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh`

Optional stress path:
- `RUN_GUARDRAILS_CHECK=1 REQUIRE_OVERFLOW=1 scripts/run_demo_checks.sh`

## Out-of-Scope (for this guide)
- Large functional redesigns in `remora-v2` runtime itself.
- Embeddy upstream local-model backend implementation.

Those should be tracked in separate cross-repo implementation guides.
