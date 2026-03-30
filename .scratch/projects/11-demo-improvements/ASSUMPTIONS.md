# Assumptions — Demo Improvements

## Audience
- Primary: developers and presenters using remora-test to demo remora-v2 capabilities.
- Secondary: LLM agents operating demos via democtl.py.

## Constraints
- remora-v2 is an external dependency; we control only the demo harness.
- Demos must remain runnable on Nix devenv (primary) and plain venv (stretch goal).
- All changes must preserve existing demo 00 functionality — no regressions.

## Key Invariants
- Manifest-driven isolation: each demo owns its own workspace, port, and config.
- Safety: wipe/cleanup must never touch paths outside `/tmp/remora-demo-*` or known workspaces.
- Reproducibility: any demo can be wiped and rebuilt from scratch with one command sequence.
