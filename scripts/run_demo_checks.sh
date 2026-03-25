#!/usr/bin/env bash
set -euo pipefail

scripts/test_demo_runtime.sh
REQUIRE_COMPANION="${REQUIRE_COMPANION:-0}" scripts/test_virtual_agents.sh
REQUIRE_COMPANION="${REQUIRE_COMPANION:-1}" scripts/test_reflection_pipeline.sh
scripts/test_subscription_filters.sh
scripts/test_proposal_flow.sh
scripts/test_proposal_accept_flow.sh
scripts/test_multilang_discovery.sh
scripts/test_sse_contract.sh
scripts/test_cursor_focus.sh
scripts/test_relationship_tools.sh
scripts/test_search.sh
scripts/test_lsp_startup.sh

if [ "${RUN_GUARDRAILS_CHECK:-0}" = "1" ]; then
  REQUIRE_OVERFLOW="${REQUIRE_OVERFLOW:-0}" scripts/test_runtime_guardrails.sh
fi

if [ "${RUN_LSP_BRIDGE_CHECK:-0}" = "1" ]; then
  REQUIRE_LSP_BRIDGE="${REQUIRE_LSP_BRIDGE:-0}" scripts/test_lsp_event_bridge.sh
fi

echo "All demo checks passed"
