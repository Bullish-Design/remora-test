#!/usr/bin/env python3
"""Standalone probe for remora LSP -> runtime event bridge behavior."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
import urllib.parse
import urllib.request

from remora.core.model.config import load_config


CHANGE_EVENT_TYPES = ("content_changed", "node_changed")


def _http_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_events(base: str, *, event_type: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    params: list[tuple[str, str]] = [("limit", str(limit))]
    if event_type:
        params.append(("event_type", event_type))
    query = urllib.parse.urlencode(params)
    payload = _http_json(f"{base}/api/events?{query}")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _event_path_matches(event_path: str, target_path: str) -> bool:
    if not event_path:
        return False
    if event_path == target_path:
        return True
    return event_path.startswith(target_path + "::")


def _send_message(proc: subprocess.Popen[bytes], payload: dict[str, Any]) -> None:
    if proc.stdin is None:
        raise RuntimeError("LSP subprocess missing stdin pipe")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    proc.stdin.write(header + body)
    proc.stdin.flush()


def _run_lsp_cycle(
    project_root: Path,
    *,
    file_uri: str,
    original_text: str,
    updated_text: str,
    warmup_s: float,
) -> str:
    proc = subprocess.Popen(
        ["remora", "lsp", "--project-root", str(project_root), "--log-level", "ERROR"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stderr_tail = ""
    try:
        _send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": None,
                    "rootUri": project_root.as_uri(),
                    "capabilities": {},
                },
            },
        )
        time.sleep(warmup_s)
        if proc.poll() is not None:
            raise RuntimeError(
                f"LSP process exited before notification cycle (code={proc.returncode})"
            )

        _send_message(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
        _send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": file_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": original_text,
                    }
                },
            },
        )
        _send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": file_uri, "version": 2},
                    "contentChanges": [{"text": updated_text}],
                },
            },
        )
        _send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didSave",
                "params": {"textDocument": {"uri": file_uri}, "text": updated_text},
            },
        )
        # Give event append/commit a moment to complete.
        time.sleep(3)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stderr is not None:
            stderr_tail = proc.stderr.read().decode("utf-8", errors="replace")[-4000:]

    return stderr_tail


def _wait_for_change_event(
    *,
    base: str,
    target_path: str,
    since_ts: float,
    timeout_s: float,
    event_limit: int,
) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for event_type in CHANGE_EVENT_TYPES:
            for event in _fetch_events(base, event_type=event_type, limit=event_limit):
                payload = event.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                event_path = str(payload.get("path") or payload.get("file_path") or "")
                if not _event_path_matches(event_path, target_path):
                    continue
                event_ts = float(event.get("timestamp", 0.0))
                if event_ts >= since_ts:
                    return True
        time.sleep(0.5)
    return False


def _event_histogram(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("event_type", ""))
        if not event_type:
            continue
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def _probe(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    base = args.base.rstrip("/")

    # Runtime and DB prechecks.
    try:
        _http_json(f"{base}/api/health")
    except Exception as exc:  # noqa: BLE001
        print(f"Runtime health check failed at {base}/api/health: {exc}", file=sys.stderr)
        return 1

    config = load_config(None)
    db_path = project_root / config.infra.workspace_root / "remora.db"
    if not db_path.exists():
        print(f"LSP bridge precheck failed: remora database not found at {db_path}", file=sys.stderr)
        return 1

    target_file = project_root / "src/services/pricing.py"
    if not target_file.exists():
        print(f"LSP bridge precheck failed: target file missing: {target_file}", file=sys.stderr)
        return 1

    target_path = str(target_file.resolve())
    target_uri = target_file.resolve().as_uri()
    original_text = target_file.read_text(encoding="utf-8")
    updated_text = original_text + "\n# remora lsp bridge probe\n"

    since_ts = time.time() - 0.5
    stderr_tail = ""
    try:
        stderr_tail = _run_lsp_cycle(
            project_root,
            file_uri=target_uri,
            original_text=original_text,
            updated_text=updated_text,
            warmup_s=min(args.timeout_s, args.warmup_s),
        )
    except Exception as exc:  # noqa: BLE001
        if not args.require_lsp_bridge:
            print(f"warning: lsp cycle failed in non-strict mode: {exc}", file=sys.stderr)
            return 0
        print(f"LSP cycle failed: {exc}", file=sys.stderr)
        if stderr_tail.strip():
            print("debug: lsp_stderr_tail=", file=sys.stderr)
            print(stderr_tail, file=sys.stderr)
        return 1

    if _wait_for_change_event(
        base=base,
        target_path=target_path,
        since_ts=since_ts,
        timeout_s=args.timeout_s,
        event_limit=args.event_limit,
    ):
        print("test_lsp_event_bridge.sh passed")
        return 0

    # Rich diagnostics on failure.
    if not args.require_lsp_bridge:
        print(
            "warning: no new LSP bridge change event observed (non-strict mode); continuing",
            file=sys.stderr,
        )
        return 0

    recent_events = _fetch_events(base, limit=args.event_limit)
    histogram = _event_histogram(recent_events)
    filtered_recent: dict[str, list[dict[str, Any]]] = {}
    file_scoped_recent: list[dict[str, Any]] = []
    for event_type in CHANGE_EVENT_TYPES:
        scoped = _fetch_events(base, event_type=event_type, limit=args.event_limit)
        filtered_recent[event_type] = scoped[:20]
        for event in scoped:
            payload = event.get("payload", {})
            if not isinstance(payload, dict):
                continue
            event_path = str(payload.get("path") or payload.get("file_path") or "")
            if not _event_path_matches(event_path, target_path):
                continue
            file_scoped_recent.append(
                {
                    "event_type": str(event.get("event_type", "")),
                    "timestamp": event.get("timestamp"),
                    "payload": {
                        "path": payload.get("path"),
                        "file_path": payload.get("file_path"),
                        "change_type": payload.get("change_type"),
                        "node_id": payload.get("node_id"),
                    },
                }
            )

    print(
        "debug: recent_event_type_histogram="
        + json.dumps(dict(sorted(histogram.items(), key=lambda kv: kv[0])), indent=2),
        file=sys.stderr,
    )
    print(
        "debug: filtered_recent_change_events=" + json.dumps(filtered_recent, indent=2),
        file=sys.stderr,
    )
    if file_scoped_recent:
        print(
            "debug: file_scoped_recent_events=" + json.dumps(file_scoped_recent[:20], indent=2),
            file=sys.stderr,
        )
    if stderr_tail.strip():
        print("debug: lsp_stderr_tail=", file=sys.stderr)
        print(stderr_tail, file=sys.stderr)
    print(
        "No new change events observed for pricing.py after LSP didOpen/didChange/didSave",
        file=sys.stderr,
    )
    return 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe remora LSP event bridge")
    parser.add_argument("--base", default=os.environ.get("BASE", "http://127.0.0.1:8080"))
    parser.add_argument("--project-root", default=os.environ.get("PROJECT_ROOT", "."))
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=float(os.environ.get("TIMEOUT_S", "25")),
    )
    parser.add_argument(
        "--warmup-s",
        type=float,
        default=float(os.environ.get("LSP_WARMUP_S", "8")),
    )
    parser.add_argument(
        "--event-limit",
        type=int,
        default=int(os.environ.get("EVENT_LIMIT", "500")),
    )
    parser.add_argument(
        "--require-lsp-bridge",
        type=lambda raw: str(raw).strip().lower() in {"1", "true", "yes", "on"},
        default=str(os.environ.get("REQUIRE_LSP_BRIDGE", "0")),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    return _probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
