#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"

devenv shell -- remora index --project-root .

curl -sS -X POST "$BASE/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"compute_total", "collection":"code", "top_k":5, "mode":"hybrid"}' | jq .
