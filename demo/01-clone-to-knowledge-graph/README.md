# 01-clone-to-knowledge-graph Demo Runbook

This demo package implements a clean-slate, clone-first workflow for Idea #6.
Default reference repository: `pallets-eco/blinker`.

## Isolation Contract

- Clone target is isolated at `demo/01-clone-to-knowledge-graph/repo/blinker`.
- Runtime workspace state is isolated under `.remora-01-clone-to-knowledge-graph` inside that clone.
- Demo assets/config/checks live under `demo/01-clone-to-knowledge-graph/`.
- Full clean slate is enforced with `democtl wipe --demo 01-clone-to-knowledge-graph --force`.

## Quick Start

Terminal A:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py setup --demo 01-clone-to-knowledge-graph --clean-workspace
devenv shell -- python scripts/democtl.py start --demo 01-clone-to-knowledge-graph
```

Terminal B:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py status --demo 01-clone-to-knowledge-graph
devenv shell -- python scripts/democtl.py queries --demo 01-clone-to-knowledge-graph
devenv shell -- python scripts/democtl.py verify --demo 01-clone-to-knowledge-graph --no-start-search-stack
```

Note: this standard flow clones first, then starts runtime, so the graph is mostly pre-built on first UI load.

## Live Pop-In Mode (Clone While Runtime Is Live)

Use this mode when you want nodes/edges to appear progressively while repository files are being cloned.

Pyproject entrypoint: `uv run demo01-live`.

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python demo/01-clone-to-knowledge-graph/scripts/run_live_boot_demo.py
# or:
devenv shell -- uv run demo01-live
```

What it does:
- wipes demo clone dir under `demo/01-clone-to-knowledge-graph/repo/` and live workspace under `demo/01-clone-to-knowledge-graph/repo/.remora-01-clone-to-knowledge-graph-live-boot/`
- starts remora against an empty project root using `config/remora.live_boot.yaml`
- clones `pallets-eco/blinker` into that live project root
- prints changing node/edge counts as graph state grows

Optional non-blocking exit after clone settles:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python demo/01-clone-to-knowledge-graph/scripts/run_live_boot_demo.py --no-keep-running
# or:
devenv shell -- uv run demo01-live --no-keep-running
```

## UI-Only Validation + Screenshot

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py verify \
  --demo 01-clone-to-knowledge-graph \
  --filter check_ui_playwright \
  --no-start-search-stack
```

If runtime is already running from live pop-in mode, use:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py verify \
  --demo 01-clone-to-knowledge-graph \
  --filter check_ui_playwright \
  --no-start-runtime \
  --no-start-search-stack
```

Screenshots are written to:
- `demo/01-clone-to-knowledge-graph/artifacts/ui_screenshots/ui-playwright-<timestamp>-<ms>.png`

## Fresh Reset

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py cleanup --demo 01-clone-to-knowledge-graph
devenv shell -- python scripts/democtl.py wipe --demo 01-clone-to-knowledge-graph --force
```
