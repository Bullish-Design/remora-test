#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
TIMEOUT_S="${TIMEOUT_S:-40}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-1}"

workdir="$(mktemp -d)"
old_file="$workdir/old_source.py"
candidate_dir="$workdir/new_candidates"
restore_needed=0
restore_target=""
proposal_artifact_file=""

cleanup() {
  if [ "$restore_needed" = "1" ] && [ -n "$restore_target" ] && [ -f "$old_file" ]; then
    cp "$old_file" "$restore_target"
    echo "Restored original file: $restore_target"
  fi
  if [ -n "$proposal_artifact_file" ]; then
    rm -f "$proposal_artifact_file" 2>/dev/null || true
    parent_dir="$(dirname "$proposal_artifact_file")"
    while [ "$parent_dir" != "." ] && [ "$parent_dir" != "/" ]; do
      if ! rmdir "$parent_dir" 2>/dev/null; then
        break
      fi
      parent_dir="$(dirname "$parent_dir")"
    done
  fi
  rm -rf "$workdir"
}
trap cleanup EXIT

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

TARGET_NODE="$(curl -fsS "$BASE/api/nodes" \
  | jq -r '.[] | select(.file_path | endswith("/src/services/pricing.py")) | select(.name=="compute_total") | .node_id' \
  | head -n 1)"

if [ -z "$TARGET_NODE" ] || [ "$TARGET_NODE" = "null" ]; then
  echo "Unable to resolve target node for compute_total" >&2
  exit 1
fi
proposal_artifact_file="${PWD}/${TARGET_NODE#/}"

echo "Triggering proposal for $TARGET_NODE"
start_ts="$(python - <<'PY'
import time
print(time.time())
PY
)"
chat_payload="$(jq -nc --arg node "$TARGET_NODE" --arg message "rewrite_to_magic accept_probe_$(date +%s)" '{node_id:$node, message:$message}')"
curl -fsS -X POST "$BASE/api/chat" \
  -H "Content-Type: application/json" \
  -d "$chat_payload" | jq .

proposal_event=""
for _ in $(seq 1 "$TIMEOUT_S"); do
  proposal_event="$(curl -fsS "$BASE/api/events?limit=500" | jq -c 'first(.[] | select(.event_type=="rewrite_proposal" and (.payload.agent_id // "")=="'"$TARGET_NODE"'" and (.timestamp // 0) >= '"$start_ts"')) // empty' || true)"
  if [ -n "$proposal_event" ] && [ "$proposal_event" != "null" ]; then
    break
  fi
  sleep "$POLL_INTERVAL_S"
done

if [ -z "$proposal_event" ] || [ "$proposal_event" = "null" ]; then
  echo "No rewrite_proposal event found for $TARGET_NODE" >&2
  echo "Recent target events snapshot:" >&2
  curl -fsS "$BASE/api/events?limit=200" | jq '[.[] | select((.payload.agent_id // "")=="'"$TARGET_NODE"'") | {event_type, correlation_id, payload}] | .[0:30]' >&2 || true
  exit 1
fi

proposal_id="$(echo "$proposal_event" | jq -r '.payload.proposal_id // empty')"
echo "Proposal event found: proposal_id=${proposal_id:-unknown}"
diff_payload="$(curl -fsS "$BASE/api/proposals/$TARGET_NODE/diff")"

echo "$diff_payload" | jq .

if ! echo "$diff_payload" | jq -e '.diffs | length > 0' >/dev/null; then
  echo "Proposal diff response had no diffs" >&2
  exit 1
fi

restore_target="$(echo "$diff_payload" | jq -r '.diffs[0].file')"
if [ -z "$restore_target" ] || [ "$restore_target" = "null" ]; then
  echo "Unable to resolve disk file path from proposal diff" >&2
  exit 1
fi

if [ ! -f "$restore_target" ]; then
  first_existing_target="$(echo "$diff_payload" | jq -r '.diffs[].file' | while IFS= read -r p; do
    if [ -f "$p" ]; then
      echo "$p"
      break
    fi
  done)"
  if [ -n "$first_existing_target" ]; then
    restore_target="$first_existing_target"
  fi
fi

cp "$restore_target" "$old_file"
mkdir -p "$candidate_dir"
candidate_count=0
echo "$diff_payload" | jq -r '.diffs[] | select(.file=="'"$restore_target"'") | .new | @base64' | while IFS= read -r encoded; do
  candidate_count=$((candidate_count + 1))
  printf '%s' "$encoded" | base64 -d > "$candidate_dir/new_$candidate_count.txt"
done

restore_needed=1

accept_resp="$(curl -fsS -X POST "$BASE/api/proposals/$TARGET_NODE/accept" -H "Content-Type: application/json" -d '{}')"
echo "$accept_resp" | jq .

if [ "$(echo "$accept_resp" | jq -r '.status // empty')" != "accepted" ]; then
  echo "Proposal accept failed: $accept_resp" >&2
  exit 1
fi

if cmp -s "$restore_target" "$old_file"; then
  echo "Accepted proposal did not mutate target file content" >&2
  exit 1
fi

match_found=0
for candidate in "$candidate_dir"/new_*.txt; do
  if [ ! -f "$candidate" ]; then
    continue
  fi
  if cmp -s "$restore_target" "$candidate"; then
    match_found=1
    break
  fi
done

if [ "$match_found" -ne 1 ]; then
  echo "Accepted proposal mutated file, but content did not match any advertised diff candidate" >&2
  exit 1
fi

events_json="$(curl -fsS "$BASE/api/events?limit=200")"
if ! echo "$events_json" | jq -e '.[] | select(.event_type=="rewrite_accepted" and (.payload.agent_id // "")=="'"$TARGET_NODE"'")' >/dev/null; then
  echo "rewrite_accepted event for target node not found" >&2
  exit 1
fi

if ! echo "$events_json" | jq -e '.[] | select(.event_type=="content_changed")' >/dev/null; then
  echo "No content_changed event found after proposal accept" >&2
  exit 1
fi

echo "test_proposal_accept_flow.sh passed"
