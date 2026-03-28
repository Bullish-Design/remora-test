# CLAUDE.md

## Repository Purpose

`remora-test` hosts isolated demo projects for validating and presenting `remora-v2` behavior.

Primary demo today:
- `demo/00_repo_baseline`

## Key Paths

- Shared control plane: `scripts/democtl.py`
- Shared democtl library: `scripts/_lib/`
- Demo manifest: `demo/<demo_id>/demo.yaml`
- Demo checks: `demo/<demo_id>/checks/`
- Demo scripts/utilities: `demo/<demo_id>/scripts/`
- Baseline demo config: `demo/00_repo_baseline/config/remora.yaml`

## Core Commands

Use `devenv shell --` when tooling is not available on the host shell.

Setup/start:

```bash
python scripts/democtl.py setup --demo 00_repo_baseline --clean-workspace
python scripts/democtl.py start --demo 00_repo_baseline
```

Status/queries/verify:

```bash
python scripts/democtl.py status --demo 00_repo_baseline
python scripts/democtl.py queries --demo 00_repo_baseline
python scripts/democtl.py verify --demo 00_repo_baseline
python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

Destructive reset:

```bash
python scripts/democtl.py wipe --demo 00_repo_baseline --force
```

## Isolation and No-Cross-Contamination Rules

- Each demo owns a unique `demo_id`, `port`, and `workspace_root`.
- `repo_url: local` demos may omit `repo_dir`.
- Non-local demos must use `repo_dir` under `/tmp/remora-demo-*`.
- `wipe` and `cleanup` must only delete allowlisted demo-owned paths.
- A demo must never target `remora-v2` directly as its `project_root`.

## Verification Contract for Agents

- Every demo must provide a deterministic Python check runner at `demo/<id>/checks/runner.py`.
- `democtl verify` is the single entrypoint agents should use for full validation.
- Verify output must clearly report pass/fail/skip with reasons.
- Strict mode should enforce required capabilities (web/search/LSP, based on manifest scope and flags).

## Testing Conventions

- Unit/contracts: `tests/unit/` and `tests/integration/test_demo_contract.py`
- Live runtime tests are opt-in and marked `@pytest.mark.live`.
- Prefer `pytest --no-cov` for targeted local iteration; run full defaults for CI-level checks.
