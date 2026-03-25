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
- `demo-review-observer` (`review-agent`): subscribes to `node_changed` and `node_discovered` events
- `demo-companion-observer` (`companion`): subscribes to `turn_digested`

Full-mode virtual behavior is now the default profile in `remora.yaml`.
Constrained fallback remains available in `remora.constrained.yaml` for environments that need reduced observer behavior.
Both virtual agents appear as `node_type == "virtual"` nodes.
Companion checks are opt-in in local scripts because some runtime builds do not emit `turn_digested`.

## Validation scripts

- `scripts/test_demo_runtime.sh`: basic API and chat contract checks
- `scripts/test_virtual_agents.sh`: validates review observer behavior from event deltas; companion can be enforced with `REQUIRE_COMPANION=1`
- `scripts/test_proposal_flow.sh`: triggers and validates proposal lifecycle
- `scripts/test_search.sh`: validates semantic search/index path (required in full check runner)
- `scripts/test_lsp_startup.sh`: validates LSP startup/dependency diagnostics
- `scripts/run_demo_checks.sh`: orchestrates full check sequence (runtime + virtual + proposal + search)
