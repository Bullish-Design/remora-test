# Remora-v2 Demo Repository Review

Date: 2026-03-22  
Demo Repo: `/home/andrew/Documents/Projects/remora-test`  
Library Baseline: `/home/andrew/Documents/Projects/remora-v2`

## Table of Contents

1. Executive Summary
- High-level judgment of how well this repository demonstrates remora-v2 today.

2. Scope and Method
- What was reviewed in remora-v2 and in this demo repo, and how the evaluation was performed.

3. Remora-v2 Capability Baseline
- The concrete feature surface expected from a representative remora-v2 demonstration.

4. Demo Repo Capability Evidence
- What this repository currently includes that exercises or documents remora-v2 behavior.

5. Capability Coverage Matrix
- Feature-by-feature assessment: demonstrated, partially demonstrated, or not demonstrated.

6. Quality Assessment
- Evaluation across correctness, completeness, onboarding clarity, reproducibility, and observability.

7. Key Findings and Risks
- The most important issues reducing demo effectiveness and the practical impact of each.

8. Prioritized Improvement Plan
- Ordered remediation steps to turn this into a high-confidence showcase.

9. Recommended “Golden Demo” Flow
- A concrete walkthrough that should be possible after improvements.

10. Evidence Index
- File and source references used for the assessment.

## 1. Executive Summary

This repository currently functions as a **narrow smoke-demo** of remora-v2, not a comprehensive demonstration of the library.

Overall assessment: **Partially effective (approximately 4/10)**.

What it does reasonably well:
- Provides a small, understandable Python codebase that can be discovered by remora.
- Includes a simple API smoke script (`scripts/test_remora.sh`) that touches key runtime endpoints (`/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`).

What limits it as a true showcase:
- Core demo configuration is **out of sync** with remora-v2 naming (`swarm_root`, `bundle_root`, `bundle_mapping` vs current `workspace_root`, `bundle_search_paths`, `bundle_overlays`).
- Major remora-v2 capabilities are not demonstrated: virtual agents, bundle authoring, tool authoring, proposal workflow, search/indexing, LSP, companion panels, and multi-language discovery.
- Repository metadata appears partially template-derived and weakens trust (e.g., `src/template_py`, `--cov=embeddify`).

Conclusion: this repo is usable for a basic “runtime starts + graph endpoints respond” demo, but it does not yet represent remora-v2’s actual breadth or best practices.

## 2. Scope and Method

The review compared:
- **Library baseline** from `/home/andrew/Documents/Projects/remora-v2`.
- **Demo implementation** from `/home/andrew/Documents/Projects/remora-test`.

Method:
1. Read remora-v2 top-level docs and guides (`README.md`, `docs/architecture.md`, `docs/user-guide.md`, `docs/HOW_TO_USE_REMORA.md`, externals docs).
2. Read remora-v2 source entry points and runtime/API surfaces (`src/remora/__main__.py`, config model, reconciler, directory manager, web routes).
3. Read all files in this demo repo (`README.md`, `remora.yaml`, `pyproject.toml`, scripts, source modules, docs, prior `DEMO_REPORT.md`).
4. Build a capability-level coverage matrix and evaluate quality dimensions.

Note on runtime validation during this review:
- A targeted config-load probe using local remora-v2 source was attempted, but environment import failed due missing `aiosqlite` in this repo shell context. This review therefore emphasizes source- and config-grounded evidence.

## 3. Remora-v2 Capability Baseline

From current remora-v2 docs and source, a representative demo should cover most of these areas:

1. CLI lifecycle and operations:
- `remora start`, `remora discover`, `remora index`, `remora lsp`.

2. Correct modern configuration model:
- Discovery controls (`discovery_paths`, `language_map`, `query_search_paths`).
- Bundle controls (`bundle_search_paths`, `bundle_overlays` / `bundle_rules`).
- Runtime/infra controls (`workspace_root`, concurrency/depth/limits).
- Optional `virtual_agents` and `search` configuration blocks.

3. Graph and reactive runtime:
- Discovery/reconciliation into nodes and containment edges.
- Event routing, actor execution, and event emission.

4. Tooling contract:
- Grail `.pym` tools executed through TurnContext externals (contract v2).

5. Web/API surface:
- Nodes/edges/events/chat/SSE.
- Health endpoint.
- Proposal endpoints.
- Search endpoint (when enabled).
- Node conversation and companion endpoints.

6. Optional integration surfaces:
- LSP integration.
- Search indexing (`remora index`) and semantic query path.

A strong demo repository does not need every capability in depth, but it should at least show a coherent slice across setup, runtime behavior, and one advanced flow beyond basic chat.

## 4. Demo Repo Capability Evidence

Current demo repo evidence is concentrated in a small subset of the baseline:

What exists:
- Small Python domain sample with multiple files/functions under `src/`.
- Basic remora config file (`remora.yaml`) with discovery and model settings.
- Smoke test script that queries runtime APIs and sends chat (`scripts/test_remora.sh`).
- Prior run report with captured runtime artifacts (`DEMO_REPORT.md` + `.scratch/projects/01-remora-v2-demo-report/...`).

What is missing or weak:
- README does not explain remora startup/config workflow; it only shows `python -m src.main`.
- No local bundles or `.pym` tools to demonstrate authoring or customization.
- No virtual agents, no search config, no LSP setup.
- No tests that validate demo behavior end-to-end.
- No modern-key alignment in `remora.yaml` for key bundle/workspace fields.

## 5. Capability Coverage Matrix

| Capability Area | remora-v2 Expectation | Demo Repo Evidence | Status |
|---|---|---|---|
| CLI startup/discovery | `remora start` + `remora discover` path is documented and reproducible | No current README instructions for remora CLI; prior report references older run | Partial |
| Config key correctness | Uses current keys (`workspace_root`, `bundle_search_paths`, `bundle_overlays`, `query_search_paths`) | Uses legacy keys (`swarm_root`, `bundle_root`, `bundle_mapping`) | Not demonstrated |
| Python discovery | Discover Python nodes from `src/` | `discovery_paths: [src]`, Python source tree exists | Demonstrated |
| Multi-language discovery | Demonstrate `.py` + `.md`/`.toml` or explicit rationale | Only Python paths/files effectively covered | Not demonstrated |
| Graph links/edges | Containment edges visible through `/api/edges` | Smoke script checks edge count, but no acceptance assertion and no current artifact in root report | Partial |
| Event streaming | `/api/events` and `/sse` usage shown | `/api/events` tested in script; SSE appears only in older report artifacts | Partial |
| Chat trigger flow | `POST /api/chat` demonstrated with valid target node | Explicitly covered in `scripts/test_remora.sh` | Demonstrated |
| Proposals/rewrite workflow | `/api/proposals`, accept/reject, proposal diff path | No demo scripts/docs for proposals | Not demonstrated |
| Bundle authoring | Local custom bundle(s) and role mapping | No `bundles/` directory in repo | Not demonstrated |
| Tool authoring | Custom `.pym` tool(s) with externals usage | No `.pym` tooling in repo | Not demonstrated |
| Virtual agents | `virtual_agents` configured and behavior shown | No `virtual_agents` in config | Not demonstrated |
| Search/index | `search.enabled` config + `remora index` + `/api/search` path | No search config, no index script | Not demonstrated |
| LSP integration | `remora start --lsp` or `remora lsp` documented and exercised | No LSP instructions/config/tests | Not demonstrated |
| Companion/conversation UX | `/api/nodes/{id}/conversation` and `/api/nodes/{id}/companion` surfaced | Not covered in scripts/docs | Not demonstrated |
| Demo test automation | Repeatable tests for key demo claims | No `tests/` directory; smoke script is manual-only | Partial |

Summary:
- Demonstrated: 2
- Partial: 4
- Not demonstrated: 9

## 6. Quality Assessment

### 6.1 Correctness

Strengths:
- Basic API smoke path aligns with current endpoints (`/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`).

Concerns:
- `remora.yaml` key naming is not aligned to current remora-v2 config vocabulary.
- `DEMO_REPORT.md` states runtime compatibility conclusions that conflict with current remora-v2 naming/tests (e.g., `bundle_mapping` claim).

Assessment: **Low-to-moderate confidence** for a new user following this repo as-is.

### 6.2 Completeness

The demo covers only the most basic runtime slice. It does not demonstrate most advanced or differentiating remora-v2 features (virtual agents, bundles/tools, proposals, search, LSP, companion).

Assessment: **Low completeness** relative to remora-v2 scope.

### 6.3 Onboarding Clarity

README and docs in this repo do not provide a coherent “start remora here” narrative. The top-level README currently describes running the sample app, not running remora.

Assessment: **Low onboarding clarity**.

### 6.4 Reproducibility

- Demo scripts assume a running remora instance and dependencies like `jq`.
- No automated acceptance test in this repo verifies that the expected demo behavior still works.
- Pyproject metadata appears stale/template-derived, which can mislead setup.

Assessment: **Low reproducibility confidence**.

### 6.5 Observability and Evidence Quality

- Some observability endpoints are checked in scripts.
- Historical artifacts exist in `.scratch/projects/01-remora-v2-demo-report/`, but not surfaced as maintained, current validation for this repo state.

Assessment: **Moderate observability, weak currency guarantees**.

### 6.6 Overall Quality Scorecard (1-5)

- Correctness: 2.5/5
- Completeness: 1.5/5
- Onboarding clarity: 1.5/5
- Reproducibility: 1.5/5
- Observability: 2.5/5
- Overall: **~2.0/5**

## 7. Key Findings and Risks

1. **High: Configuration drift against remora-v2 vocabulary**
- Evidence: `remora.yaml` uses `swarm_root`, `bundle_root`, `bundle_mapping`; remora-v2 docs and config model use `workspace_root`, `bundle_search_paths`, `bundle_overlays`.
- Risk: Startup failures or silent misconfiguration depending on runtime/version behavior; demo consumers learn outdated patterns.

2. **High: Core differentiator features are not showcased**
- Evidence: no bundles/tools/virtual agents/proposal/search/LSP demo paths.
- Risk: Stakeholders perceive remora-v2 as “graph + chat only,” underrepresenting library value.

3. **High: Repo metadata suggests incomplete curation**
- Evidence: `pyproject.toml` references `src/template_py` and `--cov=embeddify`, neither matching repo contents.
- Risk: Trust erosion during evaluation and setup friction.

4. **Medium: Documentation focus is misaligned to demo purpose**
- Evidence: README prioritizes running `src.main` rather than remora lifecycle.
- Risk: First-time evaluators may never exercise remora features.

5. **Medium: Validation artifacts are stale relative to current library evolution**
- Evidence: `DEMO_REPORT.md` includes statements likely tied to earlier behavior and naming.
- Risk: Incorrect assumptions during demos; harder to debug if behavior changed.

## 8. Prioritized Improvement Plan

### Priority 0 (must-fix before using this repo as canonical demo)

1. Align configuration to current remora-v2 schema
- Replace legacy keys with modern equivalents.
- Include explicit `query_search_paths` and `bundle_search_paths` with `@default` support.
- Add comments showing optional advanced toggles (`virtual_agents`, `search`).

2. Clean pyproject template leftovers
- Fix package target paths and pytest coverage target.
- Ensure metadata reflects this repo’s real package/module layout.

3. Rewrite README for demo-first workflow
- Provide exact commands for env setup, `remora discover`, `remora start`, and script-based verification.

### Priority 1 (expand to representative remora-v2 showcase)

4. Add one custom bundle and one simple `.pym` tool
- Demonstrate local bundle overlay plus externals usage.

5. Add one virtual agent role
- Example: test/review observer subscribed to `node_changed` for `src/**`.

6. Add proposal flow demo
- Include a script that triggers proposal creation and uses proposal endpoints.

7. Add search/index optional path
- Show `search.enabled`, `remora index`, and one `/api/search` request.

### Priority 2 (polish and long-term reliability)

8. Add automated demo verification
- A CI-friendly script/test that asserts non-empty nodes/events and successful chat.

9. Add LSP quickstart appendix
- Minimal instructions for `remora start --lsp` or standalone `remora lsp`.

10. Keep artifacts current
- Regenerate demo report outputs after major remora-v2 changes.

## 9. Recommended “Golden Demo” Flow

After the above fixes, this repo should support a 10-15 minute walkthrough:

1. Setup:
- `devenv shell -- uv sync --extra dev`

2. Validate discovery:
- `devenv shell -- remora discover --project-root .`

3. Start runtime:
- `devenv shell -- remora start --project-root . --log-events`

4. Verify API surface:
- Run `scripts/test_remora.sh` (expanded to include health + conversation + optional companion).

5. Demonstrate advanced behavior:
- Trigger a virtual-agent subscription path.
- Invoke a custom `.pym` tool.
- Show one proposal review accept/reject cycle.

6. Optional extended path:
- Run `remora index` and query `/api/search`.
- Show editor/LSP connection.

This flow would transform the repo from a smoke demo into a credible representation of remora-v2 architecture and workflow.

## 10. Evidence Index

### remora-test files reviewed
- `README.md`
- `remora.yaml`
- `pyproject.toml`
- `docs/architecture.md`
- `scripts/test_remora.sh`
- `scripts/reconcile_demo.sh`
- `DEMO_REPORT.md`
- `src/**/*.py`
- `configs/app.toml`

### remora-v2 files reviewed
- `README.md`
- `remora.yaml.example`
- `docs/architecture.md`
- `docs/user-guide.md`
- `docs/HOW_TO_USE_REMORA.md`
- `docs/externals-api.md`
- `docs/externals-contract.md`
- `src/remora/__main__.py`
- `src/remora/core/model/config.py`
- `src/remora/code/reconciler.py`
- `src/remora/code/directories.py`
- `src/remora/web/server.py`
- `src/remora/web/routes/*.py`
- `tests/unit/test_config.py`
- `tests/unit/test_refactor_naming.py`
