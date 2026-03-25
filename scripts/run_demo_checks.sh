#!/usr/bin/env bash
set -euo pipefail

scripts/test_demo_runtime.sh
REQUIRE_COMPANION="${REQUIRE_COMPANION:-0}" scripts/test_virtual_agents.sh
scripts/test_proposal_flow.sh
scripts/test_search.sh

echo "All demo checks passed"
