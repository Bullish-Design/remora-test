#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TARGET_NODE="${TARGET_NODE:-}"

health="$(curl -sS "$BASE/api/health")"
echo "$health" | jq . >/dev/null
if [ "$(echo "$health" | jq -r '.status // empty')" != "ok" ]; then
  echo "Health check failed: expected status=ok" >&2
  exit 1
fi

nodes_json="$(curl -sS "$BASE/api/nodes")"
echo "$nodes_json" | jq . >/dev/null
nodes_count="$(echo "$nodes_json" | jq 'length')"
if [ "$nodes_count" -le 0 ]; then
  echo "Expected non-empty /api/nodes" >&2
  exit 1
fi

curl -sS "$BASE/api/edges" | jq . >/dev/null
curl -sS "$BASE/api/events?limit=5" | jq . >/dev/null

if [ -z "$TARGET_NODE" ]; then
  TARGET_NODE="$(echo "$nodes_json" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
fi

if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve TARGET_NODE for /api/chat" >&2
  exit 1
fi

chat_resp="$(curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"demo_echo\"}")"

echo "$chat_resp" | jq . >/dev/null
if [ "$(echo "$chat_resp" | jq -r '.status // empty')" != "sent" ]; then
  echo "Expected /api/chat status=sent" >&2
  exit 1
fi

virtual_count="$(echo "$nodes_json" | jq '[.[] | select(.node_type=="virtual")] | length')"
if [ "$virtual_count" -lt 2 ]; then
  echo "Expected at least 2 virtual nodes" >&2
  exit 1
fi

echo "test_demo_runtime.sh passed"
