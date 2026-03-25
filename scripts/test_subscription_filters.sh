#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

SRC_OBSERVER="demo-src-filter-observer"
DOCS_OBSERVER="demo-docs-filter-observer"

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

nodes_json="$(curl -fsS "$BASE/api/nodes")"
for observer in "$SRC_OBSERVER" "$DOCS_OBSERVER"; do
  if ! echo "$nodes_json" | jq -e '.[] | select(.node_id=="'"$observer"'")' >/dev/null; then
    echo "Missing virtual observer node: $observer" >&2
    echo "$nodes_json" | jq '[.[] | select(.node_type=="virtual") | .node_id]' >&2
    exit 1
  fi
done

export SRC_PATH="$(realpath src/services/pricing.py)"
export DOCS_PATH="$(realpath docs/architecture.md)"

devenv shell -- python - <<'PY'
import os
from remora.core.events import NodeChangedEvent, SubscriptionPattern

src_path = os.environ["SRC_PATH"]
docs_path = os.environ["DOCS_PATH"]

src_pattern = SubscriptionPattern(event_types=["node_changed"], path_glob="src/**")
docs_pattern = SubscriptionPattern(event_types=["node_changed"], path_glob="docs/**")

src_event = NodeChangedEvent(node_id="src-node", old_hash="a", new_hash="b", file_path=src_path)
docs_event = NodeChangedEvent(node_id="docs-node", old_hash="a", new_hash="b", file_path=docs_path)

assert src_pattern.matches(src_event), "src/** should match absolute src path"
assert not src_pattern.matches(docs_event), "src/** should not match docs path"
assert docs_pattern.matches(docs_event), "docs/** should match absolute docs path"
assert not docs_pattern.matches(src_event), "docs/** should not match src path"

print("path_glob_matching_ok")
PY

echo "test_subscription_filters.sh passed"
