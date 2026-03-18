# Remora v2 Demo Report

Date: 2026-03-15  
Project: `/home/andrew/Documents/Projects/remora-test`

## What was done

1. Set up and validated the repo environment with:
   - `devenv shell -- uv sync --extra dev`
   - `devenv shell -- remora discover --project-root .`
2. Ran a bounded full runtime demo:
   - `remora start --project-root . --port 8080 --log-level INFO --log-events --run-seconds 35`
3. Exercised runtime APIs while live:
   - `/api/nodes`
   - `/api/edges`
   - `/api/events`
   - `/sse?replay=5&once=true`
   - `POST /api/chat`
4. Verified model backend reachability:
   - `${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}/models`

## Demo results

- Runtime started and discovery completed successfully.
- Nodes discovered in runtime graph: **18**
- Edges reported: **0**
- Events collected before chat: **20**
- Events collected after chat: **30**
- Chat request status: **sent**
- Chat target node: `src/api/orders.py::create_order`
- Model endpoint returned **1** model.

Artifacts:
- `.scratch/projects/01-remora-v2-demo-report/artifacts/demo_run_summary.txt`
- `.scratch/projects/01-remora-v2-demo-report/artifacts/runtime_demo.log`
- `.scratch/projects/01-remora-v2-demo-report/artifacts/api_nodes.json`
- `.scratch/projects/01-remora-v2-demo-report/artifacts/api_events_after_chat.json`
- `.scratch/projects/01-remora-v2-demo-report/artifacts/sse_replay.txt`

## Issues encountered and fixes

1. **Runtime readiness race**
   - Issue: Immediate API calls after startup sometimes failed.
   - Fix: Added readiness polling on `/api/nodes` before running checks.

2. **Root node chat warnings**
   - Issue: Chatting node `.` triggered status-transition warnings.
   - Fix: Updated chat tests to target a non-directory node first.

3. **Guide/runtime mismatch**
   - Issue: Guide fields/endpoints did not fully match installed runtime (`bundle_overlays`, `/api/health`).
   - Fix: Used runtime-compatible config (`bundle_mapping`) and validated with available endpoints.

4. **Open observation: edges are empty**
   - Not blocking for startup/chat demo.
   - Needs follow-up to confirm whether this is expected for current parser/runtime behavior.

## Follow-up: edge generation investigation (completed 2026-03-15)

Root-cause findings:

- `NodeStore` has an `edges` table and `add_edge()` method, but runtime code paths do not call it.
- Discovery/reconciliation persists hierarchy via `parent_id` on nodes, not via rows in `edges`.
- The web dashboard loads links from `/api/edges`, which reads only the `edges` table.
- DB evidence from this run:
  - `nodes = 18`
  - `nodes_with_parent = 17`
  - `edges = 0`
  - `missing_parent_refs = 0`

Conclusion:

The current runtime stores hierarchical relationships in `nodes.parent_id` but does not materialize those relationships into `edges`, so the graph has nodes but no rendered links.

Investigation notes artifact:
- `.scratch/projects/01-remora-v2-demo-report/artifacts/edge_investigation.md`

## What we should do next

1. **Implement containment edge materialization**
   - During reconciliation/projection, upsert `contains` edges from `parent_id` into `edges`.
   - Ensure stale containment edges are cleaned up when nodes are removed or re-parented.

2. **Add a stable demo check script**
   - Keep bounded runtime + readiness polling + API/SSE/chat verification as an automated smoke test target.
   - Add an assertion that `/api/edges` becomes non-empty after discovery.

3. **Align guide to installed runtime**
   - Update setup guide to reflect current config keys and available API endpoints.

4. **Optional short-term fallback**
   - If edge materialization is not merged yet, synthesize containment edges in `/api/edges` from `nodes.parent_id` when table is empty.

5. **Optional UX demo pass**
   - Run `remora start` without `--run-seconds` and walk through UI + SSE + chat manually for presentation.
