# DECISIONS

## 2026-03-24

1. Project workspace
- Decision: use `.scratch/projects/05-remora-test-full-functionality` for all planning and artifacts.
- Reason: continue existing numbered project convention and keep this effort isolated.

2. Guide separation
- Decision: split next-step roadmap into two files:
  - remora-test execution guide
  - remora-v2 upstream change guide
- Reason: separate local implementation work from upstream dependency work.

3. Branching
- Decision: implementation prep runs on branch `feat/full-demo-functionality`.
- Reason: isolate work from `main` and preserve a clean review path.

4. Baseline artifact location
- Decision: store baseline outputs in `05-remora-test-full-functionality/artifacts/`.
- Reason: keep kickoff evidence colocated with this project workspace.

5. Final virtual-agent default mode
- Decision: switch `remora.yaml` default virtual observer role to `review-agent` without `path_glob` filtering.
- Reason: in current runtime behavior, `path_glob` filtering prevented review observer triggers in local validation.

6. Constrained fallback profile
- Decision: keep constrained mode as explicit fallback in `remora.constrained.yaml`.
- Reason: preserves a stable fallback path when environments cannot yet run full virtual-agent behavior reliably.

7. Companion enforcement default
- Decision: keep companion checks opt-in (`REQUIRE_COMPANION=0` default in local scripts).
- Reason: current runtime does not emit `turn_digested` in this environment, so strict companion enforcement fails reliably.
