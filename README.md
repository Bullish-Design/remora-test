# remora-test-demo

Demonstration repository for `remora-v2`.

## Demo Catalog

- [`00_repo_baseline`](demo/00_repo_baseline/README.md): baseline end-to-end demo for web graph, virtual agents, proposals, SSE, search, and LSP.

## Common Demo Control

Use the shared control plane:

```bash
python scripts/democtl.py setup --demo 00_repo_baseline --clean-workspace
python scripts/democtl.py start --demo 00_repo_baseline
```

In another shell:

```bash
python scripts/democtl.py status --demo 00_repo_baseline
python scripts/democtl.py queries --demo 00_repo_baseline
python scripts/democtl.py verify --demo 00_repo_baseline
```

Strict verification (no capability skips):

```bash
python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

Direct check runner (useful for filtered validation):

```bash
python demo/00_repo_baseline/checks/runner.py --base http://127.0.0.1:8080 --project-root . --config-path demo/00_repo_baseline/config/remora.yaml
python demo/00_repo_baseline/checks/runner.py --base http://127.0.0.1:8080 --project-root . --config-path demo/00_repo_baseline/config/remora.yaml --filter check_runtime --filter check_relationships --filter check_ui_playwright
```

Frequent UI screenshot capture (shared repo-level script):

```bash
python scripts/playwright_screenshot.py --url http://127.0.0.1:8080/ --project-root . --config-path demo/00_repo_baseline/config/remora.yaml --json
```

Fresh-run wipe:

```bash
python scripts/democtl.py wipe --demo 00_repo_baseline --force
```

## Prerequisites

- `devenv`
- `uv`
- local/remote model endpoint for agent turns
- embeddy backend if running strict semantic search checks

Optional environment variables:

- `REMORA_MODEL_BASE_URL`
- `REMORA_MODEL_API_KEY`
- `REMORA_MODEL`
- `REMORA_EMBEDDY_URL`

## Notes

- Demo runtime state is isolated under `.remora-00-repo-baseline`.
- Demo assets live under `demo/00_repo_baseline/`.
- Automated checks live under `demo/00_repo_baseline/checks/`.
- `devenv` includes Playwright runtime/browser wiring for UI smoke verification.
- For detailed operator flow, use the demo-local docs and cue sheet.
