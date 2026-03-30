from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time
from typing import Any, Callable
import urllib.error
import urllib.parse
import urllib.request


class CheckFailure(RuntimeError):
    pass


@dataclass
class CheckResult:
    name: str
    passed: bool
    skipped: bool = False
    skip_reason: str = ""
    detail: str = ""
    duration_s: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckContext:
    base_url: str
    project_root: Path
    config_path: Path
    strict: bool
    require_web: bool
    require_search: bool
    require_lsp_bridge: bool
    run_lsp_bridge: bool
    run_guardrails: bool
    require_overflow: bool
    command_prefix: list[str]


class RemoraClient:
    def __init__(self, base_url: str, *, timeout_s: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_s: float | None = None,
    ) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        body: bytes | None = None
        request_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        timeout = timeout_s if timeout_s is not None else self.timeout_s
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            raise CheckFailure(f"{method} {url} failed: {exc}") from exc

        if not raw.strip():
            return status, {}
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, {"_raw": raw}

    def health(self) -> dict[str, Any]:
        status, payload = self._request("GET", "/api/health")
        if status != 200 or not isinstance(payload, dict):
            raise CheckFailure(f"/api/health failed: status={status} payload={payload}")
        return payload

    def nodes(self) -> list[dict[str, Any]]:
        status, payload = self._request("GET", "/api/nodes")
        if status != 200 or not isinstance(payload, list):
            raise CheckFailure(f"/api/nodes failed: status={status} payload={payload}")
        return [item for item in payload if isinstance(item, dict)]

    def edges(self) -> list[dict[str, Any]]:
        status, payload = self._request("GET", "/api/edges")
        if status != 200 or not isinstance(payload, list):
            raise CheckFailure(f"/api/edges failed: status={status} payload={payload}")
        return [item for item in payload if isinstance(item, dict)]

    def events(self, *, limit: int = 500, event_type: str | None = None) -> list[dict[str, Any]]:
        params: list[tuple[str, str]] = [("limit", str(limit))]
        if event_type:
            params.append(("event_type", event_type))
        query = urllib.parse.urlencode(params)
        status, payload = self._request("GET", f"/api/events?{query}")
        if status != 200 or not isinstance(payload, list):
            raise CheckFailure(f"/api/events failed: status={status} payload={payload}")
        return [item for item in payload if isinstance(item, dict)]

    def chat(self, node_id: str, message: str) -> dict[str, Any]:
        status, payload = self._request("POST", "/api/chat", payload={"node_id": node_id, "message": message})
        if status != 200 or not isinstance(payload, dict):
            raise CheckFailure(f"/api/chat failed: status={status} payload={payload}")
        return payload

    def cursor(self, file_path: str, line: int, character: int = 0) -> dict[str, Any]:
        status, payload = self._request(
            "POST",
            "/api/cursor",
            payload={"file_path": file_path, "line": line, "character": character},
        )
        if status != 200 or not isinstance(payload, dict):
            raise CheckFailure(f"/api/cursor failed: status={status} payload={payload}")
        return payload

    def search(self, query: str, *, collection: str = "code", top_k: int = 5, mode: str = "hybrid") -> tuple[int, Any]:
        return self._request(
            "POST",
            "/api/search",
            payload={"query": query, "collection": collection, "top_k": top_k, "mode": mode},
        )

    def proposals(self) -> list[dict[str, Any]]:
        status, payload = self._request("GET", "/api/proposals")
        if status != 200 or not isinstance(payload, list):
            raise CheckFailure(f"/api/proposals failed: status={status} payload={payload}")
        return [item for item in payload if isinstance(item, dict)]

    def proposal_diff(self, node_id: str) -> tuple[int, Any]:
        encoded = urllib.parse.quote(node_id, safe="")
        return self._request("GET", f"/api/proposals/{encoded}/diff")

    def proposal_accept(self, node_id: str) -> tuple[int, Any]:
        encoded = urllib.parse.quote(node_id, safe="")
        return self._request("POST", f"/api/proposals/{encoded}/accept", payload={})

    def proposal_reject(self, node_id: str, feedback: str = "") -> tuple[int, Any]:
        encoded = urllib.parse.quote(node_id, safe="")
        return self._request("POST", f"/api/proposals/{encoded}/reject", payload={"feedback": feedback})

    def companion(self, node_id: str) -> tuple[int, Any]:
        encoded = urllib.parse.quote(node_id, safe="")
        return self._request("GET", f"/api/nodes/{encoded}/companion")

    def sse(self, *, replay: int | None = None, once: bool = False, last_event_id: str | None = None) -> str:
        params: list[tuple[str, str]] = []
        if replay is not None:
            params.append(("replay", str(replay)))
        if once:
            params.append(("once", "true"))
        query = urllib.parse.urlencode(params)
        path = "/sse"
        if query:
            path = f"{path}?{query}"
        headers: dict[str, str] = {}
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id

        status, payload = self._request("GET", path, headers=headers, timeout_s=20.0)
        if status != 200:
            raise CheckFailure(f"SSE request failed: status={status} payload={payload}")
        if isinstance(payload, dict) and "_raw" in payload:
            return str(payload["_raw"])
        return json.dumps(payload)


def auto_command_prefix() -> list[str]:
    raw = os.getenv("DEMO_COMMAND_PREFIX", "").strip()
    if raw:
        return shlex.split(raw)
    if shutil.which("devenv"):
        return ["devenv", "shell", "--"]
    return []


def run_command(
    command: list[str],
    *,
    prefix: list[str] | None = None,
    env: dict[str, str] | None = None,
    timeout_s: float | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    full = [*(prefix or []), *command]
    return subprocess.run(
        full,
        text=True,
        capture_output=True,
        env=env,
        timeout=timeout_s,
        cwd=cwd,
        check=False,
    )


def wait_for_health(client: RemoraClient, *, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if client.health().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def poll_events(
    client: RemoraClient,
    *,
    predicate: Callable[[dict[str, Any], list[dict[str, Any]]], bool],
    timeout_s: float,
    poll_interval_s: float = 1.0,
    limit: int = 500,
) -> dict[str, Any] | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        events = client.events(limit=limit)
        for event in events:
            if predicate(event, events):
                return event
        time.sleep(poll_interval_s)
    return None


def find_node(
    nodes: list[dict[str, Any]],
    *,
    file_suffix: str,
    name: str,
) -> dict[str, Any] | None:
    for node in nodes:
        if str(node.get("file_path", "")).endswith(file_suffix) and str(node.get("name", "")) == name:
            return node
    for node in nodes:
        if str(node.get("node_type", "")) == "function":
            return node
    return None


def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    if isinstance(payload, dict):
        return payload
    return {}


def event_agent_id(event: dict[str, Any]) -> str:
    payload = event_payload(event)
    value = payload.get("agent_id")
    if isinstance(value, str):
        return value
    raw = event.get("agent_id")
    return raw if isinstance(raw, str) else ""


def ensure_chat_sent(response: dict[str, Any], *, error_prefix: str) -> None:
    if str(response.get("status", "")).strip() != "sent":
        raise CheckFailure(f"{error_prefix}: {response}")
