# IMPLEMENTATION GUIDE

Date: 2026-03-25
Project: `06-remora-v2-demo-integration-ideas`
Target repo: `/home/andrew/Documents/Projects/remora-test`
Reference: [INTEGRATION_IDEAS.md](/home/andrew/Documents/Projects/remora-test/.scratch/projects/06-remora-v2-demo-integration-ideas/INTEGRATION_IDEAS.md)

## Table of Contents

1. Purpose and Outcome
- Defines what this implementation should achieve and how success is measured.

2. Guardrails and Working Rules
- Constraints to preserve current demo behavior while expanding capabilities.

3. Branch and Safety Strategy
- Exact branching model, including baseline backup branch and rollout branches.

4. Environment and Preflight
- Required setup, runtime assumptions, and baseline verification commands.

5. Implementation Phases (Execution Order)
- Detailed phase-by-phase tasks with file edits, tests, and acceptance criteria.

6. Test and Verification Matrix
- Mapping each feature slice to scripts/tests and expected evidence.

7. Documentation and Demo Narrative Updates
- Required README/DEMO_SCRIPT/docs changes to keep behavior and docs aligned.

8. Rollback and Recovery
- How to safely back out individual phase changes or full rollout.

9. Commit Plan
- Recommended commit boundaries and messages for clean review/rollback.

10. Final Definition of Done
- Exit criteria for declaring integration implementation complete.

## 1. Purpose and Outcome

This guide turns the integration roadmap into an execution plan for code changes in `remora-test`.

Primary outcome:
- keep existing demo functionality stable
- add high-impact `remora-v2` showcase capabilities incrementally
- keep every increment verifiable through scripts/tests

Success means:
1. Existing core checks still pass.
2. New integration slices each have deterministic validation evidence.
3. Docs and scripts describe the same default demo behavior.
4. A pre-integration backup branch exists for fast fallback.

## 2. Guardrails and Working Rules

1. Do not break current baseline scripts while adding new ones:
- `scripts/test_demo_runtime.sh`
- `scripts/test_virtual_agents.sh`
- `scripts/test_proposal_flow.sh`
- `scripts/test_search.sh`
- `scripts/test_lsp_startup.sh`

2. Keep implementation additive first, then tighten defaults.

3. Avoid broad config flips without script coverage in the same phase.

4. Prefer introducing new validation scripts before refactoring existing scripts.

5. Keep constrained fallback (`remora.constrained.yaml`) until full-flow checks are stable.

6. Run project/runtime commands in `devenv` shell:
```bash
devenv shell -- <command>
```

## 3. Branch and Safety Strategy

## 3.1 Baseline Backup Branch

Create a persistent branch pointer from current `main` before integration implementation starts:

```bash
git checkout main
git pull --ff-only
git branch backup/main-pre-integration-2026-03-25
```

If the name already exists:
```bash
git branch --list 'backup/main-pre-integration-*'
```

## 3.2 Working Branch

Perform implementation on a dedicated feature branch:

```bash
git checkout -b feat/integration-showcase-upgrades
```

## 3.3 Merge Strategy

1. Keep each phase in one or more focused commits.
2. Verify phase acceptance criteria before moving to next phase.
3. Merge back only after full matrix pass.

## 4. Environment and Preflight

## 4.1 Dependencies

```bash
devenv shell -- uv sync --extra dev
```

## 4.2 Runtime Baseline Check

From repo root:

```bash
BASE="http://127.0.0.1:8080"
curl -sS "$BASE/api/health" | jq .
curl -sS "$BASE/api/nodes" | jq 'length'
curl -sS "$BASE/api/events?limit=5" | jq 'length'
```

## 4.3 Existing Script Baseline

```bash
scripts/test_demo_runtime.sh
scripts/test_virtual_agents.sh
scripts/test_proposal_flow.sh
scripts/test_search.sh
scripts/test_lsp_startup.sh
```

Capture outputs under:
- `.scratch/projects/06-remora-v2-demo-integration-ideas/artifacts/`

## 5. Implementation Phases (Execution Order)

Recommended execution order from highest impact and lowest ambiguity:

1. Phase A: Reflection pipeline demo
2. Phase B: Subscription precision demo
3. Phase C: Proposal accept + reconcile chain
4. Phase D: Multi-language discovery
5. Phase E: SSE replay/resume contract
6. Phase F: Cursor focus flow
7. Phase G: Relationship-aware tooling
8. Phase H: Runtime guardrails and metrics
9. Phase I: LSP event bridge
10. Phase J: Docs and runbook consolidation

### Phase A: Reflection Pipeline

Goal:
- explicitly show `agent_complete(primary)` -> reflection -> `turn_digested` -> companion aggregation.

Files:
- `bundles/demo-code-agent/bundle.yaml`
- new `scripts/test_reflection_pipeline.sh`
- `DEMO_SCRIPT.md`

Implementation tasks:
1. Ensure `self_reflect.enabled: true` in demo code-agent bundle.
2. Use deterministic reflection prompt that drives companion tools.
3. Implement `test_reflection_pipeline.sh`:
- trigger one deterministic chat turn
- fetch events by correlation
- assert presence/order of key events
- assert companion activity increments
4. Add demo script section for `/api/nodes/{node_id}/companion` inspection.

Acceptance criteria:
- script passes locally twice consecutively.
- failure mode prints concise event diagnostics.

### Phase B: Subscription Precision

Goal:
- demonstrate scoped event routing using `path_glob`.

Files:
- `remora.yaml`
- `scripts/test_virtual_agents.sh` or new `scripts/test_subscription_filters.sh`
- optional `docs/*.md` test target files

Implementation tasks:
1. Add a scoped virtual observer for docs path (`docs/**`).
2. Trigger changes in `src/` and `docs/` separately.
3. Assert only corresponding observers react.
4. Include an absolute-path event match assertion.

Acceptance criteria:
- deterministic pass/fail for both path scopes.
- no false positive observer activations.

### Phase C: Proposal Accept + Reconcile

Goal:
- demonstrate full HITL proposal lifecycle including accept path.

Files:
- new `scripts/test_proposal_accept_flow.sh`
- keep existing `scripts/test_proposal_flow.sh`

Implementation tasks:
1. Trigger proposal with controlled target node/file.
2. Retrieve proposal diff and assert non-empty diff payload.
3. Accept proposal via API.
4. Assert disk file mutation occurred.
5. Assert `rewrite_accepted` and subsequent `content_changed` events.

Acceptance criteria:
- accept flow passes with event proof.
- reject flow script remains working.

### Phase D: Multi-Language Discovery

Goal:
- show Python + Markdown + TOML nodes in same graph.

Files:
- `remora.yaml`
- demo content files under `docs/` and a config directory (`configs/`)
- new `scripts/test_multilang_discovery.sh`

Implementation tasks:
1. Expand `discovery_languages` (or remove strict allowlist).
2. Add sample markdown headings and toml tables.
3. Script asserts expected node types from `remora discover` or `/api/nodes`.

Acceptance criteria:
- stable presence of `section` and `table` node types.

### Phase E: SSE Replay/Resume

Goal:
- prove resumable observability behavior from SSE endpoint.

Files:
- new `scripts/test_sse_contract.sh`
- `DEMO_SCRIPT.md`

Implementation tasks:
1. Generate known event burst.
2. Verify `/sse?replay=N` includes expected events.
3. Resume with `Last-Event-ID` and assert continuation semantics.
4. Verify `once=true` closes stream after replay.

Acceptance criteria:
- script passes with clear replay/resume checks.

### Phase F: Cursor Focus

Goal:
- demonstrate editor-style focus-to-node linkage.

Files:
- new `scripts/test_cursor_focus.sh`
- `DEMO_SCRIPT.md`

Implementation tasks:
1. POST `/api/cursor` with known file/line.
2. Assert `node_id` is returned when line maps to node.
3. Assert `cursor_focus` event is emitted.

Acceptance criteria:
- deterministic mapping for at least one known node line.

### Phase G: Relationship-Aware Tooling

Goal:
- expose graph relationship externals in demo interactions.

Files:
- `bundles/demo-code-agent/bundle.yaml`
- new tool scripts in `bundles/demo-code-agent/tools/`
- new `scripts/test_relationship_tools.sh`

Implementation tasks:
1. Add tools for importers/dependencies/edge-type lookups.
2. Wire deterministic trigger tokens in prompt instructions.
3. Assert `remora_tool_result` contains expected relationship output.

Acceptance criteria:
- agent can answer relationship queries with graph evidence.

### Phase H: Runtime Guardrails and Metrics

Goal:
- showcase operational safety metrics from `/api/health`.

Files:
- new `remora.stress.yaml`
- new `scripts/test_runtime_guardrails.sh`
- `README.md`

Implementation tasks:
1. Add stress config with small inbox limits.
2. Flood targeted events/messages.
3. Assert overflow counters update while health stays `ok`.
4. Document metric meaning in README troubleshooting.

Acceptance criteria:
- metrics script demonstrates overflow counters and healthy runtime.

### Phase I: LSP Event Bridge

Goal:
- go beyond startup and show event emission from LSP notifications.

Files:
- new `scripts/test_lsp_event_bridge.sh`
- `README.md`
- `DEMO_SCRIPT.md`

Implementation tasks:
1. Send minimal `didOpen`/`didSave` style interactions.
2. Verify `content_changed` event appears.
3. Keep `test_lsp_startup.sh` as smoke check.

Acceptance criteria:
- bridge script confirms event path end-to-end.

### Phase J: Docs and Runbook Consolidation

Goal:
- align docs with actual scripts and default profile.

Files:
- `README.md`
- `DEMO_SCRIPT.md`
- `docs/architecture.md`
- `scripts/run_demo_checks.sh`

Implementation tasks:
1. Update docs to include all newly added scripts.
2. Clearly mark required vs optional paths.
3. Ensure defaults and fallback profiles are clearly labeled.
4. Align final run command sequence with verification matrix.

Acceptance criteria:
- no contradictory docs/config/script behavior.

## 6. Test and Verification Matrix

| Feature Slice | Primary Validation | Supporting Evidence |
|---|---|---|
| Reflection pipeline | `scripts/test_reflection_pipeline.sh` | `/api/events`, `/api/nodes/{id}/companion` |
| Subscription precision | `scripts/test_subscription_filters.sh` | observer-specific event deltas |
| Proposal accept flow | `scripts/test_proposal_accept_flow.sh` | proposal diff + `rewrite_accepted` + `content_changed` |
| Multi-language discovery | `scripts/test_multilang_discovery.sh` | `remora discover` node types |
| SSE replay/resume | `scripts/test_sse_contract.sh` | replay + resume IDs |
| Cursor focus | `scripts/test_cursor_focus.sh` | `/api/cursor` response + `cursor_focus` event |
| Relationship tools | `scripts/test_relationship_tools.sh` | `remora_tool_result` payload |
| Guardrails/metrics | `scripts/test_runtime_guardrails.sh` | `/api/health.metrics` counters |
| LSP event bridge | `scripts/test_lsp_event_bridge.sh` | `content_changed` events |

Run full suite target after all phases:

```bash
scripts/test_demo_runtime.sh
scripts/test_virtual_agents.sh
scripts/test_proposal_flow.sh
scripts/test_proposal_accept_flow.sh
scripts/test_reflection_pipeline.sh
scripts/test_subscription_filters.sh
scripts/test_multilang_discovery.sh
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
scripts/test_relationship_tools.sh
scripts/test_runtime_guardrails.sh
scripts/test_lsp_startup.sh
scripts/test_lsp_event_bridge.sh
scripts/test_search.sh
```

## 7. Documentation and Demo Narrative Updates

Required documentation updates:

1. `README.md`
- add new scripts list and required env/services by feature
- include clear “full showcase” vs “reduced fallback” section

2. `DEMO_SCRIPT.md`
- add live narrative sequence reflecting new features
- include short copy/paste blocks for each showcase slice

3. `docs/architecture.md`
- add explicit mention of reflection-to-companion pipeline
- add cursor and SSE contract references

4. `.scratch` project docs
- keep `PROGRESS.md` and `CONTEXT.md` current during implementation

## 8. Rollback and Recovery

Rollback at phase granularity:

1. Revert only the most recent phase commit(s):
```bash
git revert <commit>
```

2. If severe regression occurs, branch from backup baseline:
```bash
git checkout backup/main-pre-integration-2026-03-25
git checkout -b fix/restart-from-baseline
```

3. Keep fallback profile available:
- `remora.constrained.yaml` should remain usable until full rollout stabilizes.

## 9. Commit Plan

Recommended commit sequence:

1. `feat(demo): add reflection pipeline verification and companion evidence checks`
2. `feat(demo): add scoped subscription filter demo and assertions`
3. `feat(demo): add proposal accept flow verification`
4. `feat(demo): enable and validate multilang discovery`
5. `feat(demo): add sse replay and resume contract checks`
6. `feat(demo): add cursor focus integration checks`
7. `feat(demo): add relationship-aware demo tools and tests`
8. `feat(demo): add runtime guardrail metrics stress checks`
9. `feat(demo): add lsp event bridge verification`
10. `docs(demo): align readme, architecture, and demo script with new flow`

## 10. Final Definition of Done

Integration implementation is complete when all conditions hold:

1. All baseline scripts and all new scripts pass.
2. New showcase slices produce deterministic evidence in API/events output.
3. Docs match implementation behavior and default profile.
4. Backup branch exists and can be checked out for fast restore.
5. Demo supports both:
- concise baseline run
- full “show off remora-v2” showcase run
