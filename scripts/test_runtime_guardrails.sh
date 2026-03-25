#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
BURST_COUNT="${BURST_COUNT:-80}"
REQUIRE_OVERFLOW="${REQUIRE_OVERFLOW:-0}"

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
TARGET_NODE="$(echo "$nodes_json" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for guardrail test" >&2
  exit 1
fi

health_before="$(curl -fsS "$BASE/api/health")"
overflow_before="$(echo "$health_before" | jq -r '.metrics.actor_inbox_overflow_total // 0')"
dropped_new_before="$(echo "$health_before" | jq -r '.metrics.actor_inbox_dropped_new_total // 0')"

for i in $(seq 1 "$BURST_COUNT"); do
  msg="guardrail_burst_${i}_$(date +%s%N)"
  payload="$(jq -nc --arg node "$TARGET_NODE" --arg message "$msg" '{node_id:$node, message:$message}')"
  curl -sS -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d "$payload" >/dev/null &
done
wait
sleep 2

health_after="$(curl -fsS "$BASE/api/health")"
overflow_after="$(echo "$health_after" | jq -r '.metrics.actor_inbox_overflow_total // 0')"
dropped_new_after="$(echo "$health_after" | jq -r '.metrics.actor_inbox_dropped_new_total // 0')"

echo "overflow: before=$overflow_before after=$overflow_after"
echo "dropped_new: before=$dropped_new_before after=$dropped_new_after"

delta_overflow=$((overflow_after - overflow_before))
if [ "$REQUIRE_OVERFLOW" = "1" ] && [ "$delta_overflow" -le 0 ]; then
  echo "Expected overflow growth but none observed. Start runtime with remora.stress.yaml and retry." >&2
  exit 1
fi

if ! echo "$health_after" | jq -e '.metrics | has("actor_inbox_overflow_total") and has("pending_inbox_items") and has("active_actors")' >/dev/null; then
  echo "Health metrics payload missing expected guardrail fields" >&2
  echo "$health_after" | jq . >&2
  exit 1
fi

echo "test_runtime_guardrails.sh passed"
