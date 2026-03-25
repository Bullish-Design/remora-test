#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
TARGET_NODE="$(echo "$nodes_json" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for SSE contract test" >&2
  exit 1
fi

send_chat() {
  local message="$1"
  local payload
  payload="$(jq -nc --arg node "$TARGET_NODE" --arg message "$message" '{node_id:$node, message:$message}')"
  curl -fsS -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d "$payload" >/dev/null
}

token1="sse_probe_one_$(date +%s)"
token2="sse_probe_two_$(date +%s)"

send_chat "demo_echo $token1"
sleep 2

replay_out="$(curl -fsS "$BASE/sse?replay=200&once=true")"
replay_clean="$(printf '%s' "$replay_out" | tr -d '\r')"
if ! printf '%s' "$replay_clean" | rg -q "$token1"; then
  echo "SSE replay output did not include first probe token" >&2
  exit 1
fi

last_id="$(printf '%s\n' "$replay_clean" | awk '/^id: / {id=substr($0,5)} END {print id}')"
if [ -z "$last_id" ]; then
  echo "Unable to resolve Last-Event-ID from replay output" >&2
  exit 1
fi

send_chat "demo_echo $token2"
sleep 2

resume_out="$(curl -fsS -H "Last-Event-ID: $last_id" "$BASE/sse?once=true")"
resume_clean="$(printf '%s' "$resume_out" | tr -d '\r')"
if ! printf '%s' "$resume_clean" | rg -q "$token2"; then
  echo "SSE resume output did not include second probe token" >&2
  printf '%s\n' "$resume_clean" >&2
  exit 1
fi

echo "test_sse_contract.sh passed"
