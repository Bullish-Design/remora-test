#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-20}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"

before_count="$(curl -sS "$BASE/api/events?limit=500" | jq '[.[] | select(.event_type=="agent_start" and .agent_id=="demo-review-observer")] | length')"

echo "# demo trigger $(date +%s)" >> src/services/pricing.py

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
