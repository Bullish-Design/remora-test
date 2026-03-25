# CHECKLIST

## Setup
- [x] Create project folder `.scratch/projects/05-remora-test-full-functionality`
- [x] Move `NEXT_STEPS*.md` into project folder
- [x] Create branch `feat/full-demo-functionality`
- [x] Capture baseline discover output
- [x] Capture baseline nodes/events snapshots

## Config
- [x] (Deferred to final phase) Update `remora.yaml` default virtual roles to full mode
- [x] (Deferred to final phase) Reintroduce scoped `path_glob: "src/**"` for review observer
- [x] (Deferred to final phase) Decide constrained fallback strategy (`remora.constrained.yaml` or remove)

## Validation Scripts
- [x] Rewrite `scripts/test_virtual_agents.sh` to assert behavior outcomes
- [x] Make search required in `scripts/run_demo_checks.sh`
- [x] Harden `scripts/test_search.sh` with strict pass/fail checks
- [x] Add `scripts/test_lsp_startup.sh`

## Tests
- [x] Add `tests/integration/test_demo_live_contract.py`
- [x] Mark/guard live tests via env var
- [x] Keep structural contract tests passing

## Docs
- [x] Update README for pre-switch parity + LSP/search behavior
- [x] Update DEMO_SCRIPT for pre-switch parity + LSP path
- [x] Update docs/architecture to match actual config and scripts

## Final Validation
- [ ] Run full check flow end-to-end
- [ ] Update project `PROGRESS.md`, `DECISIONS.md`, `ISSUES.md`
