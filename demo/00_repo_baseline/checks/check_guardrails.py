from __future__ import annotations

import concurrent.futures
import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent


NAME = "check_guardrails"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    if not ctx.run_guardrails:
        return CheckResult(name=NAME, passed=True, skipped=True, skip_reason="Guardrail check disabled", duration_s=0.0)

    client = RemoraClient(ctx.base_url)
    burst_count = 80

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        target_node = ""
        for node in nodes:
            if str(node.get("node_type", "")) == "function":
                target_node = str(node.get("node_id", ""))
                if target_node:
                    break
        if not target_node:
            raise CheckFailure("Unable to resolve target node for guardrail check")

        health_before = client.health()
        overflow_before = int(health_before.get("metrics", {}).get("actor_inbox_overflow_total", 0))
        dropped_before = int(health_before.get("metrics", {}).get("actor_inbox_dropped_new_total", 0))

        def _send(idx: int) -> None:
            msg = f"guardrail_burst_{idx}_{int(time.time() * 1_000_000)}"
            resp = client.chat(target_node, msg)
            ensure_chat_sent(resp, error_prefix="Guardrail burst chat failed")

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            list(pool.map(_send, range(1, burst_count + 1)))

        time.sleep(2)

        health_after = client.health()
        metrics = health_after.get("metrics", {})
        if not isinstance(metrics, dict):
            raise CheckFailure(f"Health metrics payload missing expected object: {health_after}")

        overflow_after = int(metrics.get("actor_inbox_overflow_total", 0))
        dropped_after = int(metrics.get("actor_inbox_dropped_new_total", 0))

        for required_key in ["actor_inbox_overflow_total", "pending_inbox_items", "active_actors"]:
            if required_key not in metrics:
                raise CheckFailure(f"Health metrics payload missing expected field: {required_key}")

        delta_overflow = overflow_after - overflow_before
        if ctx.require_overflow and delta_overflow <= 0:
            raise CheckFailure(
                "Expected overflow growth but none observed. "
                "Start runtime with demo/00_repo_baseline/config/remora.stress.yaml and retry."
            )

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "overflow_before": overflow_before,
                "overflow_after": overflow_after,
                "dropped_new_before": dropped_before,
                "dropped_new_after": dropped_after,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
