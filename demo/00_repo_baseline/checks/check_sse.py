from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent


NAME = "check_sse"


def _extract_last_event_id(sse_payload: str) -> str:
    last = ""
    for line in sse_payload.splitlines():
        if line.startswith("id: "):
            last = line[4:].strip()
    return last


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        function_nodes = [str(node.get("node_id", "")) for node in nodes if str(node.get("node_type", "")) == "function"]
        if not function_nodes:
            raise CheckFailure("Unable to resolve target node for SSE contract")
        target_node = function_nodes[0]

        token1 = f"sse_probe_one_{int(time.time())}"
        token2 = f"sse_probe_two_{int(time.time())}"

        ensure_chat_sent(client.chat(target_node, f"demo_echo {token1}"), error_prefix="SSE token1 chat failed")
        time.sleep(2)

        replay_out = client.sse(replay=200, once=True).replace("\r", "")
        if token1 not in replay_out:
            raise CheckFailure("SSE replay output did not include first probe token")

        last_id = _extract_last_event_id(replay_out)
        if not last_id:
            raise CheckFailure("Unable to resolve Last-Event-ID from replay output")

        ensure_chat_sent(client.chat(target_node, f"demo_echo {token2}"), error_prefix="SSE token2 chat failed")
        time.sleep(2)

        resume_out = client.sse(once=True, last_event_id=last_id).replace("\r", "")
        if token2 not in resume_out:
            raise CheckFailure(f"SSE resume output did not include second probe token. Output={resume_out}")

        return CheckResult(name=NAME, passed=True, duration_s=time.time() - started)
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
