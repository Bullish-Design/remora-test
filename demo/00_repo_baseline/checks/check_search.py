from __future__ import annotations

import os
import re
import time
from typing import Any

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, run_command


NAME = "check_search"


def _parse_index_error_count(log: str) -> int | None:
    lines = [line.strip() for line in log.splitlines() if line.strip()]
    for line in reversed(lines):
        match = re.search(r"Done: .*? (\d+) errors", line)
        if match:
            return int(match.group(1))
    return None


def _required_search_keys(payload: dict[str, Any]) -> bool:
    return all(
        key in payload
        for key in ["results", "query", "collection", "mode", "total_results", "elapsed_ms"]
    )


def _resolve_max_index_errors(require_search: bool) -> int:
    raw = os.getenv("MAX_INDEX_ERRORS", "").strip()
    if raw:
        try:
            value = int(raw)
        except ValueError:
            raise CheckFailure(f"MAX_INDEX_ERRORS must be an integer, got: {raw!r}") from None
        if value < 0:
            raise CheckFailure(f"MAX_INDEX_ERRORS must be >= 0, got: {value}")
        return value
    return 0 if require_search else 999999


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    client = RemoraClient(ctx.base_url)

    query = "compute_total"
    collection = "code"
    top_k = 5
    mode = "hybrid"

    try:
        health = client.health()
        if health.get("status") != "ok":
            raise CheckFailure(f"Runtime health endpoint did not return status=ok: {health}")

        index_proc = run_command(
            [
                "remora",
                "index",
                "--project-root",
                str(ctx.project_root),
                "--config",
                str(ctx.config_path),
            ],
            prefix=ctx.command_prefix,
            cwd=ctx.project_root,
        )
        index_log = f"{index_proc.stdout}\n{index_proc.stderr}"

        if index_proc.returncode != 0:
            if not ctx.require_search:
                return CheckResult(
                    name=NAME,
                    passed=True,
                    skipped=True,
                    skip_reason="Search index unavailable in this environment",
                    detail=index_log[-1200:],
                    duration_s=time.time() - started,
                )
            raise CheckFailure(f"remora index failed. Last output:\n{index_log[-1200:]}")

        max_index_errors = _resolve_max_index_errors(ctx.require_search)
        index_error_count = _parse_index_error_count(index_log)
        if index_error_count is None:
            if ctx.require_search:
                raise CheckFailure(
                    "Unable to parse index error count from remora index output in strict mode."
                )
            index_error_count = 0

        if index_error_count > max_index_errors:
            raise CheckFailure(
                f"Indexing reported too many errors: {index_error_count} (max allowed: {max_index_errors})"
            )

        status, payload = client.search(query, collection=collection, top_k=top_k, mode=mode)
        if status != 200:
            if status == 503 and not ctx.require_search:
                return CheckResult(
                    name=NAME,
                    passed=True,
                    skipped=True,
                    skip_reason="Search service unavailable",
                    detail=str(payload),
                    duration_s=time.time() - started,
                )
            raise CheckFailure(f"Search request failed with HTTP {status}: {payload}")

        if not isinstance(payload, dict):
            raise CheckFailure(f"Search response was not a JSON object: {payload}")

        if not _required_search_keys(payload):
            raise CheckFailure(f"Search response missing required keys: {payload}")

        if str(payload.get("query", "")) != query:
            raise CheckFailure(f"Search response query mismatch: {payload}")
        if str(payload.get("collection", "")) != collection:
            raise CheckFailure(f"Search response collection mismatch: {payload}")
        if str(payload.get("mode", "")) != mode:
            raise CheckFailure(f"Search response mode mismatch: {payload}")

        results = payload.get("results")
        if not isinstance(results, list):
            raise CheckFailure(f"Search response results is not an array: {payload}")
        total_results = payload.get("total_results")
        if not isinstance(total_results, (int, float)) or int(total_results) < 1:
            raise CheckFailure(f"Expected at least one search result after indexing: {payload}")

        first_result = results[0] if results else None
        if first_result is not None and not isinstance(first_result, dict):
            raise CheckFailure(f"Search response first result has unexpected shape: {payload}")

        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "query": payload.get("query"),
                "collection": payload.get("collection"),
                "mode": payload.get("mode"),
                "total_results": payload.get("total_results"),
                "elapsed_ms": payload.get("elapsed_ms"),
                "max_index_errors": max_index_errors,
                "index_error_count": index_error_count,
                "first_result": first_result,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
