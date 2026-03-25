# ISSUES

## Open

1. Upstream virtual-agent tool reliability
- Status: unresolved upstream; full mode is default locally, with constrained fallback available via `remora.constrained.yaml`.
- Owner: upstream `remora-v2` workstream.

2. Search backend dependency
- Status: full-mode checks will require embeddy availability.
- Risk: local environments without embeddy will fail full-mode checks until provisioned.
- Evidence: `scripts/test_search.sh` now fails fast with `Error: search service is not available` when backend is missing.

3. LSP dependency
- Status: LSP demo path depends on `remora[lsp]`/`pygls` availability.
- Risk: startup checks need explicit failure guidance and skip strategy for non-LSP environments.

4. Runtime warning: "Task was destroyed but it is pending!"
- Status: observed during `remora start --log-events`.
- Likely source: SSE stream async-generator task cleanup in upstream remora-v2 (`src/remora/web/sse.py` around `stream_iterator.__anext__()` task handling).
- Risk: noisy logs and possible task-leak symptoms when SSE clients disconnect.

5. Full-mode runtime validation collision
- Status: validating Phase 1 full-mode startup can fail if another remora runtime is already active on the same workspace root.
- Evidence: `WorkspaceError [WORKSPACE_OPEN_FAILED]` provisioning `demo-companion-observer` workspace during startup.
- Impact: local validation may attach to the already-running (possibly constrained) runtime instance.
- Workaround: stop existing runtime and start a fresh full-mode runtime before running virtual checks.

6. `path_glob` suppresses review-observer triggers in current runtime build
- Status: reproduced locally; unresolved upstream.
- Evidence: full-mode config with `path_glob` produced no review observer turns; removing `path_glob` restored `agent_start/model_response/turn_complete` growth.
- Impact: full-mode default in this repo now omits `path_glob` to keep behavior checks functional.

7. Companion observer remains inactive by default
- Status: unresolved upstream/runtime behavior.
- Evidence: repeated validation runs show `turn_digested=0` and no `demo-companion-observer` turns.
- Impact: local scripts keep companion checks opt-in (`REQUIRE_COMPANION=1` for strict mode).
