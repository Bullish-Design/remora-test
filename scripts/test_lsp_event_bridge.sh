#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
PROJECT_ROOT="${PROJECT_ROOT:-.}"
TIMEOUT_S="${TIMEOUT_S:-25}"
REQUIRE_LSP_BRIDGE="${REQUIRE_LSP_BRIDGE:-0}"
EVENT_LIMIT="${EVENT_LIMIT:-500}"
LSP_WARMUP_S="${LSP_WARMUP_S:-8}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROBE_SCRIPT="$SCRIPT_DIR/lsp_event_bridge_probe.py"

if [ -n "${DEVENV_PROFILE:-}" ]; then
  PY_RUNNER=(python)
else
  PY_RUNNER=(devenv shell -- python)
fi

"${PY_RUNNER[@]}" "$PROBE_SCRIPT" \
  --base "$BASE" \
  --project-root "$PROJECT_ROOT" \
  --timeout-s "$TIMEOUT_S" \
  --event-limit "$EVENT_LIMIT" \
  --warmup-s "$LSP_WARMUP_S" \
  --require-lsp-bridge "$REQUIRE_LSP_BRIDGE"
