# PLAN

## CRITICAL RULE REMINDER
NO SUBAGENTS. All work for this project must be completed directly in this session.

## Objective
Implement the refactor defined in:
`/home/andrew/Documents/Projects/remora-test/.scratch/projects/03-remora-v2-demo-review-2026-03-22/REMORA_DEMO_REFACTORING_GUIDE.md`

Goal: bring `remora-test` to full demo functionality for the latest remora-v2.

## Implementation Phases
1. Foundation and baseline capture
- Sync dependencies and capture before-state artifacts.

2. Core config migration
- Replace legacy keys in `remora.yaml` with latest remora-v2 schema.
- Add `queries/` local override folder scaffold.

3. Tooling/metadata cleanup
- Correct stale template references in `pyproject.toml`.
- Add initial `tests/` scaffolding.

4. Documentation refactor
- Rewrite README and update demo architecture docs.

5. Bundle/tool demo expansion
- Add local demo bundles and custom `.pym` tools.
- Update `bundle_overlays` accordingly.

6. Virtual agent and proposal flow
- Configure virtual agents.
- Add proposal-flow and virtual-agent validation scripts.

7. Optional search path
- Add optional search config and script.

8. Validation hardening
- Add consolidated runtime verification scripts and integration checks.
- Verify Definition of Done matrix.

## Acceptance Criteria
- All required phases (except optional search) implemented.
- Validation scripts execute successfully in documented sequence.
- README reflects actual executable workflow.
- No legacy remora config keys remain.

## CRITICAL RULE REMINDER
NO SUBAGENTS. All work for this project must be completed directly in this session.
