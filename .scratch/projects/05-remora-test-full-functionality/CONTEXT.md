# CONTEXT

## Project
- ID: `05-remora-test-full-functionality`
- Date started: `2026-03-24`
- Repo: `/home/andrew/Documents/Projects/remora-test`
- Branch: `feat/full-demo-functionality`

## Objective
Prepare and execute the remora-test-side work needed to move from constrained demo behavior to full intended functionality.

Source guide:
- [NEXT_STEPS_REMORA_TEST.md](/home/andrew/Documents/Projects/remora-test/.scratch/projects/05-remora-test-full-functionality/NEXT_STEPS_REMORA_TEST.md)

Related upstream guide:
- [NEXT_STEPS_REMORA_V2.md](/home/andrew/Documents/Projects/remora-test/.scratch/projects/05-remora-test-full-functionality/NEXT_STEPS_REMORA_V2.md)

## Current Baseline
- Runtime default config maps `demo-review-observer` to `review-agent` with scoped `src/**` subscriptions.
- Virtual-agent validation script is behavior-focused and companion checks are strict by default.
- Search is required in the check runner (backend dependency remains an environment prerequisite).
- Integration now includes a live contract test module gated by `REMORA_LIVE_BASE_URL`.
- LSP demo path is documented and validated via `scripts/test_lsp_startup.sh`.
