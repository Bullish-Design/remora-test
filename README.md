# remora-test-demo

## What This Repository Demonstrates

This repository demonstrates current `remora-v2` runtime capabilities against a small Python codebase:
- code discovery into remora nodes/edges
- chat-driven node interaction
- local bundle/tool overrides
- virtual agent reactive workflows
- proposal (human-in-the-loop) review flow
- semantic search/index flow (required by full demo checks)

## Prerequisites

- `devenv`
- `uv`
- `jq`
- local `remora-v2` checkout at `../remora-v2`
- optional model endpoint (default: `http://remora-server:8000/v1`)
- embeddy backend for semantic search (required for full check runner)

Environment variables (optional):
- `REMORA_MODEL_BASE_URL`
- `REMORA_MODEL_API_KEY`
- `REMORA_MODEL`
- `REMORA_EMBEDDY_URL` (required for full check runner)

## Quick Start

```bash
devenv shell -- uv sync --extra dev
devenv shell -- remora discover --project-root .
devenv shell -- remora start --project-root . --port 8080 --log-events
```

For a full copy/paste walkthrough (including high-impact demo flows), see:
- `DEMO_SCRIPT.md`

## API Smoke Verification

With runtime running on `:8080`:

```bash
curl -sS http://127.0.0.1:8080/api/health | jq .
curl -sS http://127.0.0.1:8080/api/nodes | jq 'length'
curl -sS http://127.0.0.1:8080/api/edges | jq 'length'
curl -sS 'http://127.0.0.1:8080/api/events?limit=5' | jq 'length'

curl -sS -X POST http://127.0.0.1:8080/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"node_id":"user","message":"hello"}' | jq .
```

You can also run:

```bash
scripts/test_demo_runtime.sh
```

## Advanced Demo Paths

Virtual agents:

```bash
scripts/test_virtual_agents.sh
```

Companion enforcement is opt-in:

```bash
REQUIRE_COMPANION=1 scripts/test_virtual_agents.sh
```

Proposal flow:

```bash
scripts/test_proposal_flow.sh
```

Search/index:

```bash
scripts/test_search.sh
```

LSP startup check:

```bash
scripts/test_lsp_startup.sh
```

Constrained fallback profile (if full-mode virtual behavior is unstable in your environment):

```bash
devenv shell -- remora start --project-root . --config remora.constrained.yaml --port 8080 --log-events
```

Full check sequence:

```bash
scripts/run_demo_checks.sh
```

UI dependency check:

```bash
scripts/test_ui_dependencies.sh
```

## Troubleshooting

`remora discover` fails with unknown config keys:
- Ensure `remora.yaml` uses modern keys (`bundle_search_paths`, `bundle_overlays`, `workspace_root`).

Custom tools missing in agent workspaces:
- Verify `bundle_overlays` maps node types to `demo-code-agent` and `demo-directory-agent`.

No proposals appear:
- Confirm target node resolves and tools exist under `_bundle/tools`.
- Check `/api/events` for tool call failures.

Search returns 503:
- Full demo checks require search availability.
- Install `remora[search]`, start embeddy, and set `REMORA_EMBEDDY_URL`.

LSP startup check fails:
- Ensure `.remora/remora.db` exists by running remora runtime at least once.
- If output mentions `LSP support requires pygls`, install LSP extras (`remora[lsp]`).

Virtual companion checks fail:
- Companion behavior depends on `turn_digested` event emission from runtime.
- By default, demo checks enforce review observer behavior and keep companion optional.
- To enforce companion behavior explicitly, run `REQUIRE_COMPANION=1 scripts/test_virtual_agents.sh`.
- If your environment cannot support full-mode virtual flow yet, use `--config remora.constrained.yaml` as a temporary fallback.

Blank web UI at `/`:
- The current remora web UI loads graph libraries from `unpkg.com`.
- In network-restricted environments, the page can appear blank if CDN scripts cannot load.
- Run `scripts/test_ui_dependencies.sh` to confirm.
- Use API/script flows (`scripts/test_demo_runtime.sh`, `scripts/test_virtual_agents.sh`, `scripts/test_proposal_flow.sh`) as the reliable offline path.
