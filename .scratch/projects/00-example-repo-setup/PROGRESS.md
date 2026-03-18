# Progress

## Done
- [x] Read `.scratch/CRITICAL_RULES.md`.
- [x] Read `.scratch/projects/00-example-repo-setup/EXAMPLE_SETUP_GUIDE.md`.
- [x] Created `PLAN.md` and `ASSUMPTIONS.md`.
- [x] Created remaining standard files (`PROGRESS.md`, `CONTEXT.md`, `DECISIONS.md`, `ISSUES.md`).
- [x] Updated `remora.yaml` to the guide shape, then corrected key naming to runtime-compatible `bundle_mapping`.
- [x] Added `.remora/` to `.gitignore`.
- [x] Added smoke-test helper script at `scripts/test_remora.sh` and made it executable.
- [x] Verified dependency sync with `devenv shell -- uv sync --extra dev`.
- [x] Verified discovery with `devenv shell -- remora discover --project-root .` (11 nodes discovered).
- [x] Verified bounded startup + web APIs via `remora start --run-seconds 15` and localhost API checks.
- [x] Verified configured model endpoint responds (`/v1/models` returned 1 model).
- [x] Ran `scripts/test_remora.sh` against bounded runtime; nodes/events/chat checks succeeded.

## In Progress
- [ ] None.

## Pending
- [ ] None.
