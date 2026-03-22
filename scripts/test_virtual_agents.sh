#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-20}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"

virtual_nodes_json="$(curl -sS "$BASE/api/nodes" | jq '[.[] | select(.node_type=="virtual") | .node_id]')"
if ! echo "$virtual_nodes_json" | jq -e '. | index("demo-review-observer")' >/dev/null; then
  echo "Virtual node demo-review-observer not found. Restart remora with a fresh .remora state." >&2
  echo "Detected virtual nodes: $virtual_nodes_json" >&2
  exit 1
fi

before_count="$(curl -sS "$BASE/api/events?limit=500" | jq '[.[] | select(.event_type=="agent_start" and .agent_id=="demo-review-observer")] | length')"

trigger_dir="src/.remora_demo_trigger"
mkdir -p "$trigger_dir"
trigger_file="$trigger_dir/trigger_$(date +%s).py"

cleanup() {
  rm -f "$trigger_file"
  rmdir "$trigger_dir" 2>/dev/null || true
}
trap cleanup EXIT

cat > "$trigger_file" <<'PY'
def _remora_demo_trigger() -> int:
    return 1
PY

after_count="$before_count"
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT_S" ]; do
  sleep "$POLL_INTERVAL_S"
  elapsed=$((elapsed + POLL_INTERVAL_S))
  after_count="$(curl -sS "$BASE/api/events?limit=500" | jq '[.[] | select(.event_type=="agent_start" and .agent_id=="demo-review-observer")] | length')"
  if [ "$after_count" -gt "$before_count" ]; then
    break
  fi
done

echo "before=$before_count after=$after_count"
if [ "$after_count" -le "$before_count" ]; then
  echo "Expected demo-review-observer agent_start count did not increase within ${TIMEOUT_S}s" >&2
  exit 1
fi
