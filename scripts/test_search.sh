#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
QUERY="${QUERY:-compute_total}"
COLLECTION="${COLLECTION:-code}"
TOP_K="${TOP_K:-5}"
MODE="${MODE:-hybrid}"

workdir="$(mktemp -d)"
health_json="$workdir/health.json"
search_json="$workdir/search.json"
index_log="$workdir/index.log"

cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

if ! curl -fsS "$BASE/api/health" >"$health_json"; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

if [ "$(jq -r '.status // empty' "$health_json")" != "ok" ]; then
  echo "Runtime health endpoint did not return status=ok." >&2
  jq . "$health_json" >&2 || cat "$health_json" >&2
  exit 1
fi

echo "Indexing project before search query..."
if ! devenv shell -- remora index --project-root . >"$index_log" 2>&1; then
  echo "remora index failed. Last output:" >&2
  tail -n 40 "$index_log" >&2 || true
  exit 1
fi

payload="$(jq -nc \
  --arg query "$QUERY" \
  --arg collection "$COLLECTION" \
  --arg mode "$MODE" \
  --argjson top_k "$TOP_K" \
  '{query:$query, collection:$collection, top_k:$top_k, mode:$mode}')"

http_code="$(curl -sS -o "$search_json" -w '%{http_code}' -X POST "$BASE/api/search" \
  -H "Content-Type: application/json" \
  -d "$payload")"

if [ "$http_code" != "200" ]; then
  echo "Search request failed with HTTP $http_code." >&2
  if [ -s "$search_json" ]; then
    jq . "$search_json" >&2 || cat "$search_json" >&2
  fi
  if [ "$http_code" = "503" ]; then
    echo "Semantic search is not configured. Install remora[search], run embeddy, and set REMORA_EMBEDDY_URL." >&2
  fi
  exit 1
fi

if ! jq . "$search_json" >/dev/null; then
  echo "Search response was not valid JSON." >&2
  cat "$search_json" >&2
  exit 1
fi

if ! jq -e \
  'has("results") and has("query") and has("collection") and has("mode") and has("total_results") and has("elapsed_ms")' \
  "$search_json" >/dev/null; then
  echo "Search response missing required keys." >&2
  jq . "$search_json" >&2
  exit 1
fi

if [ "$(jq -r '.query' "$search_json")" != "$QUERY" ]; then
  echo "Search response query mismatch." >&2
  jq . "$search_json" >&2
  exit 1
fi

if [ "$(jq -r '.collection' "$search_json")" != "$COLLECTION" ]; then
  echo "Search response collection mismatch." >&2
  jq . "$search_json" >&2
  exit 1
fi

if [ "$(jq -r '.mode' "$search_json")" != "$MODE" ]; then
  echo "Search response mode mismatch." >&2
  jq . "$search_json" >&2
  exit 1
fi

if ! jq -e '.results | type == "array"' "$search_json" >/dev/null; then
  echo "Search response results is not an array." >&2
  jq . "$search_json" >&2
  exit 1
fi

if ! jq -e '.total_results | type == "number" and . >= 1' "$search_json" >/dev/null; then
  echo "Expected at least one search result after indexing." >&2
  jq . "$search_json" >&2
  exit 1
fi

if ! jq -e '.results[0] | type == "object"' "$search_json" >/dev/null; then
  echo "Search response first result does not have expected object shape." >&2
  jq . "$search_json" >&2
  exit 1
fi

jq '{
  query,
  collection,
  mode,
  total_results,
  elapsed_ms,
  first_result: (.results[0] // null)
}' "$search_json"
echo "test_search.sh passed"
