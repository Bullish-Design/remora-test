#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

workdir="$(mktemp -d)"
discover_out="$workdir/discover.txt"
cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

devenv shell -- remora discover --project-root . > "$discover_out"

if ! rg -q '^function\s' "$discover_out"; then
  echo "Expected at least one function node in discover output" >&2
  cat "$discover_out" >&2
  exit 1
fi

if ! rg -q '^section\s' "$discover_out"; then
  echo "Expected markdown section nodes in discover output" >&2
  cat "$discover_out" >&2
  exit 1
fi

if ! rg -q '^table\s' "$discover_out"; then
  echo "Expected TOML table nodes in discover output" >&2
  cat "$discover_out" >&2
  exit 1
fi

if curl -fsS "$BASE/api/health" >/dev/null 2>&1; then
  virtual_count="$(curl -fsS "$BASE/api/nodes" | jq '[.[] | select(.node_type=="virtual")] | length')"
  if [ "$virtual_count" -lt 2 ]; then
    echo "Expected at least 2 virtual nodes when runtime is running" >&2
    exit 1
  fi
fi

echo "test_multilang_discovery.sh passed"
