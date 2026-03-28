from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient


NAME = "check_smoke"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)

    try:
        health = client.health()
        if health.get("status") != "ok":
            raise CheckFailure(f"Health check failed: {health}")

        nodes = client.nodes()
        edges = client.edges()
        _ = client.events(limit=5)

        if not nodes:
            raise CheckFailure("No nodes available for smoke check")

        node_id = str(nodes[0].get("node_id", ""))
        if not node_id:
            raise CheckFailure("First node missing node_id")

        chat = client.chat(node_id, "What do you do?")
        if str(chat.get("status", "")) != "sent":
            raise CheckFailure(f"Smoke chat failed: {chat}")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={"node_count": len(nodes), "edge_count": len(edges), "chat": chat},
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
