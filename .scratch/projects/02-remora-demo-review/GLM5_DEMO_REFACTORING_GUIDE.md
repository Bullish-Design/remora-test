# Remora v2 Demo Refactoring Guide

**Purpose:** Transform remora-test into a showcase demo that delivers the "wow factor" for remora-v2's capabilities.  
**Audience:** Developers refactoring the demo for presentation-quality output.  
**Scope:** Configuration, code structure, demo scripts, and documentation.

---

## Overview

The refactoring aims to transform remora-test from a basic smoke-test project into a **compelling demonstration** that:

1. **Showcases every major remora-v2 feature** in an accessible way
2. **Runs reliably out-of-the-box** with correct configuration
3. **Provides visual and interactive "wow moments"** (graph visualization, live agent chat, code proposals)
4. **Demonstrates real-world applicability** through meaningful code structure

### Target Demo Experience

```
User runs: remora start
     ↓
Browser opens: http://localhost:8080
     ↓
Graph visualization shows 20+ nodes with containment edges
     ↓
User clicks a node → sees source code + agent panel
     ↓
User chats: "What does this function do?"
     ↓
Agent responds intelligently using query_agents tool
     ↓
User requests: "Add input validation"
     ↓
Agent proposes code change → User reviews diff → Accepts
     ↓
File watcher detects change → Agents react
     ↓
Companion panel shows reflections and links
```

---

## Phase 1: Configuration Alignment

### Step 1.1: Fix remora.yaml Schema

**Current Issue:** Config uses deprecated flat keys that don't match `Config` model.

**File:** `remora.yaml`

**Replace entire file with:**

```yaml
# Remora v2 Demo Configuration
# Aligned with remora v0.5.0 config schema

project:
  project_path: "."
  discovery_paths:
    - "src/"
  workspace_ignore_patterns:
    - ".git"
    - ".venv"
    - "__pycache__"
    - ".remora"

behavior:
  language_map:
    ".py": "python"
  bundle_search_paths:
    - "bundles/"
    - "@default"
  bundle_overlays:
    function: "code-agent"
    class: "code-agent"
    method: "code-agent"
    file: "code-agent"
    directory: "directory-agent"
  query_search_paths:
    - "queries/"
    - "@default"

infra:
  model_base_url: "${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}"
  model_api_key: "${REMORA_MODEL_API_KEY:-}"
  workspace_root: ".remora"
  timeout_s: 300.0

runtime:
  max_concurrency: 4
  max_trigger_depth: 5
  trigger_cooldown_ms: 1000
  max_turns: 8

# Enable semantic search for "wow" semantic code queries
search:
  enabled: true
  mode: "remote"
  embeddy_url: "${EMBEDDY_URL:-http://localhost:8585}"
  timeout: 30.0
  default_collection: "demo-code"
  collection_map:
    ".py": "demo-code"

# Virtual agent: observes all agent activity for demo insights
virtual_agents:
  - id: "demo-observer"
    role: "companion"
    subscriptions:
      - event_types: ["TurnDigestedEvent"]
  - id: "test-observer"
    role: "test-agent"
    subscriptions:
      - event_types: ["NodeChangedEvent", "NodeDiscoveredEvent"]
        path_glob: "src/**"
```

### Step 1.2: Create Local Bundle Override

**Purpose:** Show how to customize agent behavior without modifying library defaults.

**Create:** `bundles/demo-agent/bundle.yaml`

```yaml
name: demo-agent
externals_version: 1

system_prompt_extension: |
  You are a demo agent for the remora-v2 showcase.
  
  ## Your Mission
  Demonstrate the power of autonomous code agents by:
  1. Answering questions about your code clearly and concisely
  2. Proposing thoughtful improvements when asked
  3. Using query_agents to find related code elements
  4. Recording insights via companion tools
  
  ## Demo Behavior
  - Respond in first person as the code element
  - Keep responses under 4 sentences unless explaining complex logic
  - Always use send_message to reply to users
  - Proactively check query_agents for context before answering

prompts:
  chat: |
    A user wants to understand or modify your code.
    Read their message carefully and respond helpfully.
    Use query_agents if you need context about callers or dependencies.
    Reply via send_message to "user".
  reactive: |
    Your source code changed. Reflect on the modification and update
    your understanding using the reflect tool.

max_turns: 6

self_reflect:
  enabled: true
  model: "Qwen/Qwen3-1.7B"
  max_turns: 2
  prompt: |
    Reflect on this conversation turn.
    Use companion_summarize and companion_reflect to record insights.
    Tag vocabulary: demo, explanation, refactor, insight, question
```

### Step 1.3: Create Custom Tree-Sitter Queries

**Purpose:** Demonstrate query customization for domain-specific discovery.

**Create:** `queries/python.scm`

```scheme
; Standard Python discovery
(function_definition
  name: (identifier) @node.name) @node

(class_definition
  name: (identifier) @node.name) @node

(decorated_definition
  definition: (function_definition
    name: (identifier) @node.name)) @node

; Demo-specific: capture docstrings for context
(function_definition
  body: (block
    (expression_statement
      (string) @node.docstring))?)
  name: (identifier) @node.name) @node

; Demo-specific: capture type hints for richer context
(function_definition
  parameters: (parameters
    (typed_parameter
      name: (identifier) @node.param
      type: (type) @node.param_type))?)
  name: (identifier) @node.name) @node
```

---

## Phase 2: Code Structure Enhancement

### Step 2.1: Add Demo-Worthy Code Patterns

**Purpose:** Make the code structure interesting for agent exploration.

**File:** `src/services/analytics.py` (NEW)

```python
"""Analytics service demonstrating cross-module relationships."""


def calculate_metrics(orders: list[dict]) -> dict:
    """Calculate aggregate metrics from order data.
    
    Called by: src/api/orders.py::get_analytics
    Depends on: src/services/pricing.py::compute_total
    """
    if not orders:
        return {"total_orders": 0, "average_value": 0.0}
    
    total_value = sum(o.get("total", 0) for o in orders)
    return {
        "total_orders": len(orders),
        "average_value": total_value / len(orders),
        "total_revenue": total_value,
    }


def segment_customers(orders: list[dict]) -> dict[str, list]:
    """Segment customers by order frequency and value.
    
    This function demonstrates:
    - Complex business logic agents can reason about
    - Multiple return paths and data transformations
    - Cross-cutting concerns (called by multiple endpoints)
    """
    tiers = {"gold": [], "silver": [], "bronze": []}
    
    for order in orders:
        user_id = order.get("user_id")
        order_count = order.get("order_count", 0)
        total_spent = order.get("total_spent", 0)
        
        if order_count >= 10 or total_spent >= 1000:
            tiers["gold"].append(user_id)
        elif order_count >= 5 or total_spent >= 500:
            tiers["silver"].append(user_id)
        else:
            tiers["bronze"].append(user_id)
    
    return tiers
```

**File:** `src/api/orders.py` (ENHANCED)

```python
"""Order API endpoints demonstrating agent-calling patterns."""

from src.models.order import OrderRequest, OrderSummary
from src.services.discounts import discount_for_tier
from src.services.pricing import compute_total
from src.services.tax import apply_tax
from src.services.fraud import risk_score
from src.services.analytics import calculate_metrics


def create_order(request: OrderRequest) -> OrderSummary:
    """Create an order summary with tier discount and tax.
    
    Flow:
    1. Compute subtotal via pricing.compute_total
    2. Apply tier discount via discounts.discount_for_tier
    3. Apply tax via tax.apply_tax
    
    Agents can query this function to understand the order pipeline.
    """
    subtotal = compute_total(request.item_prices)
    discount = discount_for_tier(request.user_tier, subtotal)
    taxed_total = apply_tax(subtotal - discount, request.tax_rate)
    
    return OrderSummary(
        subtotal=subtotal,
        discount=discount,
        total=round(taxed_total, 2),
    )


def validate_order(request: OrderRequest) -> tuple[bool, str]:
    """Validate an order request for fraud and errors.
    
    Uses fraud.risk_score to assess risk.
    Called before create_order in production flow.
    """
    subtotal = compute_total(request.item_prices)
    risk = risk_score(subtotal, request.user_tier)
    
    if risk > 0.8:
        return False, "Order flagged for review: high risk score"
    if not request.item_prices:
        return False, "Order must contain at least one item"
    if subtotal > 10000:
        return False, "Order exceeds maximum value, please contact support"
    
    return True, ""


def get_analytics(orders: list[dict]) -> dict:
    """Get analytics for a list of processed orders.
    
    Delegates to analytics.calculate_metrics.
    Demonstrates cross-module agent relationships.
    """
    return calculate_metrics(orders)
```

### Step 2.2: Add Test Coverage (for demo credibility)

**File:** `tests/test_orders.py` (NEW)

```python
"""Tests demonstrating the order processing pipeline."""

import pytest
from src.api.orders import create_order, validate_order
from src.models.order import OrderRequest


def test_create_order_basic():
    """Basic order creation with default tax."""
    request = OrderRequest(user_tier="standard", item_prices=[10.0, 20.0])
    summary = create_order(request)
    
    assert summary.subtotal == 30.0
    assert summary.discount == 0.0
    assert summary.total == pytest.approx(32.1, rel=0.01)


def test_create_order_gold_tier():
    """Gold tier gets 15% discount."""
    request = OrderRequest(user_tier="gold", item_prices=[100.0])
    summary = create_order(request)
    
    assert summary.subtotal == 100.0
    assert summary.discount == 15.0  # 15% of 100


def test_validate_order_high_risk():
    """High-value orders should be flagged."""
    request = OrderRequest(user_tier="bronze", item_prices=[500.0] * 25)
    valid, message = validate_order(request)
    
    assert not valid
    assert "risk" in message.lower()


def test_validate_order_empty():
    """Empty orders should be rejected."""
    request = OrderRequest(user_tier="gold", item_prices=[])
    valid, message = validate_order(request)
    
    assert not valid
    assert "at least one item" in message
```

---

## Phase 3: Demo Scripts & Tooling

### Step 3.1: Create Interactive Demo Script

**File:** `scripts/demo_interactive.py` (NEW)

```python
#!/usr/bin/env python3
"""
Interactive demo script for remora-v2 showcase.

Usage:
    python scripts/demo_interactive.py
    
Requires:
    - remora start running on localhost:8080
    - Model endpoint accessible
"""

import asyncio
import json
import time
from urllib.request import Request, urlopen


BASE_URL = "http://localhost:8080"


def api_get(path: str) -> dict | list:
    """GET from API endpoint."""
    with urlopen(f"{BASE_URL}{path}") as resp:
        return json.loads(resp.read().decode())


def api_post(path: str, data: dict) -> dict:
    """POST to API endpoint."""
    req = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


def wait_for_runtime(timeout: float = 30.0) -> bool:
    """Poll until runtime is ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            nodes = api_get("/api/nodes")
            if len(nodes) > 0:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def demo_discovery():
    """Show discovered nodes."""
    print("\n" + "=" * 60)
    print("DISCOVERY DEMO")
    print("=" * 60)
    
    nodes = api_get("/api/nodes")
    print(f"\nDiscovered {len(nodes)} nodes:\n")
    
    # Group by file
    by_file = {}
    for node in nodes:
        file = node.get("file_path", "unknown")
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(node)
    
    for file, file_nodes in sorted(by_file.items()):
        print(f"  {file}")
        for node in file_nodes:
            status = node.get("status", "unknown")
            node_type = node.get("node_type", "unknown")
            name = node.get("name", "unknown")
            print(f"    [{status:8}] {node_type:8} {name}")
    
    return nodes


def demo_edges():
    """Show containment edges."""
    print("\n" + "=" * 60)
    print("EDGE DEMO")
    print("=" * 60)
    
    edges = api_get("/api/edges")
    print(f"\nFound {len(edges)} edges:\n")
    
    for edge in edges[:10]:  # Show first 10
        from_name = edge["from_id"].split("::")[-1]
        to_name = edge["to_id"].split("::")[-1]
        print(f"  {from_name} --[{edge['edge_type']}]--> {to_name}")
    
    if len(edges) > 10:
        print(f"  ... and {len(edges) - 10} more")


def demo_chat(node_id: str, message: str) -> None:
    """Send chat message and show result."""
    print("\n" + "=" * 60)
    print("CHAT DEMO")
    print("=" * 60)
    
    print(f"\nSending to: {node_id}")
    print(f"Message: {message}\n")
    
    result = api_post("/api/chat", {"node_id": node_id, "message": message})
    print(f"Status: {result.get('status', 'unknown')}")
    
    print("\nWait a few seconds for agent response...")
    time.sleep(5)
    
    # Get conversation
    try:
        conv = api_get(f"/api/nodes/{node_id.replace('/', '%2F')}/conversation")
        history = conv.get("history", [])
        print(f"\nConversation history ({len(history)} messages):")
        for msg in history[-4:]:  # Show last 4
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            print(f"  [{role}] {content}...")
    except Exception as e:
        print(f"(Could not fetch conversation: {e})")


def demo_companion(node_id: str) -> None:
    """Show companion data for a node."""
    print("\n" + "=" * 60)
    print("COMPANION DEMO")
    print("=" * 60)
    
    try:
        companion = api_get(f"/api/nodes/{node_id.replace('/', '%2F')}/companion")
        print(f"\nCompanion data for {node_id}:\n")
        
        for key, value in companion.items():
            print(f"  {key}:")
            if isinstance(value, list):
                for item in value[:3]:
                    print(f"    - {item}")
            else:
                print(f"    {value}")
    except Exception as e:
        print(f"(Could not fetch companion data: {e})")


def main():
    print("\n" + "=" * 60)
    print("REMORA V2 INTERACTIVE DEMO")
    print("=" * 60)
    
    # Wait for runtime
    print("\nWaiting for runtime...")
    if not wait_for_runtime():
        print("ERROR: Runtime not responding. Run 'remora start' first.")
        return
    
    print("Runtime ready!")
    
    # Discovery
    nodes = demo_discovery()
    
    # Edges
    demo_edges()
    
    # Find a good node for chat
    target_node = None
    for node in nodes:
        if "create_order" in node.get("name", ""):
            target_node = node["node_id"]
            break
    
    if not target_node and nodes:
        target_node = nodes[0]["node_id"]
    
    if target_node:
        # Chat demo
        demo_chat(target_node, "What do you do? Explain in one sentence.")
        
        # Companion demo
        demo_companion(target_node)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nOpen http://localhost:8080 in your browser for the full experience!")
    print("Try chatting with different nodes using the Agent Panel.\n")


if __name__ == "__main__":
    main()
```

### Step 3.2: Create Quick-Start Script

**File:** `scripts/demo_quickstart.sh` (NEW)

```bash
#!/bin/bash
# Quick-start demo script for remora-v2

set -e

echo "=================================================="
echo "REMORA V2 DEMO QUICK START"
echo "=================================================="

# Check for remora
if ! command -v remora &> /dev/null; then
    echo "ERROR: remora not found. Install with: uv pip install remora"
    exit 1
fi

# Check for model endpoint
echo ""
echo "Checking model endpoint..."
if curl -s http://remora-server:8000/v1/models > /dev/null 2>&1; then
    echo "✓ Model endpoint reachable"
else
    echo "⚠ Model endpoint not reachable at http://remora-server:8000"
    echo "  Set REMORA_MODEL_BASE_URL to override"
fi

# Discovery
echo ""
echo "Running discovery..."
remora discover --project-root .

# Start runtime
echo ""
echo "Starting remora runtime..."
echo "Open http://localhost:8080 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

remora start --project-root . --port 8080 --log-level INFO --log-events
```

### Step 3.3: Create LSP Demo Instructions

**File:** `docs/LSP_DEMO.md` (NEW)

```markdown
# LSP Integration Demo

The LSP (Language Server Protocol) integration allows editors to interact with remora agents.

## Starting the LSP Server

### Option 1: Combined Runtime + LSP

```bash
remora start --lsp
```

This starts both the web server and LSP server.

### Option 2: Standalone LSP

```bash
# Terminal 1: Start runtime
remora start

# Terminal 2: Start LSP
remora lsp
```

## Editor Configuration

### Neovim (nvim-lspconfig)

```lua
lspconfig.remora.setup {
  cmd = {"remora", "lsp"},
  filetypes = {"python"},
  root_dir = lspconfig.util.root_pattern("remora.yaml"),
}
```

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "languageserver": {
    "remora": {
      "command": "remora",
      "args": ["lsp"],
      "filetypes": ["python"],
      "rootPatterns": ["remora.yaml"]
    }
  }
}
```

## LSP Features

- **Code Lenses:** See agent status above functions
- **Hover:** View agent context and reflections
- **Save/Open Events:** Trigger agent reconciliation
```

---

## Phase 4: Documentation & Polish

### Step 4.1: Create Comprehensive README

**File:** `README.md` (REPLACE)

```markdown
# Remora v2 Demo

A showcase demonstration of [remora-v2](https://github.com/Bullish-Design/remora-v2), the reactive agent substrate for autonomous code agents.

## What This Demo Shows

- **Code Discovery:** Tree-sitter based parsing of Python code into agent nodes
- **Agent Chat:** Direct messaging with code element agents
- **Graph Visualization:** Interactive node graph with Sigma.js
- **Proposal Flow:** Agent-initiated code changes with human approval
- **File Watching:** Real-time reconciliation on file changes
- **Companion System:** Reflection and insight tracking
- **Virtual Agents:** Declarative event-driven agents
- **Semantic Search:** Code similarity via embeddings

## Quick Start

```bash
# Install dependencies
uv sync

# Run discovery
remora discover --project-root .

# Start runtime
remora start --project-root . --port 8080

# Open browser
open http://localhost:8080
```

## Demo Scenarios

### 1. Basic Chat

1. Click on `create_order` node in the graph
2. In the Agent Panel, type: "What does this function do?"
3. Watch the agent respond in the panel

### 2. Code Proposal

1. Select a node and type: "Add input validation"
2. Agent proposes a change
3. Click "View Diff" to see the proposal
4. Click "Accept" or "Reject"

### 3. File Watch

1. Edit `src/services/discounts.py` in your editor
2. Watch the graph update in real-time
3. Check the timeline for `node_changed` events

### 4. Semantic Search

1. In the API, search for similar code:
   ```bash
   curl "http://localhost:8080/api/search?q=discount+calculation"
   ```

## Project Structure

```
remora-test/
├── remora.yaml           # Runtime configuration
├── bundles/              # Custom agent bundles (NEW)
│   └── demo-agent/
│       └── bundle.yaml
├── queries/              # Custom tree-sitter queries (NEW)
│   └── python.scm
├── src/
│   ├── api/              # API endpoints
│   │   └── orders.py     # Order processing functions
│   ├── models/           # Data models
│   │   └── order.py
│   ├── services/         # Business logic
│   │   ├── pricing.py    # Price calculations
│   │   ├── discounts.py  # Tier discount logic
│   │   ├── tax.py        # Tax calculations
│   │   ├── fraud.py      # Risk scoring
│   │   └── analytics.py  # Metrics (NEW)
│   └── utils/
│       └── money.py      # Currency utilities
├── tests/                # Test coverage (NEW)
│   └── test_orders.py
└── scripts/              # Demo scripts (NEW)
    ├── demo_interactive.py
    └── demo_quickstart.sh
```

## Configuration

See `remora.yaml` for all configuration options. Key settings:

| Setting | Purpose |
|---------|---------|
| `discovery_paths` | Directories to scan for nodes |
| `bundle_overlays` | Map node types to agent bundles |
| `virtual_agents` | Declarative event-driven agents |
| `search.enabled` | Enable semantic search |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/nodes` | List all discovered nodes |
| `GET /api/edges` | List containment edges |
| `GET /api/nodes/{id}` | Get node details |
| `GET /api/nodes/{id}/companion` | Get companion reflections |
| `POST /api/chat` | Send message to agent |
| `GET /sse` | Server-sent events stream |
| `GET /api/search?q=...` | Semantic code search |

## Development

```bash
# Run tests
pytest tests/

# Type check
pyright src/

# Format
ruff format .

# Lint
ruff check .
```

## License

MIT
```

### Step 4.2: Update pyproject.toml

**File:** `pyproject.toml` (UPDATE)

```toml
[project]
name = "remora-demo"
version = "0.2.0"
description = "Showcase demo for remora-v2 autonomous code agents"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "Bullish Design", email = "BullishDesignEngineering@gmail.com" },
]

dependencies = [
    "pydantic>=2.12.5",
    "remora",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.9.0",
    "pyright>=1.1.0",
]

[tool.uv.sources]
remora = { path = "../remora-v2", editable = true }

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
addopts = "-q --cov=src --cov-report=term-missing"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py313"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pyright]
typeCheckingMode = "basic"
include = ["src", "tests"]
```

---

## Phase 5: Testing & Validation

### Step 5.1: Create Validation Script

**File:** `scripts/validate_demo.py` (NEW)

```python
#!/usr/bin/env python3
"""Validate demo is properly configured."""

import json
import subprocess
import sys
from pathlib import Path


def check_file(path: str, required: bool = True) -> bool:
    """Check if file exists."""
    p = Path(path)
    if p.exists():
        print(f"  ✓ {path}")
        return True
    else:
        status = "✗" if required else "?"
        print(f"  {status} {path} (missing)")
        return not required


def check_config_keys() -> bool:
    """Check remora.yaml has correct keys."""
    import yaml
    
    with open("remora.yaml") as f:
        config = yaml.safe_load(f)
    
    required_keys = [
        ("behavior", "bundle_overlays"),
        ("behavior", "language_map"),
        ("infra", "workspace_root"),
        ("runtime", "max_concurrency"),
    ]
    
    all_ok = True
    for *path, key in required_keys:
        d = config
        for p in path:
            d = d.get(p, {})
        if key in d:
            print(f"  ✓ {'. '.join(path)}.{key}")
        else:
            print(f"  ✗ {'. '.join(path)}.{key} (missing)")
            all_ok = False
    
    # Check for deprecated keys
    deprecated = ["bundle_mapping", "swarm_root", "bundle_root", "discovery_languages"]
    for key in deprecated:
        if key in config:
            print(f"  ⚠ {key} is deprecated, remove it")
            all_ok = False
    
    return all_ok


def check_nodes_discovered() -> bool:
    """Run discovery and check nodes."""
    result = subprocess.run(
        ["remora", "discover", "--project-root", "."],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"  ✗ Discovery failed: {result.stderr}")
        return False
    
    lines = result.stdout.strip().split("\n")
    if lines and "nodes" in lines[0]:
        count = lines[0].split()[1]
        print(f"  ✓ Discovered {count} nodes")
        return int(count) > 0
    
    return False


def main():
    print("=" * 60)
    print("REMORA DEMO VALIDATION")
    print("=" * 60)
    
    all_ok = True
    
    print("\nChecking files...")
    all_ok &= check_file("remora.yaml")
    all_ok &= check_file("src/api/orders.py")
    all_ok &= check_file("src/models/order.py")
    all_ok &= check_file("src/services/pricing.py")
    all_ok &= check_file("bundles/demo-agent/bundle.yaml", required=False)
    all_ok &= check_file("queries/python.scm", required=False)
    
    print("\nChecking configuration...")
    all_ok &= check_config_keys()
    
    print("\nChecking discovery...")
    all_ok &= check_nodes_discovered()
    
    print("\n" + "=" * 60)
    if all_ok:
        print("VALIDATION PASSED ✓")
        print("=" * 60)
        return 0
    else:
        print("VALIDATION FAILED ✗")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 5.2: Final Checklist

Run through this checklist before demo:

```markdown
## Pre-Demo Checklist

### Configuration
- [ ] `remora.yaml` uses nested config structure
- [ ] No deprecated keys (`bundle_mapping`, `swarm_root`)
- [ ] `language_map` has `.py: python` entry
- [ ] Model endpoint is reachable

### Code
- [ ] All Python files parse without errors
- [ ] Tests pass: `pytest tests/`
- [ ] No type errors: `pyright src/`

### Discovery
- [ ] `remora discover` finds 15+ nodes
- [ ] Nodes include functions, classes, methods

### Runtime
- [ ] `remora start` completes without errors
- [ ] Web UI loads at http://localhost:8080
- [ ] Graph shows nodes with proper layout

### API
- [ ] `GET /api/nodes` returns JSON array
- [ ] `GET /api/edges` returns containment edges
- [ ] `POST /api/chat` accepts messages

### Visual
- [ ] Graph visualization renders correctly
- [ ] Clicking nodes shows source code
- [ ] Chat input sends messages
- [ ] Timeline shows events
- [ ] SSE connection indicator is green
```

---

## Summary of Changes

| File | Action | Purpose |
|------|--------|---------|
| `remora.yaml` | REPLACE | Align with v0.5.0 config schema |
| `bundles/demo-agent/bundle.yaml` | CREATE | Custom bundle demonstration |
| `queries/python.scm` | CREATE | Custom query demonstration |
| `src/api/orders.py` | ENHANCE | Add cross-module functions |
| `src/services/analytics.py` | CREATE | Add demo-worthy complexity |
| `tests/test_orders.py` | CREATE | Demonstrate test coverage |
| `scripts/demo_interactive.py` | CREATE | Automated demo walkthrough |
| `scripts/demo_quickstart.sh` | CREATE | One-command demo start |
| `scripts/validate_demo.py` | CREATE | Pre-demo validation |
| `docs/LSP_DEMO.md` | CREATE | LSP integration guide |
| `README.md` | REPLACE | Comprehensive documentation |
| `pyproject.toml` | UPDATE | Use local editable remora |

---

## "Wow Factor" Checklist

After refactoring, verify these wow moments work:

1. **Visual Wow:**
   - Graph shows 20+ nodes clustered by file
   - Edges show containment hierarchy
   - Node colors change on agent activity

2. **Interactive Wow:**
   - Chat with `create_order` about order flow
   - Ask `discount_for_tier` about pricing tiers
   - Query `validate_order` about risk factors

3. **Proposal Wow:**
   - Request a change to `compute_total`
   - See diff preview in browser
   - Accept and watch file update

4. **Real-time Wow:**
   - Edit a file in editor
   - Watch graph update instantly
   - See agent react in timeline

5. **Search Wow:**
   - Search for "discount logic"
   - See semantically similar code
   - Jump between related functions

---

## Appendix: Edge Case Handling

### If edges are still empty:

The edge materialization happens in `FileReconciler._reconcile_events()` at line 272. Verify:

1. Nodes have `parent_id` set (check with `GET /api/nodes/{id}`)
2. `add_edge` is being called (add logging)
3. Edge cleanup isn't removing them immediately

### If chat doesn't respond:

1. Check model endpoint: `curl http://remora-server:8000/v1/models`
2. Check logs: `.remora/remora.log`
3. Verify node status is `idle`, not `running`

### If graph doesn't render:

1. Open browser console for JS errors
2. Check SSE connection status (green dot)
3. Verify `/api/nodes` and `/api/edges` return valid JSON
