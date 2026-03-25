#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-30}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"
EVENT_LIMIT="${EVENT_LIMIT:-500}"
REQUIRE_COMPANION="${REQUIRE_COMPANION:-1}"

workdir="$(mktemp -d)"
after_events="$workdir/after_events.json"

cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

fetch_events() {
  curl -fsS "$BASE/api/events?limit=$EVENT_LIMIT"
}

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
TARGET_NODE="$(echo "$nodes_json" | jq -r '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total") | .node_id' | head -n 1)"
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  TARGET_NODE="$(echo "$nodes_json" | jq -r 'map(select(.node_type=="function"))[0].node_id')"
fi
if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target function node for reflection test" >&2
  exit 1
fi

probe_token="reflection_probe_$(date +%s)"
chat_payload="$(jq -nc --arg node "$TARGET_NODE" --arg message "Please review this function and respond briefly. token=$probe_token" '{node_id:$node, message:$message}')"
chat_resp="$(curl -fsS -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d "$chat_payload")"
if [ "$(echo "$chat_resp" | jq -r '.status // empty')" != "sent" ]; then
  echo "Chat send failed: $chat_resp" >&2
  exit 1
fi

primary_ok=0
reflection_ok=0
turn_digested_ok=0
companion_ok=0
probe_corr=""
elapsed=0

while [ "$elapsed" -lt "$TIMEOUT_S" ]; do
  sleep "$POLL_INTERVAL_S"
  elapsed=$((elapsed + POLL_INTERVAL_S))
  fetch_events > "$after_events"

  if [ -z "$probe_corr" ]; then
    probe_corr="$(jq -r 'first(.[] | select(.event_type=="agent_complete" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and ((.tags // []) | index("primary")) != null and ((.payload.user_message // "") | contains("'"$probe_token"'"))).correlation_id // empty)' "$after_events")"
  fi

  if [ -n "$probe_corr" ]; then
    primary_ok=1
    if jq -e '.[] | select((.correlation_id // "")=="'"$probe_corr"'" and .event_type=="agent_complete" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and ((.tags // []) | index("reflection")) != null)' "$after_events" >/dev/null; then
      reflection_ok=1
    fi
    if jq -e '.[] | select((.correlation_id // "")=="'"$probe_corr"'" and .event_type=="turn_digested" and (.payload.agent_id // "")=="'"$TARGET_NODE"'")' "$after_events" >/dev/null; then
      turn_digested_ok=1
    fi
    if jq -e '.[] | select((.correlation_id // "")=="'"$probe_corr"'" and ((.event_type=="turn_complete" or .event_type=="agent_complete") and (.payload.agent_id // "")=="demo-companion-observer"))' "$after_events" >/dev/null; then
      companion_ok=1
    fi
  fi

  if [ "$primary_ok" -eq 1 ] && [ "$reflection_ok" -eq 1 ] && [ "$turn_digested_ok" -eq 1 ] && { [ "$REQUIRE_COMPANION" != "1" ] || [ "$companion_ok" -eq 1 ]; }; then
    break
  fi
done

encoded_node="$(printf '%s' "$TARGET_NODE" | jq -sRr @uri)"
companion_payload="$(curl -fsS "$BASE/api/nodes/$encoded_node/companion" || true)"

echo "target_node=$TARGET_NODE probe_corr=${probe_corr:-none}"
echo "primary_ok=$primary_ok reflection_ok=$reflection_ok turn_digested_ok=$turn_digested_ok companion_ok=$companion_ok"
echo "companion_payload=$companion_payload"

if [ "$primary_ok" -ne 1 ]; then
  echo "Did not observe primary completion for probe token" >&2
  jq '[.[] | select((.payload.agent_id // "")=="'"$TARGET_NODE"'" and ((.payload.user_message // "") | contains("'"$probe_token"'"))) | {event_type, tags, correlation_id, payload}] | .[0:30]' "$after_events" >&2
  exit 1
fi

if [ "$reflection_ok" -ne 1 ]; then
  echo "Did not observe reflection completion for probe correlation" >&2
  jq '[.[] | select((.correlation_id // "")=="'"$probe_corr"'" and (.payload.agent_id // "")=="'"$TARGET_NODE"'") | {event_type, tags, correlation_id, payload}] | .[0:40]' "$after_events" >&2
  exit 1
fi

if [ "$turn_digested_ok" -ne 1 ]; then
  echo "Did not observe turn_digested for probe correlation" >&2
  jq '[.[] | select((.correlation_id // "")=="'"$probe_corr"'" and ((.payload.agent_id // "")=="'"$TARGET_NODE"'" or .event_type=="turn_digested")) | {event_type, tags, correlation_id, payload}] | .[0:40]' "$after_events" >&2
  exit 1
fi

if [ "$REQUIRE_COMPANION" = "1" ] && [ "$companion_ok" -ne 1 ]; then
  echo "Companion observer did not complete for probe correlation" >&2
  jq '[.[] | select((.correlation_id // "")=="'"$probe_corr"'" and ((.payload.agent_id // "")=="demo-companion-observer" or .event_type=="turn_digested")) | {event_type, tags, correlation_id, payload}] | .[0:40]' "$after_events" >&2
  exit 1
fi

echo "test_reflection_pipeline.sh passed"
