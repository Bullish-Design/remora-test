# Remora v2 Demo Review

**Date:** 2026-03-18  
**Reviewer:** Analysis of remora-test as a demo for remora-v2  
**remora-v2 version:** 0.5.0  
**remora-test project:** Order processing microservice simulation

---

## Executive Summary

The remora-test repo is a **partially aligned** demo of remora-v2. While it successfully demonstrates basic discovery and runtime capabilities, several configuration mismatches and code structure issues reduce its effectiveness as a "real world usage" showcase.

**Overall Assessment:** ⚠️ Needs Updates

---

## 1. Configuration Alignment Analysis

### Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| Config schema mismatch | **High** | `remora.yaml` uses deprecated flat config keys (`bundle_root`, `bundle_mapping`, `swarm_root`) instead of nested structure (`behavior.bundle_search_paths`, `behavior.bundle_overlays`) |
| Missing `language_map` | **High** | Config specifies `discovery_languages: [python]` but lacks the required `language_map` for extension→language mapping |
| Incorrect `discovery_paths` | Medium | Uses `src` (no trailing slash) instead of `src/` convention shown in examples |

### Current remora-test config:
```yaml
discovery_paths:
  - src
discovery_languages:
  - python
swarm_root: .remora
bundle_root: /home/andrew/Documents/Projects/remora-v2/bundles
bundle_mapping: {...}
```

### Expected remora-v2 config structure:
```yaml
discovery_paths:
  - "src/"
language_map:
  ".py": "python"
bundle_search_paths:
  - "bundles/"
  - "@default"
bundle_overlays:  # Note: overlays, not mapping
  function: "code-agent"
  class: "code-agent"
  ...
workspace_root: ".remora"  # Note: workspace_root, not swarm_root
```

### Impact

The flat config keys (`bundle_mapping`, `swarm_root`, `bundle_root`) are **not recognized** by the current `Config` model in remora-v2. The `_nest_flat_config()` function in `config.py` only maps recognized field names. These custom keys would be silently ignored or cause validation errors depending on how strictly the config loader validates.

---

## 2. Code Structure Analysis

### What remora-test Does Well

✅ **Realistic domain modeling**: The e-commerce order processing domain (orders, discounts, tax, fraud, fulfillment) represents a plausible microservice structure that agents could reason about.

✅ **Hierarchical organization**: 
- `src/api/orders.py` - Entry point functions
- `src/services/` - Business logic modules
- `src/models/order.py` - Data models
- `src/utils/money.py` - Utility functions

✅ **Cross-module dependencies**: Functions call other modules (`create_order` calls `compute_total`, `discount_for_tier`, `apply_tax`), creating realistic agent relationships.

### What's Missing for Demo Purposes

❌ **No bundle customization**: The demo uses default bundles but doesn't show how to create custom agent behaviors via local `bundles/` directory.

❌ **No virtual agents configured**: The `virtual_agents` feature for declarative event subscriptions is not demonstrated.

❌ **No query customization**: No local `queries/` directory showing how to customize tree-sitter discovery.

❌ **No search enabled**: The semantic search feature (`search.enabled: true`) is not demonstrated.

❌ **No LSP integration**: The LSP adapter capability (`--lsp` flag) is not shown.

---

## 3. Feature Coverage Matrix

| Feature | remora-v2 Capability | Demo Coverage | Notes |
|---------|---------------------|---------------|-------|
| Discovery (`remora discover`) | ✅ Full | ✅ Tested | 18 nodes discovered |
| Runtime startup (`remora start`) | ✅ Full | ✅ Tested | Works with config fixes |
| Web API (`/api/nodes`, `/api/edges`) | ✅ Full | ✅ Tested | Returns data correctly |
| SSE streaming | ✅ Full | ✅ Tested | Replay works |
| Chat endpoint (`POST /api/chat`) | ✅ Full | ✅ Tested | Messages sent successfully |
| LLM integration | ✅ Full | ✅ Tested | Model endpoint reachable |
| Edge generation | ⚠️ Contains edges materialized | ❌ Empty | `edges` table not populated |
| LSP server | ✅ Full | ❌ Not demoed | `--lsp` flag not tested |
| Semantic search | ✅ Full | ❌ Not demoed | `search.enabled: false` |
| Virtual agents | ✅ Full | ❌ Not demoed | Not configured |
| Custom bundles | ✅ Full | ❌ Not demoed | Uses defaults only |
| File watching | ✅ Full | ⚠️ Partial | Implicit in runtime |
| Proposal approval flow | ✅ Full | ❌ Not demoed | `rewrite_self` not exercised |

---

## 4. Edge Materialization Issue

**Status:** Confirmed bug in edge generation

The `FileReconciler._reconcile_events()` method at line 272 calls:
```python
await self._node_store.add_edge(node.parent_id, node.node_id, "contains")
```

However, the previous DEMO_REPORT.md noted 0 edges. This suggests either:
1. The edge insertion path isn't being hit (nodes lack `parent_id`)
2. The `add_edge` method has a bug
3. Edge cleanup is removing them

**Investigation needed:** The demo code should verify edges are created. This is critical for the graph visualization to work.

---

## 5. pyproject.toml Alignment

### Current Issues

```toml
[tool.uv.sources]
remora = { git = "https://github.com/Bullish-Design/remora-v2.git", rev = "main" }
```

**Problems:**
1. Uses git remote instead of local path during development
2. Package name mismatch: project is `"remora"` but imports as `remora` (correct)
3. No dev dependencies for testing remora integration

### Recommended for dev/demo:

```toml
[tool.uv.sources]
remora = { path = "../remora-v2", editable = true }
```

---

## 6. Recommendations

### Priority 1: Fix Configuration

Update `remora.yaml` to match remora-v2 schema:

```yaml
project_path: "."
discovery_paths:
  - "src/"
language_map:
  ".py": "python"
bundle_search_paths:
  - "@default"
bundle_overlays:
  function: "code-agent"
  class: "code-agent"
  method: "code-agent"
  file: "code-agent"
  directory: "directory-agent"
model_base_url: "${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}"
model_default: "${REMORA_MODEL:-Qwen/Qwen3-4B-Instruct-2507-FP8}"
model_api_key: "${REMORA_MODEL_API_KEY:-}"
workspace_root: ".remora"
max_concurrency: 4
max_turns: 8
timeout_s: 300.0
```

### Priority 2: Add Demo Features

1. **Create local `bundles/` directory** with a custom bundle showing how to override agent behavior
2. **Create local `queries/` directory** with custom tree-sitter queries
3. **Enable semantic search** with local embeddy configuration
4. **Add virtual agent** example for cross-cutting concerns (e.g., logging agent)

### Priority 3: Demonstrate Agent Interactions

Create a `scripts/demo_chat.py` that:
1. Starts the runtime
2. Sends targeted chat messages to specific nodes
3. Demonstrates `query_agents` tool usage
4. Shows `rewrite_self` proposal flow
5. Displays companion data (reflections, links)

### Priority 4: Add LSP Demo

Document how to run:
```bash
remora start --lsp
# In another terminal:
remora lsp
```

---

## 7. Demo Quality Score

| Criterion | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Configuration correctness | 2/5 | 25% | 0.5 |
| Feature coverage | 3/5 | 30% | 0.9 |
| Real-world plausibility | 4/5 | 20% | 0.8 |
| Documentation | 2/5 | 15% | 0.3 |
| Runnable out-of-box | 3/5 | 10% | 0.3 |
| **Total** | | | **2.8/5** |

---

## 8. Files Reviewed

### remora-v2 (library)
- `src/remora/__init__.py` - Version 0.5.0
- `src/remora/__main__.py` - CLI commands
- `src/remora/core/model/config.py` - Configuration schema
- `src/remora/core/services/lifecycle.py` - Runtime lifecycle
- `src/remora/core/agents/actor.py` - Agent actor model
- `src/remora/code/discovery.py` - Tree-sitter discovery
- `src/remora/code/reconciler.py` - File reconciliation
- `src/remora/web/server.py` - Web API server
- `src/remora/web/routes/*.py` - API endpoints
- `src/remora/defaults/defaults.yaml` - Default configuration
- `src/remora/defaults/bundles/code-agent/bundle.yaml` - Default bundle

### remora-test (demo project)
- `remora.yaml` - Project configuration (misaligned)
- `pyproject.toml` - Package configuration
- `src/main.py` - Entry point
- `src/api/orders.py` - Order creation endpoint
- `src/models/order.py` - Data models
- `src/services/*.py` - Business logic modules
- `DEMO_REPORT.md` - Previous demo findings

---

## 9. Conclusion

The remora-test repo demonstrates **basic remora-v2 functionality** but falls short of being a comprehensive demo. The primary issues are:

1. **Configuration drift** from library schema changes
2. **Missing advanced features** (search, LSP, virtual agents, custom bundles)
3. **Edge generation bug** affecting graph visualization
4. **Insufficient documentation** for demo usage

With the recommended fixes, remora-test could serve as an effective "real world usage" demonstration of remora-v2's agent substrate capabilities.

---

## Appendix: Quick Start Validation Commands

```bash
# Install dependencies
devenv shell -- uv sync --extra dev

# Validate configuration
remora discover --project-root .

# Run bounded demo
remora start --project-root . --port 8080 --run-seconds 30 --log-events

# Test endpoints
curl http://localhost:8080/api/nodes
curl http://localhost:8080/api/edges
curl http://localhost:8080/sse?replay=5&once=true
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"node_id":"src/api/orders.py::create_order","message":"What do you do?"}'
```
