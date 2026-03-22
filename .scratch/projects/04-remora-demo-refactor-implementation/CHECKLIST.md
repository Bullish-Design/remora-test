# CHECKLIST

## Foundation
- [ ] Run `devenv shell -- uv sync --extra dev`
- [ ] Capture baseline `remora discover` output
- [ ] Capture baseline API responses (`health`, `nodes`, `events`) if runtime starts

## Core Migration
- [ ] Replace `remora.yaml` legacy keys
- [ ] Create `queries/README.md`
- [ ] Verify no legacy keys remain via `rg`

## Tooling Cleanup
- [ ] Fix stale `pyproject.toml` references (`template_py`, `embeddify`)
- [ ] Create `tests/smoke/test_placeholder.py`
- [ ] Run placeholder test

## Demo Expansion
- [ ] Add `bundles/demo-code-agent`
- [ ] Add `bundles/demo-directory-agent`
- [ ] Add custom tools: `demo_echo.pym`, `rewrite_to_magic.pym`
- [ ] Update bundle overlays

## Reactive Features
- [ ] Configure `virtual_agents`
- [ ] Add `scripts/test_virtual_agents.sh`
- [ ] Add `scripts/test_proposal_flow.sh`

## Validation
- [ ] Add `scripts/test_demo_runtime.sh`
- [ ] Add `scripts/run_demo_checks.sh`
- [ ] Add `tests/integration/test_demo_contract.py`
- [ ] Run required validation matrix
