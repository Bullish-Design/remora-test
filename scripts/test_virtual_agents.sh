#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-20}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"
EVENT_LIMIT="${EVENT_LIMIT:-500}"
REQUIRE_COMPANION="${REQUIRE_COMPANION:-0}"

workdir="$(mktemp -d)"
before_events="$workdir/events_before.json"
after_events="$workdir/events_after.json"

cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

fetch_events() {
  curl -fsS "$BASE/api/events?limit=$EVENT_LIMIT"
}

count_query() {
  local file="$1"
  local query="$2"
  jq -r "$query" "$file"
}

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

virtual_nodes_json="$(curl -fsS "$BASE/api/nodes" | jq '[.[] | select(.node_type=="virtual") | .node_id]')"
if ! echo "$virtual_nodes_json" | jq -e '. | index("demo-review-observer")' >/dev/null; then
  echo "Virtual node demo-review-observer not found. Restart remora with a fresh .remora state." >&2
  echo "Detected virtual nodes: $virtual_nodes_json" >&2
  exit 1
fi
if ! echo "$virtual_nodes_json" | jq -e '. | index("demo-companion-observer")' >/dev/null; then
  echo "Virtual node demo-companion-observer not found. Restart remora with a fresh .remora state." >&2
  echo "Detected virtual nodes: $virtual_nodes_json" >&2
  exit 1
fi

fetch_events > "$before_events"

before_review_start="$(count_query "$before_events" '[.[] | select(.event_type=="agent_start" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
before_review_turn_complete="$(count_query "$before_events" '[.[] | select(.event_type=="turn_complete" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
before_review_model_response="$(count_query "$before_events" '[.[] | select(.event_type=="model_response" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
before_review_output="$(count_query "$before_events" '[.[] | select(.event_type=="agent_complete" and (.payload.agent_id // "")=="demo-review-observer" and (((.payload.user_message // "") != "") or ((.payload.result_summary // "") != "") or ((.payload.full_response // "") != "")))] | length')"
before_review_tool_activity="$(count_query "$before_events" '[.[] | select(((.event_type=="turn_complete" or .event_type=="model_response") and (.payload.agent_id // "")=="demo-review-observer" and ((.payload.tool_calls_count // 0) > 0)))] | length')"

before_companion_start="$(count_query "$before_events" '[.[] | select(.event_type=="agent_start" and (.payload.agent_id // "")=="demo-companion-observer")] | length')"
before_companion_turn_complete="$(count_query "$before_events" '[.[] | select(.event_type=="turn_complete" and (.payload.agent_id // "")=="demo-companion-observer")] | length')"
before_companion_tool_activity="$(count_query "$before_events" '[.[] | select(((.event_type=="turn_complete" or .event_type=="model_response") and (.payload.agent_id // "")=="demo-companion-observer" and ((.payload.tool_calls_count // 0) > 0)))] | length')"
before_turn_digested="$(count_query "$before_events" '[.[] | select(.event_type=="turn_digested")] | length')"

max_review_start="$before_review_start"
max_review_turn_complete="$before_review_turn_complete"
max_review_model_response="$before_review_model_response"
max_review_output="$before_review_output"
max_review_tool_activity="$before_review_tool_activity"
max_companion_start="$before_companion_start"
max_companion_turn_complete="$before_companion_turn_complete"
max_companion_tool_activity="$before_companion_tool_activity"
max_turn_digested="$before_turn_digested"

trigger_dir="src/.remora_demo_trigger"
mkdir -p "$trigger_dir"
trigger_file="$trigger_dir/trigger_$(date +%s).py"
trap 'rm -f "$trigger_file"; rmdir "$trigger_dir" 2>/dev/null || true; cleanup' EXIT

cat > "$trigger_file" <<'PY'
def _remora_demo_trigger() -> int:
    return 1
PY

review_ok=0
companion_ok=0
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT_S" ]; do
  printf "# remora_demo_tick %s\n" "$elapsed" >> "$trigger_file"
  sleep "$POLL_INTERVAL_S"
  elapsed=$((elapsed + POLL_INTERVAL_S))

  fetch_events > "$after_events"

  after_review_start="$(count_query "$after_events" '[.[] | select(.event_type=="agent_start" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
  after_review_turn_complete="$(count_query "$after_events" '[.[] | select(.event_type=="turn_complete" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
  after_review_model_response="$(count_query "$after_events" '[.[] | select(.event_type=="model_response" and (.payload.agent_id // "")=="demo-review-observer")] | length')"
  after_review_output="$(count_query "$after_events" '[.[] | select(.event_type=="agent_complete" and (.payload.agent_id // "")=="demo-review-observer" and (((.payload.user_message // "") != "") or ((.payload.result_summary // "") != "") or ((.payload.full_response // "") != "")))] | length')"
  after_review_tool_activity="$(count_query "$after_events" '[.[] | select(((.event_type=="turn_complete" or .event_type=="model_response") and (.payload.agent_id // "")=="demo-review-observer" and ((.payload.tool_calls_count // 0) > 0)))] | length')"

  after_companion_start="$(count_query "$after_events" '[.[] | select(.event_type=="agent_start" and (.payload.agent_id // "")=="demo-companion-observer")] | length')"
  after_companion_turn_complete="$(count_query "$after_events" '[.[] | select(.event_type=="turn_complete" and (.payload.agent_id // "")=="demo-companion-observer")] | length')"
  after_companion_tool_activity="$(count_query "$after_events" '[.[] | select(((.event_type=="turn_complete" or .event_type=="model_response") and (.payload.agent_id // "")=="demo-companion-observer" and ((.payload.tool_calls_count // 0) > 0)))] | length')"
  after_turn_digested="$(count_query "$after_events" '[.[] | select(.event_type=="turn_digested")] | length')"

  if [ "$after_review_start" -gt "$max_review_start" ]; then max_review_start="$after_review_start"; fi
  if [ "$after_review_turn_complete" -gt "$max_review_turn_complete" ]; then max_review_turn_complete="$after_review_turn_complete"; fi
  if [ "$after_review_model_response" -gt "$max_review_model_response" ]; then max_review_model_response="$after_review_model_response"; fi
  if [ "$after_review_output" -gt "$max_review_output" ]; then max_review_output="$after_review_output"; fi
  if [ "$after_review_tool_activity" -gt "$max_review_tool_activity" ]; then max_review_tool_activity="$after_review_tool_activity"; fi
  if [ "$after_companion_start" -gt "$max_companion_start" ]; then max_companion_start="$after_companion_start"; fi
  if [ "$after_companion_turn_complete" -gt "$max_companion_turn_complete" ]; then max_companion_turn_complete="$after_companion_turn_complete"; fi
  if [ "$after_companion_tool_activity" -gt "$max_companion_tool_activity" ]; then max_companion_tool_activity="$after_companion_tool_activity"; fi
  if [ "$after_turn_digested" -gt "$max_turn_digested" ]; then max_turn_digested="$after_turn_digested"; fi

  if [ "$max_review_turn_complete" -gt "$before_review_turn_complete" ] &&
     [ "$max_review_model_response" -gt "$before_review_model_response" ] &&
     { [ "$max_review_output" -gt "$before_review_output" ] || [ "$max_review_tool_activity" -gt "$before_review_tool_activity" ]; }; then
    review_ok=1
  fi

  if [ "$max_companion_turn_complete" -gt "$before_companion_turn_complete" ] &&
     { [ "$max_companion_tool_activity" -gt "$before_companion_tool_activity" ] || [ "$max_turn_digested" -gt "$before_turn_digested" ]; }; then
    companion_ok=1
  fi

  if [ "$review_ok" -eq 1 ] && { [ "$REQUIRE_COMPANION" != "1" ] || [ "$companion_ok" -eq 1 ]; }; then
    break
  fi
done

if [ ! -f "$after_events" ]; then
  fetch_events > "$after_events"
fi

after_review_start="$max_review_start"
after_review_turn_complete="$max_review_turn_complete"
after_review_model_response="$max_review_model_response"
after_review_output="$max_review_output"
after_review_tool_activity="$max_review_tool_activity"
after_companion_start="$max_companion_start"
after_companion_turn_complete="$max_companion_turn_complete"
after_companion_tool_activity="$max_companion_tool_activity"
after_turn_digested="$max_turn_digested"

echo "review_start: before=$before_review_start after=$after_review_start"
echo "review_turn_complete: before=$before_review_turn_complete after=$after_review_turn_complete"
echo "review_model_response: before=$before_review_model_response after=$after_review_model_response"
echo "review_output: before=$before_review_output after=$after_review_output"
echo "review_tool_activity: before=$before_review_tool_activity after=$after_review_tool_activity"
echo "companion_start: before=$before_companion_start after=$after_companion_start"
echo "companion_turn_complete: before=$before_companion_turn_complete after=$after_companion_turn_complete"
echo "companion_tool_activity: before=$before_companion_tool_activity after=$after_companion_tool_activity"
echo "turn_digested: before=$before_turn_digested after=$after_turn_digested"

if [ "$review_ok" -ne 1 ]; then
  echo "Review observer behavior check failed within ${TIMEOUT_S}s." >&2
  echo "Expected: model_response + turn_complete growth, plus output/tool activity evidence." >&2
  echo "Recent review observer events:" >&2
  jq '[.[] | select((.payload.agent_id // "")=="demo-review-observer") | {event_type, payload}] | .[0:20]' "$after_events" >&2
  exit 1
fi

if [ "$REQUIRE_COMPANION" = "1" ] && [ "$companion_ok" -ne 1 ]; then
  echo "Companion observer behavior check failed within ${TIMEOUT_S}s." >&2
  echo "Expected: companion turn_complete growth and digest/tool evidence." >&2
  echo "Note: if no turn_digested events are emitted by runtime, companion may never trigger." >&2
  echo "Set REQUIRE_COMPANION=0 to run review-only mode (default)." >&2
  echo "Recent companion-related events:" >&2
  jq '[.[] | select((.payload.agent_id // "")=="demo-companion-observer" or .event_type=="turn_digested") | {event_type, payload}] | .[0:30]' "$after_events" >&2
  exit 1
fi

echo "test_virtual_agents.sh passed"
