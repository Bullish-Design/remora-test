# Issues

## 1) Runtime readiness race (resolved)
- **Symptom:** Immediate API calls after launching `remora start` intermittently failed with connection errors.
- **Fix:** Added readiness polling on `GET /api/nodes` before running API/SSE/chat checks.
- **Result:** Demo checks became stable and repeatable.

## 2) Chatting root directory node caused noisy warnings (resolved)
- **Symptom:** Targeting node `.` produced `Invalid agent status transition ... RUNNING -> RUNNING` warnings in runtime logs.
- **Fix:** Updated chat targeting to prefer a non-directory node (`node_type != "directory"`), falling back only if needed.
- **Result:** Chat flow executed cleanly against `create_order` and produced a valid agent response.

## 3) Guide/runtime mismatch for this installed remora build (resolved)
- **Symptom:** Guide references `bundle_overlays` and `/api/health`, but installed runtime expects `bundle_mapping` and has no `/api/health`.
- **Fix:** Kept `bundle_mapping` in `remora.yaml`; used `/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`, and `/sse` for validation.
- **Result:** Runtime and smoke tests succeeded.

## 4) Graph edges count is zero (root-cause identified, fix pending)
- **Symptom:** `/api/edges` returned `[]` during demo runs.
- **Root cause:** Runtime persists `parent_id` on nodes but does not call `NodeStore.add_edge()`, so `edges` table stays empty.
- **Current status:** Not blocking for chat/runtime demo; blocking for connected graph visualization.
- **Suggested follow-up:** Implement containment edge materialization during reconciliation, then re-run demo smoke checks with `edges > 0` assertion.
