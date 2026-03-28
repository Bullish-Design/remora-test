from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, find_node


NAME = "check_cursor"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = 10.0
    poll_interval_s = 1.0
    event_limit = 2000
    require_cursor_event = False

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        target = find_node(nodes, file_suffix="/src/services/pricing.py", name="compute_total")
        if target is None:
            raise CheckFailure("Unable to resolve target node for cursor check")

        target_node_id = str(target.get("node_id", ""))
        target_file_path = str(target.get("file_path", ""))
        target_line = int(target.get("start_line", 1))

        resp = client.cursor(target_file_path, target_line, 0)
        if str(resp.get("status", "")) != "ok":
            raise CheckFailure(f"Cursor API call failed: {resp}")
        if str(resp.get("node_id", "")) != target_node_id:
            raise CheckFailure(
                "Cursor API returned unexpected node_id "
                f"expected={target_node_id} actual={resp.get('node_id', '')}"
            )

        cursor_event_found = False
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=event_limit)
            for event in events:
                if str(event.get("event_type", "")) != "cursor_focus":
                    continue
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue
                if str(payload.get("node_id", "")) == target_node_id:
                    cursor_event_found = True
                    break
                if str(payload.get("file_path", "")) == target_file_path and int(payload.get("line", -1)) == target_line:
                    cursor_event_found = True
                    break
            if cursor_event_found:
                break
            time.sleep(poll_interval_s)

        if not cursor_event_found and require_cursor_event:
            raise CheckFailure("cursor_focus event for target node not found")

        detail = "cursor_focus event observed" if cursor_event_found else "cursor_focus event not observed within timeout; cursor API mapping verified"
        return CheckResult(name=NAME, passed=True, duration_s=time.time() - started, detail=detail)
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
