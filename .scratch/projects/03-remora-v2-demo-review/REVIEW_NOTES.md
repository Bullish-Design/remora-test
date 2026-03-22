# REVIEW NOTES

## remora-v2 capability baseline (from docs + source)

- CLI commands: `start`, `discover`, `index`, `lsp` (`src/remora/__main__.py`)
- Config keys: `query_search_paths`, `bundle_search_paths`, `bundle_overlays`, `workspace_root`, `virtual_agents`, `search` (`remora.yaml.example`, `src/remora/core/model/config.py`)
- Runtime model: discovery -> reconcile -> events -> actor turns -> tools (`docs/architecture.md`, `src/remora/code/reconciler.py`)
- Tool API: 28 externals via `TurnContext` contract v2 (`docs/externals-api.md`, `docs/externals-contract.md`)
- Web routes: `/api/nodes`, `/api/edges`, `/api/events`, `/api/chat`, `/api/health`, `/api/search`, `/api/proposals*`, `/sse` (`src/remora/web/routes/*.py`)
- Discovery supports `.py`, `.md`, `.toml` and query overrides (`README.md`, defaults)
- Virtual agent materialization exists (`src/remora/code/virtual_agents.py`)
- Edge materialization now present in reconcile and directory projection (`src/remora/code/reconciler.py`, `src/remora/code/directories.py`)

## remora-test demo evidence

- README is minimal and only shows app execution (`README.md`)
- `remora.yaml` uses legacy/incorrect keys for v2: `swarm_root`, `bundle_root`, `bundle_mapping` (`remora.yaml`)
- No `bundle_search_paths`/`query_search_paths`/`bundle_overlays` in demo config (`remora.yaml`)
- No local bundles, no queries, no virtual agents, no tests directories (`ls bundles/tests/queries`)
- Smoke script exercises only a narrow web/API path: nodes, edges, events, chat (`scripts/test_remora.sh`)
- Reconcile script is instructional text only (`scripts/reconcile_demo.sh`)
- Previous report (`DEMO_REPORT.md`) contains likely stale statement claiming `bundle_mapping` runtime compatibility
- Pyproject has template leftovers and likely broken packaging/test settings:
  - `packages = ["src/template_py"]` though no `src/template_py`
  - pytest coverage target `embeddify` does not exist

## capability coverage snapshot

- Demonstrated (partial): discovery + basic web API + chat trigger path
- Weak/partial: onboarding, reproducibility, observability guidance
- Missing as demo surface: virtual agents, bundle authoring, tool authoring, proposal workflow, search/index, LSP, companion APIs, multi-language discovery, robust tests

## key risks for demo credibility

1. Config drift can break startup or silently mislead users depending on remora-v2 version behavior.
2. Repository metadata (`pyproject.toml`) suggests template carryover rather than intentional demo curation.
3. Demo path is too narrow relative to remora-v2 feature set, so stakeholders may undervalue the library.
