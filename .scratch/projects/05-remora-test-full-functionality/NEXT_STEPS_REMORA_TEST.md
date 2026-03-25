# Next Steps for remora-test

Date: 2026-03-24  
Repository: `/home/andrew/Documents/Projects/remora-test`

## Scope

This document covers only changes that should be implemented in this repository.

Goals:
- switch demo default to full virtual-agent behavior
- strengthen behavior-level validation scripts
- make search checks required in the local demo contract
- add live integration tests
- add an explicit LSP demo path
- keep docs/config/scripts consistent

Out of scope:
- fixing upstream default bundle/tool bugs in `remora-v2` (tracked in `NEXT_STEPS_REMORA_V2.md`)

## Execution Order Override

Per current implementation direction, do **not** start with Phase 1.
Use this execution order:
1. Phase 2
2. Phase 3
3. Phase 4
4. Phase 5
5. Phase 6
6. Phase 1 (final switch to full-mode virtual-agent defaults)

## Phase 0: Baseline and Branching

1. Create a work branch.
```bash
git checkout -b feat/full-demo-functionality
```

2. Capture baseline artifacts.
```bash
mkdir -p .scratch/projects/05-remora-test-full-functionality/artifacts
devenv shell -- remora discover --project-root . \
  | tee .scratch/projects/05-remora-test-full-functionality/artifacts/discover_before.txt
```

3. Snapshot runtime state while current runtime is running.
```bash
BASE="http://127.0.0.1:8080"
curl -sS "$BASE/api/nodes" | tee .scratch/projects/05-remora-test-full-functionality/artifacts/nodes_before.json
curl -sS "$BASE/api/events?limit=200" | tee .scratch/projects/05-remora-test-full-functionality/artifacts/events_before.json
```

## Phase 1: Restore Full Virtual-Agent Config

Primary file: [remora.yaml](/home/andrew/Documents/Projects/remora-test/remora.yaml)

1. Set `demo-review-observer` role to `review-agent`.
2. Keep `demo-companion-observer` role as `companion`.
3. Keep review observer subscriptions on `node_changed` and `node_discovered`.
4. Do not enforce `path_glob` locally unless runtime event payload/path filtering is confirmed functional.
5. Keep constrained mode available only as explicit fallback profile:
- add `remora.constrained.yaml` for the `demo-virtual-observer` path if needed.
- keep default `remora.yaml` as full mode.

Target full-mode virtual agent block:

```yaml
virtual_agents:
  - id: "demo-review-observer"
    role: "review-agent"
    subscriptions:
      - event_types: ["node_changed", "node_discovered"]

  - id: "demo-companion-observer"
    role: "companion"
    subscriptions:
      - event_types: ["turn_digested"]
```

## Phase 2: Harden Virtual-Agent Verification

Primary file: [scripts/test_virtual_agents.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_virtual_agents.sh)

Replace pure liveness checks with behavior checks.

Required script assertions:
1. Review observer turn/model activity increases after source change.
2. Review observer emits meaningful work evidence:
- tool usage evidence (`review_diff`, `submit_review`, or equivalent)
- or review output message evidence
3. Companion observer emits aggregation evidence when enabled (`REQUIRE_COMPANION=1`):
- `aggregate_digest` tool evidence or comparable companion output.
4. Script prints diagnostic event excerpts on failure.

Implementation details:
1. Poll events with timeout window.
2. Parse with robust `jq` filters tolerant of event payload differences.
3. Keep temp trigger file under `src/.remora_demo_trigger/` and clean up.

## Phase 3: Make Search Required in Demo Checks

Primary files:
- [scripts/run_demo_checks.sh](/home/andrew/Documents/Projects/remora-test/scripts/run_demo_checks.sh)
- [scripts/test_search.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_search.sh)
- [README.md](/home/andrew/Documents/Projects/remora-test/README.md)

Changes:
1. Remove optional search gate from `run_demo_checks.sh`.
2. Always execute `scripts/test_search.sh`.
3. Harden `test_search.sh` to fail clearly when:
- indexing fails
- search endpoint returns invalid payload
- backend is unavailable
4. Update docs so search is either:
- required for full mode, or
- explicitly split: `full mode` vs `constrained mode`.

Note:
- dependency provisioning or backend fixes in upstream are tracked separately, but this repo must enforce expected contract for its selected mode.

## Phase 4: Add Live Integration Behavior Tests

Primary target:
- new [tests/integration/test_demo_live_contract.py](/home/andrew/Documents/Projects/remora-test/tests/integration/test_demo_live_contract.py)

Keep existing structural test:
- [tests/integration/test_demo_contract.py](/home/andrew/Documents/Projects/remora-test/tests/integration/test_demo_contract.py)

Live test coverage:
1. runtime health + graph endpoints (`/api/health`, `/api/nodes`, `/api/edges`)
2. virtual-agent behavior evidence after trigger
3. proposal flow lifecycle (create, diff, reject)
4. search/index flow

Execution model:
1. gate live tests behind env var, for example `REMORA_LIVE_BASE_URL`.
2. mark tests (`@pytest.mark.live`) and skip cleanly when runtime unavailable.

## Phase 5: Add LSP Demo Path

Primary files:
- [README.md](/home/andrew/Documents/Projects/remora-test/README.md)
- [DEMO_SCRIPT.md](/home/andrew/Documents/Projects/remora-test/DEMO_SCRIPT.md)
- new [scripts/test_lsp_startup.sh](/home/andrew/Documents/Projects/remora-test/scripts/test_lsp_startup.sh)

Required additions:
1. Document two supported LSP startup paths:
```bash
devenv shell -- remora start --project-root . --port 8080 --lsp
devenv shell -- remora lsp --project-root .
```
2. Add `test_lsp_startup.sh` to validate startup behavior and dependency diagnostics.
3. Document exact remediation if LSP extras are missing.

## Phase 6: Docs and Config Parity

Files to align:
- [remora.yaml](/home/andrew/Documents/Projects/remora-test/remora.yaml)
- [docs/architecture.md](/home/andrew/Documents/Projects/remora-test/docs/architecture.md)
- [README.md](/home/andrew/Documents/Projects/remora-test/README.md)
- [DEMO_SCRIPT.md](/home/andrew/Documents/Projects/remora-test/DEMO_SCRIPT.md)
- [scripts/run_demo_checks.sh](/home/andrew/Documents/Projects/remora-test/scripts/run_demo_checks.sh)

Required outcome:
1. default mode documented as full behavior.
2. fallback constrained mode (if retained) clearly labeled and isolated.
3. no contradictions between docs and executable scripts.

## Definition of Done (remora-test)

1. default `remora.yaml` uses `review-agent` + `companion` for virtual agents.
2. `test_virtual_agents.sh` validates meaningful behavior, not just process start.
3. `run_demo_checks.sh` includes search by default for full mode.
4. live integration tests exist for runtime, virtual, proposal, and search behavior.
5. LSP run path is documented and validated by script.
6. docs/config/scripts agree on one canonical full-mode flow.

## Suggested Commit Plan

1. `feat(config): switch default virtual agent config to full-mode roles`
2. `test(virtual): upgrade virtual agent check from liveness to behavior`
3. `feat(checks): make search mandatory in full-mode demo checks`
4. `test(integration): add live runtime behavior contract tests`
5. `feat(lsp): add LSP demo docs and startup verification script`
6. `docs(demo): align README/architecture/demo script with full-mode contract`
