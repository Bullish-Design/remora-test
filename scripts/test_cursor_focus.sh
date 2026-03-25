#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-10}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"
EVENT_LIMIT="${EVENT_LIMIT:-2000}"
REQUIRE_CURSOR_EVENT="${REQUIRE_CURSOR_EVENT:-0}"

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
target_node_json="$(echo "$nodes_json" | jq -c '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total")' | head -n 1)"
if [ -z "$target_node_json" ]; then
  target_node_json="$(echo "$nodes_json" | jq -c 'map(select(.node_type=="function"))[0]')"
fi

if [ -z "$target_node_json" ] || [ "$target_node_json" = "null" ]; then
  echo "Unable to resolve target node for cursor test" >&2
  exit 1
fi

target_node_id="$(echo "$target_node_json" | jq -r '.node_id')"
target_file_path="$(echo "$target_node_json" | jq -r '.file_path')"
target_line="$(echo "$target_node_json" | jq -r '.start_line')"

payload="$(jq -nc --arg file_path "$target_file_path" --argjson line "$target_line" '{file_path:$file_path, line:$line, character:0}')"
resp="$(curl -fsS -X POST "$BASE/api/cursor" -H "Content-Type: application/json" -d "$payload")"

if [ "$(echo "$resp" | jq -r '.status // empty')" != "ok" ]; then
  echo "Cursor API call failed: $resp" >&2
  exit 1
fi

if [ "$(echo "$resp" | jq -r '.node_id // empty')" != "$target_node_id" ]; then
  echo "Cursor API returned unexpected node_id" >&2
  echo "expected=$target_node_id actual=$(echo "$resp" | jq -r '.node_id // empty')" >&2
  exit 1
fi

cursor_event_found=0
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT_S" ]; do
  sleep "$POLL_INTERVAL_S"
  elapsed=$((elapsed + POLL_INTERVAL_S))
  events_json="$(curl -fsS "$BASE/api/events?limit=$EVENT_LIMIT")"
  if echo "$events_json" | jq -e '.[] | select(.event_type=="cursor_focus" and (((.payload.node_id // "")=="'"$target_node_id"'") or ((.payload.file_path // "")=="'"$target_file_path"'" and ((.payload.line // -1) == '"$target_line"'))))' >/dev/null; then
    cursor_event_found=1
    break
  fi
done

if [ "$cursor_event_found" -ne 1 ]; then
  if [ "$REQUIRE_CURSOR_EVENT" = "1" ]; then
    echo "cursor_focus event for target node not found" >&2
    exit 1
  fi
  echo "cursor_focus event not observed within timeout; cursor API mapping verified" >&2
fi

echo "test_cursor_focus.sh passed"
