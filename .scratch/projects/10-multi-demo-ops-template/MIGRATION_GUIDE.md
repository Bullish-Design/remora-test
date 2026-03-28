# Migration Guide — Move Existing Root Demo into Its Own Subdirectory

## Objective
Migrate the current "repo demo" that is spread across `remora-test` repo root into a single isolated demo package under `demo/`, without losing current functionality.

Primary outcomes:
1. Existing demo is self-contained and runnable as one demo ID.
2. Shared setup/cleanup/wipe controls can treat it like any other demo.
3. Fresh-run reset is deterministic and safe.

## Recommended Demo ID
Use `repo_baseline` for the existing demo.

Target location:
```text
demo/repo_baseline/
```

## Current-State Inventory (What Is Coupled to Repo Root)
Current root-coupled demo assets:
1. Configs: `remora.yaml`, `remora.constrained.yaml`, `remora.stress.yaml`
2. Bundles: `bundles/demo-*`
3. Queries: `queries/README.md` (+ future query overrides)
4. Demo scripts: `scripts/test_*.sh`, `scripts/run_demo_checks.sh`, probes/utils used by those scripts
5. Demo docs: `README.md`, `DEMO_SCRIPT.md`, `DEMO_SCRIPT_LIVE.md`
6. Contract tests: `tests/integration/test_demo_contract.py`, plus script-contract unit tests
7. Live test assumptions about project root and sample file paths in `tests/integration/test_demo_live_contract.py`

## Target End State

### Directory Model
```text
remora-test/
  demo/
    repo_baseline/
      README.md
      PRESENTER_CUE_SHEET.md
      demo.yaml
      config/
        remora.yaml
        remora.constrained.yaml
        remora.stress.yaml
      bundles/
        demo-code-agent/...
        demo-directory-agent/...
        demo-virtual-observer/...
      queries/
        README.md
      scripts/
        test_demo_runtime.sh
        test_virtual_agents.sh
        test_reflection_pipeline.sh
        test_subscription_filters.sh
        test_proposal_flow.sh
        test_proposal_accept_flow.sh
        test_multilang_discovery.sh
        test_sse_contract.sh
        test_cursor_focus.sh
        test_relationship_tools.sh
        test_search.sh
        test_lsp_startup.sh
        test_lsp_event_bridge.sh
        test_runtime_guardrails.sh
        run_demo_checks.sh
        install_local_ui_assets.sh
        reconcile_demo.sh
        lsp_event_bridge_probe.py
        mock_embedder_server.py
```

### Optional (Stronger Isolation)
If you want complete separation from repo-root fixture content, move demo fixture code into:
```text
demo/repo_baseline/fixture/
  src/
  docs/
  configs/
```
Then set project root for this demo to `demo/repo_baseline/fixture`.

If you want lower risk first, keep current fixture files in repo root for Phase 1 and isolate orchestration assets first.

## Migration Strategy (Phased)

## Phase 0 — Baseline and Safety Net
1. Create a branch: `feature/migrate-root-demo-to-subdir`.
2. Record current passing baseline:
   - `devenv shell -- pytest tests/integration/test_demo_contract.py tests/unit/test_scripts_contracts.py -q --tb=short`
3. Snapshot script behavior by saving outputs from:
   - `scripts/test_demo_runtime.sh`
   - `scripts/run_demo_checks.sh` (or partial subset)

Exit gate:
- Current baseline is known-good before file moves.

## Phase 1 — Create New Demo Package Skeleton
1. Create `demo/repo_baseline/` and subdirectories: `config/`, `bundles/`, `queries/`, `scripts/`.
2. Add `demo/repo_baseline/demo.yaml` (manifest) with unique identifiers:

```yaml
demo_id: repo_baseline
repo_url: local
repo_dir: /tmp/remora-demo-repo-baseline
config_file: remora.yaml
workspace_root: .remora-repo-baseline
port: 8080
project_root_mode: local_fixture
```

3. Add `demo/repo_baseline/README.md` and `PRESENTER_CUE_SHEET.md` placeholders.

Exit gate:
- Package skeleton exists; no behavioral changes yet.

## Phase 2 — Move Assets with Deterministic Path Updates
Move files using `git mv` so history is preserved.

### File Move Map
1. `bundles/demo-code-agent` -> `demo/repo_baseline/bundles/demo-code-agent`
2. `bundles/demo-directory-agent` -> `demo/repo_baseline/bundles/demo-directory-agent`
3. `bundles/demo-virtual-observer` -> `demo/repo_baseline/bundles/demo-virtual-observer`
4. `queries/README.md` -> `demo/repo_baseline/queries/README.md`
5. `remora.yaml` -> `demo/repo_baseline/config/remora.yaml`
6. `remora.constrained.yaml` -> `demo/repo_baseline/config/remora.constrained.yaml`
7. `remora.stress.yaml` -> `demo/repo_baseline/config/remora.stress.yaml`
8. Demo scripts from `scripts/` -> `demo/repo_baseline/scripts/`
9. `DEMO_SCRIPT.md` -> `demo/repo_baseline/README.md` (merge/refactor content)
10. `DEMO_SCRIPT_LIVE.md` -> `demo/repo_baseline/PRESENTER_CUE_SHEET.md` (merge/refactor content)

### Path Rewrites Required in Config
In each moved config file:
1. `query_search_paths: ["queries/", "@default"]` -> `query_search_paths: ["../queries/", "@default"]` if config remains in `config/`.
2. `bundle_search_paths: ["bundles/", "@default"]` -> `bundle_search_paths: ["../bundles/", "@default"]`.
3. `workspace_root` -> demo-unique value (for example `.remora-repo-baseline`).

Note: if you prefer simpler relative paths, place config at `demo/repo_baseline/remora.yaml` beside `bundles/` and `queries/`.

Exit gate:
- All assets relocated under demo subdirectory and config references resolve.

## Phase 3 — Script Hardening for Relocatability
Every demo script should be runnable from any CWD.

In each shell script:
1. Compute script directory:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
```
2. Replace hardcoded `scripts/...` chained calls with `"${SCRIPT_DIR}/..."`.
3. Replace implicit project root `.` with explicit `PROJECT_ROOT` default:
```bash
PROJECT_ROOT="${PROJECT_ROOT:-$DEMO_ROOT}"
```
(or `$DEMO_ROOT/fixture` if using fixture subdir)
4. Replace config defaults with explicit path:
```bash
CONFIG_PATH="${CONFIG_PATH:-$DEMO_ROOT/config/remora.yaml}"
```
5. Keep `BASE` overridable, but avoid embedded assumptions beyond default port.

In Python scripts:
1. Resolve relative files from `Path(__file__).resolve().parent`.
2. Add CLI args for `--project-root`, `--config`, `--base` where appropriate.

Exit gate:
- Scripts pass when invoked from repo root and from within `demo/repo_baseline/scripts`.

## Phase 4 — Add Shared Control Plane (`democtl`) and Wipe Semantics
Implement common entrypoint (from overview):
```bash
python scripts/democtl.py <setup|start|status|queries|cleanup|wipe|rehearse> --demo repo_baseline
```

For `repo_baseline`, `wipe` must delete:
1. `/tmp/remora-demo-repo-baseline` clone (if used)
2. Demo workspace path (for example `<project_root>/.remora-repo-baseline`)
3. Generated config artifacts (if generated)
4. Demo run logs in a demo-specific temp/log directory

Safety checks:
1. Reject delete targets outside allowlist roots.
2. Reject empty/home/root/parent-traversal paths.
3. Require `--force` for destructive operations in non-interactive mode.

Exit gate:
- One command produces fully clean state for `repo_baseline`.

## Phase 5 — Update Tests and Contracts

## Update Integration Contract
Revise `tests/integration/test_demo_contract.py` to check new paths under `demo/repo_baseline/...` and shared `scripts/democtl.py`.

## Add Isolation Tests
Add `tests/unit/test_demo_isolation_contracts.py`:
1. unique `demo_id`
2. unique `workspace_root`
3. unique `repo_dir`
4. unique `port`
5. manifests do not target `remora-v2` or repo root as mutable workspace

## Update Script Contract Tests
Either:
1. Migrate existing checks in `tests/unit/test_scripts_contracts.py` to point to `demo/repo_baseline/scripts/...`, or
2. Keep wrapper scripts at root temporarily and test both layers.

## Update Live Contract Tests
In `tests/integration/test_demo_live_contract.py`:
1. Add optional env vars:
   - `REMORA_LIVE_PROJECT_ROOT`
   - `REMORA_LIVE_CONFIG_PATH`
2. Remove hard dependency on repo-root relative assumptions where possible.

Exit gate:
- Tests validate new demo package structure and isolation invariants.

## Phase 6 — Documentation Cutover
1. Top-level `README.md` becomes index to demos.
2. Move old command walkthrough into `demo/repo_baseline/README.md`.
3. Keep a short deprecation notice for old root script paths (one release cycle).

Recommended temporary compatibility wrappers (optional):
- Keep root `scripts/test_*.sh` wrappers that exec `demo/repo_baseline/scripts/test_*.sh`.
- Remove wrappers after all docs/CI references are updated.

Exit gate:
- Operator reads one demo-specific README and runs only demo-scoped commands.

## Detailed Checklist (Execution Order)
1. Create demo skeleton + manifest.
2. `git mv` configs, bundles, queries, scripts, demo docs.
3. Update all moved scripts to use `SCRIPT_DIR` + `DEMO_ROOT`.
4. Update config relative paths and demo-specific `workspace_root`.
5. Add/enable `democtl.py` commands for `repo_baseline`.
6. Add `cleanup` + `wipe` tests.
7. Update integration + unit contract tests.
8. Update top-level README index and old references.
9. Run validation suite.
10. Rehearse `wipe -> setup -> start -> queries` twice to confirm fresh-run determinism.

## Validation Commands
Run from repo root:

```bash
# static checks
bash -n demo/repo_baseline/scripts/*.sh
devenv shell -- python -m py_compile demo/repo_baseline/scripts/*.py scripts/democtl.py

# contract tests
devenv shell -- pytest \
  tests/integration/test_demo_contract.py \
  tests/unit/test_scripts_contracts.py \
  tests/unit/test_demo_isolation_contracts.py \
  -q --tb=short

# migration smoke
python scripts/democtl.py wipe --demo repo_baseline --force
python scripts/democtl.py setup --demo repo_baseline
# start in separate shell:
# python scripts/democtl.py start --demo repo_baseline
python scripts/democtl.py status --demo repo_baseline
python scripts/democtl.py queries --demo repo_baseline
```

## Risks and Mitigations
1. Risk: path regressions after moving scripts.
Mitigation: enforce `SCRIPT_DIR`/`DEMO_ROOT` pattern in every script.

2. Risk: stale state from old `.remora` contaminates behavior.
Mitigation: switch to demo-specific `workspace_root` and require `wipe` during rehearsal.

3. Risk: tests still assume old root paths.
Mitigation: update contract tests first, keep temporary wrapper scripts only if needed.

4. Risk: accidental destructive wipes.
Mitigation: strict allowlist deletion guards and `--force` confirmation.

## Rollback Plan
If migration breaks runtime/demo flow:
1. Re-enable root wrappers (or keep them until migration is fully green).
2. Restore README references to old paths temporarily.
3. Re-run old baseline scripts to verify core behavior.
4. Resume migration in smaller slices (assets first, then scripts, then tests).

## Definition of Done
1. Existing repo demo runs entirely from `demo/repo_baseline/` assets.
2. No required demo asset remains root-coupled.
3. `democtl wipe --demo repo_baseline --force` yields a provably clean state.
4. Contract/isolation tests pass.
5. Top-level docs point to demo subdirectory workflows, not root scripts.
