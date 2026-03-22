#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

before_count="$(curl -sS "$BASE/api/events?limit=200" | jq '[.[] | select(.agent_id=="demo-review-observer")] | length')"

echo "# demo trigger $(date +%s)" >> src/services/pricing.py
sleep 2

after_count="$(curl -sS "$BASE/api/events?limit=200" | jq '[.[] | select(.agent_id=="demo-review-observer")] | length')"

echo "before=$before_count after=$after_count"
if [ "$after_count" -le "$before_count" ]; then
  echo "Expected demo-review-observer activity did not increase" >&2
  exit 1
fi
