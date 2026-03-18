# Remora v2 Demo Repository Review

**Date:** 2026-03-18  
**Reviewer:** Code Review  
**Repository:** `/home/andrew/Documents/Projects/remora-test`  
**Target Library:** `/home/andrew/Documents/Projects/remora-v2`  

---

## Executive Summary

The remora-test repository serves as a basic demonstration environment for remora-v2, but has **significant gaps** that limit its ability to "show off" the library's full capabilities. While the core runtime functionality works (as evidenced by DEMO_REPORT.md), the demo project itself lacks the depth needed to showcase remora-v2's agent-driven code analysis features.

**Overall Assessment:** ⚠️ **PARTIAL ALIGNMENT** - Functional but incomplete demonstration

---

## 1. Remora-v2 Capabilities Overview

Based on codebase analysis of remora-v2, the library provides:

### Core Capabilities
- **Multi-language Tree-sitter Discovery**: Parses `.py`, `.md`, `.toml` files using tree-sitter queries
- **Agent-per-Node Architecture**: Each discovered code element becomes an autonomous agent
- **Event-Driven Runtime**: Agents respond to code changes via events (NodeChangedEvent, NodeDiscoveredEvent)
- **Bundle System**: Configurable agent behavior per node type (function, class, method, directory)
- **Web Interface**: SSE streaming + REST API for graph exploration
- **LSP Integration**: Code lens, hover, save/open event forwarding
- **Typer CLI**: Commands - `remora start`, `remora discover`, `remora index`, `remora lsp`
- **Incremental Reconciliation**: Continuous file watching with add/change/delete sync
- **Semantic Search**: Optional embeddy integration for code search

### Key Tools Available to Agents
- `send_message`: Communicate with other agents or user
- `query_agents`: Search graph for related elements
- `rewrite_self`: Propose source rewrites
- `reflect`: Write notes to workspace
- `kv_get/kv_set`: Persistent memory
- `subscribe/unsubscribe`: Event subscription management

---

## 2. Configuration Alignment Analysis

### Current remora-test Config (remora.yaml)

```yaml
# Current (remora-test)
discovery_paths:
  - src

discovery_languages:
  - python

swarm_root: .remora
bundle_root: /home/andrew/Documents/Projects/remora-v2/bundles

bundle_mapping:           # ❌ DEPRECATED KEY
  function: code-agent
  class: code-agent
  method: code-agent
  file: code-agent
  directory: directory-agent

# ... infra settings
```

### Correct v2 Config Structure (remora.yaml.example)

```yaml
# Recommended (aligned with v2)
project_path: "."
discovery_paths:
  - "src/"

language_map:            # ✅ Use this instead
  ".py": "python"
  ".md": "markdown"
  ".toml": "toml"

query_search_paths:
  - "queries/"
  - "@default"

bundle_search_paths:
  - "bundles/"
  - "@default"

bundle_overlays:         # ✅ Use this instead of bundle_mapping
  function: "code-agent"
  class: "code-agent"
  method: "code-agent"
  file: "code-agent"
  directory: "directory-agent"

# Optional: Virtual agents for testing
virtual_agents:
  - id: "test-agent"
    role: "test-agent"
    subscriptions:
      - event_types: ["NodeChangedEvent", "NodeDiscoveredEvent"]
        path_glob: "tests/**"

workspace_root: ".remora"
workspace_ignore_patterns:
  - ".git"
  - ".venv"
  - "__pycache__"
```

### Configuration Issues Found

| Issue | Severity | Current State | Required Action |
|-------|----------|---------------|---------------|
| `bundle_mapping` deprecated | 🔴 **HIGH** | Using old key | Rename to `bundle_overlays` |
| Missing `project_path` | 🟡 **MEDIUM** | Not specified | Add `project_path: "."` |
| Missing `language_map` | 🟡 **MEDIUM** | Using `discovery_languages` | Add proper extension mapping |
| Hardcoded `bundle_root` | 🟡 **MEDIUM** | Absolute path | Use relative or `@default` |
| Missing virtual agents | 🟢 **LOW** | None configured | Consider adding for demo |

---

## 3. Code Structure Analysis

### Current Demo Code (src/)

```
src/
├── main.py                    # Simple entry point
├── api/
│   └── orders.py             # Business logic entry
├── models/
│   └── order.py              # Dataclasses
├── services/
│   ├── pricing.py            # Simple math
│   ├── discounts.py          # Tier discount logic
│   ├── tax.py                # Tax calculation
│   ├── fraud.py              # Risk scoring
│   ├── fulfillment/
│   │   └── allocator.py      # Warehouse allocation
│   └── ...
└── utils/
    └── money.py              # Formatting utility
```

### Demo Code Characteristics

**Strengths:**
- Clean separation of concerns
- Simple, understandable business logic
- Realistic e-commerce domain
- Type hints on dataclasses

**Weaknesses:**
- ❌ **Too simple** - functions are trivial (3-8 lines each)
- ❌ **No classes** - remora-v2 discovers classes/methods, but demo has none
- ❌ **Static code** - no inheritance, decorators, generics, or complex patterns
- ❌ **No inter-service communication** - services don't call each other
- ❌ **No docstrings** - agents lack context for meaningful responses
- ❌ **Single file type** - only `.py` files, no markdown configs or toml

### Agent Discovery Results (from DEMO_REPORT.md)

```
- Nodes discovered: 18
- Edges reported: 0 (known issue)
- Events collected: 30
```

**Analysis:** 18 nodes is minimal. A proper demo should have:
- 50+ nodes to showcase graph navigation
- Multiple classes with methods
- Cross-references between services
- Configuration files (markdown, toml)
- Documentation that agents can reference

---

## 4. Missing Demonstration Features

### Features NOT Showcased

| Feature | Status | Impact |
|---------|--------|--------|
| **Multi-language discovery** | ❌ Missing | No `.md` or `.toml` files in demo |
| **Class/Method agents** | ❌ Missing | Demo has only functions |
| **Agent-to-agent messaging** | ⚠️ Partial | Services don't call each other |
| **Code rewrite proposals** | ❌ Missing | No demonstrated workflow |
| **Query customization** | ❌ Missing | No `queries/` directory |
| **Bundle customization** | ❌ Missing | Uses default bundles only |
| **Virtual agents** | ❌ Missing | No declarative agents |
| **Event subscription** | ⚠️ Partial | Not explicitly demonstrated |
| **LSP integration** | ❌ Missing | Not mentioned in docs |
| **Search/indexing** | ❌ Missing | No `remora index` demonstration |
| **Web UI interaction** | ⚠️ Partial | API tested but no UI walkthrough |
| **Self-reflection** | ⚠️ Partial | Enabled but not demonstrated |
| **Companion observer** | ❌ Missing | Not enabled |

### What This Means

A visitor to this demo would miss understanding:
- How agents collaborate across service boundaries
- How remora handles object-oriented code
- The full power of the graph visualization
- The proposal/approval workflow
- The self-reflection capability

---

## 5. PyProject.toml Alignment

### Current Dependencies

```toml
dependencies = [
    "pydantic>=2.12.5",
    "remora"
]
```

### Required Improvements

```toml
dependencies = [
    "pydantic>=2.12.5",
    "remora[all-languages]",  # ✅ Include markdown, toml support
]

[project.optional-dependencies]
dev = [
    "remora[lsp]",           # ✅ Optional LSP support
    "remora[search]",        # ✅ Optional search support
    # ... existing dev deps
]
```

**Note:** Demo explicitly references remora-v2 via git in `[tool.uv.sources]`, which is correct for tracking the refactored version.

---

## 6. Documentation Gaps

### README.md Issues

**Current:**
```markdown
# remora-test

Sample project used to demonstrate `remora-v2` in realistic usage.

Run app:
```bash
python -m src.main
```
```

**Problems:**
1. ❌ No instructions for running with remora
2. ❌ No explanation of what agents do
3. ❌ No architecture overview
4. ❌ No link to remora-v2 documentation

### Missing Documentation

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Explain discovered agents and their roles |
| `DEMO_SCRIPT.md` | Step-by-step demo walkthrough |
| `ARCHITECTURE.md` | How the demo code is structured |
| `TROUBLESHOOTING.md` | Common issues (like edges=0) |

---

## 7. Strengths of Current Demo

1. **Basic runtime works** - Can start and discover nodes
2. **Realistic domain** - E-commerce order processing is relatable
3. **Clean code structure** - Easy to understand
4. **DEMO_REPORT.md** - Good artifact showing runtime testing
5. **Proper tooling** - Uses devenv, uv, modern Python packaging

---

## 8. Recommendations

### Immediate Fixes (High Priority)

1. **Fix configuration keys**
   - Rename `bundle_mapping` → `bundle_overlays`
   - Add `project_path: "."`
   - Add `language_map` with extension mappings

2. **Add complexity to demo code**
   - Create 3-5 classes with methods
   - Add service-to-service calls
   - Add docstrings explaining "why" not just "what"

3. **Expand README.md**
   - Add remora quickstart instructions
   - Document the agent architecture
   - Link to remora-v2 docs

### Medium Priority

4. **Add multi-language files**
   - `README.md` (already exists - ensure it's discovered)
   - `pyproject.toml` documentation
   - Config files for demonstration

5. **Create demo scenarios**
   - "Ask the pricing agent about discounts"
   - "Watch the order service react to tax changes"
   - "Propose a code change via agent"

6. **Add query customization**
   - Create `queries/python.scm` with custom tree-sitter rules
   - Demonstrate how to extract specific patterns

### Long Term (Nice to Have)

7. **Add LSP demonstration**
   - Document `remora start --lsp`
   - Show IDE integration

8. **Add search demonstration**
   - Run `remora index`
   - Show semantic code search

9. **Create interactive tutorial**
   - Jupyter notebook or guided script
   - Step through agent capabilities

---

## 9. Alignment Score

| Category | Score | Notes |
|----------|-------|-------|
| **Configuration** | 6/10 | Works but uses deprecated keys |
| **Code Structure** | 5/10 | Too simple, no classes |
| **Feature Coverage** | 4/10 | Many features not demonstrated |
| **Documentation** | 3/10 | Minimal guidance |
| **Realism** | 7/10 | Good domain, but shallow |
| **Overall** | **5/10** | Functional but not compelling |

---

## 10. Quick Wins

To quickly improve the demo without major refactoring:

1. ✅ Fix `remora.yaml` configuration keys (5 minutes)
2. ✅ Add docstrings to all functions (10 minutes)
3. ✅ Add one class with 2-3 methods (10 minutes)
4. ✅ Expand README with remora commands (15 minutes)
5. ✅ Add a `docs/` markdown file to show multi-language discovery (5 minutes)

**Total time: ~45 minutes for significant improvement**

---

## Conclusion

The remora-test repository is a **working but minimal** demonstration of remora-v2. It validates that the library can start and discover nodes, but fails to showcase the library's differentiating features: agent autonomy, code intelligence, and multi-language support.

**Recommendation:** Keep the current simple structure as a "hello world" example, but create additional numbered template directories (02-intermediate, 03-advanced) that demonstrate progressively more sophisticated use cases.

---

*Generated for project template directory: `/home/andrew/Documents/Projects/remora-test/01-project-template/`*
