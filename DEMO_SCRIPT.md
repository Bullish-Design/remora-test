# Remora Demo WOW Script

This guide is a copy/paste walkthrough for a new user to:
- set up the environment
- start the remora runtime
- verify baseline functionality
- run high-impact demo flows (reflection, virtual routing, proposal lifecycle, SSE/cursor, relationship tools)

Assumes repo path:
- `/home/andrew/Documents/Projects/remora-test`

## 1. Open Terminal and Prepare Environment

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- uv sync --extra dev
```

Quick sanity check:

```bash
remora discover --project-root .
```

Expected: `Discovered <N> nodes` and no config-key validation errors.

## 2. Start Runtime (Terminal A)

```bash
cd /home/andrew/Documents/Projects/remora-test
remora start --project-root . --port 8080 --log-events
```

Leave this terminal running.

## 3. Baseline API Checks (Terminal B)

```bash
cd /home/andrew/Documents/Projects/remora-test
BASE="http://127.0.0.1:8080"

curl -sS "$BASE/api/health" | jq .
curl -sS "$BASE/api/nodes" | jq 'length'
curl -sS "$BASE/api/edges" | jq 'length'
curl -sS "$BASE/api/events?limit=5" | jq 'length'
```

Expected:
- health status is `ok`
- nodes count is > 0

## 4. WOW #1: Trigger Custom Tools Through Chat

Find a function node:

```bash
TARGET_NODE="$(curl -sS "$BASE/api/nodes" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
echo "$TARGET_NODE"
```

Send chat with deterministic tokens:

```bash
curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"demo_echo show_dependencies\"}" | jq .
```

Expected:
- response contains `"status": "sent"`
- logs/events show `demo_echo` and/or `show_dependencies` tool activity.

## 5. WOW #2: Reflection Pipeline + Companion Digest

```bash
scripts/test_reflection_pipeline.sh
```

Expected:
- target code node executes a primary turn
- `turn_digested` event appears for that node
- companion observer turn activity increases

Optional strict mode:

```bash
REQUIRE_COMPANION=1 scripts/test_reflection_pipeline.sh
```

## 6. WOW #3: Scoped Virtual-Agent Routing (`path_glob`)

```bash
scripts/test_subscription_filters.sh
```

Expected:
- src-only changes trigger `demo-src-filter-observer`
- docs-only changes trigger `demo-docs-filter-observer`
- no cross-triggering between the two observers.

## 7. WOW #4: Human-in-the-Loop Proposal Flow (Reject + Accept)

Reject path:

```bash
scripts/test_proposal_flow.sh
```

Accept path with auto-restore:

```bash
scripts/test_proposal_accept_flow.sh
```

Expected:
- proposal appears in `/api/proposals`
- diff endpoint returns content
- accept path emits `rewrite_accepted` and `content_changed`
- script restores file after acceptance to keep repo clean.

## 8. WOW #5: Multi-Language Discovery

```bash
scripts/test_multilang_discovery.sh
```

Expected:
- discover output includes `function`, `section`, and `table` nodes.

## 9. WOW #6: SSE Replay/Resume + Cursor Focus

SSE contract:

```bash
scripts/test_sse_contract.sh
```

Cursor focus:

```bash
scripts/test_cursor_focus.sh
```

Expected:
- SSE replay includes earlier probe events
- SSE resume with `Last-Event-ID` includes newer probe events
- cursor call emits `cursor_focus` and resolves node id.

## 10. WOW #7: Relationship-Aware Agent Tooling

```bash
scripts/test_relationship_tools.sh
```

Expected:
- `show_dependencies` tool execution appears in events for target node.

## 11. WOW #8: Search/Index Demo

Requires embeddy backend available at `REMORA_EMBEDDY_URL`.

```bash
scripts/test_search.sh
```

If unavailable, this script skips in non-strict mode with diagnostics.
Use strict mode when you want the search path to be mandatory:

```bash
REQUIRE_SEARCH=1 scripts/test_search.sh
```

## 12. WOW #9: LSP Paths

Startup diagnostics path:

```bash
scripts/test_lsp_startup.sh
```

Event bridge path:

```bash
scripts/test_lsp_event_bridge.sh
```

Expected:
- LSP starts (or returns clear dependency diagnostics)
- event bridge path emits `content_changed` from LSP open/save.

For strict bridge enforcement:

```bash
REQUIRE_LSP_BRIDGE=1 scripts/test_lsp_event_bridge.sh
```

## 13. Guardrails Metrics (Optional)

Start runtime with stress config in Terminal A:

```bash
remora start --project-root . --config remora.stress.yaml --port 8080 --log-events
```

Then run:

```bash
REQUIRE_OVERFLOW=1 scripts/test_runtime_guardrails.sh
```

Expected:
- overflow-related metrics increase while runtime remains healthy.

## 14. One-Command Demo Check Runner

After runtime is up, run:

```bash
scripts/run_demo_checks.sh
```

Enable optional checks:

```bash
REQUIRE_SEARCH=1 scripts/run_demo_checks.sh
RUN_GUARDRAILS_CHECK=1 REQUIRE_OVERFLOW=1 scripts/run_demo_checks.sh
RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh
```

## 15. Fallback Profile (If Needed)

If full-mode virtual behavior is unstable in your environment:

```bash
remora start --project-root . --config remora.constrained.yaml --port 8080 --log-events
```

## 16. Demo Narration Tips

1. Start with runtime health + discovered graph size.
2. Trigger deterministic tools via chat token prompts.
3. Show reflection -> digest -> companion flow.
4. Show scoped virtual-agent routing.
5. Show proposal reject and accept safety controls.
6. Show SSE replay/resume and cursor focus.
7. End with `scripts/run_demo_checks.sh` for repeatability.
