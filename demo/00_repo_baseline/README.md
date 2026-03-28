# 00_repo_baseline Demo Runbook

This demo showcases remora graph/runtime capabilities against this repository with a manifest-driven, isolated workflow.

## Scope

- API graph contracts (`/api/health`, `/api/nodes`, `/api/edges`, `/api/events`)
- Deterministic tool routing via bundle overlays
- Virtual observers, subscription filters, and reflection pipeline
- Proposal reject/accept lifecycle
- SSE replay/resume and cursor focus behavior
- Semantic search indexing/query path
- LSP startup and LSP event bridge behavior
- Optional stress guardrail overflow checks

## Prerequisites

- `devenv`
- `uv`
- model endpoint configured for runtime turns
- embeddy backend if you require strict search checks

## Quick Start

Terminal A:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py setup --demo 00_repo_baseline --clean-workspace
devenv shell -- python scripts/democtl.py start --demo 00_repo_baseline
```

Terminal B:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py status --demo 00_repo_baseline
devenv shell -- python scripts/democtl.py queries --demo 00_repo_baseline
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline
```

Strict verification (no scoped capability skips):

```bash
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

## Python Check Runner

Checks are implemented in `demo/00_repo_baseline/checks/` and orchestrated by `runner.py`.

Run all default checks directly:

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base http://127.0.0.1:8080 \
  --project-root . \
  --config-path demo/00_repo_baseline/config/remora.yaml
```

Run selected checks:

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base http://127.0.0.1:8080 \
  --project-root . \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --filter check_runtime \
  --filter check_relationships \
  --filter check_virtual_agents
```

Enable optional guardrails and strict LSP/search requirements:

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base http://127.0.0.1:8080 \
  --project-root . \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --strict \
  --require-search \
  --require-lsp-bridge \
  --run-lsp-bridge \
  --run-guardrails \
  --require-overflow
```

If strict search is noisy in your environment, set an explicit index error threshold:

```bash
MAX_INDEX_ERRORS=10 devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

Run UI-only Playwright smoke check:

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base http://127.0.0.1:8080 \
  --project-root . \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --filter check_ui_playwright
```

Playwright screenshots are saved to:
- `demo/00_repo_baseline/artifacts/ui_screenshots/ui-playwright-<timestamp>-<ms>.png`

Shared repo-level screenshot command (can be reused by other demos):

```bash
devenv shell -- uv run python scripts/playwright_screenshot.py \
  --url http://127.0.0.1:8080/ \
  --project-root . \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --json
```

## Strict Search Setup (if needed)

Terminal C:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python demo/00_repo_baseline/scripts/mock_embedder_server.py
```

Terminal D:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- embeddy serve --config configs/embeddy.remote.yaml
```

Restart runtime with embeddy URL if needed:

```bash
cd /home/andrew/Documents/Projects/remora-test
REMORA_EMBEDDY_URL=http://127.0.0.1:8585 devenv shell -- python scripts/democtl.py start --demo 00_repo_baseline
```

## UI Source

The demo UI is served directly from the installed `remora` package (`remora/web/static/*`).
No repo-local vendor sync or HTML patch step is used.

## Fresh Reset

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py cleanup --demo 00_repo_baseline
devenv shell -- python scripts/democtl.py wipe --demo 00_repo_baseline --force
```

## Troubleshooting

- Health fails: runtime is not running on the expected base URL.
- Search strict fails: embeddy/mock embedder unavailable or indexing errors exceed strict threshold.
- LSP strict fails: missing LSP extras (`remora[lsp]`) or no observed bridge change event in-window.
- Proposal accept check fails: inspect `/api/proposals` and recent `/api/events` for rewrite lifecycle events.
