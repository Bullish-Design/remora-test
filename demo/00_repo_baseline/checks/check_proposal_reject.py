from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent, event_agent_id, find_node


NAME = "check_proposal_reject"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = 25.0
    poll_interval_s = 1.0

    try:
        nodes = client.nodes()
        target = find_node(nodes, file_suffix="/src/services/pricing.py", name="compute_total")
        if target is None:
            raise CheckFailure("Unable to resolve target node for compute_total")
        target_node = str(target.get("node_id", ""))
        if not target_node:
            raise CheckFailure("Target node missing node_id")

        start_ts = time.time()
        chat = client.chat(target_node, f"rewrite_to_magic reject_probe_{int(time.time())}")
        ensure_chat_sent(chat, error_prefix="Chat send failed for proposal-flow trigger")

        proposal_event: dict | None = None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=400)
            for event in events:
                if str(event.get("event_type", "")) != "rewrite_proposal":
                    continue
                if event_agent_id(event) != target_node:
                    continue
                if float(event.get("timestamp", 0.0)) < start_ts:
                    continue
                proposal_event = event
                break
            if proposal_event is not None:
                break
            time.sleep(poll_interval_s)

        if proposal_event is None:
            raise CheckFailure(f"No rewrite_proposal event found for {target_node}")

        status, diff_payload = client.proposal_diff(target_node)
        if status != 200 or not isinstance(diff_payload, dict):
            raise CheckFailure(f"Proposal diff failed: status={status} payload={diff_payload}")

        status, reject_payload = client.proposal_reject(target_node, "demo reviewed and rejected intentionally")
        if status != 200 or not isinstance(reject_payload, dict):
            raise CheckFailure(f"Proposal reject failed: status={status} payload={reject_payload}")
        if str(reject_payload.get("status", "")) != "rejected":
            raise CheckFailure(f"Unexpected reject status payload: {reject_payload}")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "target_node": target_node,
                "proposal_id": proposal_event.get("payload", {}).get("proposal_id"),
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
