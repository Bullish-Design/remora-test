# Decisions

## 2026-03-15 - Use bounded runtime for demo verification
- **Context:** Need to demonstrate behavior without leaving background services running.
- **Decision:** Use `remora start --run-seconds` and exercise APIs while runtime is live.
- **Rationale:** Produces deterministic, repeatable evidence.
- **Assumptions used:** `ASSUMPTIONS.md` items 1 and 2.

## 2026-03-15 - Target non-directory node for chat checks
- **Context:** Chatting the root directory node created avoidable status-transition warnings.
- **Decision:** Prefer a non-directory node for demo chat tests.
- **Rationale:** Better represents typical user chat behavior and cleaner runtime signal.
- **Assumptions used:** `ASSUMPTIONS.md` item 1.
