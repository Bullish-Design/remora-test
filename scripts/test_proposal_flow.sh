#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TARGET_NODE="${TARGET_NODE:-}"
TIMEOUT_S="${TIMEOUT_S:-25}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"

if [ -z "$TARGET_NODE" ]; then
  TARGET_NODE="$(curl -sS "$BASE/api/nodes" \
    | jq -r '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total") | .node_id' \
    | head -n 1)"
fi

if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for compute_total" >&2
  exit 1
fi

start_ts="$(python - <<'PY'
import time
print(time.time())
PY
)"

curl -sS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$TARGET_NODE\", \"message\": \"rewrite_to_magic reject_probe_$(date +%s)\"}" | jq .

proposal_event=""
for _ in $(seq 1 "$TIMEOUT_S"); do
  proposal_event="$(curl -sS "$BASE/api/events?limit=400" | jq -c 'first(.[] | select(.event_type=="rewrite_proposal" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and (.timestamp // 0) >= '"$start_ts"')) // empty' || true)"
  if [ -n "$proposal_event" ] && [ "$proposal_event" != "null" ]; then
    break
  fi
  sleep "$POLL_INTERVAL_S"
done

if [ -z "$proposal_event" ] || [ "$proposal_event" = "null" ]; then
  echo "No rewrite_proposal event found for $TARGET_NODE" >&2
  curl -sS "$BASE/api/events?limit=200" | jq '[.[] | select((.payload.agent_id // "")=="'"$TARGET_NODE"'") | {event_type, correlation_id, payload}] | .[0:30]' >&2 || true
  exit 1
fi

proposal_id="$(echo "$proposal_event" | jq -r '.payload.proposal_id // empty')"
echo "Proposal event found: proposal_id=${proposal_id:-unknown}"

curl -sS "$BASE/api/proposals/$TARGET_NODE/diff" | jq .

curl -sS -X POST "$BASE/api/proposals/$TARGET_NODE/reject" \
  -H "Content-Type: application/json" \
  -d '{"feedback":"demo reviewed and rejected intentionally"}' | jq .
