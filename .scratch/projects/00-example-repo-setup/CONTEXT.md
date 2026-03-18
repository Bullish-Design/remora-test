# Context

- Active project: `00-example-repo-setup`.
- Request completed:
  1. Project directory now contains all standard template files.
  2. `remora-test` has been configured and validated for remora-v2 demo startup.
- Notable compatibility findings versus guide:
  - Installed remora expects `bundle_mapping` (not `bundle_overlays`); config was adjusted to match runtime.
  - Current web API exposes `/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`, `/sse`; `/api/health` is not present in this build.
- Verification results:
  - `devenv shell -- uv sync --extra dev` succeeded.
  - `devenv shell -- remora discover --project-root .` succeeded with 11 discovered source nodes.
  - Bounded startup (`--run-seconds 15`) succeeded; localhost API checks returned: nodes=18, edges=0, events=5.
  - Model backend check succeeded: `${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}/models` returned 1 model.
  - `scripts/test_remora.sh` succeeded against a bounded runtime (nodes listed, events fetched, chat accepted).
- Supporting artifacts:
  - Startup log: `.scratch/projects/00-example-repo-setup/remora_start_smoke.log`
  - Smoke helper script: `scripts/test_remora.sh`
  - Smoke script output: `.scratch/projects/00-example-repo-setup/test_remora_output.log`
