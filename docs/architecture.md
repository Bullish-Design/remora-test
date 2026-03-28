# remora-test demo architecture

## Source graph mapping

Remora discovers nodes from:
- `src/` (Python code graph)
- `docs/` (Markdown sections)
- `configs/` (TOML tables)

Discovery output is exposed through `/api/nodes` and `/api/edges`.

## Bundle roles

`demo/00_repo_baseline/config/remora.yaml` maps node types with `bundle_overlays`:
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

## Validation checks

Primary Python checks (under `demo/00_repo_baseline/checks/`):
- `check_runtime.py`: baseline API/chat contract checks
- `check_virtual_agents.py`: review/companion reactive behavior checks
- `check_reflection.py`: reflection-to-digest-to-companion flow
- `check_subscriptions.py`: path-scoped virtual routing
- `check_proposal_reject.py`: proposal reject path
- `check_proposal_accept.py`: proposal accept + materialization path with cleanup
- `check_discovery.py`: Python/Markdown/TOML discovery checks
- `check_sse.py`: SSE replay/resume contract checks
- `check_cursor.py`: cursor-to-node event checks
- `check_relationships.py`: graph relationship tool checks
- `check_guardrails.py`: metrics/overflow guardrail checks (stress profile)
- `check_lsp_startup.py`: LSP startup/dependency diagnostics
- `check_lsp_bridge.py`: LSP didOpen/didSave -> change events with fixture restore safety
- `check_search.py`: semantic search/index checks with strict error thresholds
- `check_ui_dependencies.py`: CDN reachability + UI dependency mode diagnostics
- `check_ui_playwright.py`: headless browser UI render smoke via Playwright screenshot
- `runner.py`: orchestrated check runner (`--strict`, capability flags, optional filtered runs)

## Repository artifact policy

Runtime-generated `.grail/*/check.json` and `.grail/*/run.log` are ignored and untracked.
Stable `.grail` sources (such as `monty_code.py`, `inputs.json`, `externals.json`, and `stubs.pyi`) remain tracked.

## Runtime profiles

- Default profile: `demo/00_repo_baseline/config/remora.yaml` (full showcase behavior)
- Constrained fallback: `demo/00_repo_baseline/config/remora.constrained.yaml` (reduced virtual behavior for unstable environments)
- Stress profile: `demo/00_repo_baseline/config/remora.stress.yaml` (small inbox limits for overflow/guardrail demonstrations)
