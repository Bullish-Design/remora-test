# PLAN

## CRITICAL RULE REMINDER
NO SUBAGENTS. All work for this project should be completed directly in-session.

## Objective
Implement the remora-test changes defined in:
- [NEXT_STEPS_REMORA_TEST.md](/home/andrew/Documents/Projects/remora-test/.scratch/projects/05-remora-test-full-functionality/NEXT_STEPS_REMORA_TEST.md)

## Implementation Phases
1. Baseline capture and branch prep
- Capture discover/event artifacts in `artifacts/`.

2. Behavior-level virtual checks (current-mode first)
- Upgrade `scripts/test_virtual_agents.sh` to assert meaningful actions.

3. Full-mode check enforcement
- Make search required in `scripts/run_demo_checks.sh`.
- Harden `scripts/test_search.sh` error handling.

4. Live integration tests
- Add live runtime contract tests (`pytest -m live` style).

5. LSP demo path
- Add docs + `scripts/test_lsp_startup.sh`.

6. Docs and parity sweep (pre-config-switch)
- Align docs/scripts for execution order and troubleshooting.

7. Full-mode virtual agent config (deferred to end)
- Switch default role mapping to `review-agent` + `companion`.
- Keep constrained mode only as explicit fallback profile (if retained).

8. Final validation sweep
- Align `remora.yaml`, docs, and check scripts.

## Acceptance Criteria
- Full-mode config and checks are default.
- Behavior checks validate real virtual-agent work.
- Live tests exist for runtime, virtual agents, proposals, search.
- LSP path is documented and script-validated.
- Docs and executable flow are consistent.

## CRITICAL RULE REMINDER
NO SUBAGENTS. All work for this project should be completed directly in-session.
