#!/usr/bin/env bash
set -euo pipefail

scripts/test_demo_runtime.sh
scripts/test_virtual_agents.sh
scripts/test_proposal_flow.sh

if [ "${RUN_SEARCH:-0}" = "1" ]; then
  scripts/test_search.sh
fi

echo "All demo checks passed"
