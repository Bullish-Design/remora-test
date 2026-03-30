# 00_repo_baseline Presenter Cue Sheet

Repo root assumed:
- `/home/andrew/Documents/Projects/remora-test`

## Pre-show setup

Terminal A:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py setup --demo 00_repo_baseline --clean-workspace
devenv shell -- python scripts/democtl.py start --demo 00_repo_baseline
```

Terminal B:

```bash
cd /home/andrew/Documents/Projects/remora-test
BASE="http://127.0.0.1:8080"
devenv shell -- python scripts/democtl.py status --demo 00_repo_baseline
devenv shell -- python scripts/democtl.py queries --demo 00_repo_baseline
```

## 5-minute path

1. Baseline runtime + graph + deterministic tooling

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base "$BASE" \
  --project-root demo/00_repo_baseline/fixture \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --filter check_runtime \
  --filter check_relationships
```

2. Virtual/reactive behavior + reflection + proposals + SSE/cursor

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base "$BASE" \
  --project-root demo/00_repo_baseline/fixture \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --filter check_virtual_agents \
  --filter check_reflection \
  --filter check_proposal_reject \
  --filter check_sse \
  --filter check_cursor
```

3. Close with full orchestration summary

```bash
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline
```

Optional UI render proof (Playwright):

```bash
devenv shell -- python demo/00_repo_baseline/checks/runner.py \
  --base "$BASE" \
  --project-root demo/00_repo_baseline/fixture \
  --config-path demo/00_repo_baseline/config/remora.yaml \
  --filter check_ui_playwright
```

## 30-minute full path

1. Full verify in default mode

```bash
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline
```

2. If search backend and LSP dependencies are available, run strict mode

```bash
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

If indexing emits non-fatal parser errors in your environment, set an explicit threshold:

```bash
MAX_INDEX_ERRORS=10 devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline --strict
```

3. Optional stress/guardrail segment

Terminal A restart with stress profile:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py start --demo 00_repo_baseline --profile stress
```

Terminal B run guardrails:

```bash
devenv shell -- python scripts/democtl.py verify --demo 00_repo_baseline --run-guardrails --require-overflow
```

## Strict search backend quick setup

Terminal C:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python demo/00_repo_baseline/scripts/mock_embedder_server.py
```

Terminal D:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- embeddy serve --config demo/00_repo_baseline/fixture/configs/embeddy.remote.yaml
```

## Recovery paths

- Runtime not healthy: restart Terminal A with `democtl.py start`.
- Search strict failure: verify embeddy + mock embedder health first.
- LSP strict failure: ensure `remora[lsp]` extras are installed and runtime has built workspace DB.
- Need clean reset between rehearsals:

```bash
cd /home/andrew/Documents/Projects/remora-test
devenv shell -- python scripts/democtl.py wipe --demo 00_repo_baseline --force
devenv shell -- python scripts/democtl.py setup --demo 00_repo_baseline --clean-workspace
```
