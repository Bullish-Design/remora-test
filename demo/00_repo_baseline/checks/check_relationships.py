from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent, event_agent_id, event_payload, find_node


NAME = "check_relationships"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = 20.0
    poll_interval_s = 1.0
    event_limit = 400

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        target = find_node(nodes, file_suffix="/src/api/orders.py", name="create_order")
        if target is None:
            raise CheckFailure("Unable to resolve target function node for relationship tool check")
        target_node = str(target.get("node_id", ""))
        if not target_node:
            raise CheckFailure("Target node missing node_id")

        before_events = client.events(limit=event_limit)
        before_count = 0
        for event in before_events:
            if str(event.get("event_type", "")) == "remora_tool_result" and event_agent_id(event) == target_node:
                payload = event_payload(event)
                if str(payload.get("tool_name", "")) == "show_dependencies":
                    before_count += 1

        ensure_chat_sent(client.chat(target_node, "show_dependencies"), error_prefix="Chat send failed")

        tool_seen = False
        latest_preview = ""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=event_limit)
            after_count = 0
            for event in events:
                if str(event.get("event_type", "")) == "remora_tool_result" and event_agent_id(event) == target_node:
                    payload = event_payload(event)
                    if str(payload.get("tool_name", "")) == "show_dependencies":
                        after_count += 1
                        if not latest_preview:
                            latest_preview = str(payload.get("output_preview", ""))
            if after_count > before_count:
                tool_seen = True
                break
            time.sleep(poll_interval_s)

        if not tool_seen:
            raise CheckFailure(f"Did not observe show_dependencies tool execution for {target_node}")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={"latest_tool_output_preview": latest_preview},
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
