from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient


NAME = "check_lsp_bridge"
CHANGE_EVENT_TYPES = ("content_changed", "node_changed")


def _send_message(proc: subprocess.Popen[bytes], payload: dict[str, Any]) -> None:
    if proc.stdin is None:
        raise CheckFailure("LSP subprocess missing stdin pipe")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    proc.stdin.write(header + body)
    proc.stdin.flush()


def _event_path_matches(event_path: str, target_path: str) -> bool:
    if not event_path:
        return False
    return event_path == target_path or event_path.startswith(target_path + "::")


def _fetch_events(client: RemoraClient, *, event_type: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    return client.events(limit=limit, event_type=event_type)


def _wait_for_change_event(
    client: RemoraClient,
    *,
    target_path: str,
    since_ts: float,
    timeout_s: float,
    event_limit: int,
) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for event_type in CHANGE_EVENT_TYPES:
            events = _fetch_events(client, event_type=event_type, limit=event_limit)
            for event in events:
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue
                event_path = str(payload.get("path") or payload.get("file_path") or "")
                if not _event_path_matches(event_path, target_path):
                    continue
                if float(event.get("timestamp", 0.0)) >= since_ts:
                    return True
        time.sleep(0.5)
    return False


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    timeout_s = 25.0
    warmup_s = 8.0
    event_limit = 500

    if not ctx.run_lsp_bridge:
        return CheckResult(name=NAME, passed=True, skipped=True, skip_reason="LSP bridge disabled", duration_s=0.0)

    client = RemoraClient(ctx.base_url)
    target_file = (ctx.project_root / "src/services/pricing.py").resolve()
    original_text = ""

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        from remora.core.model.config import load_config

        config = load_config(ctx.config_path)
        db_path = ctx.project_root / config.infra.workspace_root / "remora.db"
        if not db_path.exists():
            raise CheckFailure(f"LSP bridge precheck failed: remora database not found at {db_path}")
        if not target_file.exists():
            raise CheckFailure(f"LSP bridge precheck failed: target file missing: {target_file}")

        target_path = str(target_file)
        target_uri = target_file.as_uri()
        original_text = target_file.read_text(encoding="utf-8")
        updated_text = original_text + "\n# remora lsp bridge probe\n"

        since_ts = time.time() - 0.5
        stderr_tail = ""

        proc = subprocess.Popen(
            [
                *(ctx.command_prefix or []),
                "remora",
                "lsp",
                "--project-root",
                str(ctx.project_root),
                "--config",
                str(ctx.config_path),
                "--log-level",
                "ERROR",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            _send_message(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "processId": None,
                        "rootUri": ctx.project_root.as_uri(),
                        "capabilities": {},
                    },
                },
            )
            time.sleep(min(timeout_s, warmup_s))
            if proc.poll() is not None:
                raise CheckFailure(f"LSP process exited before notification cycle (code={proc.returncode})")

            _send_message(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
            _send_message(
                proc,
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didOpen",
                    "params": {
                        "textDocument": {
                            "uri": target_uri,
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
                        "textDocument": {"uri": target_uri, "version": 2},
                        "contentChanges": [{"text": updated_text}],
                    },
                },
            )
            _send_message(
                proc,
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didSave",
                    "params": {"textDocument": {"uri": target_uri}, "text": updated_text},
                },
            )
            time.sleep(3)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            if proc.stderr is not None:
                stderr_tail = proc.stderr.read().decode("utf-8", errors="replace")[-4000:]

        if _wait_for_change_event(
            client,
            target_path=target_path,
            since_ts=since_ts,
            timeout_s=timeout_s,
            event_limit=event_limit,
        ):
            return CheckResult(name=NAME, passed=True, duration_s=time.time() - started)

        if not ctx.require_lsp_bridge:
            return CheckResult(
                name=NAME,
                passed=True,
                skipped=True,
                skip_reason="No new LSP bridge change event observed",
                duration_s=time.time() - started,
            )

        recent_events = _fetch_events(client, limit=event_limit)
        histogram: dict[str, int] = {}
        for event in recent_events:
            event_type = str(event.get("event_type", ""))
            if event_type:
                histogram[event_type] = histogram.get(event_type, 0) + 1

        detail = {
            "histogram": dict(sorted(histogram.items(), key=lambda kv: kv[0])),
            "lsp_stderr_tail": stderr_tail,
        }
        raise CheckFailure(f"No new change events observed for pricing.py after LSP cycle: {detail}")
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
    finally:
        if original_text and target_file.exists():
            # Ensure probe text does not leak into fixture if runtime or lsp side-effects write to disk.
            target_file.write_text(original_text, encoding="utf-8")
