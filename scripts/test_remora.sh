#!/usr/bin/env bash
# Quick smoke test for a running remora instance.
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

echo "=== Nodes ==="
NODES="$(curl -sS "$BASE/api/nodes")"
echo "$NODES" | jq 'length'
echo "First node:"
echo "$NODES" | jq '.[0]'

echo
echo "=== Edges ==="
curl -sS "$BASE/api/edges" | jq 'length'

echo
echo "=== Recent Events ==="
curl -sS "$BASE/api/events?limit=5" | jq 'length'

echo
echo "=== Chat Test ==="
NODE_ID="$(echo "$NODES" | jq -r '[.[] | select(.node_type != "directory")][0].node_id // .[0].node_id')"
echo "Sending message to node: $NODE_ID"
curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$NODE_ID\", \"message\": \"What do you do?\"}" | jq .

echo
echo "Done! Check the web dashboard at $BASE"
