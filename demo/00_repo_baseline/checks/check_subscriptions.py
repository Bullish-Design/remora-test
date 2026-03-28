from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient


NAME = "check_subscriptions"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        virtuals = [str(node.get("node_id", "")) for node in nodes if str(node.get("node_type", "")) == "virtual"]
        for observer in ["demo-src-filter-observer", "demo-docs-filter-observer"]:
            if observer not in virtuals:
                raise CheckFailure(f"Missing virtual observer node: {observer}; found={virtuals}")

        from remora.core.events import NodeChangedEvent, SubscriptionPattern

        src_path = str((ctx.project_root / "src/services/pricing.py").resolve())
        docs_path = str((ctx.project_root / "docs/architecture.md").resolve())

        src_pattern = SubscriptionPattern(event_types=["node_changed"], path_glob="src/**")
        docs_pattern = SubscriptionPattern(event_types=["node_changed"], path_glob="docs/**")

        src_event = NodeChangedEvent(node_id="src-node", old_hash="a", new_hash="b", file_path=src_path)
        docs_event = NodeChangedEvent(node_id="docs-node", old_hash="a", new_hash="b", file_path=docs_path)

        if not src_pattern.matches(src_event):
            raise CheckFailure("src/** should match absolute src path")
        if src_pattern.matches(docs_event):
            raise CheckFailure("src/** should not match docs path")
        if not docs_pattern.matches(docs_event):
            raise CheckFailure("docs/** should match absolute docs path")
        if docs_pattern.matches(src_event):
            raise CheckFailure("docs/** should not match src path")

        return CheckResult(name=NAME, passed=True, duration_s=time.time() - started, detail="path_glob_matching_ok")
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
