# Remora-v2 Demo Walkthrough (remora-test)

This is the up-to-date operator runbook for demonstrating **all remora-v2 capabilities exercised by this repository**.

Scope of this demo repo:
- graph discovery across Python, Markdown, TOML
- bundle overlays and deterministic tool routing
- virtual agents, event subscriptions, and path filters
- reflection and companion digest pipeline
- proposal review flow (reject + accept)
- event stream features (SSE replay/resume, cursor focus)
- relationship-aware graph tools
- search/index path (with strict and non-strict modes)
- LSP startup + LSP event bridge
- runtime guardrails/overflow metrics
- UI dependency diagnostics and local asset patching

Note: `src/` exists mainly as discovery/tooling fixture content for the demo.

## 1. Prerequisites

Required tools:
- `devenv`
- `uv`
- `jq`
- local `remora-v2` checkout at `../remora-v2`

Optional for deeper paths:
- model endpoint (default `http://remora-server:8000/v1`)
- embeddy backend for semantic search
- LSP extras (`remora[lsp]`) for LSP checks

## 2. Terminal Setup

Use 2 terminals:
- Terminal A: runtime server
- Terminal B: demo commands/scripts

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- uv sync --extra dev
```

## 3. Discovery Preflight

```bash
devenv shell -- remora discover --project-root .
scripts/test_multilang_discovery.sh
```

Expected: discovery output includes at least one `function` node. In full profile you should also see Markdown `section` and TOML `table` nodes.

## 4. Start Runtime (Default Profile)

Terminal A:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- remora start --project-root . --port 8080 --log-events
```

## 5. Baseline API + Smoke

Terminal B:

```bash
cd /home/andrew/Documents/Projects/remora-test
BASE="http://127.0.0.1:8080"

curl -sS "$BASE/api/health" | jq .
curl -sS "$BASE/api/nodes" | jq 'length'
curl -sS "$BASE/api/edges" | jq 'length'
curl -sS "$BASE/api/events?limit=5" | jq 'length'

scripts/test_demo_runtime.sh
scripts/test_remora.sh
```

## 6. WOW: Bundle Tools and Deterministic Trigger Tokens

The `demo-code-agent` bundle reacts to tokens:
- `demo_echo`
- `show_dependencies`
- `show_importers`
- `show_relationship_edges`
- `rewrite_to_magic` (proposal path)

Quick manual trigger:

```bash
TARGET_NODE="$(curl -sS "$BASE/api/nodes" | jq -r 'map(select(.node_type=="function"))[0].node_id')"

curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\":\"$TARGET_NODE\",\"message\":\"demo_echo show_dependencies show_importers show_relationship_edges\"}" | jq .
```

Relationship tool check:

```bash
scripts/test_relationship_tools.sh
```

## 7. WOW: Virtual Agents + Subscription Filters

```bash
scripts/test_virtual_agents.sh
REQUIRE_COMPANION=1 scripts/test_virtual_agents.sh
scripts/test_subscription_filters.sh
```

What this demonstrates:
- review observer activation
- companion observer activation (strict mode)
- `path_glob` matching semantics for `src/**` vs `docs/**`

## 8. WOW: Reflection -> Digest -> Companion Pipeline

```bash
scripts/test_reflection_pipeline.sh
REQUIRE_COMPANION=1 scripts/test_reflection_pipeline.sh
```

Expected chain:
- primary completion
- reflection completion
- `turn_digested`
- companion turn on same correlation (strict mode)

## 9. WOW: Proposal Lifecycle (Human-in-the-Loop)

Reject path:

```bash
scripts/test_proposal_flow.sh
```

Accept path (auto-restores target file during cleanup):

```bash
scripts/test_proposal_accept_flow.sh
```

Expected:
- `rewrite_proposal` event
- diff available at proposal diff endpoint
- reject or accept outcome
- accept path emits `rewrite_accepted` and `content_changed`

## 10. WOW: Event Contracts (SSE + Cursor)

```bash
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
```

What this proves:
- SSE replay contains prior probe events
- `Last-Event-ID` resume yields newer events
- cursor API resolves node and emits `cursor_focus`

## 11. WOW: Search and Indexing

Non-strict mode (default, can skip if backend unavailable):

```bash
scripts/test_search.sh
```

Strict mode:

```bash
REQUIRE_SEARCH=1 MAX_INDEX_ERRORS=0 scripts/test_search.sh
```

### Strict Search Setup (if semantic backend is not already available)

Terminal C (mock embedder):

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/mock_embedder_server.py
```

Terminal D (embeddy in remote mode):

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- embeddy serve --config configs/embeddy.remote.yaml
```

Restart runtime in Terminal A with embeddy URL:

```bash
cd /home/andrew/Documents/Projects/remora-test
REMORA_EMBEDDY_URL=http://127.0.0.1:8585 devenv shell -- remora start --project-root . --port 8080 --log-events
```

Then rerun strict search.

## 12. WOW: LSP Startup and LSP Event Bridge

Startup diagnostic:

```bash
scripts/test_lsp_startup.sh
```

Bridge probe:

```bash
scripts/test_lsp_event_bridge.sh
REQUIRE_LSP_BRIDGE=1 scripts/test_lsp_event_bridge.sh
```

Notes:
- LSP startup requires `.remora/remora.db` to exist (run runtime at least once).
- If `pygls` is missing, startup script reports required extras.

## 13. WOW: Guardrails and Overflow Metrics (Stress Profile)

Stop default runtime and restart with stress config in Terminal A:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- remora start --project-root . --config remora.stress.yaml --port 8080 --log-events
```

Run guardrail test:

```bash
REQUIRE_OVERFLOW=1 scripts/test_runtime_guardrails.sh
```

Expected: inbox overflow metrics increase while health remains valid.

## 14. WOW: UI Dependency Diagnostics and Local Asset Mode

Check UI dependency mode:

```bash
scripts/test_ui_dependencies.sh
```

Install local vendor assets and patch index to avoid CDN dependencies:

```bash
scripts/install_local_ui_assets.sh
```

This copies vendor JS into remora static assets and rewrites CDN URLs to `/static/vendor/*`.

## 15. Constrained Fallback Profile

If full virtual behavior is unstable:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- remora start --project-root . --config remora.constrained.yaml --port 8080 --log-events
```

## 16. One-Command Orchestration

Default orchestrated run:

```bash
scripts/run_demo_checks.sh
```

With optional gates:

```bash
REQUIRE_SEARCH=1 scripts/run_demo_checks.sh
RUN_GUARDRAILS_CHECK=1 REQUIRE_OVERFLOW=1 scripts/run_demo_checks.sh
RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh
```

## 17. Demo Narration Sequence (Recommended)

Use this order for a strong live demo:
1. Baseline health/graph (`test_demo_runtime.sh`)
2. Deterministic tool call behavior (`test_relationship_tools.sh`)
3. Virtual + filter routing (`test_virtual_agents.sh`, `test_subscription_filters.sh`)
4. Reflection pipeline (`test_reflection_pipeline.sh`)
5. Proposal reject + accept (`test_proposal_flow.sh`, `test_proposal_accept_flow.sh`)
6. SSE + cursor (`test_sse_contract.sh`, `test_cursor_focus.sh`)
7. Search (`test_search.sh`, then strict mode if backend ready)
8. LSP startup + bridge (`test_lsp_startup.sh`, `test_lsp_event_bridge.sh`)
9. Stress guardrails (`remora.stress.yaml` + `test_runtime_guardrails.sh`)
10. Final orchestration (`run_demo_checks.sh`)

## 18. Quick Troubleshooting

- Health fails: runtime is not running on `BASE`.
- No virtual nodes: runtime state/config mismatch; restart with configured profile.
- Search strict fails: embeddy not up or indexing errors exceed `MAX_INDEX_ERRORS`.
- LSP startup fails: missing DB bootstrap or missing `remora[lsp]` extras.
- LSP bridge strict fails: no post-notification change event observed.
- UI blank in offline environment: run `scripts/install_local_ui_assets.sh`.

## 19. Optional Helper Script

`reconcile_demo.sh` is a reminder helper for manually touching files to trigger reconciliation behavior:

```bash
scripts/reconcile_demo.sh
```
