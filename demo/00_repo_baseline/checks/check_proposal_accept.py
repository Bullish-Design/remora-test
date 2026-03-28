from __future__ import annotations

import time
from pathlib import Path

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, ensure_chat_sent, event_agent_id, find_node


NAME = "check_proposal_accept"


def _cleanup_proposal_artifact(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.unlink()
    except OSError:
        return
    parent = path.parent
    while str(parent) not in {".", "/"}:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)
    timeout_s = 40.0
    poll_interval_s = 1.0

    restore_path: Path | None = None
    original_content: str | None = None
    proposal_artifact_path: Path | None = None

    try:
        if client.health().get("status") != "ok":
            raise CheckFailure("Runtime health check failed")

        nodes = client.nodes()
        target = find_node(nodes, file_suffix="/src/services/pricing.py", name="compute_total")
        if target is None:
            raise CheckFailure("Unable to resolve target node for compute_total")
        target_node = str(target.get("node_id", ""))
        if not target_node:
            raise CheckFailure("Target node missing node_id")

        proposal_artifact_path = ctx.project_root / target_node.lstrip("/")

        start_ts = time.time()
        chat = client.chat(target_node, f"rewrite_to_magic accept_probe_{int(time.time())}")
        ensure_chat_sent(chat, error_prefix="Chat send failed for proposal-accept trigger")

        proposal_event: dict | None = None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            events = client.events(limit=500)
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

        diffs = diff_payload.get("diffs")
        if not isinstance(diffs, list) or not diffs:
            raise CheckFailure("Proposal diff response had no diffs")

        restore_candidate = str(diffs[0].get("file", "")) if isinstance(diffs[0], dict) else ""
        if not restore_candidate:
            raise CheckFailure("Unable to resolve file path from proposal diff")

        restore_path = Path(restore_candidate)
        if not restore_path.exists():
            for diff in diffs:
                if not isinstance(diff, dict):
                    continue
                candidate = Path(str(diff.get("file", "")))
                if candidate.exists():
                    restore_path = candidate
                    break

        if not restore_path.exists():
            raise CheckFailure(f"No existing file path found in proposal diff for node: {target_node}")

        original_content = restore_path.read_text(encoding="utf-8")

        candidates = [
            str(diff.get("new", ""))
            for diff in diffs
            if isinstance(diff, dict) and str(diff.get("file", "")) == str(restore_path)
        ]

        status, accept_payload = client.proposal_accept(target_node)
        if status != 200 or not isinstance(accept_payload, dict):
            raise CheckFailure(f"Proposal accept failed: status={status} payload={accept_payload}")
        if str(accept_payload.get("status", "")) != "accepted":
            raise CheckFailure(f"Unexpected accept status payload: {accept_payload}")

        updated_content = restore_path.read_text(encoding="utf-8")
        if updated_content == original_content:
            raise CheckFailure("Accepted proposal did not mutate target file content")

        if candidates and updated_content not in candidates:
            raise CheckFailure(
                "Accepted proposal mutated file, but content did not match any advertised diff candidate"
            )

        events = client.events(limit=200)
        accepted_seen = False
        content_changed_seen = False
        for event in events:
            event_type = str(event.get("event_type", ""))
            if event_type == "rewrite_accepted" and event_agent_id(event) == target_node:
                accepted_seen = True
            if event_type == "content_changed":
                content_changed_seen = True

        if not accepted_seen:
            raise CheckFailure("rewrite_accepted event for target node not found")
        if not content_changed_seen:
            raise CheckFailure("No content_changed event found after proposal accept")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "target_node": target_node,
                "proposal_id": proposal_event.get("payload", {}).get("proposal_id"),
                "restored_file": str(restore_path),
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
    finally:
        if restore_path is not None and original_content is not None:
            restore_path.write_text(original_content, encoding="utf-8")
        if proposal_artifact_path is not None:
            _cleanup_proposal_artifact(proposal_artifact_path)
