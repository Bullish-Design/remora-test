#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

echo "Checking remora web root..."
curl -sS "$BASE/" >/tmp/remora_ui_index.html

if rg -q "unpkg.com/(graphology|sigma|graphology-layout-forceatlas2)" /tmp/remora_ui_index.html; then
  echo "UI depends on CDN scripts from unpkg.com"
else
  echo "UI does not appear to require unpkg CDN graph scripts"
fi

echo "Checking CDN reachability (unpkg)..."
if curl -sS -I https://unpkg.com/ >/tmp/remora_ui_unpkg_head.txt 2>/dev/null; then
  echo "unpkg reachable"
else
  echo "unpkg NOT reachable from this environment"
  echo "If / is blank in browser, this is expected in offline-restricted environments."
  echo "Use API/script demos instead: scripts/test_demo_runtime.sh, scripts/test_virtual_agents.sh, scripts/test_proposal_flow.sh"
fi
