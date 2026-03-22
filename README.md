# remora-test-demo

## What This Repository Demonstrates

This repository demonstrates current `remora-v2` runtime capabilities against a small Python codebase:
- code discovery into remora nodes/edges
- chat-driven node interaction
- local bundle/tool overrides
- virtual agent reactive workflows
- proposal (human-in-the-loop) review flow
- optional semantic search/index flow

## Prerequisites

- `devenv`
- `uv`
- `jq`
- local `remora-v2` checkout at `../remora-v2`
- optional model endpoint (default: `http://remora-server:8000/v1`)

Environment variables (optional):
- `REMORA_MODEL_BASE_URL`
- `REMORA_MODEL_API_KEY`
- `REMORA_MODEL`
- `REMORA_EMBEDDY_URL` (for optional search demo)

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

Proposal flow:

```bash
scripts/test_proposal_flow.sh
```

Optional search/index:

```bash
RUN_SEARCH=1 scripts/run_demo_checks.sh
```

Full check sequence:

```bash
scripts/run_demo_checks.sh
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
- Search is optional; start embeddy and set `REMORA_EMBEDDY_URL` if needed.
