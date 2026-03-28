from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent


NAME = "check_runtime"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    try:
        health = client.health()
        if health.get("status") != "ok":
            raise CheckFailure(f"Health status is not ok: {health}")

        nodes = client.nodes()
        if not nodes:
            raise CheckFailure("Expected non-empty /api/nodes")

        edges = client.edges()
        _ = client.events(limit=5)

        target_node = ""
        for node in nodes:
            if str(node.get("node_type", "")) == "function":
                target_node = str(node.get("node_id", ""))
                if target_node:
                    break
        if not target_node:
            raise CheckFailure("Unable to resolve target function node for /api/chat")

        chat = client.chat(target_node, "demo_echo")
        ensure_chat_sent(chat, error_prefix="Expected /api/chat status=sent")

        virtual_count = sum(1 for node in nodes if str(node.get("node_type", "")) == "virtual")
        if virtual_count < 2:
            raise CheckFailure("Expected at least 2 virtual nodes")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "nodes": len(nodes),
                "edges": len(edges),
                "virtual_nodes": virtual_count,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
