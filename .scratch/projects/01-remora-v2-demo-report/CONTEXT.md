# Context

- Active project: `01-remora-v2-demo-report`.
- User requested:
  1. Create a new numbered project template directory.
  2. Take notes on issues/fixes during the demo.
  3. Produce a final `DEMO_REPORT.md` with next steps.
- Execution completed:
  - Bounded runtime demo run completed successfully with captured evidence under `.scratch/projects/01-remora-v2-demo-report/artifacts/`.
  - Chat message sent to `create_order` node and accepted (`{"status":"sent"}`).
  - SSE replay captured (`sse_replay.txt`).
  - Model endpoint check succeeded (`model_count=1`).
- Main findings:
  - Setup is demo-ready for runtime/chat/SSE flow.
  - Graph edges currently report `0`; root cause identified: runtime never materializes `parent_id` relationships into the `edges` table.
- Final deliverable:
  - `DEMO_REPORT.md` created at repo root with summary, issues/fixes, and next steps.
  - Follow-up edge investigation added to `DEMO_REPORT.md`.
- Supporting follow-up artifact:
  - `.scratch/projects/01-remora-v2-demo-report/artifacts/edge_investigation.md`
- Implementation planning artifact:
  - `.scratch/projects/01-remora-v2-demo-report/EDGE_CHANGE_OVERVIEW.md`
