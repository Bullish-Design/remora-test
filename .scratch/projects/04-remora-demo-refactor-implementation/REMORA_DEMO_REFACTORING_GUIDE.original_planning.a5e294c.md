# Remora Demo Refactoring Guide (Intern Implementation Playbook)

Date: 2026-03-22  
Target repo: `/home/andrew/Documents/Projects/remora-test`  
Reference library: `/home/andrew/Documents/Projects/remora-v2`

## Table of Contents

1. Purpose and Success Criteria
- What this migration achieves and what "full functionality" means for this demo.

2. Current-State Problems (What Is Broken / Outdated)
- Concrete mismatches between current `remora-test` and latest `remora-v2`.

3. Refactor Strategy Overview
- Phase-based sequence and why the order matters.

4. Prerequisites and Setup
- Required tools, environment checks, branch workflow, and baseline snapshot steps.

5. Phase 1: Align Core Configuration to Latest remora-v2
- Replace legacy keys and establish a modern, valid `remora.yaml` foundation.

6. Phase 2: Clean Project Metadata and Packaging Hygiene
- Fix `pyproject.toml` template leftovers and make tooling coherent.

7. Phase 3: Rewrite Demo Documentation for Correct Onboarding
- Replace minimal README with a demo-first quickstart and operator instructions.

8. Phase 4: Add Local Bundles and Tooling Demo Surface
- Introduce local bundles and at least one custom `.pym` tool path.

9. Phase 5: Add Virtual Agent and Reactive Workflow Demonstration
- Demonstrate cross-cutting automation using `virtual_agents`.

10. Phase 6: Add Proposal (Human-in-the-Loop Rewrite) Demonstration
- Exercise proposal endpoints and acceptance/rejection flow end-to-end.

11. Phase 7: Add Search/Index Demonstration (Optional but Recommended)
- Add semantic search config and a runnable indexing + query flow.

12. Phase 8: Add Automated Demo Validation
- Add repeatable smoke/integration checks so regressions are caught early.

13. Validation Matrix and Definition of Done
- Exact checks that must pass before declaring migration complete.

14. Troubleshooting and Common Failure Modes
- Fast diagnosis guide for likely intern blockers.

15. Execution Checklist (Intern Task Board)
- Actionable checklist with completion gates.

16. Appendix A: Canonical Reference Files in remora-v2
- Exact files in remora-v2 to consult if behavior drifts.

17. Appendix B: Suggested Commit Plan
- Recommended commit slicing to keep the migration reviewable.

## 1. Purpose and Success Criteria

This guide describes how to migrate `remora-test` from an older remora-v2 integration pattern to the **current** remora-v2 architecture and config/API contracts.

"Full functionality" for this demo means:
- The demo uses current remora-v2 config keys and behavior.
- The demo starts cleanly with current remora CLI workflows.
- The demo shows more than chat: at minimum bundles/tools, virtual agent behavior, and proposal workflow.
- The demo has repeatable verification steps (scripted, not only manual).
- A new engineer (intern) can run the demo and understand what each capability proves.

Hard success criteria:
1. `remora.yaml` is aligned with current remora-v2 schema.
2. README documents end-to-end remora demo flow.
3. At least one local custom tool is added and exercised.
4. Virtual agent path is configured and demonstrably active.
5. Proposal endpoints are exercised in a runnable script.
6. Automated validation script(s) pass on a fresh environment.

## 2. Current-State Problems (What Is Broken / Outdated)

These are the concrete mismatches that must be fixed:

1. Legacy config keys in `remora.yaml`:
- `swarm_root` should be `workspace_root`.
- `bundle_root` should be replaced by `bundle_search_paths`.
- `bundle_mapping` should be replaced by `bundle_overlays` (or `bundle_rules`).

2. Demo scope is too narrow:
- Current scripts mostly prove `/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`.
- No built-in demonstration of proposals, virtual agents, search, or LSP.

3. Repository metadata is template-derived and misleading:
- `pyproject.toml` points to `src/template_py` and `--cov=embeddify`, not this repo.

4. Onboarding docs are insufficient:
- Top-level README currently shows app execution (`python -m src.main`) rather than remora workflow.

5. Missing local demo assets:
- No local `bundles/` directory.
- No local `queries/` directory.
- No tests folder for repeatable verification.

## 3. Refactor Strategy Overview

Execute in strict phase order to avoid compounding failures:

1. **Schema alignment first**
- Fix config and packaging foundations before adding advanced features.

2. **Docs + developer UX second**
- Ensure anyone can run the base flow after foundational fixes.

3. **Feature expansion third**
- Add local bundles/tools, virtual agent, and proposal flow.

4. **Automation and hardening last**
- Add scripts/tests that lock behavior and catch regressions.

Why this order:
- Most downstream issues during remora integration come from config drift.
- Advanced demo features are hard to debug when base startup/discovery is unstable.

## 4. Prerequisites and Setup

### 4.1 Required Environment

- OS shell with `bash`/`zsh`
- `devenv`
- `uv`
- `jq`
- local access to `/home/andrew/Documents/Projects/remora-v2`
- optional live model endpoint (for real LLM behavior)

### 4.2 Branch and Baseline Snapshot

From `/home/andrew/Documents/Projects/remora-test`:

```bash
git checkout -b chore/remora-demo-v2-refactor
mkdir -p .scratch/projects/03-remora-v2-demo-review-2026-03-22/artifacts
```

Capture baseline diagnostics (before edits):

```bash
devenv shell -- uv sync --extra dev

devenv shell -- remora discover --project-root . \
  | tee .scratch/projects/03-remora-v2-demo-review-2026-03-22/artifacts/baseline_discover.txt
```

If runtime starts, capture endpoint snapshots:

```bash
# terminal A
devenv shell -- remora start --project-root . --port 8080 --log-events

# terminal B
curl -sS http://127.0.0.1:8080/api/health \
  | tee .scratch/projects/03-remora-v2-demo-review-2026-03-22/artifacts/baseline_health.json
curl -sS http://127.0.0.1:8080/api/nodes \
  | tee .scratch/projects/03-remora-v2-demo-review-2026-03-22/artifacts/baseline_nodes.json
curl -sS http://127.0.0.1:8080/api/events?limit=20 \
  | tee .scratch/projects/03-remora-v2-demo-review-2026-03-22/artifacts/baseline_events.json
```

### 4.3 Mandatory Reference Inputs (Read Before Editing)

The intern must keep these open while implementing:
- `/home/andrew/Documents/Projects/remora-v2/remora.yaml.example`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/core/model/config.py`
- `/home/andrew/Documents/Projects/remora-v2/docs/HOW_TO_USE_REMORA.md`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/**`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/*.py`

Rule: when this guide and remora-v2 source disagree, follow remora-v2 source.

## 5. Phase 1: Align Core Configuration to Latest remora-v2

### 5.1 Replace `remora.yaml` with Current-Key Version

Current file uses legacy keys and must be fully replaced.

Target file: `/home/andrew/Documents/Projects/remora-test/remora.yaml`

Use this baseline content first (copy exactly, then adjust optional sections in later phases):

```yaml
project_path: "."
discovery_paths:
  - "src/"

discovery_languages:
  - "python"

language_map:
  ".py": "python"
  ".md": "markdown"
  ".toml": "toml"

query_search_paths:
  - "queries/"
  - "@default"

bundle_search_paths:
  - "bundles/"
  - "@default"

bundle_overlays:
  function: "code-agent"
  class: "code-agent"
  method: "code-agent"
  file: "code-agent"
  directory: "directory-agent"

model_base_url: "${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}"
model_api_key: "${REMORA_MODEL_API_KEY:-EMPTY}"
model_default: "${REMORA_MODEL:-Qwen/Qwen3-4B-Instruct-2507-FP8}"
timeout_s: 300.0
max_turns: 8

workspace_root: ".remora"
max_concurrency: 4
max_trigger_depth: 5
trigger_cooldown_ms: 1000
workspace_ignore_patterns:
  - ".git"
  - ".venv"
  - "__pycache__"
  - "node_modules"
  - ".remora"
```

Why this works:
- Keys align with `remora.core.model.config.Config` nesting behavior.
- `query_search_paths` and `bundle_search_paths` include `@default`, so shipped defaults remain available even if local folders are absent.

### 5.2 Create Missing `queries/` Directory

This demo does not require custom tree-sitter queries yet, but `queries/` should exist because config points to it.

```bash
mkdir -p queries
printf "# local query overrides live here\n" > queries/README.md
```

### 5.3 Validate Config Parsing and Discovery

```bash
devenv shell -- remora discover --project-root .
```

Expected:
- Command succeeds.
- Node count is non-zero.
- No validation errors about unknown keys such as `swarm_root` / `bundle_mapping`.

### 5.4 Guardrail Check (Must Pass)

Run a quick grep to ensure legacy keys are gone:

```bash
rg -n "swarm_root|bundle_root|bundle_mapping" remora.yaml
```

Expected: no matches.

## 6. Phase 2: Clean Project Metadata and Packaging Hygiene

### 6.1 Update `pyproject.toml` Identity and Tooling Targets

Target file: `/home/andrew/Documents/Projects/remora-test/pyproject.toml`

Required corrections:

1. Rename project metadata:
- `name = "remora-test-demo"`
- description should mention remora-v2 demo repository.

2. Replace stale package targets:
- Remove references to `src/template_py`.
- For this demo repo (not a distributable library), use minimal packaging config or align to real module layout.

3. Fix pytest coverage target:
- Replace `--cov=embeddify` with either:
  - `--cov=src` (simple), or
  - remove coverage addopts if tests are not yet in place.

4. Fix mypy package target:
- Replace `packages = ["src/template_py"]` with paths that exist, or temporarily scope to `src`.

Recommended minimal working snippet changes:

```toml
[project]
name = "remora-test-demo"
version = "0.1.0"
description = "Demonstration repository for remora-v2 runtime capabilities."

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
addopts = "-q --cov=src --cov-report=term-missing"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.13"
files = ["src"]
strict = true
```

If wheel packaging with `packages = ["src"]` is undesirable, set this repo as non-package demo and remove wheel target entirely. Choose one approach and document it in README.

### 6.2 Create `tests/` Scaffolding Immediately

Even before full tests are written, create test dirs now to match tooling configuration:

```bash
mkdir -p tests/integration tests/smoke
printf "def test_placeholder() -> None:\n    assert True\n" > tests/smoke/test_placeholder.py
```

### 6.3 Validate Local Tooling Consistency

```bash
devenv shell -- uv sync --extra dev
devenv shell -- pytest tests/smoke/test_placeholder.py -q
```

Expected:
- dependency sync succeeds
- placeholder test passes
- no immediate pyproject target errors

## 7. Phase 3: Rewrite Demo Documentation for Correct Onboarding

### 7.1 Replace Top-Level README

Target file: `/home/andrew/Documents/Projects/remora-test/README.md`

The new README must include these sections, in this order:
1. What this repository demonstrates.
2. Prerequisites (`devenv`, model endpoint expectations).
3. Quick start (sync deps, discover, start runtime).
4. API smoke verification.
5. Advanced demo paths (virtual agent, proposal flow, optional search/LSP).
6. Troubleshooting.

Minimum command block to include:

```bash
devenv shell -- uv sync --extra dev
devenv shell -- remora discover --project-root .
devenv shell -- remora start --project-root . --port 8080 --log-events
```

### 7.2 Add a Demo-Oriented Architecture Note

Update or replace `/home/andrew/Documents/Projects/remora-test/docs/architecture.md` so it explains:
- How `src/` maps into remora nodes/edges.
- Which bundle role each node type uses.
- Which virtual agents are active and why.
- Which scripts validate which subsystem.

### 7.3 Documentation Acceptance Check

A new engineer should be able to execute this exact sequence from README without extra tribal knowledge:

```bash
devenv shell -- uv sync --extra dev
devenv shell -- remora discover --project-root .
# then start runtime and run smoke script from a second terminal
```

If you needed any undocumented local setup, README is incomplete and must be fixed.

## 8. Phase 4: Add Local Bundles and Tooling Demo Surface

### 8.1 Create Local Bundle Structure

Create directories:

```bash
mkdir -p bundles/demo-code-agent/tools
mkdir -p bundles/demo-directory-agent/tools
```

Important design rule:
- Use **new bundle names** (`demo-code-agent`, `demo-directory-agent`) instead of overriding shipped names (`code-agent`, `directory-agent`) to avoid merge-order ambiguity.

### 8.2 Add Local Bundle Configs

Create `bundles/demo-code-agent/bundle.yaml`:

```yaml
name: demo-code-agent
externals_version: 2
system_prompt_extension: |
  You are a demo code agent for remora-test.
  If a user message contains the token rewrite_to_magic, call the rewrite_to_magic tool exactly once.
  If a user message contains the token demo_echo, call demo_echo exactly once.
  Always use send_message to reply to "user".
prompts:
  chat: |
    Respond to user requests using tools when appropriate.
  reactive: |
    React to code events and keep notes concise.
max_turns: 8
```

Create `bundles/demo-directory-agent/bundle.yaml`:

```yaml
name: demo-directory-agent
externals_version: 2
system_prompt_extension: |
  You coordinate subtree-level behavior for the demo repository.
  Use summarize_tree and list_children when asked about project organization.
max_turns: 6
```

### 8.3 Add Custom Tools

Create `bundles/demo-code-agent/tools/demo_echo.pym`:

```python
from grail import Input, external

message: str = Input("message", default="hello from demo_echo")

@external
async def send_message(to_node_id: str, content: str) -> dict[str, object]: ...

send_result = await send_message("user", f"demo_echo: {message}")
result = "sent" if send_result.get("sent") else "failed"
result
```

Create `bundles/demo-code-agent/tools/rewrite_to_magic.pym`:

```python
from grail import external

@external
async def write_file(path: str, content: str) -> None: ...

@external
async def propose_changes(reason: str = "") -> str: ...

@external
async def my_node_id() -> str: ...

node_id = await my_node_id()
await write_file(f"source/{node_id}", "def compute_total(item_prices: list[float]) -> float:\n    return 42.0\n")
proposal_id = await propose_changes("demo rewrite_to_magic proposal")
proposal_id
```

### 8.4 Update Bundle Mapping in `remora.yaml`

Modify `bundle_overlays`:

```yaml
bundle_overlays:
  function: "demo-code-agent"
  class: "demo-code-agent"
  method: "demo-code-agent"
  file: "demo-code-agent"
  directory: "demo-directory-agent"
```

### 8.5 Validate Bundle Materialization

Start runtime, then inspect one agent workspace:

```bash
# terminal A
devenv shell -- remora start --project-root . --port 8080

# terminal B
NODE_ID="$(curl -sS http://127.0.0.1:8080/api/nodes | jq -r '[.[] | select(.node_type=="function")][0].node_id')"
AGENT_DIR="$(find .remora/agents -maxdepth 1 -mindepth 1 -type d | head -n 1)"
ls -la "$AGENT_DIR/_bundle/tools"
```

Expected:
- `_bundle/tools/demo_echo.pym` exists.
- `_bundle/tools/rewrite_to_magic.pym` exists.

## 9. Phase 5: Add Virtual Agent and Reactive Workflow Demonstration

### 9.1 Configure Virtual Agents in `remora.yaml`

Append this block:

```yaml
virtual_agents:
  - id: "demo-review-observer"
    role: "review-agent"
    subscriptions:
      - event_types: ["node_changed", "node_discovered"]
        path_glob: "src/**"

  - id: "demo-companion-observer"
    role: "companion"
    subscriptions:
      - event_types: ["turn_digested"]
```

Why these two:
- `demo-review-observer` demonstrates cross-cutting reactive behavior tied to source paths.
- `demo-companion-observer` demonstrates project-level digest aggregation flow.

### 9.2 Add Verification Script

Create `scripts/test_virtual_agents.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

before_count="$(curl -sS "$BASE/api/events?limit=200" | jq '[.[] | select(.agent_id=="demo-review-observer")] | length')"

echo "# demo trigger $(date +%s)" >> src/services/pricing.py
sleep 2

after_count="$(curl -sS "$BASE/api/events?limit=200" | jq '[.[] | select(.agent_id=="demo-review-observer")] | length')"

echo "before=$before_count after=$after_count"
if [ "$after_count" -le "$before_count" ]; then
  echo "Expected demo-review-observer activity did not increase" >&2
  exit 1
fi
```

Note:
- This modifies a tracked source file by appending a comment. Run in a branch and revert afterward if needed.

### 9.3 Validate Virtual Agent Node Presence

```bash
curl -sS http://127.0.0.1:8080/api/nodes \
  | jq '[.[] | select(.node_type=="virtual") | .node_id]'
```

Expected includes:
- `demo-review-observer`
- `demo-companion-observer`

## 10. Phase 6: Add Proposal (Human-in-the-Loop Rewrite) Demonstration

### 10.1 Add Proposal Demo Script

Create `scripts/test_proposal_flow.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TARGET_NODE="${TARGET_NODE:-}"

if [ -z "$TARGET_NODE" ]; then
  TARGET_NODE="$(curl -sS "$BASE/api/nodes" \
    | jq -r '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total") | .node_id' \
    | head -n 1)"
fi

if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for compute_total" >&2
  exit 1
fi

# 1) Ask the target node to trigger rewrite_to_magic.
curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"rewrite_to_magic\"}" | jq .

# 2) Poll for pending proposal.
found=""
for _ in $(seq 1 20); do
  found="$(curl -sS "$BASE/api/proposals" | jq -c '.[] | select(.node_id=="'"$TARGET_NODE"'" )' || true)"
  if [ -n "$found" ]; then
    break
  fi
  sleep 1
done

if [ -z "$found" ]; then
  echo "No proposal found for $TARGET_NODE" >&2
  exit 1
fi

echo "Proposal found: $found"

# 3) Show diff endpoint payload.
curl -sS "$BASE/api/proposals/$TARGET_NODE/diff" | jq .

# 4) Default behavior is reject to keep source clean.
curl -sS -X POST "$BASE/api/proposals/$TARGET_NODE/reject" \
  -H "Content-Type: application/json" \
  -d '{"feedback":"demo reviewed and rejected intentionally"}' | jq .
```

### 10.2 Proposal Flow Acceptance Criteria

- `POST /api/chat` returns `{"status":"sent"}`.
- `/api/proposals` includes target node at least once.
- `/api/proposals/{node_id}/diff` returns non-empty `diffs`.
- Reject endpoint returns `{"status":"rejected", ...}`.

### 10.3 Optional Accept Path (Only on Disposable Branch)

To test accept path, replace reject call with:

```bash
curl -sS -X POST "$BASE/api/proposals/$TARGET_NODE/accept" | jq .
```

Then validate file change and reconcile behavior. Revert source afterward if this is not intended as permanent change.

## 11. Phase 7: Add Search/Index Demonstration (Optional but Recommended)

### 11.1 Add Search Block to `remora.yaml`

If embeddy is available, add:

```yaml
search:
  enabled: true
  mode: "remote"
  embeddy_url: "${REMORA_EMBEDDY_URL:-http://localhost:8585}"
  timeout: 30.0
  default_collection: "code"
```

### 11.2 Add Search Script

Create `scripts/test_search.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

devenv shell -- remora index --project-root .

curl -sS -X POST "$BASE/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"compute_total", "collection":"code", "top_k":5, "mode":"hybrid"}' | jq .
```

If search service is unavailable and endpoint returns 503, document as optional runtime dependency rather than demo failure.

## 12. Phase 8: Add Automated Demo Validation

### 12.1 Consolidate Smoke Validation Script

Replace or supersede `scripts/test_remora.sh` with `scripts/test_demo_runtime.sh` that checks:
- `/api/health` returns `status=ok`.
- `/api/nodes` non-empty.
- `/api/edges` request succeeds.
- `/api/events?limit=5` request succeeds.
- `POST /api/chat` returns `status=sent`.
- virtual nodes exist (`node_type == "virtual"`) after virtual agents are configured.

### 12.2 Add End-to-End Script Runner

Create `scripts/run_demo_checks.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

scripts/test_demo_runtime.sh
scripts/test_virtual_agents.sh
scripts/test_proposal_flow.sh

# Optional
if [ "${RUN_SEARCH:-0}" = "1" ]; then
  scripts/test_search.sh
fi

echo "All demo checks passed"
```

Remember to mark all new scripts executable:

```bash
chmod +x scripts/test_demo_runtime.sh \
  scripts/test_virtual_agents.sh \
  scripts/test_proposal_flow.sh \
  scripts/run_demo_checks.sh \
  scripts/test_search.sh
```

### 12.3 Add Pytest Wrapper for CI Entry

Create `tests/integration/test_demo_contract.py` with subprocess calls or HTTP checks against a running runtime.

At minimum, include a marker-based test that verifies:
- required scripts exist and are executable
- required files/directories exist (`bundles/`, `queries/`, `tests/`)
- `remora.yaml` contains modern keys and no legacy keys

This gives immediate CI signal even without full live model loop.

### 12.4 Expected Post-Refactor File Additions

After Phases 1-8, this minimum structure should exist:

```text
bundles/
  demo-code-agent/
    bundle.yaml
    tools/
      demo_echo.pym
      rewrite_to_magic.pym
  demo-directory-agent/
    bundle.yaml
    tools/
queries/
  README.md
tests/
  smoke/
    test_placeholder.py
  integration/
    test_demo_contract.py
scripts/
  test_demo_runtime.sh
  test_virtual_agents.sh
  test_proposal_flow.sh
  run_demo_checks.sh
  test_search.sh  # optional
```

## 13. Validation Matrix and Definition of Done

Use this matrix at the end of implementation:

| Area | Check | Pass Criteria |
|---|---|---|
| Config schema | `remora discover` | completes without config validation errors |
| Modern keys | grep check | no `swarm_root`, `bundle_root`, `bundle_mapping` |
| Node graph | `/api/nodes` | non-empty list |
| Edge graph | `/api/edges` | endpoint returns valid JSON array |
| Chat | `POST /api/chat` | returns `status=sent` |
| Bundle customizations | agent `_bundle/tools` | includes `demo_echo.pym` and `rewrite_to_magic.pym` |
| Virtual agents | `/api/nodes` filter | includes expected virtual node IDs |
| Virtual reactive activity | `scripts/test_virtual_agents.sh` | observer event count increases |
| Proposal flow | `scripts/test_proposal_flow.sh` | proposal is created and diff endpoint works |
| Tooling hygiene | pytest smoke | placeholder/integration checks run successfully |
| Docs quality | fresh-run test | another engineer can run README flow unaided |

Definition of done:
- All matrix rows pass.
- README and scripts are internally consistent.
- A single command sequence exists to run full demo checks.

## 14. Troubleshooting and Common Failure Modes

1. `remora discover` fails with config key errors
- Cause: legacy keys still present.
- Fix: replace with `workspace_root`, `bundle_search_paths`, `bundle_overlays`.

2. Runtime starts but custom tools do not appear
- Cause: `bundle_overlays` not pointing to demo bundle names.
- Fix: verify `bundle_overlays.function/class/method/file` map to `demo-code-agent`.

3. Proposal flow never appears in `/api/proposals`
- Cause A: target node not using bundle with `rewrite_to_magic`.
- Cause B: model never called the tool.
- Fix:
  - confirm tool exists in `_bundle/tools`
  - strengthen bundle prompt instruction for `rewrite_to_magic` token
  - inspect `/api/events` for `remora_tool_call` or errors

4. Virtual agents never trigger
- Cause A: `virtual_agents` block missing or malformed.
- Cause B: event types/path_glob do not match emitted events.
- Fix:
  - verify `node_type == "virtual"` nodes exist
  - use snake_case event IDs (`node_changed`, `node_discovered`, `turn_digested`)
  - ensure changed file path matches `src/**`

5. Search endpoint returns 503
- Cause: search backend unavailable or not enabled.
- Fix: treat as optional unless search is in scope for required demo pass.

6. Endpoint path confusion
- Always verify against current route source:
  - `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/*.py`

## 15. Execution Checklist (Intern Task Board)

### 15.1 Foundation

- [ ] Create branch `chore/remora-demo-v2-refactor`.
- [ ] Run `devenv shell -- uv sync --extra dev`.
- [ ] Capture baseline outputs in `.scratch/.../artifacts/`.

### 15.2 Config and Metadata

- [ ] Replace `remora.yaml` with modern-key version.
- [ ] Create `queries/README.md`.
- [ ] Fix `pyproject.toml` stale template targets.
- [ ] Create `tests/smoke/test_placeholder.py`.

### 15.3 Documentation

- [ ] Rewrite README to be remora-first, not app-first.
- [ ] Update `docs/architecture.md` to reflect demo runtime architecture.

### 15.4 Capability Expansion

- [ ] Add `bundles/demo-code-agent` and `bundles/demo-directory-agent`.
- [ ] Add `demo_echo.pym` and `rewrite_to_magic.pym`.
- [ ] Update `bundle_overlays` to demo bundle names.
- [ ] Add `virtual_agents` config block.

### 15.5 Verification Automation

- [ ] Add `scripts/test_demo_runtime.sh`.
- [ ] Add `scripts/test_virtual_agents.sh`.
- [ ] Add `scripts/test_proposal_flow.sh`.
- [ ] Add `scripts/run_demo_checks.sh`.
- [ ] (Optional) Add `scripts/test_search.sh`.

### 15.6 Final Validation

- [ ] Run all required scripts against running runtime.
- [ ] Confirm validation matrix rows all pass.
- [ ] Update docs if any command differs from reality.
- [ ] Commit using structured commit plan below.

## 16. Appendix A: Canonical Reference Files in remora-v2

Use these files as the source of truth during implementation:

Configuration and schema:
- `/home/andrew/Documents/Projects/remora-v2/remora.yaml.example`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/core/model/config.py`

CLI behavior:
- `/home/andrew/Documents/Projects/remora-v2/src/remora/__main__.py`

Bundle and tool defaults:
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/system/bundle.yaml`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/code-agent/bundle.yaml`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/directory-agent/bundle.yaml`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/review-agent/bundle.yaml`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/companion/bundle.yaml`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/defaults/bundles/**/tools/*.pym`

Web/API contracts:
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/nodes.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/chat.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/events.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/proposals.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/search.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/web/routes/health.py`

Event semantics:
- `/home/andrew/Documents/Projects/remora-v2/src/remora/core/model/types.py`
- `/home/andrew/Documents/Projects/remora-v2/src/remora/core/events/types.py`

## 17. Appendix B: Suggested Commit Plan

Use small, reviewable commits in this order:

1. `chore(config): migrate remora.yaml to current remora-v2 keys`
- includes `queries/README.md`

2. `chore(tooling): clean pyproject metadata and add test scaffolding`
- includes `tests/smoke/test_placeholder.py`

3. `docs(demo): rewrite README and architecture guide for remora workflow`

4. `feat(demo-bundles): add demo-code-agent and demo-directory-agent bundles/tools`

5. `feat(demo-virtual): configure virtual agents and add verification script`

6. `feat(demo-proposals): add proposal flow script and docs`

7. `feat(demo-checks): add consolidated runtime validation scripts`

8. `feat(demo-search): optional search/index demo path`

After each commit:
- run the smallest relevant validation command
- paste command + result into commit message body or PR notes
