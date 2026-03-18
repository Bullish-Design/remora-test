# Decisions

## 2026-03-15 - Treat readiness as validated setup, not a persistent running process
- **Context:** The request asks to make the repo "ready to run the remora-v2 demo."
- **Decision:** Perform full configuration and dependency setup plus bounded smoke checks (`discover`, startup API checks), but do not leave long-lived background services running.
- **Rationale:** This proves setup correctness while keeping the session deterministic and clean.
- **Assumptions used:** `ASSUMPTIONS.md` items 1, 2, and 4.

## 2026-03-15 - Keep runtime-compatible config key for bundle mapping
- **Context:** The setup guide says to rename `bundle_mapping` to `bundle_overlays`, but installed remora rejects `bundle_overlays` as an extra field.
- **Decision:** Use `bundle_mapping` in `remora.yaml`.
- **Rationale:** Runtime compatibility is required for a working demo setup.
- **Assumptions used:** `ASSUMPTIONS.md` items 2 and 4.

## 2026-03-15 - Align smoke checks with actual API surface
- **Context:** The guide references `/api/health`, but this remora build does not expose that endpoint.
- **Decision:** Validate readiness against `/api/nodes`, `/api/edges`, `/api/events`, and `/api/chat`.
- **Rationale:** These are the endpoints implemented by the installed `remora.web.server`.
- **Assumptions used:** `ASSUMPTIONS.md` items 2 and 4.
