from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

import pytest


def _request_json(
    method: str,
    url: str,
    *,
    data: dict[str, Any] | None = None,
    timeout_s: float = 10.0,
) -> tuple[int, Any]:
    payload: bytes | None = None
    headers: dict[str, str] = {}
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    response_body = ""
    status_code = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        response_body = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc

    if not response_body.strip():
        return status_code, {}

    try:
        return status_code, json.loads(response_body)
    except json.JSONDecodeError:
        return status_code, {"_raw": response_body}


def _agent_id(event: dict[str, Any]) -> str:
    payload = event.get("payload")
    if isinstance(payload, dict):
        candidate = payload.get("agent_id")
        if isinstance(candidate, str):
            return candidate
    candidate = event.get("agent_id")
    return candidate if isinstance(candidate, str) else ""


def _to_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _virtual_event_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "review_start": 0,
        "review_turn_complete": 0,
        "review_model_response": 0,
        "review_output": 0,
        "review_tool_activity": 0,
        "companion_start": 0,
        "companion_turn_complete": 0,
        "companion_tool_activity": 0,
        "turn_digested": 0,
    }

    for event in events:
        event_type = event.get("event_type")
        if not isinstance(event_type, str):
            continue
        payload = event.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        agent_id = _agent_id(event)

        if event_type == "turn_digested":
            counts["turn_digested"] += 1

        if agent_id == "demo-review-observer":
            if event_type == "agent_start":
                counts["review_start"] += 1
            elif event_type == "turn_complete":
                counts["review_turn_complete"] += 1
            elif event_type == "model_response":
                counts["review_model_response"] += 1
            elif event_type == "agent_complete":
                if any(
                    bool(str(payload_dict.get(key, "")).strip())
                    for key in ("user_message", "result_summary", "full_response")
                ):
                    counts["review_output"] += 1
            if event_type in {"turn_complete", "model_response"} and _to_int(
                payload_dict.get("tool_calls_count", 0)
            ) > 0:
                counts["review_tool_activity"] += 1

        if agent_id == "demo-companion-observer":
            if event_type == "agent_start":
                counts["companion_start"] += 1
            elif event_type == "turn_complete":
                counts["companion_turn_complete"] += 1
            if event_type in {"turn_complete", "model_response"} and _to_int(
                payload_dict.get("tool_calls_count", 0)
            ) > 0:
                counts["companion_tool_activity"] += 1

    return counts


@pytest.fixture(scope="module")
def live_base_url() -> str:
    base_url = os.getenv("REMORA_LIVE_BASE_URL", "").strip()
    if not base_url:
        pytest.skip("Set REMORA_LIVE_BASE_URL to run live integration tests.")
    return base_url.rstrip("/")


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def live_project_root(repo_root: Path) -> Path:
    raw = os.getenv("REMORA_LIVE_PROJECT_ROOT", "").strip()
    if not raw:
        return repo_root
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return path


@pytest.fixture(scope="module")
def live_config_path(repo_root: Path) -> Path:
    raw = os.getenv("REMORA_LIVE_CONFIG_PATH", "").strip()
    if not raw:
        return (repo_root / "demo/00_repo_baseline/config/remora.yaml").resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return path


@pytest.fixture(scope="module")
def live_runtime(live_base_url: str) -> str:
    try:
        status, body = _request_json("GET", f"{live_base_url}/api/health")
    except RuntimeError as exc:
        pytest.skip(f"Runtime unavailable: {exc}")

    if status != 200 or not isinstance(body, dict) or body.get("status") != "ok":
        pytest.skip(f"Runtime not healthy at {live_base_url}/api/health")
    return live_base_url


@pytest.mark.live
def test_runtime_health_and_graph_live(live_runtime: str) -> None:
    status, health = _request_json("GET", f"{live_runtime}/api/health")
    assert status == 200
    assert isinstance(health, dict)
    assert health.get("status") == "ok"

    status, nodes = _request_json("GET", f"{live_runtime}/api/nodes")
    assert status == 200
    assert isinstance(nodes, list)
    assert len(nodes) > 0

    status, edges = _request_json("GET", f"{live_runtime}/api/edges")
    assert status == 200
    assert isinstance(edges, list)


@pytest.mark.live
def test_virtual_agent_behavior_live(live_runtime: str, live_project_root: Path) -> None:
    require_companion = os.getenv("REMORA_LIVE_REQUIRE_COMPANION", "0") == "1"
    timeout_s = max(5, int(os.getenv("REMORA_LIVE_VIRTUAL_TIMEOUT_S", "20")))
    poll_interval_s = max(1, int(os.getenv("REMORA_LIVE_VIRTUAL_POLL_INTERVAL_S", "1")))

    status, nodes = _request_json("GET", f"{live_runtime}/api/nodes")
    assert status == 200
    assert isinstance(nodes, list)
    virtual_node_ids = [node.get("node_id") for node in nodes if node.get("node_type") == "virtual"]
    assert "demo-review-observer" in virtual_node_ids
    assert "demo-companion-observer" in virtual_node_ids

    status, before_events = _request_json("GET", f"{live_runtime}/api/events?limit=500")
    assert status == 200
    assert isinstance(before_events, list)
    before_counts = _virtual_event_counts([event for event in before_events if isinstance(event, dict)])

    trigger_dir = live_project_root / "src/.remora_demo_trigger"
    trigger_dir.mkdir(parents=True, exist_ok=True)
    trigger_file = trigger_dir / f"trigger_live_{int(time.time())}.py"
    trigger_file.write_text("def _remora_live_trigger() -> int:\n    return 1\n", encoding="utf-8")
    try:
        review_ok = False
        companion_ok = False
        after_counts = before_counts.copy()

        start = time.time()
        while time.time() - start < timeout_s:
            time.sleep(poll_interval_s)
            status, after_events = _request_json("GET", f"{live_runtime}/api/events?limit=500")
            assert status == 200
            assert isinstance(after_events, list)
            after_counts = _virtual_event_counts(
                [event for event in after_events if isinstance(event, dict)]
            )

            review_ok = (
                after_counts["review_start"] > before_counts["review_start"]
                and after_counts["review_turn_complete"] > before_counts["review_turn_complete"]
                and after_counts["review_model_response"] > before_counts["review_model_response"]
                and (
                    after_counts["review_output"] > before_counts["review_output"]
                    or after_counts["review_tool_activity"] > before_counts["review_tool_activity"]
                )
            )

            companion_ok = (
                after_counts["companion_start"] > before_counts["companion_start"]
                and after_counts["companion_turn_complete"] > before_counts["companion_turn_complete"]
                and (
                    after_counts["companion_tool_activity"] > before_counts["companion_tool_activity"]
                    or after_counts["turn_digested"] > before_counts["turn_digested"]
                )
            )

            if review_ok and (companion_ok or not require_companion):
                break
    finally:
        if trigger_file.exists():
            trigger_file.unlink()
        try:
            trigger_dir.rmdir()
        except OSError:
            pass

    assert review_ok, f"Review observer did not show expected behavior growth: {after_counts}"
    if require_companion:
        assert companion_ok, f"Companion observer did not show expected behavior growth: {after_counts}"


@pytest.mark.live
def test_proposal_flow_live(live_runtime: str) -> None:
    timeout_s = max(5, int(os.getenv("REMORA_LIVE_PROPOSAL_TIMEOUT_S", "25")))
    poll_interval_s = max(1, int(os.getenv("REMORA_LIVE_PROPOSAL_POLL_INTERVAL_S", "1")))

    status, nodes = _request_json("GET", f"{live_runtime}/api/nodes")
    assert status == 200
    assert isinstance(nodes, list)

    target_node = ""
    for node in nodes:
        file_path = str(node.get("file_path", ""))
        if file_path.endswith("/src/services/pricing.py") and node.get("name") == "compute_total":
            candidate = node.get("node_id")
            if isinstance(candidate, str) and candidate:
                target_node = candidate
                break
    assert target_node, "Unable to resolve compute_total node in src/services/pricing.py"

    status, chat = _request_json(
        "POST",
        f"{live_runtime}/api/chat",
        data={"node_id": target_node, "message": "rewrite_to_magic"},
    )
    assert status == 200
    assert isinstance(chat, dict)
    assert chat.get("status") == "sent"

    proposal = None
    start = time.time()
    while time.time() - start < timeout_s:
        time.sleep(poll_interval_s)
        status, proposals = _request_json("GET", f"{live_runtime}/api/proposals")
        assert status == 200
        assert isinstance(proposals, list)
        for item in proposals:
            if isinstance(item, dict) and item.get("node_id") == target_node:
                proposal = item
                break
        if proposal is not None:
            break

    assert proposal is not None, f"No proposal found for node {target_node}"

    encoded_node = urllib.parse.quote(target_node, safe="")
    status, diff = _request_json("GET", f"{live_runtime}/api/proposals/{encoded_node}/diff")
    assert status == 200
    assert isinstance(diff, dict)
    diffs = diff.get("diffs")
    assert isinstance(diffs, list)
    assert len(diffs) > 0

    status, reject = _request_json(
        "POST",
        f"{live_runtime}/api/proposals/{encoded_node}/reject",
        data={"feedback": "live test auto-reject"},
    )
    assert status == 200
    assert isinstance(reject, dict)
    assert reject.get("status") == "rejected"


@pytest.mark.live
def test_search_live(live_runtime: str, live_project_root: Path, live_config_path: Path) -> None:
    require_search = os.getenv("REMORA_LIVE_REQUIRE_SEARCH", "0") == "1"
    index_timeout_s = max(60, int(os.getenv("REMORA_LIVE_INDEX_TIMEOUT_S", "180")))

    index_proc = subprocess.run(
        [
            "devenv",
            "shell",
            "--",
            "remora",
            "index",
            "--project-root",
            str(live_project_root),
            "--config",
            str(live_config_path),
        ],
        cwd=live_project_root,
        capture_output=True,
        text=True,
        timeout=index_timeout_s,
        check=False,
    )
    if index_proc.returncode != 0:
        combined_output = f"{index_proc.stdout}\n{index_proc.stderr}"
        if (
            not require_search
            and "search service is not available" in combined_output.lower()
        ):
            pytest.skip("Search backend is not configured in this environment.")
        pytest.fail(
            "remora index failed.\n"
            f"stdout:\n{index_proc.stdout}\n"
            f"stderr:\n{index_proc.stderr}"
        )

    status, search = _request_json(
        "POST",
        f"{live_runtime}/api/search",
        data={"query": "compute_total", "collection": "code", "top_k": 5, "mode": "hybrid"},
        timeout_s=20.0,
    )

    if status == 503 and not require_search:
        pytest.skip("Search API returned 503 (semantic search not configured).")

    assert status == 200, f"Search request failed: status={status}, body={search}"
    assert isinstance(search, dict)
    assert search.get("query") == "compute_total"
    assert search.get("collection") == "code"
    assert search.get("mode") == "hybrid"
    assert isinstance(search.get("results"), list)
    assert isinstance(search.get("total_results"), int)
    assert search["total_results"] >= 1
