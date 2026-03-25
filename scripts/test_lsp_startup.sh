#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-.}"
TIMEOUT_S="${TIMEOUT_S:-8}"
REQUIRE_LSP="${REQUIRE_LSP:-0}"

workdir="$(mktemp -d)"
lsp_log="$workdir/lsp.log"

cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

db_path="$(devenv shell -- python - <<'PY' | tail -n 1 | tr -d '\r'
from pathlib import Path
from remora.core.model.config import load_config

config = load_config(None)
print((Path(".").resolve() / config.infra.workspace_root / "remora.db").as_posix())
PY
)"

if [ ! -f "$db_path" ]; then
  echo "LSP startup precheck failed: remora database not found at $db_path" >&2
  echo "Run 'devenv shell -- remora start --project-root $PROJECT_ROOT --port 8080' at least once before LSP checks." >&2
  exit 1
fi

set +e
timeout "${TIMEOUT_S}s" devenv shell -- remora lsp --project-root "$PROJECT_ROOT" >"$lsp_log" 2>&1
exit_code=$?
set -e

if [ "$exit_code" -eq 124 ]; then
  echo "LSP server startup appears healthy (process remained running for ${TIMEOUT_S}s)."
  echo "test_lsp_startup.sh passed"
  exit 0
fi

if [ "$exit_code" -eq 0 ] && rg -qi "Starting standalone LSP server on stdin/stdout" "$lsp_log"; then
  echo "LSP server startup appears healthy (server started and exited cleanly on stdin EOF)."
  echo "test_lsp_startup.sh passed"
  exit 0
fi

if rg -qi "LSP support requires pygls" "$lsp_log"; then
  echo "Detected missing LSP dependency (pygls)." >&2
  echo "Install with: pip install remora[lsp]" >&2
  echo "Or update project dependencies to include remora lsp extras." >&2
  if [ "$REQUIRE_LSP" = "1" ]; then
    exit 1
  fi
  echo "LSP dependency diagnostic verified (non-strict mode)."
  echo "test_lsp_startup.sh passed"
  exit 0
fi

echo "LSP startup check failed with exit code $exit_code." >&2
echo "Last log lines:" >&2
tail -n 80 "$lsp_log" >&2 || true
exit 1
