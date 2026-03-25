# CHECKLIST

## Foundation
- [ ] Run `devenv shell -- uv sync --extra dev` (historical execution not re-captured in this folder)
- [ ] Capture baseline `remora discover` output (artifact not present in this folder)
- [ ] Capture baseline API responses (`health`, `nodes`, `events`) if runtime starts (artifact not present in this folder)

## Core Migration
- [x] Replace `remora.yaml` legacy keys
- [x] Create `queries/README.md`
- [x] Verify no legacy keys remain via `rg`

## Tooling Cleanup
- [x] Fix stale `pyproject.toml` references (`template_py`, `embeddify`)
- [x] Create `tests/smoke/test_placeholder.py`
- [x] Run placeholder test

## Demo Expansion
- [x] Add `bundles/demo-code-agent`
- [x] Add `bundles/demo-directory-agent`
- [x] Add custom tools: `demo_echo.pym`, `rewrite_to_magic.pym`
- [x] Update bundle overlays

## Reactive Features
- [x] Configure `virtual_agents`
- [x] Add `scripts/test_virtual_agents.sh`
- [x] Add `scripts/test_proposal_flow.sh`

## Validation
- [x] Add `scripts/test_demo_runtime.sh`
- [x] Add `scripts/run_demo_checks.sh`
- [x] Add `tests/integration/test_demo_contract.py`
- [ ] Run required validation matrix (needs fresh run artifact capture)
