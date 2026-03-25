# remora-test demo architecture

## Source graph mapping

Remora discovers nodes from:
- `src/` (Python code graph)
- `docs/` (Markdown sections)
- `configs/` (TOML tables)

Discovery output is exposed through `/api/nodes` and `/api/edges`.

## Bundle roles

`remora.yaml` maps node types with `bundle_overlays`:
- `function|class|method|file` => `demo-code-agent`
- `directory` => `demo-directory-agent`

`demo-code-agent` adds deterministic tool trigger tokens and enables `self_reflect`, which emits `turn_digested` after reflection turns.

## Virtual agents

Configured virtual agents:
- `demo-review-observer` (`demo-virtual-observer`): subscribes to `node_changed` and `node_discovered`
- `demo-companion-observer` (`companion`): subscribes to `turn_digested`
- `demo-src-filter-observer` (`demo-virtual-observer`): subscribes to `node_changed` with `path_glob: src/**`
- `demo-docs-filter-observer` (`demo-virtual-observer`): subscribes to `node_changed` with `path_glob: docs/**`

This supports both:
- end-to-end observer/companion flow
- explicit path-filter routing demonstrations

## Evented showcase paths

The demo explicitly showcases:
- reflection pipeline (`agent_complete` -> `turn_digested` -> companion turns)
- SSE replay/resume (`/sse?replay=...`, `Last-Event-ID`, `once=true`)
- cursor focus events (`/api/cursor` -> `cursor_focus`)
- proposal accept/reject lifecycle (`/api/proposals/*`)
- relationship-aware tool execution (`show_dependencies`, `show_importers`, `show_relationship_edges`)

## Validation scripts

Primary scripts:
- `scripts/test_demo_runtime.sh`: baseline API/chat contract checks
- `scripts/test_virtual_agents.sh`: review/companion reactive behavior checks
- `scripts/test_reflection_pipeline.sh`: reflection-to-digest-to-companion flow
- `scripts/test_subscription_filters.sh`: path-scoped virtual routing
- `scripts/test_proposal_flow.sh`: proposal reject path
- `scripts/test_proposal_accept_flow.sh`: proposal accept + materialization path
- `scripts/test_multilang_discovery.sh`: Python/Markdown/TOML discovery checks
- `scripts/test_sse_contract.sh`: SSE replay/resume contract checks
- `scripts/test_cursor_focus.sh`: cursor-to-node event checks
- `scripts/test_relationship_tools.sh`: graph relationship tool checks
- `scripts/test_runtime_guardrails.sh`: metrics/overflow guardrail checks (stress profile)
- `scripts/test_lsp_startup.sh`: LSP startup/dependency diagnostics
- `scripts/test_lsp_event_bridge.sh`: LSP didOpen/didSave -> `content_changed`
- `scripts/test_search.sh`: semantic search/index checks
- `scripts/run_demo_checks.sh`: orchestrated check runner with optional guardrails/LSP bridge gates

## Runtime profiles

- Default profile: `remora.yaml` (full showcase behavior)
- Constrained fallback: `remora.constrained.yaml` (reduced virtual behavior for unstable environments)
- Stress profile: `remora.stress.yaml` (small inbox limits for overflow/guardrail demonstrations)
