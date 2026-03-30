from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient


NAME = "check_graph_boot"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)

    try:
        health = client.health()
        if health.get("status") != "ok":
            raise CheckFailure(f"Health status is not ok: {health}")

        nodes = client.nodes()
        edges = client.edges()
        events = client.events(limit=20)

        if not nodes:
            raise CheckFailure("Expected non-empty /api/nodes for cloned repository")
        if not edges:
            raise CheckFailure("Expected non-empty /api/edges for cloned repository")

        function_nodes = sum(1 for node in nodes if str(node.get("node_type", "")) == "function")
        class_nodes = sum(1 for node in nodes if str(node.get("node_type", "")) == "class")
        if function_nodes <= 0:
            raise CheckFailure("Expected at least one function node")

        src_path_seen = any("/src/" in str(node.get("file_path", "")) for node in nodes)
        if not src_path_seen:
            raise CheckFailure("Expected discovered nodes under a src/ path")

        edge_type_counts: dict[str, int] = {}
        for edge in edges:
            edge_type = str(edge.get("edge_type", ""))
            edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "event_count": len(events),
                "function_nodes": function_nodes,
                "class_nodes": class_nodes,
                "edge_type_counts": dict(sorted(edge_type_counts.items())),
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
