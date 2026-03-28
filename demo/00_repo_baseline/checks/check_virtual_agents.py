from __future__ import annotations

import time

from _harness import (
    CheckContext,
    CheckFailure,
    CheckResult,
    RemoraClient,
    ensure_chat_sent,
    event_agent_id,
    event_payload,
)


NAME = "check_virtual_agents"


def _count(events: list[dict], *, event_type: str, agent_id: str) -> int:
    total = 0
    for event in events:
        if str(event.get("event_type", "")) != event_type:
            continue
        if event_agent_id(event) == agent_id:
            total += 1
    return total


def _tool_activity(events: list[dict], *, agent_id: str) -> int:
    total = 0
    for event in events:
        event_type = str(event.get("event_type", ""))
        if event_type not in {"turn_complete", "model_response"}:
            continue
        if event_agent_id(event) != agent_id:
            continue
        payload = event_payload(event)
        try:
            if int(payload.get("tool_calls_count", 0)) > 0:
                total += 1
        except (TypeError, ValueError):
            continue
    return total


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = float(20)
    poll_interval_s = float(1)
    event_limit = 500
    require_companion = False

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        virtual_node_ids = [str(node.get("node_id", "")) for node in nodes if str(node.get("node_type", "")) == "virtual"]
        for required in ["demo-review-observer", "demo-companion-observer"]:
            if required not in virtual_node_ids:
                raise CheckFailure(f"Missing virtual node: {required}; found={virtual_node_ids}")

        before_events = client.events(limit=event_limit)
        before_review_turn = _count(before_events, event_type="turn_complete", agent_id="demo-review-observer")
        before_companion_turn = _count(before_events, event_type="turn_complete", agent_id="demo-companion-observer")

        probe_token = f"virtual_observer_probe_{int(time.time())}"
        chat = client.chat("demo-review-observer", probe_token)
        ensure_chat_sent(chat, error_prefix="Failed to send chat probe to demo-review-observer")

        review_ok = False
        companion_ok = False
        probe_corr = ""
        max_review_turn = before_review_turn
        max_companion_turn = before_companion_turn

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=event_limit)

            if not probe_corr:
                for event in events:
                    if str(event.get("event_type", "")) != "agent_complete":
                        continue
                    if event_agent_id(event) != "demo-review-observer":
                        continue
                    payload = event_payload(event)
                    if probe_token in str(payload.get("user_message", "")):
                        probe_corr = str(event.get("correlation_id", ""))
                        break

            max_review_turn = max(max_review_turn, _count(events, event_type="turn_complete", agent_id="demo-review-observer"))
            max_companion_turn = max(
                max_companion_turn,
                _count(events, event_type="turn_complete", agent_id="demo-companion-observer"),
            )

            if probe_corr:
                review_ok = True
                for event in events:
                    if str(event.get("correlation_id", "")) != probe_corr:
                        continue
                    if event_agent_id(event) == "demo-companion-observer" and str(event.get("event_type", "")) in {
                        "turn_complete",
                        "agent_complete",
                    }:
                        companion_ok = True
                        break

            if review_ok and (companion_ok or not require_companion):
                break
            time.sleep(poll_interval_s)

        if not review_ok:
            raise CheckFailure("Review observer did not complete for probe correlation")
        if require_companion and not companion_ok:
            raise CheckFailure("Companion observer did not complete for probe correlation")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "probe_correlation_id": probe_corr,
                "review_turn_complete_before": before_review_turn,
                "review_turn_complete_after": max_review_turn,
                "review_tool_activity_after": _tool_activity(client.events(limit=event_limit), agent_id="demo-review-observer"),
                "companion_turn_complete_before": before_companion_turn,
                "companion_turn_complete_after": max_companion_turn,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
