# Remora-v2 Live Demo Script (Presenter Mode)

This is a presenter-first runbook with:
- a fast **5-minute wow path**
- a **30-minute full path**
- explicit `Say / Run / Expect / If it fails` blocks

Repo path assumed:
- `/home/andrew/Documents/Projects/remora-test`

---

## 0. Stage Setup (Do Before Audience Joins)

### Say
`This repo is a capability harness for remora-v2. We’ll walk from baseline graph/runtime behavior through event pipelines, proposal controls, search, and LSP bridge.`

### Run
```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- uv sync --extra dev
```

Terminal A (runtime):
```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- remora start --project-root . --port 8080 --log-events
```

Terminal B (operator):
```bash
cd /home/andrew/Documents/Projects/remora-test
BASE="http://127.0.0.1:8080"
```

### Expect
- Runtime stays up in Terminal A.
- Terminal B commands can hit `/api/health`.

### If it fails
- If runtime won’t start, run:
```bash
devenv shell -- remora discover --project-root .
```
- Fix any config/dependency issue before going live.

---

## 1. 5-Minute Wow Path

### Minute 0-1: Health + Graph

#### Say
`First, remora discovers and serves a live graph of project structure and behavior.`

#### Run
```bash
curl -sS "$BASE/api/health" | jq .
curl -sS "$BASE/api/nodes" | jq 'length'
curl -sS "$BASE/api/edges" | jq 'length'
scripts/test_demo_runtime.sh
```

#### Expect
- Health status `ok`
- Non-zero nodes/edges
- `test_demo_runtime.sh passed`

#### If it fails
- Confirm runtime is still running on `:8080`.

### Minute 1-2: Deterministic Tool Trigger

#### Say
`Bundle overlays can force deterministic tool invocation based on message tokens.`

#### Run
```bash
scripts/test_relationship_tools.sh
```

#### Expect
- `show_dependencies` tool execution observed in events
- Script passes

#### If it fails
- Retry once; if still failing, move on and continue with `test_virtual_agents.sh`.

### Minute 2-3: Virtual Agents + Filter Routing

#### Say
`Virtual observers subscribe to events, and path globs let us route reactivity by scope.`

#### Run
```bash
scripts/test_virtual_agents.sh
scripts/test_subscription_filters.sh
```

#### Expect
- Review observer activity grows
- Path filter checks pass (`src/**` and `docs/**` separation)

#### If it fails
- For companion instability, keep going with review-only mode:
```bash
REQUIRE_COMPANION=0 scripts/test_virtual_agents.sh
```

### Minute 3-4: Proposal Flow (Safety Control)

#### Say
`Here is human-in-the-loop governance: proposals can be reviewed, diffed, rejected, or accepted.`

#### Run
```bash
scripts/test_proposal_flow.sh
```

#### Expect
- `rewrite_proposal` appears
- diff endpoint responds
- reject path completes

### Minute 4-5: Event Contract (SSE + Cursor)

#### Say
`Event stream replay/resume and editor cursor focus are first-class runtime contracts.`

#### Run
```bash
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
```

#### Expect
- SSE replay and resume tokens found
- cursor resolution and `cursor_focus` behavior validated

---

## 2. 30-Minute Full Path

## 2.1 Minute 0-3: Intro + Baseline

### Say
`We’ll progress from graph/runtime fundamentals to advanced paths: reflection, proposals, search, LSP bridge, and guardrails under stress.`

### Run
```bash
scripts/test_multilang_discovery.sh
scripts/test_demo_runtime.sh
scripts/test_remora.sh
```

### Expect
- Discovery includes function/section/table
- Runtime smoke checks pass

---

## 2.2 Minute 3-7: Bundle Overlay + Deterministic Tool Routing

### Say
`Different node types map to bundle roles, and these bundles expose predictable tool behavior.`

### Run
```bash
scripts/test_relationship_tools.sh
```

Optional manual trigger:
```bash
TARGET_NODE="$(curl -sS "$BASE/api/nodes" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\":\"$TARGET_NODE\",\"message\":\"demo_echo show_dependencies show_importers show_relationship_edges\"}" | jq .
```

### Expect
- Tool result events tied to target node

---

## 2.3 Minute 7-11: Virtual Agents + Subscription Filters

### Say
`Reactive virtual agents subscribe to runtime events and can be constrained by path scope.`

### Run
```bash
scripts/test_virtual_agents.sh
REQUIRE_COMPANION=1 scripts/test_virtual_agents.sh
scripts/test_subscription_filters.sh
```

### Expect
- review observer behavior verified
- companion behavior verified (strict run)
- subscription filter semantics verified

### If it fails
- If strict companion fails, continue with:
```bash
REQUIRE_COMPANION=0 scripts/test_virtual_agents.sh
```

---

## 2.4 Minute 11-14: Reflection -> Digest -> Companion

### Say
`Primary completion can trigger a reflection phase, then digest emission, then companion follow-up.`

### Run
```bash
scripts/test_reflection_pipeline.sh
REQUIRE_COMPANION=1 scripts/test_reflection_pipeline.sh
```

### Expect
- primary and reflection completions
- `turn_digested`
- companion completion (strict mode)

---

## 2.5 Minute 14-18: Proposal Reject + Accept Lifecycle

### Say
`Proposal controls provide review checkpoints before source mutation.`

### Run
```bash
scripts/test_proposal_flow.sh
scripts/test_proposal_accept_flow.sh
```

### Expect
- reject path works
- accept path mutates content, validates against diff candidates, emits `rewrite_accepted` and `content_changed`, then restores file

---

## 2.6 Minute 18-21: SSE Replay/Resume + Cursor Focus

### Say
`Operational consumers can replay and resume stream state; editor integrations can map cursor location to graph node identity.`

### Run
```bash
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
```

### Expect
- replay token found
- resume token found after `Last-Event-ID`
- cursor mapping contract passes

---

## 2.7 Minute 21-25: Search and Index Path

### Say
`Search can run in non-strict mode for portability, and strict mode when semantic backend is guaranteed.`

### Run
```bash
scripts/test_search.sh
```

Strict mode:
```bash
REQUIRE_SEARCH=1 MAX_INDEX_ERRORS=0 scripts/test_search.sh
```

### Expect
- non-strict: pass or explicit skip with diagnostics
- strict: must pass with bounded index errors

### If it fails (backend missing)
Terminal C:
```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/mock_embedder_server.py
```

Terminal D:
```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- embeddy serve --config configs/embeddy.remote.yaml
```

Restart runtime in Terminal A:
```bash
cd /home/andrew/Documents/Projects/remora-test
REMORA_EMBEDDY_URL=http://127.0.0.1:8585 devenv shell -- remora start --project-root . --port 8080 --log-events
```

Then rerun strict search.

---

## 2.8 Minute 25-28: LSP Startup + Event Bridge

### Say
`LSP support is validated both at startup and by probing didOpen/didChange/didSave bridge behavior into runtime events.`

### Run
```bash
scripts/test_lsp_startup.sh
scripts/test_lsp_event_bridge.sh
REQUIRE_LSP_BRIDGE=1 scripts/test_lsp_event_bridge.sh
```

### Expect
- startup healthy or clear dependency diagnosis
- bridge script passes in default mode
- strict mode verifies explicit bridge behavior

### If it fails
- Ensure `.remora/remora.db` exists (runtime started at least once).
- Install LSP extras (`remora[lsp]`) in your environment.

---

## 2.9 Minute 28-30: Guardrails + Final Orchestration

### Say
`Finally, we validate runtime guardrails under pressure and run the integrated check orchestration.`

### Run
Restart runtime with stress profile (Terminal A):
```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- remora start --project-root . --config remora.stress.yaml --port 8080 --log-events
```

Then in Terminal B:
```bash
REQUIRE_OVERFLOW=1 scripts/test_runtime_guardrails.sh
scripts/run_demo_checks.sh
```

Optional strict orchestration:
```bash
REQUIRE_SEARCH=1 RUN_GUARDRAILS_CHECK=1 REQUIRE_OVERFLOW=1 RUN_LSP_BRIDGE_CHECK=1 REQUIRE_LSP_BRIDGE=1 scripts/run_demo_checks.sh
```

### Expect
- overflow metrics increase in stress mode
- orchestration completes with all configured checks passing

---

## 3. UI Segment (Optional, 2-3 Minutes)

### Say
`In restricted networks, CDN-backed UI assets can fail. This repo includes a local asset patch path.`

### Run
```bash
scripts/test_ui_dependencies.sh
scripts/install_local_ui_assets.sh
```

### Expect
- dependency diagnostic output
- local vendor assets copied and index patched to `/static/vendor/*`

---

## 4. Fast Recovery Playbook (On Stage)

If a step fails and you need flow continuity:
1. Re-run `scripts/test_demo_runtime.sh` to re-establish baseline.
2. Use non-strict modes (`REQUIRE_COMPANION=0`, default `test_search.sh`, non-strict LSP bridge).
3. Continue narrative with already passing capability families.

---

## 5. Closing Line

### Say
`This demo showed remora-v2 as an evented runtime for graph-aware agents: deterministic tool routing, reactive observers, governed code-change proposals, replayable event streams, search and LSP integration, and stress-tested guardrails in one repeatable harness.`

