# Context — Demo Improvements

## Current State
DEMO_IMPROVEMENTS.md is complete with two major structural refactors added per user request:
1. **democtl.py refactor** into `scripts/_lib/` modules (manifest, paths, http, runtime, commands)
2. **Shell-to-Python conversion** of 18 bash scripts into a `checks/` module with shared `_harness.py`

## What Just Happened
- Read all 18 shell scripts + democtl.py to map dependencies, patterns, and external tool usage
- Designed `_harness.py` with `RemoraClient`, `poll_events`, `find_node`, `CheckResult`
- Designed `checks/` module layout mapping each shell script to a Python check
- Removed the democtl refactor from "not worth fixing" and promoted it to priority #1
- Removed ripgrep dep, file mutation, orphan cleanup, companion determinism as standalone items (absorbed into Python conversion)

## Next
- Triage with user to decide which items to implement and in what order.
