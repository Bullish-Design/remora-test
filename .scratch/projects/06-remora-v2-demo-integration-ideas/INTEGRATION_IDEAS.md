# remora-v2 Integration Ideas for remora-test

Date: 2026-03-25  
Reviewed source: `/home/andrew/Documents/Projects/remora-v2`  
Target demo repo: `/home/andrew/Documents/Projects/remora-test`

## Goal

Use `remora-test` to demonstrate the strongest capabilities in the latest `remora-v2` runtime, not just basic runtime liveness.

This guide focuses on what to add or adjust in `remora-test` so a live demo clearly shows:
- reactive multi-agent behavior
- observability and event traceability
- safe human-in-the-loop code changes
- IDE/editor integration paths
- search and graph intelligence

## What the Demo Already Covers Well

Current `remora-test` already demonstrates:
- node/edge discovery and chat (`/api/nodes`, `/api/edges`, `/api/chat`)
- virtual agents (`demo-review-observer`, `demo-companion-observer`)
- proposal flow (`/api/proposals`, diff, reject)
- search indexing/check script
- LSP startup check script

Current scripts providing baseline coverage:
- `scripts/test_demo_runtime.sh`
- `scripts/test_virtual_agents.sh`
- `scripts/test_proposal_flow.sh`
- `scripts/test_search.sh`
- `scripts/test_lsp_startup.sh`

## High-Impact Showcase Gaps

These are the biggest opportunities to better show off latest `remora-v2`.

1. The layered reflection pipeline is not explicitly showcased end-to-end.
2. Subscription precision (`path_glob`, `from_agents`, tags) is not showcased explicitly.
3. Multi-language discovery breadth (`python` + `markdown` + `toml`) is underused.
4. SSE replay/resume (`replay`, `Last-Event-ID`, `once`) is not demoed.
5. Cursor focus API (`/api/cursor`) is not demoed.
6. Proposal accept path + follow-up reactive loop is not shown (reject-only path is shown).
7. Relationship-aware graph queries (imports/inheritance) are not surfaced in the demo narrative.
8. Runtime limits/overflow metrics from `/api/health` are not showcased.

## Integration Ideas (Prioritized)

## Priority 1: End-to-End Reactive Reflection Pipeline

Capability to showcase:
- code-agent turn -> self-reflection -> `turn_digested` -> companion aggregation -> inspect companion state

Why it is a strong demo:
- It demonstrates the core layered architecture of modern `remora-v2`, not just single-turn chat.

Recommended `remora-test` changes:
1. Add/ensure `self_reflect` in `bundles/demo-code-agent/bundle.yaml` with a deterministic prompt that calls companion tools.
2. Add script `scripts/test_reflection_pipeline.sh` that:
- triggers a deterministic chat turn
- captures correlation ID
- verifies ordered evidence in `/api/events` for that correlation:
`agent_start` -> `model_request` -> `remora_tool_*` -> `turn_complete` -> `agent_complete` -> `turn_digested`
- verifies companion activity after digest (`demo-companion-observer` events)
3. Add demo section in `DEMO_SCRIPT.md` showing `/api/nodes/{id}/companion`.

Acceptance signal:
- reflection pipeline script passes and companion KV data shows updated `chat_index`/`reflections`/`links`.

## Priority 1: Subscription Precision Demo (`path_glob` and Filters)

Capability to showcase:
- virtual agents reacting only to intended file/event scopes.

Why it is a strong demo:
- Shows deterministic event routing and that virtual agents are controllable, not noisy.

Recommended `remora-test` changes:
1. Add a second scoped virtual agent in `remora.yaml` (for example docs observer) with narrow subscription:
- `event_types: ["content_changed"]`
- `path_glob: "docs/**"`
2. Update `scripts/test_virtual_agents.sh` or add `scripts/test_subscription_filters.sh`:
- mutate `src/*` and confirm only src-bound virtual agent reacts
- mutate `docs/*` and confirm docs-bound virtual agent reacts
3. Include explicit checks for absolute-path event matching behavior.

Acceptance signal:
- deterministic pass/fail showing correct selective triggering.

## Priority 1: Proposal Accept + Reconcile Chain

Capability to showcase:
- human approval materializes workspace changes, emits `content_changed`, and re-enters reactive loop.

Why it is a strong demo:
- Shows full safety workflow, not just proposal creation.

Recommended `remora-test` changes:
1. Add `scripts/test_proposal_accept_flow.sh`:
- trigger rewrite proposal
- fetch diff
- accept proposal
- assert file changed on disk
- assert `rewrite_accepted` and subsequent `content_changed` event(s)
2. Keep current reject script for clean default runs.
3. Add an isolated scratch file path for accept flow to avoid mutating core demo source.

Acceptance signal:
- accept flow script demonstrates end-to-end state transition and event trail.

## Priority 2: Multi-Language Discovery + Cross-Type Nodes

Capability to showcase:
- discovery of `section` and `table` nodes alongside Python nodes.

Why it is a strong demo:
- Demonstrates that `remora-v2` is language-agnostic graph runtime, not Python-only.

Recommended `remora-test` changes:
1. Expand `discovery_languages` in `remora.yaml` to include `markdown` and `toml` (or remove strict allowlist).
2. Add representative `docs/*.md` and `configs/*.toml` content with clear headings/tables.
3. Add script `scripts/test_multilang_discovery.sh`:
- run `remora discover`
- assert node types include `function`, `class`/`method`, `section`, `table`, `directory`, `virtual`.

Acceptance signal:
- discovery output and `/api/nodes` include non-Python node types consistently.

## Priority 2: SSE Replay/Resume Contract Demo

Capability to showcase:
- reliable event catch-up using `/sse?replay=N`, `Last-Event-ID`, and `once=true`.

Why it is a strong demo:
- Highlights production-ready observability semantics.

Recommended `remora-test` changes:
1. Add `scripts/test_sse_contract.sh`:
- trigger events
- read `replay` stream
- reconnect with `Last-Event-ID`
- verify no missed/duplicated replay behavior
- verify `once=true` closes as expected
2. Add short section in `DEMO_SCRIPT.md` showing SSE recovery after reconnect.

Acceptance signal:
- script validates replay and resume behavior with clear IDs.

## Priority 2: Cursor Focus + Companion Panel Flow

Capability to showcase:
- editor-like focus events (`/api/cursor`) and focused-node context.

Why it is a strong demo:
- Connects runtime to IDE workflow and UI behavior.

Recommended `remora-test` changes:
1. Add `scripts/test_cursor_focus.sh`:
- post file path + line
- assert response includes focused `node_id`
- assert `cursor_focus` event in `/api/events`
2. Add demo narrative for cursor-driven exploration in UI.

Acceptance signal:
- cursor script passes and event payload includes node metadata.

## Priority 2: Relationship-Aware Agent Tooling

Capability to showcase:
- new graph externals beyond basic node listing (`graph_get_importers`, `graph_get_dependencies`, `graph_get_edges_by_type`).

Why it is a strong demo:
- Makes graph intelligence visible and useful to agents.

Recommended `remora-test` changes:
1. Add tool(s) in `bundles/demo-code-agent/tools/`, for example:
- `show_importers.pym`
- `show_dependencies.pym`
2. Add deterministic token triggers in `bundles/demo-code-agent/bundle.yaml` for these tools.
3. Add script `scripts/test_relationship_tools.sh` to verify tool activity via `remora_tool_result`.

Acceptance signal:
- agent can answer “who depends on me?” based on graph edges.

## Priority 3: Runtime Guardrails and Metrics Story

Capability to showcase:
- queue overflow behavior and rate limiting visibility via `/api/health` metrics.

Why it is a strong demo:
- Shows operational maturity and safe runtime behavior under load.

Recommended `remora-test` changes:
1. Add a stress profile config (for example `remora.stress.yaml`) with tiny inbox limits.
2. Add script `scripts/test_runtime_guardrails.sh` that floods events and asserts:
- overflow counters grow in health metrics
- runtime remains healthy
3. Add short troubleshooting section in README on interpreting these metrics.

Acceptance signal:
- measurable overflow counters with deterministic stress test.

## Priority 3: LSP End-to-End Event Bridge (Beyond Startup)

Capability to showcase:
- `didOpen`/`didSave` producing `content_changed` and triggering reactive flow.

Why it is a strong demo:
- Demonstrates concrete editor-runtime loop, not just process startup.

Recommended `remora-test` changes:
1. Add `scripts/test_lsp_event_bridge.sh` that sends minimal LSP notifications and checks `/api/events`.
2. Keep startup check as fast smoke; add bridge script as full demo path.

Acceptance signal:
- end-to-end event evidence from LSP notifications.

## Suggested Implementation Sequence

Recommended sequence for maximum demo impact with low risk:

1. Reflection pipeline demo.
2. Subscription precision demo.
3. Proposal accept flow.
4. Multi-language discovery.
5. SSE replay/resume.
6. Cursor focus.
7. Relationship tools.
8. Metrics/guardrails.
9. LSP event bridge.

## Concrete File-Level Plan

Likely files to touch in `remora-test`:
- `remora.yaml`
- `bundles/demo-code-agent/bundle.yaml`
- `bundles/demo-code-agent/tools/*.pym`
- `scripts/test_virtual_agents.sh`
- `scripts/test_proposal_flow.sh` (or new accept companion script)
- new scripts:
`scripts/test_reflection_pipeline.sh`, `scripts/test_subscription_filters.sh`,
`scripts/test_multilang_discovery.sh`, `scripts/test_sse_contract.sh`,
`scripts/test_cursor_focus.sh`, `scripts/test_relationship_tools.sh`,
`scripts/test_runtime_guardrails.sh`, `scripts/test_lsp_event_bridge.sh`
- `scripts/run_demo_checks.sh`
- `DEMO_SCRIPT.md`
- `README.md`
- `docs/architecture.md`
- optional live tests under `tests/integration/`

## Known Contract Notes from Review

Important observations from latest `remora-v2` source review:

1. Runtime `EXTERNALS_VERSION` is `3` in code, while many bundle/docs references still use `2`.  
Practical guidance: keep demo bundles at `externals_version: 2` unless you intentionally require new externals only available in `3`.

2. `graph_query_nodes` now supports a compatibility fallback for role-like inputs in `node_type` and explicit `role` filtering.  
Practical guidance: add at least one demo/tool test that queries role-backed virtual agents to prevent regressions.

3. `path_glob` matching includes handling for absolute event paths against relative globs.  
Practical guidance: keep one explicit script assertion for this so future regressions are obvious.

## Demo Narrative Blueprint (Recommended)

A concise “best of remora-v2” live flow:

1. Show graph breadth (`/api/nodes`, multi-language node types).
2. Trigger a targeted chat turn and show tool execution trace.
3. Trace correlation across `turn_complete` and `turn_digested`.
4. Show companion project-level aggregation for that turn.
5. Trigger scoped source change and show precise virtual-agent routing.
6. Trigger rewrite proposal, inspect diff, accept it, and show resulting change events.
7. Show SSE replay/resume and cursor focus event for IDE-style workflow.

This sequence makes the architecture legible while proving production-relevant behavior.
