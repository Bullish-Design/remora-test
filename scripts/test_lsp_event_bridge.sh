#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8080}"
PROJECT_ROOT="${PROJECT_ROOT:-.}"
TIMEOUT_S="${TIMEOUT_S:-25}"
REQUIRE_LSP_BRIDGE="${REQUIRE_LSP_BRIDGE:-0}"

workdir="$(mktemp -d)"
lsp_preflight_log="$workdir/lsp_preflight.log"

cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

if ! curl -fsS "$BASE/api/health" >/dev/null; then
  echo "Runtime health check failed at $BASE/api/health. Start remora runtime first." >&2
  exit 1
fi

db_path="$(devenv shell -- python - <<'PY' | tail -n 1 | tr -d '\r'
from pathlib import Path
from remora.core.model.config import load_config
config = load_config(None)
print((Path('.').resolve() / config.infra.workspace_root / 'remora.db').as_posix())
PY
)"
if [ ! -f "$db_path" ]; then
  echo "LSP bridge precheck failed: remora database not found at $db_path" >&2
  exit 1
fi

# Verify LSP extras are available before attempting bridge interactions.
set +e
timeout 8s devenv shell -- remora lsp --project-root "$PROJECT_ROOT" --log-level ERROR >"$lsp_preflight_log" 2>&1
lsp_preflight_code=$?
set -e

if [ "$lsp_preflight_code" -ne 124 ] && [ "$lsp_preflight_code" -ne 0 ]; then
  if rg -qi "LSP support requires pygls" "$lsp_preflight_log"; then
    echo "Detected missing LSP dependency (pygls)." >&2
    echo "Install with: pip install remora[lsp]" >&2
    if [ "$REQUIRE_LSP_BRIDGE" = "1" ]; then
      exit 1
    fi
    echo "LSP bridge check skipped (non-strict mode)." >&2
    echo "test_lsp_event_bridge.sh skipped"
    exit 0
  fi

  echo "LSP bridge preflight failed with exit code $lsp_preflight_code." >&2
  tail -n 80 "$lsp_preflight_log" >&2 || true
  exit 1
fi

export BASE PROJECT_ROOT TIMEOUT_S
devenv shell -- python - <<'PY'
import json
import os
import pathlib
import select
import subprocess
import sys
import time
import urllib.request

BASE = os.environ.get("BASE", "http://127.0.0.1:8080")
PROJECT_ROOT = pathlib.Path(os.environ.get("PROJECT_ROOT", ".")).resolve()
TIMEOUT_S = float(os.environ.get("TIMEOUT_S", "25"))


def http_json(url: str):
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_message(proc: subprocess.Popen[bytes], payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\\r\\n\\r\\n".encode("utf-8")
    assert proc.stdin is not None
    proc.stdin.write(header + body)
    proc.stdin.flush()


def read_message(proc: subprocess.Popen[bytes], timeout_s: float = 15.0) -> dict | None:
    assert proc.stdout is not None
    fd = proc.stdout.fileno()
    start = time.time()
    headers = b""
    while b"\r\n\r\n" not in headers:
        if time.time() - start > timeout_s:
            return None
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        chunk = os.read(fd, 1)
        if not chunk:
            return None
        headers += chunk

    header_text = headers.decode("utf-8", errors="replace")
    content_length = None
    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length is None:
        return None

    body = b""
    while len(body) < content_length:
        if time.time() - start > timeout_s:
            return None
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        chunk = os.read(fd, content_length - len(body))
        if not chunk:
            return None
        body += chunk

    if not body:
        return None
    return json.loads(body.decode("utf-8"))


file_path = PROJECT_ROOT / "src/services/pricing.py"
uri = file_path.resolve().as_uri()
text = file_path.read_text(encoding="utf-8")
updated_text = text + "\n# remora lsp bridge probe\n"

baseline_events = http_json(f"{BASE}/api/events?limit=200")
before_ts = max([float(item.get("timestamp", 0.0)) for item in baseline_events] + [time.time()])

proc = subprocess.Popen(
    ["remora", "lsp", "--project-root", str(PROJECT_ROOT), "--log-level", "ERROR"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

try:
    send_message(
        proc,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": PROJECT_ROOT.as_uri(),
                "capabilities": {},
            },
        },
    )

    init_response = None
    deadline = time.time() + TIMEOUT_S
    while time.time() < deadline:
        remaining = max(0.5, deadline - time.time())
        msg = read_message(proc, timeout_s=remaining)
        if msg is None:
            continue
        if msg.get("id") == 1:
            init_response = msg
            break
    if init_response is None:
        print(
            "warning: LSP initialize response not observed within timeout; proceeding with notifications",
            file=sys.stderr,
        )

    send_message(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

    send_message(
        proc,
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": text,
                }
            },
        },
    )

    send_message(
        proc,
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "version": 2,
                },
                "contentChanges": [
                    {
                        "text": updated_text,
                    }
                ],
            },
        },
    )

    send_message(
        proc,
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didSave",
            "params": {"textDocument": {"uri": uri}, "text": updated_text},
        },
    )

    time.sleep(2)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

seen_content_changed = False
deadline = time.time() + TIMEOUT_S
while time.time() < deadline:
    updated_events = http_json(f"{BASE}/api/events?limit=2000")
    for item in updated_events:
        if item.get("event_type") != "content_changed":
            continue
        if item.get("payload", {}).get("path") != str(file_path.resolve()):
            continue
        if float(item.get("timestamp", 0.0)) >= before_ts:
            seen_content_changed = True
            break
    if seen_content_changed:
        break
    time.sleep(0.5)

if not seen_content_changed:
    raise SystemExit(
        "No new content_changed events observed for pricing.py after LSP didOpen/didSave"
    )

print("test_lsp_event_bridge.sh passed")
PY
