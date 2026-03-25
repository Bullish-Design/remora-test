# remora-test-demo

## What This Repository Demonstrates

This repository demonstrates current `remora-v2` runtime capabilities against a small multi-language codebase:
- graph discovery across Python, Markdown, and TOML
- chat-driven node interaction with local bundle/tool overrides
- layered reflection flow (`turn_digested` + companion observer)
- scoped virtual-agent routing (`path_glob` filtering)
- proposal (human-in-the-loop) review flow (reject and accept paths)
- SSE replay/resume, cursor focus events, and relationship-aware tools
- semantic search/index path
- LSP startup and LSP event-bridge path

## Prerequisites

- `devenv`
- `uv`
- `jq`
- local `remora-v2` checkout at `../remora-v2`
- optional model endpoint (default: `http://remora-server:8000/v1`)
- embeddy backend for semantic search (required only for strict search checks)
- local mock embedder adapter (`scripts/mock_embedder_server.py`) for strict search in environments without a real embeddy local model

Environment variables (optional):
- `REMORA_MODEL_BASE_URL`
- `REMORA_MODEL_API_KEY`
- `REMORA_MODEL`
- `REMORA_EMBEDDY_URL` (required for search checks)

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
```

Baseline script:

```bash
scripts/test_demo_runtime.sh
```

## Advanced Demo Paths

Core behavior checks:

```bash
scripts/test_virtual_agents.sh
scripts/test_reflection_pipeline.sh
scripts/test_subscription_filters.sh
scripts/test_proposal_flow.sh
scripts/test_proposal_accept_flow.sh
scripts/test_multilang_discovery.sh
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
scripts/test_relationship_tools.sh
scripts/test_search.sh
scripts/test_lsp_startup.sh
```

Optional high-load / deep integration checks:

```bash
# requires runtime started with remora.stress.yaml for strict overflow expectation
REQUIRE_OVERFLOW=1 scripts/test_runtime_guardrails.sh

# requires healthy remora runtime and lsp extras available
scripts/test_lsp_event_bridge.sh
```

Companion strict mode examples:

```bash
REQUIRE_COMPANION=1 scripts/test_virtual_agents.sh
REQUIRE_COMPANION=1 scripts/test_reflection_pipeline.sh
```

Constrained fallback profile (if full-mode virtual behavior is unstable in your environment):

```bash
devenv shell -- remora start --project-root . --config remora.constrained.yaml --port 8080 --log-events
```

Stress profile (for guardrail metrics demo):

```bash
devenv shell -- remora start --project-root . --config remora.stress.yaml --port 8080 --log-events
```

Full check runner:

```bash
scripts/run_demo_checks.sh
```

Runner options:

```bash
REQUIRE_SEARCH=1 scripts/run_demo_checks.sh
RUN_GUARDRAILS_CHECK=1 REQUIRE_OVERFLOW=1 scripts/run_demo_checks.sh
RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh
```

## Troubleshooting

`remora discover` fails with unknown config keys:
- Ensure `remora.yaml` uses modern keys (`bundle_search_paths`, `bundle_overlays`, `workspace_root`).

Custom tools missing in agent workspaces:
- Verify `bundle_overlays` maps node types to `demo-code-agent` and `demo-directory-agent`.
- Confirm tool files exist under `bundles/demo-code-agent/tools/`.

No proposals appear:
- Confirm target node resolves and tools exist under `_bundle/tools`.
- Check `/api/events` for tool call failures.

Search returns 503:
- In default mode, `scripts/test_search.sh` skips with diagnostics.
- For strict behavior, run with `REQUIRE_SEARCH=1` after installing `remora[search]`, starting embeddy, and setting `REMORA_EMBEDDY_URL`.

Search returns 500 with `Model not loaded`:
- Start the local adapter in one shell:
  `devenv shell -- python scripts/mock_embedder_server.py`
- Start embeddy in a second shell with remote config:
  `devenv shell -- embeddy serve --config configs/embeddy.remote.yaml`
- Start remora with:
  `REMORA_EMBEDDY_URL=http://127.0.0.1:8585 devenv shell -- remora start --project-root . --port 8080 --log-events`

LSP startup check fails:
- Ensure `.remora/remora.db` exists by running runtime at least once.
- If output mentions `LSP support requires pygls`, install LSP extras (`remora[lsp]`).

LSP bridge check fails:
- Ensure runtime is already running on `BASE` and points to same `.remora/remora.db`.
- Install `remora[lsp]` (pygls dependency).
- In default mode, bridge check can skip when LSP extras are missing.
- For strict behavior, run with `REQUIRE_LSP_BRIDGE=1`.

Guardrails check shows no overflow increase:
- Start runtime with `remora.stress.yaml` and retry with `REQUIRE_OVERFLOW=1`.
- Without stress profile, metrics keys still validate but overflow may remain zero.
