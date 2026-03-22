# Remora Demo WOW Script

This guide is a copy/paste walkthrough for a new user to:
- set up the environment
- start the remora runtime
- verify baseline functionality
- run high-impact demo flows (tool calls, reactive virtual agents, proposal review)

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

## 4. WOW #1: Trigger a Custom Tool Through Chat

This uses the local `demo-code-agent` bundle and `demo_echo.pym` tool.

Find a function node:

```bash
TARGET_NODE="$(curl -sS "$BASE/api/nodes" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
echo "$TARGET_NODE"
```

Send chat with `demo_echo` token:

```bash
curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"demo_echo\"}" | jq .
```

Expected:
- response contains `"status": "sent"`
- in Terminal A logs, you should see the turn and tool invocation activity.

## 5. WOW #2: Show Virtual Agent Reactivity

This demonstrates `demo-review-observer` reacting to source changes.

```bash
scripts/test_virtual_agents.sh
```

Expected:
- output like `before=X after=Y`
- `after` is greater than `before`

Optional direct proof:

```bash
curl -sS "$BASE/api/nodes" | jq '[.[] | select(.node_type=="virtual") | .node_id]'
```

Expected includes:
- `demo-review-observer`
- `demo-companion-observer`

## 6. WOW #3: Human-in-the-Loop Proposal Flow

This demonstrates AI-generated code changes going to proposal review instead of direct commit.

```bash
scripts/test_proposal_flow.sh
```

What this does:
- asks `compute_total` node to run `rewrite_to_magic`
- waits for proposal creation
- shows proposal diff
- rejects proposal (intentionally, to keep source clean)

Expected:
- proposal appears in `/api/proposals`
- diff endpoint returns content
- reject call returns status `rejected`

## 7. Optional WOW #4: Search/Index Demo

Requires embeddy backend available at `REMORA_EMBEDDY_URL`.

```bash
scripts/test_search.sh
```

If unavailable, this may fail with 503; that is environment-related, not a core demo failure.

## 8. One-Command Demo Check Runner

After runtime is up, run:

```bash
scripts/run_demo_checks.sh
```

With optional search included:

```bash
RUN_SEARCH=1 scripts/run_demo_checks.sh
```

## 8.1 UI Dependency Check (If Graph UI Is Blank)

```bash
scripts/test_ui_dependencies.sh
```

If `unpkg` is unreachable, browser UI can appear blank while APIs still work.
In that case, continue with script/API-based demo flows.

## 9. Reset Notes (If Needed)

`test_virtual_agents.sh` appends a comment line to `src/services/pricing.py`.
If you want to clean it up after demo:

```bash
git checkout -- src/services/pricing.py
```

(Only do this if you are not preserving that temporary demo marker.)

## 10. Demo Narration Tips (For Live Presentation)

1. Start with runtime health + discovered graph size to establish credibility.
2. Trigger `demo_echo` to show deterministic tool use from prompt token.
3. Run virtual-agent test to show event-driven automation.
4. Run proposal flow to show safety/human approval controls.
5. End with `run_demo_checks.sh` as proof of repeatable validation.
