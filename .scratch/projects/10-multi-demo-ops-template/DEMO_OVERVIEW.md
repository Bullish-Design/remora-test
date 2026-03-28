# Demo Overview — Multi-Demo Operations Plan for `remora-test`

## Goal
Run many independent remora demos from one repo with zero cross-contamination and one-command full reset per demo.

## Design Principles
1. Each demo is isolated by ID (`idea6_click`, `idea7_event_storm`, etc.).
2. Shared logic lives in common scripts; demo-specific scripts only declare metadata.
3. Every demo can be fully wiped (clone, workspace DB, temp artifacts, logs) and rebuilt from scratch.
4. Rehearsals are reproducible by pinning `remora-v2` revision for the demo cycle.

## Proposed Repository Layout
```text
remora-test/
  demo/
    idea6_click/
      README.md
      PRESENTER_CUE_SHEET.md
      demo.env.example
    idea7_event_storm/
      README.md
      PRESENTER_CUE_SHEET.md
      demo.env.example
  scripts/
    democtl.py                     # common control plane for all demos
    _lib/
      manifest.py                  # manifest loading/validation
      paths.py                     # per-demo path derivation + delete safety
      http.py                      # API polling helpers
      runtime.py                   # start/stop + search-stack helpers
      commands.py                  # setup/start/status/queries/cleanup/wipe/verify
  tests/
    unit/
      test_demo_manifests.py
      test_demo_isolation_contracts.py
    integration/
      test_demo_contract.py
```

## Manifest-Driven Demo Contract
Create one manifest per demo (for example `demo/idea6_click/demo.yaml`) with required fields:

```yaml
demo_id: idea6_click
repo_url: https://github.com/pallets/click.git
repo_dir: /tmp/remora-demo-idea6-click
project_root: /tmp/remora-demo-idea6-click
config_path: demo/idea6_click/config/remora.yaml
workspace_root: .remora-idea6
port: 8080
base_url: http://127.0.0.1:8080
requires:
  web: true
  search: true
  lsp: true
```

Invariants:
1. `demo_id`, `repo_dir`, `workspace_root`, and `port` must be unique across demos.
2. `repo_dir` must be under `/tmp/remora-demo-*`.
3. `repo_dir` may be omitted when `repo_url: local`.
4. No manifest may point `project_root` at `remora-v2`.

## Common Script Strategy
Implement one shared command entrypoint:

```bash
python scripts/democtl.py <command> --demo <demo_id> [flags]
```

Commands:
1. `setup`
Behavior: clone/update target repo, generate config file from manifest, verify toolchain.

2. `start`
Behavior: launch `remora start` using manifest paths and port.

3. `status`
Behavior: poll `/api/health` and print node/edge quick counts.

4. `queries`
Behavior: run demo-standard evidence queries (health, counts, edge-type distribution, hotspots, SSE sample).

5. `cleanup`
Behavior: remove only runtime artifacts (workspace DB/logs, transient output), preserve clone by default.

6. `wipe`
Behavior: full reset for fresh run. Remove clone dir, workspace artifacts, generated config, and demo logs.

7. `rehearse`
Behavior: `wipe -> setup -> start instructions -> queries` in a deterministic operator flow.

8. `verify`
Behavior: run demo-local Python checks (`demo/<id>/checks/runner.py`) with default or strict capability gating.

## Fresh-Run Guarantee
Define “fresh demo run” as:
1. No existing clone at demo repo dir.
2. No existing remora workspace directory (from `workspace_root`).
3. No stale process on demo port.
4. Config regenerated from manifest.

`wipe` should enforce all four conditions and print a final checklist.

## Safety Rules for Wipe/Cleanup
1. Refuse deletion unless target path starts with `/tmp/remora-demo-` or is a known workspace under that clone.
2. Refuse to run if computed delete path is `/`, empty, home dir, repo root, or parent traversal.
3. Require explicit `--force` for destructive operations in non-interactive mode.
4. Print every path to be deleted before deletion.

## Operational Workflow
1. Add new demo folder + manifest + docs.
2. Run `democtl.py setup --demo <id>`.
3. Start runtime with `democtl.py start --demo <id>`.
4. Validate with `democtl.py status/queries --demo <id>`.
5. After rehearsal, run `democtl.py wipe --demo <id> --force`.

## Testing Plan
Unit tests:
1. Manifest validation (required fields, uniqueness, safe paths).
2. Path safety checks for cleanup/wipe.
3. Command rendering for `remora start`.

Integration tests:
1. Contract test confirms required demo files and `democtl.py` exist.
2. Wipe test verifies demo temp directories are removed and recreated cleanly.
3. Cross-demo isolation test verifies unique workspace roots, repo dirs, and ports.

## LLM Agent Verification Requirement
Every demo must expose a deterministic verification path that an LLM agent can run end-to-end without ad-hoc manual steps.

Required:
1. `democtl verify --demo <id>` command that executes the demo's full automated validation suite.
2. Verification must include web/API contract checks (`/api/health`, `/api/nodes`, `/api/edges`, `/api/events`, `/sse`).
3. Verification must include LSP checks (startup + bridge behavior) when LSP is in demo scope.
4. Verification must include semantic search/index checks when search is in demo scope.
5. Verification must emit clear pass/fail output and explicit skip reasons for optional dependencies.
6. Verification must be runnable in both:
   - default mode (best-effort, dependency-aware skips), and
   - strict mode (no skips allowed for scoped capabilities).

Suggested interface:
```bash
python scripts/democtl.py verify --demo <id>
python scripts/democtl.py verify --demo <id> --strict
```

## Rollout Plan
Phase 1:
1. Implement `democtl.py` + `_lib/*` shared modules.
2. Convert Idea #6 to manifest-driven format.

Phase 2:
1. Add second demo to prove multi-demo isolation.
2. Add contract and isolation tests.

Phase 3:
1. Add presenter-facing docs template and checklist generation.
2. Add CI smoke target for `setup` + `wipe` on at least one demo.

## Definition of Done
1. At least two demos run through shared `democtl.py` flow.
2. `wipe` produces a deterministic fresh state for each demo.
3. Isolation tests pass and prevent config/path collisions.
4. Operator can rehearse any demo with one command sequence and no manual cleanup.
