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
    find_node,
)


NAME = "check_reflection"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = 30.0
    poll_interval_s = 1.0
    event_limit = 500
    require_companion = True

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        target = find_node(nodes, file_suffix="/src/services/pricing.py", name="compute_total")
        if target is None:
            raise CheckFailure("Unable to resolve target function node for reflection check")
        target_node = str(target.get("node_id", ""))
        if not target_node:
            raise CheckFailure("Target node missing node_id")

        probe_token = f"reflection_probe_{int(time.time())}"
        response = client.chat(target_node, f"Please review this function and respond briefly. token={probe_token}")
        ensure_chat_sent(response, error_prefix="Chat send failed")

        primary_ok = False
        reflection_ok = False
        turn_digested_ok = False
        companion_ok = False
        probe_corr = ""

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=event_limit)

            if not probe_corr:
                for event in events:
                    if str(event.get("event_type", "")) != "agent_complete":
                        continue
                    if event_agent_id(event) != target_node:
                        continue
                    payload = event_payload(event)
                    tags = event.get("tags")
                    if not isinstance(tags, list) or "primary" not in tags:
                        continue
                    if probe_token not in str(payload.get("user_message", "")):
                        continue
                    probe_corr = str(event.get("correlation_id", ""))
                    break

            if probe_corr:
                primary_ok = True
                for event in events:
                    if str(event.get("correlation_id", "")) != probe_corr:
                        continue
                    event_type = str(event.get("event_type", ""))
                    agent_id = event_agent_id(event)
                    tags = event.get("tags")
                    if event_type == "agent_complete" and agent_id == target_node and isinstance(tags, list) and "reflection" in tags:
                        reflection_ok = True
                    if event_type == "turn_digested" and agent_id == target_node:
                        turn_digested_ok = True
                    if event_type in {"turn_complete", "agent_complete"} and agent_id == "demo-companion-observer":
                        companion_ok = True

            if primary_ok and reflection_ok and turn_digested_ok and (companion_ok or not require_companion):
                break
            time.sleep(poll_interval_s)

        if not primary_ok:
            raise CheckFailure("Did not observe primary completion for probe token")
        if not reflection_ok:
            raise CheckFailure("Did not observe reflection completion for probe correlation")
        if not turn_digested_ok:
            raise CheckFailure("Did not observe turn_digested for probe correlation")
        if require_companion and not companion_ok:
            raise CheckFailure("Companion observer did not complete for probe correlation")

        _, companion_payload = client.companion(target_node)

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "target_node": target_node,
                "probe_corr": probe_corr,
                "companion_payload": companion_payload,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
