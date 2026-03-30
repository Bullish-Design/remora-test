# ASSUMPTIONS

Date: 2026-03-25
Project: `06-remora-v2-demo-integration-ideas`

1. Primary target repo for integration work is `remora-test`.
2. Reference behavior source is the latest local `remora-v2` at `/home/andrew/Documents/Projects/remora-v2`.
3. Objective is demo quality and clarity, not feature parity with every upstream test.
4. Existing demo scripts in `remora-test/scripts/` are considered baseline and should be extended rather than replaced where possible.
5. Validation should remain runnable via `devenv shell -- ...` for environment consistency.
6. High-priority showcase areas are reactive flow, observability, proposal safety, and integration surfaces (SSE/LSP/cursor/search).
7. Any upstream-only fixes should be documented as upstream dependencies, not silently worked around in demo claims.
