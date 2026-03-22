#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TARGET_NODE="${TARGET_NODE:-}"

if [ -z "$TARGET_NODE" ]; then
  TARGET_NODE="$(curl -sS "$BASE/api/nodes" \
    | jq -r '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total") | .node_id' \
    | head -n 1)"
fi

if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for compute_total" >&2
  exit 1
fi

curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"rewrite_to_magic\"}" | jq .

found=""
for _ in $(seq 1 20); do
  found="$(curl -sS "$BASE/api/proposals" | jq -c '.[] | select(.node_id=="'"$TARGET_NODE"'" )' || true)"
  if [ -n "$found" ]; then
    break
  fi
  sleep 1
done

if [ -z "$found" ]; then
  echo "No proposal found for $TARGET_NODE" >&2
  exit 1
fi

echo "Proposal found: $found"

curl -sS "$BASE/api/proposals/$TARGET_NODE/diff" | jq .

curl -sS -X POST "$BASE/api/proposals/$TARGET_NODE/reject" \
  -H "Content-Type: application/json" \
  -d '{"feedback":"demo reviewed and rejected intentionally"}' | jq .
