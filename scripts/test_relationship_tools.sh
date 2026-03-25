#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-20}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"
EVENT_LIMIT="${EVENT_LIMIT:-400}"

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
TARGET_NODE="$(echo "$nodes_json" | jq -r '.[] | select(.file_path | endswith("/src/api/orders.py")) | select(.name=="create_order") | .node_id' | head -n 1)"
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  TARGET_NODE="$(echo "$nodes_json" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
fi
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target function node for relationship tool check" >&2
  exit 1
fi

before_events="$(curl -fsS "$BASE/api/events?limit=$EVENT_LIMIT")"
before_count="$(echo "$before_events" | jq '[.[] | select(.event_type=="remora_tool_result" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and (.payload.tool_name // "")=="show_dependencies")] | length')"

payload="$(jq -nc --arg node "$TARGET_NODE" --arg message "show_dependencies" '{node_id:$node, message:$message}')"
chat_resp="$(curl -fsS -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d "$payload")"
if [ "$(echo "$chat_resp" | jq -r '.status // empty')" != "sent" ]; then
  echo "Chat send failed: $chat_resp" >&2
  exit 1
fi

tool_seen=0
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT_S" ]; do
  sleep "$POLL_INTERVAL_S"
  elapsed=$((elapsed + POLL_INTERVAL_S))

  events_json="$(curl -fsS "$BASE/api/events?limit=$EVENT_LIMIT")"
  after_count="$(echo "$events_json" | jq '[.[] | select(.event_type=="remora_tool_result" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and (.payload.tool_name // "")=="show_dependencies")] | length')"
  if [ "$after_count" -gt "$before_count" ]; then
    tool_seen=1
    latest_preview="$(echo "$events_json" | jq -r '[.[] | select(.event_type=="remora_tool_result" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and (.payload.tool_name // "")=="show_dependencies")][0].payload.output_preview // ""')"
    echo "latest_tool_output_preview=$latest_preview"
    break
  fi
done

if [ "$tool_seen" -ne 1 ]; then
  echo "Did not observe show_dependencies tool execution for $TARGET_NODE" >&2
  echo "$events_json" | jq '[.[] | select((.payload.agent_id // "")=="'"$TARGET_NODE"'") | {event_type, payload}] | .[0:35]' >&2
  exit 1
fi

echo "test_relationship_tools.sh passed"
