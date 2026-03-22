# remora-test demo architecture

## Source graph mapping

Remora discovers nodes from `src/`:
- `src/api/*` => API/orchestration function nodes
- `src/services/*` => core domain function nodes
- `src/models/*` => class/function nodes
- `src/utils/*` => helper function nodes

Discovery output is exposed through `/api/nodes` and `/api/edges`.

## Bundle roles

`remora.yaml` maps node types with `bundle_overlays`:
- `function|class|method|file` => `demo-code-agent`
- `directory` => `demo-directory-agent`

This makes local demo bundles first-class and avoids relying only on shipped defaults.

## Virtual agents

Two virtual agents are configured:
- `demo-review-observer` (`review-agent`): subscribes to `node_changed` and `node_discovered` events for `src/**`
- `demo-companion-observer` (`companion`): subscribes to `turn_digested`

They appear as `node_type == "virtual"` nodes and provide reactive, cross-cutting behavior.

## Validation scripts

- `scripts/test_demo_runtime.sh`: basic API and chat contract checks
- `scripts/test_virtual_agents.sh`: verifies observer activity increments on source change
- `scripts/test_proposal_flow.sh`: triggers and validates proposal lifecycle
- `scripts/run_demo_checks.sh`: orchestrates all checks (plus optional search)
