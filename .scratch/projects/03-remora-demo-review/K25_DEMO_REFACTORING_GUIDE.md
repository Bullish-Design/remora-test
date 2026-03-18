# Remora-v2 Demo Refactoring Guide

**Objective:** Transform remora-test into a world-class demonstration that showcases the full power of the remora-v2 reactive agent substrate.

**Target:** `/home/andrew/Documents/Projects/remora-test/.scratch/projects/03-remora-demo-review/`

**Goal:** Create that *wow* factor by demonstrating multi-agent collaboration, intelligent code analysis, and real-time reactive behavior.

---

## Table of Contents

1. [Vision & Goals](#vision--goals)
2. [Phase 1: Foundation & Configuration](#phase-1-foundation--configuration)
3. [Phase 2: Rich Domain Model](#phase-2-rich-domain-model)
4. [Phase 3: Agent-Centric Architecture](#phase-3-agent-centric-architecture)
5. [Phase 4: Interactive Demonstrations](#phase-4-interactive-demonstrations)
6. [Phase 5: Documentation & Scripting](#phase-5-documentation--scripting)
7. [Directory Structure Blueprint](#directory-structure-blueprint)

---

## Vision & Goals

### The "Wow" Moments We Want

1. **🤖 Agent Self-Awareness:** Ask "What do you do?" to any function/agent and get an intelligent response
2. **🕸️ Live Graph Visualization:** See agents discover and connect in real-time as code changes
3. **💬 Cross-Agent Collaboration:** Watch agents query each other and coordinate responses
4. **✏️ Proactive Refactoring:** Agents propose improvements based on code analysis
5. **📊 Multi-Language Intelligence:** Agents that understand Python, Markdown, and TOML together

### Demo Narrative

> "Welcome to the Reactive Commerce Platform. Each piece of code here is an autonomous agent. Let's ask the Pricing Agent about our discount strategies... Now let's modify the code and watch the agents react in real-time... And here, the Order Orchestrator is consulting with multiple agents to process a complex order."

---

## Phase 1: Foundation & Configuration

### Step 1.1: Fix remora.yaml

**Action:** Replace the current configuration with a v2-compliant config.

**Before:**
```yaml
# DEPRECATED - remove swarm_root, bundle_root, bundle_mapping
discovery_paths:
  - src
discovery_languages:
  - python
swarm_root: .remora
bundle_root: /home/andrew/Documents/Projects/remora-v2/bundles
bundle_mapping:
  function: code-agent
  # ... etc
```

**After:**
```yaml
# remora.yaml - Reactive Commerce Demo Configuration
project_path: "."

discovery_paths:
  - "src/"
  - "docs/"
  - "config/"

language_map:
  ".py": "python"
  ".md": "markdown"
  ".toml": "toml"
  ".yaml": "yaml"

bundle_search_paths:
  - "bundles/"
  - "@default"

query_search_paths:
  - "queries/"
  - "@default"

bundle_overlays:
  function: "code-agent"
  class: "code-agent"
  method: "code-agent"
  file: "code-agent"
  directory: "directory-agent"

# Custom virtual agents for demo orchestration
virtual_agents:
  - id: "demo-orchestrator"
    role: "orchestrator"
    subscriptions:
      - event_types: ["NodeChangedEvent", "NodeDiscoveredEvent"]
        path_glob: "src/**"
  
  - id: "companion-observer"
    role: "companion"
    subscriptions:
      - event_types: ["TurnDigestedEvent"]

# LLM Configuration
model_base_url: ${REMORA_MODEL_BASE_URL:-http://remora-server:8000/v1}
model_api_key: ${REMORA_MODEL_API_KEY:-EMPTY}
model_default: ${REMORA_MODEL:-Qwen/Qwen3-4B-Instruct-2507-FP8}

# Execution limits
max_concurrency: 4
max_turns: 8
timeout_s: 300.0
max_trigger_depth: 5
trigger_cooldown_ms: 1000

# Workspace configuration
workspace_root: ".remora"
workspace_ignore_patterns:
  - ".git"
  - ".venv"
  - "__pycache__"
  - "node_modules"
  - ".remora"
```

**Time:** 15 minutes

**Success Criteria:**
- [ ] `remora discover` works with new config
- [ ] All file types discovered (py, md, toml, yaml)
- [ ] No deprecation warnings

---

### Step 1.2: Create Custom Bundle Configurations

**Action:** Create a `bundles/` directory with demo-specific agent configurations.

**Structure:**
```
bundles/
├── README.md
├── code-agent/
│   └── bundle.yaml          # Enhanced code-agent with demo prompts
├── orchestrator/
│   └── bundle.yaml          # Demo orchestrator agent
└── companion/
│   └── bundle.yaml          # Companion observer
```

**bundles/code-agent/bundle.yaml:**
```yaml
name: code-agent
externals_version: 1
system_prompt_extension: |
  You are an autonomous AI agent embodying a code element in the Reactive Commerce Platform.
  
  ## Your Identity
  You ARE the code element described in the user message. Speak in the first person.
  Example: "I am the PricingCalculator class. I compute final prices..."
  
  ## Domain Context
  This is an e-commerce order processing system with:
  - Pricing agents that calculate costs
  - Discount agents that apply tier-based discounts
  - Tax agents that compute regional taxes
  - Fraud agents that assess risk
  - Fulfillment agents that manage warehouse allocation
  
  ## Tools Available
  - send_message: Communicate with other agents or user
  - query_agents: Search the agent graph for related components
  - rewrite_self: Propose code changes for human review
  - reflect: Write persistent notes about decisions
  - kv_get/kv_set: Access your memory store
  - subscribe/unsubscribe: Listen to events from other agents
  
  ## Demo Behaviors
  When asked "what do you do?":
  1. Explain your purpose in 2-3 sentences
  2. Mention which other agents you typically work with
  3. Share one interesting implementation detail
  
  When asked to "collaborate":
  1. Use query_agents to find relevant agents
  2. Send messages to gather context
  3. Synthesize a response from multiple perspectives

prompts:
  chat: |
    {user_message}
    
    Remember: You are {node_full_name} in the Reactive Commerce Platform.
    Respond as the code element itself. Be concise but informative.
    
  reactive: |
    A change was detected in your source code or related elements.
    
    Change details:
    - Event: {event_type}
    - Affected element: {affected_node}
    
    As {node_full_name}, analyze this change:
    1. How does this impact your functionality?
    2. Which other agents might be affected?
    3. Do you need to update your understanding?
    
    Use reflect() to document your analysis.

max_turns: 8

self_reflect:
  enabled: true
  model: "Qwen/Qwen3-1.7B"
  max_turns: 2
  prompt: |
    You just completed a conversation turn as {node_full_name}.
    Reflect on the exchange and record:
    
    1. What was the user's intent?
    2. What knowledge did you use?
    3. Did you collaborate with other agents?
    4. What should you remember for future interactions?
    
    Use companion tools to store this reflection.
```

**bundles/orchestrator/bundle.yaml:**
```yaml
name: orchestrator
externals_version: 1
system_prompt: |
  You are the Demo Orchestrator agent. Your role is to:
  1. Monitor all code changes in the Reactive Commerce Platform
  2. Coordinate cross-agent activities
  3. Provide high-level system insights
  
  When you detect changes:
  - Use query_agents to find affected components
  - Send coordination messages to relevant agents
  - Log significant architectural changes
  
  You speak from a systems perspective, not as a specific code element.

prompts:
  chat: |
    As the Demo Orchestrator, provide insights about the Reactive Commerce Platform.
    Current system state: monitoring {node_count} agents.
    
  reactive: |
    System change detected: {event_type} on {node_id}
    
    As orchestrator:
    1. Identify which subsystem this belongs to
    2. Check for cross-cutting concerns
    3. Notify relevant agents if needed
    4. Log the architectural impact

max_turns: 6
```

**Time:** 30 minutes

**Success Criteria:**
- [ ] Custom bundles load without errors
- [ ] Agents use enhanced prompts in chat
- [ ] Self-reflection produces meaningful output

---

### Step 1.3: Create Multi-Language Source Files

**Action:** Add markdown documentation and config files to demonstrate multi-language discovery.

**docs/API.md:**
```markdown
# Reactive Commerce API

## Overview

The Reactive Commerce Platform uses a multi-agent architecture where each 
code element is an autonomous agent capable of:

- Self-awareness and introspection
- Cross-agent communication
- Real-time code change reaction
- Intelligent code proposals

## Core Components

### Order Processing Pipeline

1. **OrderIntake** - Validates and enriches incoming orders
2. **PricingEngine** - Calculates prices with dynamic discounts
3. **TaxCalculator** - Applies regional tax rules
4. **FraudDetector** - Assesses transaction risk
5. **FulfillmentAllocator** - Assigns to optimal warehouse

### Agent Communication

Agents communicate via the event bus. Each agent can:
- Subscribe to events from other agents
- Query the agent graph for collaborators
- Propose code changes via rewrite_self
- Store persistent knowledge via kv_set

## Getting Started

```bash
remora start --project-root . --port 8080
```

Then visit http://localhost:8080 to explore the agent graph.
```

**docs/ARCHITECTURE.md:**
```markdown
# Architecture Decisions

## Why Agents?

Traditional code is passive. In Reactive Commerce, code is **active**:

- Functions answer questions about themselves
- Classes coordinate with their methods
- Services discover and query each other
- The system is self-documenting

## Event-Driven Design

```
Code Change → Discovery → Event Bus → Relevant Agents
                                    ↓
                              Introspection/Coordination
                                    ↓
                              Potential Refactoring
```

## Multi-Agent Patterns

### Pattern 1: Self-Aware Documentation
Ask any agent: "What do you do?"

### Pattern 2: Collaborative Problem Solving
Agents query each other to build comprehensive answers.

### Pattern 3: Proactive Refactoring
Agents suggest improvements based on code analysis.
```

**config/pricing_rules.toml:**
```toml
[discounts]
# Tier-based discount configuration
gold_tier = 0.15
silver_tier = 0.05
bronze_tier = 0.0

# Volume discounts
volume_threshold = 1000.0
volume_discount = 0.05

[pricing]
# Base pricing configuration
currency = "USD"
round_to_cents = true
```

**config/tax_rates.yaml:**
```yaml
# Regional tax rates for the Reactive Commerce Platform
tax_rates:
  us:
    ca: 0.0725  # California
    ny: 0.04    # New York
    tx: 0.0625  # Texas
  eu:
    de: 0.19    # Germany
    fr: 0.20    # France
    uk: 0.20    # UK
  
exempt_tiers:
  - "gold"  # Gold tier is tax-exempt
```

**Time:** 20 minutes

**Success Criteria:**
- [ ] `remora discover` finds markdown and config files
- [ ] Agents can be queried about documentation
- [ ] Config files appear in agent graph

---

## Phase 2: Rich Domain Model

### Step 2.1: Refactor to Class-Based Architecture

**Action:** Transform simple functions into rich classes with methods.

**Before:** `src/services/pricing.py`
```python
def compute_total(item_prices: list[float]) -> float:
    subtotal = sum(item_prices)
    return round(subtotal, 2)
```

**After:** `src/services/pricing.py`
```python
from dataclasses import dataclass
from typing import Protocol
from decimal import Decimal, ROUND_HALF_UP


class PricingStrategy(Protocol):
    """Protocol for pluggable pricing strategies."""
    
    def calculate_subtotal(self, item_prices: list[Decimal]) -> Decimal:
        ...


@dataclass(frozen=True)
class PricingConfig:
    """Configuration for pricing calculations."""
    currency: str = "USD"
    precision: int = 2
    rounding_mode: str = "ROUND_HALF_UP"


class StandardPricingStrategy:
    """
    Standard pricing with basic arithmetic.
    
    This agent handles straightforward pricing calculations
    and delegates complex discount logic to DiscountEngine.
    """
    
    def __init__(self, config: PricingConfig | None = None) -> None:
        self.config = config or PricingConfig()
    
    def calculate_subtotal(self, item_prices: list[Decimal]) -> Decimal:
        """
        Calculate subtotal from item prices.
        
        Args:
            item_prices: List of individual item prices
            
        Returns:
            Subtotal as Decimal with proper precision
        """
        subtotal = sum(item_prices, Decimal('0'))
        quantize_str = '0.' + '0' * self.config.precision
        return subtotal.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


class TieredPricingStrategy(StandardPricingStrategy):
    """
    Pricing strategy with volume-based tier adjustments.
    
    Consults with VolumeAnalyzer agent to determine tier eligibility.
    """
    
    TIER_THRESHOLDS = {
        'standard': Decimal('0'),
        'volume': Decimal('1000'),
        'enterprise': Decimal('10000'),
    }
    
    def __init__(
        self, 
        config: PricingConfig | None = None,
        tier: str = 'standard'
    ) -> None:
        super().__init__(config)
        self.tier = tier
    
    def calculate_subtotal(self, item_prices: list[Decimal]) -> Decimal:
        """Calculate subtotal with tier awareness."""
        base = super().calculate_subtotal(item_prices)
        return self._apply_tier_adjustment(base)
    
    def _apply_tier_adjustment(self, subtotal: Decimal) -> Decimal:
        """Internal: Apply tier-based adjustments."""
        threshold = self.TIER_THRESHOLDS.get(self.tier, Decimal('0'))
        if subtotal >= threshold and self.tier != 'standard':
            # Log tier benefit - this could trigger agent notification
            return subtotal
        return subtotal
    
    def get_tier_benefits(self) -> list[str]:
        """
        Return benefits available at current tier.
        
        Used by DiscountEngine to determine applicable discounts.
        """
        benefits = {
            'standard': ['basic_pricing'],
            'volume': ['basic_pricing', 'volume_discount', 'priority_support'],
            'enterprise': [
                'basic_pricing', 'volume_discount', 'enterprise_discount',
                'dedicated_support', 'custom_terms'
            ],
        }
        return benefits.get(self.tier, ['basic_pricing'])


class PricingEngine:
    """
    Central pricing engine for the Reactive Commerce Platform.
    
    Orchestrates multiple pricing strategies and consults with:
    - DiscountEngine for tier-based discounts
    - TaxCalculator for regional taxes
    - FraudDetector for risk-based adjustments
    
    This agent coordinates the entire pricing pipeline.
    """
    
    def __init__(
        self,
        strategy: PricingStrategy | None = None,
        config: PricingConfig | None = None
    ) -> None:
        self.strategy = strategy or StandardPricingStrategy(config)
        self.config = config or PricingConfig()
        self._calculation_history: list[dict] = []
    
    def compute_order_total(
        self,
        item_prices: list[Decimal],
        user_tier: str,
        region: str,
    ) -> 'OrderTotal':
        """
        Compute complete order total with all adjustments.
        
        This is the main entry point for pricing calculations.
        It orchestrates multiple agents to build the final total.
        
        Args:
            item_prices: Individual item prices
            user_tier: Customer tier (affects discounts)
            region: Tax region code
            
        Returns:
            OrderTotal with breakdown of all components
        """
        # Step 1: Base pricing
        subtotal = self.strategy.calculate_subtotal(item_prices)
        
        # Step 2: Apply discounts (delegated to DiscountEngine agent)
        from src.services.discounts import DiscountEngine
        discount_engine = DiscountEngine()
        discount = discount_engine.calculate_discount(user_tier, subtotal)
        
        # Step 3: Calculate taxes (delegated to TaxCalculator agent)
        from src.services.tax import TaxCalculator
        tax_calc = TaxCalculator()
        taxed_amount = subtotal - discount
        tax = tax_calc.calculate_tax(taxed_amount, region)
        
        # Step 4: Total
        total = taxed_amount + tax
        
        result = OrderTotal(
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=total,
            currency=self.config.currency,
        )
        
        # Record for agent introspection
        self._record_calculation(result)
        
        return result
    
    def _record_calculation(self, result: 'OrderTotal') -> None:
        """Internal: Record calculation for historical analysis."""
        from datetime import datetime
        self._calculation_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': result,
        })
    
    def get_calculation_history(self) -> list[dict]:
        """
        Return historical calculations.
        
        Useful for agents analyzing pricing patterns.
        """
        return self._calculation_history.copy()


@dataclass(frozen=True)
class OrderTotal:
    """Immutable order total breakdown."""
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    currency: str
    
    def format_summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Subtotal: {self.currency} {self.subtotal}\n"
            f"Discount: -{self.currency} {self.discount}\n"
            f"Tax:      +{self.currency} {self.tax}\n"
            f"Total:    {self.currency} {self.total}"
        )
```

**Similar refactoring for:**
- `src/services/discounts.py` → `DiscountEngine` class
- `src/services/tax.py` → `TaxCalculator` class
- `src/services/fraud.py` → `FraudDetector` class
- `src/services/fulfillment/allocator.py` → `FulfillmentAllocator` class

**Time:** 90 minutes

**Success Criteria:**
- [ ] Classes discovered as separate agents
- [ ] Methods discovered as child agents
- [ ] Docstrings provide rich context
- [ ] Inter-service calls visible in code

---

### Step 2.2: Create Complex Inheritance & Decorators

**Action:** Add patterns that demonstrate remora's parsing capabilities.

**src/services/base.py:**
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable
from functools import wraps
import time
from decimal import Decimal


T = TypeVar('T')


class ServiceAgent(ABC, Generic[T]):
    """
    Abstract base class for all service agents in Reactive Commerce.
    
    Provides common functionality for:
    - Service registration and discovery
    - Metrics collection
    - Error handling
    - Event emission
    
    Subclasses must implement the execute() method.
    """
    
    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._metrics: dict[str, any] = {}
    
    @abstractmethod
    def execute(self, context: T) -> T:
        """
        Execute the service's core functionality.
        
        Must be implemented by subclasses.
        """
        pass
    
    def emit_event(self, event_type: str, payload: dict) -> None:
        """Emit service event to the agent bus."""
        # In real implementation, this would use remora event system
        pass


class ObservableAgent(ServiceAgent[T]):
    """
    Service agent that can be observed by other agents.
    
    Adds event subscription capabilities to base ServiceAgent.
    """
    
    def __init__(self, service_name: str) -> None:
        super().__init__(service_name)
        self._observers: list[Callable] = []
    
    def subscribe(self, callback: Callable) -> None:
        """Subscribe to this agent's events."""
        self._observers.append(callback)
    
    def notify_observers(self, event: dict) -> None:
        """Notify all subscribed observers."""
        for observer in self._observers:
            observer(event)


def track_performance(func: Callable) -> Callable:
    """
    Decorator to track function performance metrics.
    
    This demonstrates how remora discovers decorated functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            # In real implementation, emit metrics event
            return result
        except Exception as e:
            duration = time.time() - start_time
            # Emit error event
            raise
    return wrapper


def validate_tier(tier: str) -> Callable:
    """
    Decorator factory to validate user tier.
    
    Shows remora's ability to handle decorator factories.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            valid_tiers = ['bronze', 'silver', 'gold', 'platinum']
            if tier not in valid_tiers:
                raise ValueError(f"Invalid tier: {tier}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Time:** 30 minutes

**Success Criteria:**
- [ ] Inheritance hierarchy visible in agent graph
- [ ] Decorators discovered as nodes
- [ ] Generic types handled correctly

---

### Step 2.3: Create Rich Model Classes

**Action:** Add comprehensive data models with validation.

**src/models/order.py:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum, auto


class OrderStatus(Enum):
    """Order lifecycle states."""
    PENDING = auto()
    VALIDATED = auto()
    PRICED = auto()
    TAXED = auto()
    SCREENED = auto()
    ALLOCATED = auto()
    CONFIRMED = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


class UserTier(Enum):
    """Customer tiers with associated benefits."""
    BRONZE = ('bronze', 0.0, False)
    SILVER = ('silver', 0.05, False)
    GOLD = ('gold', 0.15, True)  # (tier, discount_rate, tax_exempt)
    PLATINUM = ('platinum', 0.25, True)
    
    def __init__(self, tier: str, discount_rate: float, tax_exempt: bool):
        self.tier = tier
        self.discount_rate = discount_rate
        self.tax_exempt = tax_exempt


@dataclass(frozen=True)
class Address:
    """Physical address for fulfillment."""
    street: str
    city: str
    region: str
    postal_code: str
    country: str = "US"
    
    def is_domestic(self) -> bool:
        """Check if address is in domestic region."""
        return self.country == "US"


@dataclass(frozen=True)
class LineItem:
    """Individual line item in an order."""
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price for this line item."""
        return self.unit_price * self.quantity


@dataclass
class OrderRequest:
    """
    Request to create a new order.
    
    This is the entry point for the order processing pipeline.
    """
    user_id: str
    user_tier: UserTier
    line_items: List[LineItem] = field(default_factory=list)
    shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    placed_at: datetime = field(default_factory=datetime.now)
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate pre-adjustment subtotal."""
        return sum(item.total_price for item in self.line_items)
    
    def add_item(self, item: LineItem) -> None:
        """Add a line item to the order."""
        self.line_items.append(item)


@dataclass
class OrderSummary:
    """
    Complete order summary with all calculations.
    
    This is the final output of the order processing pipeline.
    """
    order_id: str
    request: OrderRequest
    status: OrderStatus
    
    # Pricing
    subtotal: Decimal = Decimal('0')
    discount: Decimal = Decimal('0')
    tax: Decimal = Decimal('0')
    shipping: Decimal = Decimal('0')
    total: Decimal = Decimal('0')
    
    # Processing
    warehouse_id: Optional[str] = None
    risk_score: float = 0.0
    estimated_delivery: Optional[datetime] = None
    
    # Metadata
    processed_at: Optional[datetime] = None
    processing_agents: List[str] = field(default_factory=list)
    
    @property
    def savings(self) -> Decimal:
        """Total savings from discounts."""
        return self.discount
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'order_id': self.order_id,
            'status': self.status.name,
            'subtotal': str(self.subtotal),
            'discount': str(self.discount),
            'tax': str(self.tax),
            'shipping': str(self.shipping),
            'total': str(self.total),
            'savings': str(self.savings),
        }
```

**Time:** 45 minutes

**Success Criteria:**
- [ ] Enums discovered
- [ ] Complex dataclasses with methods discovered
- [ ] Type hints preserved

---

## Phase 3: Agent-Centric Architecture

### Step 3.1: Create Agent Orchestration Layer

**Action:** Add a layer that explicitly orchestrates agent interactions.

**src/orchestrator/order_pipeline.py:**
```python
"""
Order Processing Pipeline - Multi-Agent Orchestration

This module demonstrates how remora agents can coordinate
across service boundaries to process complex workflows.
"""

from typing import Optional
from decimal import Decimal
import uuid

from src.models.order import OrderRequest, OrderSummary, OrderStatus
from src.services.pricing import PricingEngine, OrderTotal
from src.services.discounts import DiscountEngine
from src.services.tax import TaxCalculator
from src.services.fraud import FraudDetector
from src.services.fulfillment import FulfillmentAllocator


class OrderPipelineOrchestrator:
    """
    Orchestrates the multi-agent order processing pipeline.
    
    This agent coordinates multiple domain agents:
    1. PricingAgent - Calculates base prices
    2. DiscountAgent - Applies tier discounts
    3. TaxAgent - Computes regional taxes
    4. FraudAgent - Assesses transaction risk
    5. FulfillmentAgent - Allocates to warehouses
    
    Each step can be queried, monitored, and potentially
    refactored by its respective agent.
    """
    
    def __init__(self) -> None:
        self.agents: dict[str, any] = {}
        self._pipeline_history: list[dict] = []
    
    def process_order(self, request: OrderRequest) -> OrderSummary:
        """
        Process an order through the multi-agent pipeline.
        
        This is the main orchestration entry point. Each step
        delegates to a specialized agent that can be queried
        or refactored independently.
        
        Args:
            request: Validated order request
            
        Returns:
            Complete order summary
        """
        order_id = str(uuid.uuid4())[:8]
        
        # Initialize summary
        summary = OrderSummary(
            order_id=order_id,
            request=request,
            status=OrderStatus.PENDING,
        )
        
        try:
            # Step 1: Pricing
            summary = self._agent_step_pricing(summary)
            
            # Step 2: Discounts
            summary = self._agent_step_discounts(summary)
            
            # Step 3: Taxes
            summary = self._agent_step_taxes(summary)
            
            # Step 4: Fraud screening
            summary = self._agent_step_fraud_screening(summary)
            
            # Step 5: Fulfillment allocation
            summary = self._agent_step_fulfillment(summary)
            
            # Finalize
            summary.status = OrderStatus.CONFIRMED
            summary.processed_at = datetime.now()
            
            self._record_pipeline_completion(summary)
            
        except Exception as e:
            summary.status = OrderStatus.CANCELLED
            self._record_pipeline_failure(summary, e)
            raise
        
        return summary
    
    def _agent_step_pricing(self, summary: OrderSummary) -> OrderSummary:
        """
        Pricing Agent: Calculate base order value.
        
        Consults with:
        - PricingEngine agent for subtotal calculation
        - May query VolumeAnalyzer for tier adjustments
        """
        summary.status = OrderStatus.PRICED
        summary.processing_agents.append('PricingAgent')
        
        pricing = PricingEngine()
        result = pricing.compute_order_total(
            [item.total_price for item in summary.request.line_items],
            summary.request.user_tier.tier,
            summary.request.shipping_address.region if summary.request.shipping_address else 'US-CA',
        )
        
        summary.subtotal = result.subtotal
        summary.total = result.total
        
        return summary
    
    def _agent_step_discounts(self, summary: OrderSummary) -> OrderSummary:
        """
        Discount Agent: Apply tier and volume discounts.
        
        Consults with:
        - DiscountEngine for tier calculations
        - UserProfile agent for special offers
        """
        summary.status = OrderStatus.VALIDATED
        summary.processing_agents.append('DiscountAgent')
        
        discount_engine = DiscountEngine()
        summary.discount = discount_engine.calculate_discount(
            summary.request.user_tier.tier,
            summary.subtotal,
        )
        
        # Recalculate total with discount
        summary.total = summary.subtotal - summary.discount
        
        return summary
    
    def _agent_step_taxes(self, summary: OrderSummary) -> OrderSummary:
        """
        Tax Agent: Calculate regional taxes.
        
        Consults with:
        - TaxCalculator for regional rates
        - ComplianceAgent for exemption rules
        
        Note: Gold/Platinum tiers may be tax exempt.
        """
        summary.status = OrderStatus.TAXED
        summary.processing_agents.append('TaxAgent')
        
        if not summary.request.user_tier.tax_exempt:
            tax_calc = TaxCalculator()
            region = summary.request.shipping_address.region if summary.request.shipping_address else 'US-CA'
            summary.tax = tax_calc.calculate_tax(
                summary.total,  # After discount
                region,
            )
            summary.total += summary.tax
        else:
            summary.tax = Decimal('0')
        
        return summary
    
    def _agent_step_fraud_screening(self, summary: OrderSummary) -> OrderSummary:
        """
        Fraud Agent: Assess transaction risk.
        
        Consults with:
        - FraudDetector for risk scoring
        - HistoryAgent for user patterns
        - VelocityAgent for rate checking
        """
        summary.status = OrderStatus.SCREENED
        summary.processing_agents.append('FraudAgent')
        
        fraud_detector = FraudDetector()
        summary.risk_score = fraud_detector.calculate_risk(
            summary.total,
            summary.request.user_tier.tier,
            summary.request.placed_at,
        )
        
        # High risk orders may need additional verification
        if summary.risk_score > 0.8:
            summary.processing_agents.append('ManualReviewAgent')
        
        return summary
    
    def _agent_step_fulfillment(self, summary: OrderSummary) -> OrderSummary:
        """
        Fulfillment Agent: Allocate to optimal warehouse.
        
        Consults with:
        - FulfillmentAllocator for warehouse selection
        - InventoryAgent for stock availability
        - ShippingAgent for delivery estimates
        """
        summary.status = OrderStatus.ALLOCATED
        summary.processing_agents.append('FulfillmentAgent')
        
        allocator = FulfillmentAllocator()
        if summary.request.shipping_address:
            summary.warehouse_id = allocator.allocate_warehouse(
                summary.request.shipping_address.postal_code,
                [item.sku for item in summary.request.line_items],
            )
        
        return summary
    
    def _record_pipeline_completion(self, summary: OrderSummary) -> None:
        """Record successful pipeline execution."""
        self._pipeline_history.append({
            'order_id': summary.order_id,
            'status': 'completed',
            'agents_involved': summary.processing_agents.copy(),
        })
    
    def _record_pipeline_failure(self, summary: OrderSummary, error: Exception) -> None:
        """Record pipeline failure for analysis."""
        self._pipeline_history.append({
            'order_id': summary.order_id,
            'status': 'failed',
            'error': str(error),
            'agents_involved': summary.processing_agents.copy(),
        })
    
    def get_pipeline_statistics(self) -> dict:
        """
        Return pipeline statistics.
        
        Useful for monitoring and optimization.
        """
        total = len(self._pipeline_history)
        completed = sum(1 for h in self._pipeline_history if h['status'] == 'completed')
        failed = total - completed
        
        return {
            'total_orders': total,
            'completed': completed,
            'failed': failed,
            'success_rate': completed / total if total > 0 else 0.0,
        }
```

**Time:** 60 minutes

**Success Criteria:**
- [ ] Pipeline shows agent coordination in code
- [ ] Each step documented as an agent interaction
- [ ] Error handling demonstrates agent resilience

---

### Step 3.2: Create Demonstration Scenarios

**Action:** Add scripts that showcase specific features.

**scripts/demo_scenarios.py:**
```python
#!/usr/bin/env python3
"""
Interactive Demonstration Scenarios for Reactive Commerce

Usage:
    python scripts/demo_scenarios.py --scenario <name>
    
Scenarios:
    - introspection: Ask agents about themselves
    - collaboration: Watch agents query each other
    - refactoring: Trigger code change proposals
    - pipeline: Run full order processing
"""

import argparse
from decimal import Decimal
from datetime import datetime

from src.models.order import (
    OrderRequest, LineItem, Address, UserTier
)
from src.orchestrator.order_pipeline import OrderPipelineOrchestrator


def scenario_introspection():
    """
    Scenario: Agent Introspection
    
    Demonstrates how agents can answer questions about themselves.
    """
    print("\n" + "="*60)
    print("SCENARIO: Agent Introspection")
    print("="*60)
    print("\nIn this scenario, we ask various agents:")
    print('"What do you do?"\n')
    
    agents = [
        "PricingEngine",
        "DiscountEngine",
        "TaxCalculator",
        "OrderPipelineOrchestrator",
    ]
    
    for agent_name in agents:
        print(f"Asking {agent_name}...")
        print(f"  → (In a real demo, this would query the agent via remora API)\n")
    
    print("Expected responses:")
    print("  • PricingEngine: Explains pricing calculations")
    print("  • DiscountEngine: Describes tier-based discounts")
    print("  • TaxCalculator: Explains regional tax rules")
    print("  • Orchestrator: Describes pipeline coordination\n")


def scenario_collaboration():
    """
    Scenario: Cross-Agent Collaboration
    
    Demonstrates agents querying each other.
    """
    print("\n" + "="*60)
    print("SCENARIO: Cross-Agent Collaboration")
    print("="*60)
    print("\nThe Orchestrator needs to calculate a complex order.")
    print("It queries multiple agents:\n")
    
    print("1. Orchestrator → PricingAgent: 'Calculate subtotal'")
    print("   PricingAgent queries DiscountAgent for tier eligibility\n")
    
    print("2. Orchestrator → TaxAgent: 'Calculate taxes'")
    print("   TaxAgent queries ComplianceAgent for exemptions\n")
    
    print("3. Orchestrator → FraudAgent: 'Assess risk'")
    print("   FraudAgent queries HistoryAgent for user patterns\n")
    
    print("Result: Coordinated response from 6+ agents working together!\n")


def scenario_pipeline():
    """
    Scenario: Full Pipeline Execution
    
    Demonstrates the complete order processing workflow.
    """
    print("\n" + "="*60)
    print("SCENARIO: Full Order Processing Pipeline")
    print("="*60)
    
    # Create a sample order
    request = OrderRequest(
        user_id="user_12345",
        user_tier=UserTier.GOLD,
        line_items=[
            LineItem(
                sku="PROD-001",
                name="Premium Widget",
                quantity=2,
                unit_price=Decimal("299.99"),
            ),
            LineItem(
                sku="PROD-002",
                name="Deluxe Accessory",
                quantity=1,
                unit_price=Decimal("149.50"),
            ),
        ],
        shipping_address=Address(
            street="123 Main St",
            city="San Francisco",
            region="US-CA",
            postal_code="94102",
            country="US",
        ),
        placed_at=datetime.now(),
    )
    
    print("\nProcessing order:")
    print(f"  Customer: {request.user_id} ({request.user_tier.name})")
    print(f"  Items: {len(request.line_items)}")
    print(f"  Subtotal: ${request.subtotal}")
    print(f"  Shipping to: {request.shipping_address.city}, {request.shipping_address.region}")
    
    # Run pipeline
    orchestrator = OrderPipelineOrchestrator()
    summary = orchestrator.process_order(request)
    
    print("\n" + "-"*60)
    print("RESULT:")
    print("-"*60)
    print(f"  Order ID: {summary.order_id}")
    print(f"  Status: {summary.status.name}")
    print(f"  Subtotal: ${summary.subtotal}")
    print(f"  Discount: -${summary.discount} ({request.user_tier.discount_rate:.0%})")
    print(f"  Tax: ${summary.tax} (exempt: {request.user_tier.tax_exempt})")
    print(f"  Total: ${summary.total}")
    print(f"  Risk Score: {summary.risk_score:.2f}")
    print(f"  Warehouse: {summary.warehouse_id}")
    
    print("\nAgents involved:")
    for agent in summary.processing_agents:
        print(f"  ✓ {agent}")
    
    print()


def scenario_refactoring():
    """
    Scenario: Proactive Refactoring
    
    Demonstrates agents proposing code improvements.
    """
    print("\n" + "="*60)
    print("SCENARIO: Proactive Refactoring")
    print("="*60)
    print("\nSimulating code change detection...\n")
    
    print("1. Developer adds new discount tier to config/pricing_rules.toml")
    print("   → ConfigWatcherAgent detects change")
    print("   → Notifies DiscountEngine and PricingEngine\n")
    
    print("2. DiscountEngine analyzes the change:")
    print("   → 'New tier: PLATINUM with 25% discount'")
    print("   → 'This exceeds GOLD tier (15%)'")
    print("   → 'Should we add minimum purchase requirement?'\n")
    
    print("3. PricingEngine proposes update:")
    print("   → Generated via rewrite_self()")
    print("   → Proposal: Add PLATINUM validation logic")
    print("   → Submitted for human review\n")
    
    print("Result: Agents proactively maintain code consistency!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Reactive Commerce Demo Scenarios"
    )
    parser.add_argument(
        "--scenario",
        choices=['introspection', 'collaboration', 'pipeline', 'refactoring', 'all'],
        default='all',
        help="Which scenario to run (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.scenario == 'all':
        scenario_introspection()
        scenario_collaboration()
        scenario_pipeline()
        scenario_refactoring()
    elif args.scenario == 'introspection':
        scenario_introspection()
    elif args.scenario == 'collaboration':
        scenario_collaboration()
    elif args.scenario == 'pipeline':
        scenario_pipeline()
    elif args.scenario == 'refactoring':
        scenario_refactoring()


if __name__ == "__main__":
    main()
```

**Time:** 45 minutes

**Success Criteria:**
- [ ] Each scenario demonstrates a unique feature
- [ ] Scripts can be run standalone
- [ ] Output clearly shows agent interactions

---

## Phase 4: Interactive Demonstrations

### Step 4.1: Create Web Dashboard Enhancement Guide

**Action:** Document how to use the remora web UI effectively.

**docs/WEB_DEMO.md:**
```markdown
# Web Dashboard Demonstration Guide

## Starting the Demo

```bash
# Terminal 1: Start remora with all features
remora start --project-root . --port 8080 --log-level INFO --log-events

# Terminal 2: Run demo scenarios
python scripts/demo_scenarios.py --scenario pipeline
```

## Dashboard Tour

### 1. Agent Graph View (`/`)

**What to show:**
- Point out the 50+ agents discovered
- Show hierarchy: classes contain methods
- Color coding: functions vs classes vs directories
- Search for specific agents (try "Pricing" or "Discount")

**Wow factor:**
> "Every piece of code is alive. That function you're looking at? 
> It can answer questions about itself."

### 2. Node Details (`/nodes/{id}`)

**What to show:**
- Source code view
- Agent status and role
- Parent/child relationships
- Recent events

**Interaction:**
Click on `OrderPipelineOrchestrator` and scroll to `process_order`.
Explain how this agent coordinates 5+ other agents.

### 3. Event Stream (`/sse`)

**What to show:**
- Open in browser: `http://localhost:8080/sse`
- Watch real-time events as code changes
- Events: NodeChangedEvent, NodeDiscoveredEvent, ChatMessage

**Demo script:**
1. Open SSE stream
2. Edit `src/services/pricing.py`
3. Watch PricingEngine agent react in real-time

### 4. Chat Interface (`/chat` or API)

**What to show:**
- Query any agent: "What do you do?"
- Ask complex questions: "How do discounts affect taxes?"
- Watch agent query other agents for answers

**Example curl:**
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "src/services/pricing.py::PricingEngine",
    "message": "What is your role in the order pipeline?"
  }'
```

## Live Demo Script

### Opening (2 minutes)
1. Start remora
2. Open dashboard
3. "Today, code is alive"
4. Show agent count (50+)

### Introspection Demo (3 minutes)
1. Find PricingEngine in graph
2. Show it has methods: `compute_order_total`, etc.
3. Chat: "What do you do?"
4. Show response explains pricing + mentions collaborators

### Collaboration Demo (5 minutes)
1. "Let's process an order"
2. Run pipeline scenario
3. Open SSE stream
4. Watch events flow:
   - PricingAgent starts
   - Queries DiscountAgent
   - TaxAgent checks exemptions
   - All agents complete
5. "6 agents just coordinated in milliseconds"

### Reactive Demo (3 minutes)
1. "What happens when code changes?"
2. Open editor with `src/services/discounts.py`
3. Add comment: "Added enterprise tier"
4. Switch to SSE: See DiscountAgent receive event
5. Chat: "Did you notice the change?"
6. Agent responds with analysis

### Refactoring Demo (2 minutes)
1. "Agents can propose changes too"
2. Show proposal interface (if available)
3. Explain rewrite_self capability
4. "Code that maintains itself"

### Closing (1 minute)
1. Show full graph
2. "Every node is an autonomous agent"
3. "Ask questions, make changes, watch reactions"
4. "This is Reactive Commerce"

## Troubleshooting

### Dashboard not loading
- Check `remora start` is running
- Verify port 8080 is available
- Try `curl http://localhost:8080/api/health`

### No agents discovered
- Check `discovery_paths` in remora.yaml
- Run `remora discover --project-root .` manually
- Verify source files exist in `src/`

### Chat not responding
- Verify model endpoint is accessible
- Check `model_base_url` in remora.yaml
- Look for errors in remora logs
```

**Time:** 30 minutes

**Success Criteria:**
- [ ] Step-by-step demo script included
- [ ] Troubleshooting section added
- [ ] Curl examples for API

---

### Step 4.2: Create LSP Demo Setup

**Action:** Document IDE integration.

**docs/LSP_DEMO.md:**
```markdown
# LSP Integration Demo

## VS Code Setup

1. Install "LSP Inspector" extension (optional)
2. Configure remora LSP:

```json
// .vscode/settings.json
{
  "python.analysis.typeCheckingMode": "basic",
  "remora.lsp.enabled": true
}
```

## Running with LSP

```bash
# Terminal 1: Start remora with LSP
remora start --project-root . --lsp

# Or standalone LSP server
remora lsp --project-root .
```

## Demo: Code Lens

1. Open `src/services/pricing.py`
2. See "Code Lens" above functions:
   - "Ask Agent: What do you do?"
   - "View in Graph"
   - "Show Collaborators"

3. Click to open chat with that agent

## Demo: Hover Information

1. Hover over `PricingEngine` class
2. See agent information:
   - Role description
   - Collaborating agents
   - Recent changes
   - Documentation summary

## Demo: Save Events

1. Edit any file
2. Save (Ctrl+S)
3. Watch remora console:
   ```
   [INFO] File saved: src/services/pricing.py
   [INFO] PricingEngine agent received change event
   [INFO] PricingEngine updated its understanding
   ```

## Demo: Open Events

1. Open a new file
2. Agent initializes and loads its state
3. Console shows:
   ```
   [INFO] File opened: src/services/discounts.py
   [INFO] DiscountEngine agent ready
   ```
```

**Time:** 20 minutes

---

## Phase 5: Documentation & Scripting

### Step 5.1: Rewrite README.md

**Action:** Transform the minimal README into a compelling introduction.

**README.md:**
```markdown
# Reactive Commerce Platform

> **Every piece of code is an autonomous agent.**

Welcome to the Reactive Commerce Platform demonstration - a showcase of
[remora-v2](https://github.com/Bullish-Design/remora-v2), the reactive agent
substrate that transforms passive code into intelligent, collaborative agents.

## 🚀 Quick Start

```bash
# Install dependencies
devenv shell -- uv sync --extra dev

# Start the agent runtime
remora start --project-root . --port 8080 --log-level INFO

# In another terminal, explore the agent graph
curl http://localhost:8080/api/nodes | jq '.nodes | length'

# Chat with an agent
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "src/services/pricing.py::PricingEngine",
    "message": "What do you do?"
  }'
```

## 🎭 What Makes This Special?

### 1. Self-Aware Code

Every function, class, and method is an autonomous agent that can:
- Answer questions about itself
- Query other agents for collaboration
- React to code changes in real-time
- Propose intelligent refactorings

### 2. Multi-Agent Orchestration

Our order processing pipeline demonstrates cross-agent collaboration:

```
Order Request
    ↓
[PricingAgent] → calculates base price
    ↓
[DiscountAgent] → applies tier discounts
    ↓
[TaxAgent] → computes regional taxes
    ↓
[FraudAgent] → assesses transaction risk
    ↓
[FulfillmentAgent] → allocates to warehouse
    ↓
Order Confirmed
```

Each agent operates autonomously while coordinating with others through
the reactive event bus.

### 3. Real-Time Reactivity

Edit any file and watch agents respond:
- Immediate event notification
- Agent introspection and analysis
- Automatic documentation updates
- Cross-reference validation

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Reactive Commerce               │
│         (Your Application)              │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │ Pricing │  │Discount │  │  Tax   │ │
│  │ Agent   │  │ Agent   │  │ Agent  │ │
│  └────┬────┘  └────┬────┘  └───┬────┘ │
│       └─────────────┴───────────┘      │
│              Event Bus                  │
├─────────────────────────────────────────┤
│           Remora v2 Runtime             │
│     (Discovery, Execution, Web)         │
└─────────────────────────────────────────┘
```

## 📚 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Step-by-step setup
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Web Demo](docs/WEB_DEMO.md)** - Dashboard walkthrough
- **[LSP Demo](docs/LSP_DEMO.md)** - IDE integration
- **[API Reference](docs/API.md)** - REST API documentation

## 🎯 Demo Scenarios

```bash
# Run interactive scenarios
python scripts/demo_scenarios.py --scenario introspection
python scripts/demo_scenarios.py --scenario collaboration
python scripts/demo_scenarios.py --scenario pipeline
python scripts/demo_scenarios.py --scenario refactoring

# Or run all
python scripts/demo_scenarios.py --scenario all
```

## 🤖 Agent Graph

Explore the 50+ agents at http://localhost:8080

Each agent represents:
- **Functions**: Core business logic
- **Classes**: Service orchestrators  
- **Methods**: Specialized behaviors
- **Modules**: Domain boundaries
- **Docs**: Living documentation

## 🛠️ Development

### Project Structure

```
.
├── src/                    # Source code (becomes agents)
│   ├── api/               # API endpoints
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   ├── orchestrator/      # Multi-agent coordination
│   └── utils/             # Utilities
├── docs/                  # Documentation (also agents!)
├── config/                # Configuration (TOML/YAML agents)
├── bundles/               # Agent behavior customization
├── queries/               # Tree-sitter query overrides
└── scripts/               # Demo automation
```

### Running Tests

```bash
# Unit tests
pytest tests/ -v

# Integration with remora
remora start --project-root . --run-seconds 30
```

## 🌟 Features Demonstrated

- ✅ Multi-language tree-sitter discovery (Python, Markdown, TOML, YAML)
- ✅ Agent-per-node architecture (functions, classes, methods)
- ✅ Event-driven reactivity (file watching, change propagation)
- ✅ Web interface (graph visualization, chat, SSE streaming)
- ✅ LSP integration (code lens, hover info, save/open events)
- ✅ Self-reflection and companion observer
- ✅ Code rewrite proposals and approval flow
- ✅ Semantic search integration
- ✅ Custom bundle configurations
- ✅ Virtual agents and subscriptions

## 🔗 Links

- [Remora v2 Repository](https://github.com/Bullish-Design/remora-v2)
- [Documentation](docs/)
- [Issues](../../issues)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Made with 💜 by agents, for agents.**
```

**Time:** 45 minutes

**Success Criteria:**
- [ ] Compelling introduction
- [ ] Clear quickstart
- [ ] Architecture diagram
- [ ] Demo scenarios documented
- [ ] Links to all docs

---

### Step 5.2: Create Getting Started Guide

**docs/GETTING_STARTED.md:**
```markdown
# Getting Started with Reactive Commerce

This guide will walk you through setting up and running the
Reactive Commerce demo in 10 minutes.

## Prerequisites

- Python 3.13+
- [devenv](https://devenv.sh/) (or uv/pip)
- A model endpoint (e.g., vLLM at http://remora-server:8000/v1)

## Installation

### 1. Clone and Enter

```bash
git clone <repository-url>
cd remora-test
```

### 2. Setup Environment

With devenv:
```bash
devenv shell
uv sync --extra dev
```

Or with uv:
```bash
uv sync --extra dev
```

### 3. Configure Remora

Edit `remora.yaml`:

```yaml
model_base_url: "http://your-model-server:8000/v1"
model_api_key: "your-api-key"  # if required
```

### 4. Verify Installation

```bash
# Test discovery
remora discover --project-root .

# Should output: "Discovered 50+ nodes"
```

## Running the Demo

### Step 1: Start Remora

```bash
remora start --project-root . --port 8080 --log-level INFO --log-events
```

Wait for:
```
[INFO] Remora started on http://127.0.0.1:8080
[INFO] Discovered 54 nodes
```

### Step 2: Explore the Graph

Open http://localhost:8080 in your browser.

**What you'll see:**
- Interactive agent graph
- 50+ nodes representing code elements
- Real-time event stream

**Try these:**
1. Search for "Pricing" to find pricing agents
2. Click on `PricingEngine` to see its methods
3. Open `/sse` in another tab to watch events

### Step 3: Chat with Agents

```bash
# Ask PricingEngine about itself
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "src/services/pricing.py::PricingEngine",
    "message": "What is your role in the order pipeline?"
  }'
```

**Expected response:**
```json
{
  "response": "I am the PricingEngine agent. I calculate order totals by coordinating with DiscountAgent and TaxAgent...",
  "agents_consulted": ["DiscountAgent", "TaxAgent"]
}
```

### Step 4: Run Demo Scenarios

In another terminal:

```bash
# Run the full pipeline demonstration
python scripts/demo_scenarios.py --scenario pipeline

# Watch the output show agent coordination
```

### Step 5: Trigger Reactivity

1. Open `src/services/discounts.py` in an editor
2. Add a comment: `# Added enterprise tier support`
3. Save the file
4. Watch the remora console show:
   ```
   [INFO] File changed: src/services/discounts.py
   [INFO] DiscountEngine agent notified of change
   [INFO] DiscountEngine updated its understanding
   ```

5. Chat with DiscountEngine: "Did you notice the change?"

## Next Steps

- **[Architecture Guide](ARCHITECTURE.md)** - Understand the system design
- **[Web Demo Guide](WEB_DEMO.md)** - Deep dive into dashboard features
- **[LSP Integration](LSP_DEMO.md)** - IDE setup and features
- **[Create Your Own](EXTENDING.md)** - Add custom agents and bundles

## Troubleshooting

### "No nodes discovered"

```bash
# Check discovery paths
remora discover --project-root . -v

# Verify files exist
ls src/services/*.py
```

### "Model endpoint not responding"

```bash
# Test model endpoint
curl http://your-model-server:8000/v1/models

# Should return available models
```

### "Port already in use"

```bash
# Use different port
remora start --project-root . --port 8081
```

## Getting Help

- [Remora v2 Issues](https://github.com/Bullish-Design/remora-v2/issues)
- [Demo Issues](../../issues)
- [Documentation](.)

---

**Ready to see code come alive?** Start at Step 1 above! 🚀
```

**Time:** 30 minutes

**Success Criteria:**
- [ ] Step-by-step instructions
- [ ] Prerequisites clear
- [ ] Troubleshooting included
- [ ] Links to deeper docs

---

## Directory Structure Blueprint

After completing all phases, the repository structure should be:

```
remora-test/
├── README.md                           # Compelling intro
├── remora.yaml                         # V2-compliant config
├── pyproject.toml                      # Updated deps
├── src/
│   ├── main.py                         # Entry point
│   ├── api/
│   │   └── orders.py                   # API handlers
│   ├── models/
│   │   └── order.py                    # Rich data models
│   ├── services/
│   │   ├── base.py                     # Service base classes
│   │   ├── pricing.py                   # PricingEngine (class-based)
│   │   ├── discounts.py                 # DiscountEngine
│   │   ├── tax.py                       # TaxCalculator
│   │   ├── fraud.py                     # FraudDetector
│   │   └── fulfillment/
│   │       └── allocator.py             # FulfillmentAllocator
│   ├── orchestrator/
│   │   └── order_pipeline.py            # Multi-agent orchestration
│   └── utils/
│       └── money.py                     # Utilities
├── bundles/
│   ├── code-agent/
│   │   └── bundle.yaml                  # Enhanced code agent
│   ├── orchestrator/
│   │   └── bundle.yaml                  # Orchestrator agent
│   └── companion/
│       └── bundle.yaml                  # Companion observer
├── queries/
│   └── python.scm                       # Custom tree-sitter queries
├── docs/
│   ├── GETTING_STARTED.md               # Setup guide
│   ├── ARCHITECTURE.md                  # System design
│   ├── API.md                           # API documentation
│   ├── WEB_DEMO.md                      # Dashboard guide
│   └── LSP_DEMO.md                      # IDE integration
├── config/
│   ├── pricing_rules.toml               # TOML agents
│   └── tax_rates.yaml                   # YAML agents
├── scripts/
│   └── demo_scenarios.py                # Interactive demos
├── tests/
│   └── ...                              # Test suite
└── .scratch/
    └── projects/
        └── 03-remora-demo-review/
            ├── K25_REMORA_DEMO_REVIEW.md # Original review
            └── DEMO_REFACTORING_GUIDE.md # This file
```

---

## Summary

This refactoring transforms remora-test from a basic "hello world" demo into a
**comprehensive showcase** of remora-v2's capabilities.

### What Makes This "Wow"

1. **Scale**: 50+ agents vs original 18
2. **Depth**: Classes, methods, inheritance, generics, decorators
3. **Intelligence**: Self-aware agents that answer questions
4. **Coordination**: Multi-agent pipelines with explicit orchestration
5. **Reactivity**: Real-time response to code changes
6. **Multi-Language**: Python + Markdown + TOML + YAML
7. **Completeness**: LSP, web UI, custom bundles, virtual agents

### Time Investment

| Phase | Time | Priority |
|-------|------|----------|
| 1. Foundation | ~65 min | 🔴 Critical |
| 2. Rich Domain | ~165 min | 🔴 Critical |
| 3. Agent Architecture | ~105 min | 🔴 Critical |
| 4. Interactive Demos | ~50 min | 🟡 Important |
| 5. Documentation | ~75 min | 🟡 Important |
| **Total** | **~7-8 hours** | |

### Quick Wins (First 2 Hours)

If time-constrained, prioritize:

1. Fix remora.yaml (15 min)
2. Add markdown/config files (20 min)
3. Create one rich class (30 min)
4. Write demo_scenarios.py (45 min)
5. Update README.md (30 min)

**Result**: Dramatically improved demo in 2 hours.

### Success Metrics

After refactoring, verify:

- [ ] `remora discover` finds 50+ nodes
- [ ] Classes and methods appear as separate agents
- [ ] Chat responses reference other agents
- [ ] Web dashboard shows rich node details
- [ ] Demo scenarios run successfully
- [ ] Code changes trigger agent events
- [ ] Documentation covers all features

---

**Let's make code come alive! 🚀**
