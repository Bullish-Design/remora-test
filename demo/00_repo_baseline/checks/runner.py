#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable

import check_cursor
import check_discovery
import check_guardrails
import check_lsp_bridge
import check_lsp_startup
import check_proposal_accept
import check_proposal_reject
import check_reflection
import check_relationships
import check_runtime
import check_search
import check_smoke
import check_sse
import check_subscriptions
import check_ui_dependencies
import check_ui_playwright
import check_virtual_agents
from _harness import CheckContext, CheckResult, auto_command_prefix


RunFn = Callable[[CheckContext], CheckResult]

CHECKS: dict[str, RunFn] = {
    "check_runtime": check_runtime.run,
    "check_virtual_agents": check_virtual_agents.run,
    "check_reflection": check_reflection.run,
    "check_subscriptions": check_subscriptions.run,
    "check_proposal_reject": check_proposal_reject.run,
    "check_proposal_accept": check_proposal_accept.run,
    "check_discovery": check_discovery.run,
    "check_sse": check_sse.run,
    "check_cursor": check_cursor.run,
    "check_relationships": check_relationships.run,
    "check_search": check_search.run,
    "check_smoke": check_smoke.run,
    "check_lsp_startup": check_lsp_startup.run,
    "check_lsp_bridge": check_lsp_bridge.run,
    "check_guardrails": check_guardrails.run,
    "check_ui_dependencies": check_ui_dependencies.run,
    "check_ui_playwright": check_ui_playwright.run,
}

DEFAULT_ORDER = [
    "check_runtime",
    "check_virtual_agents",
    "check_reflection",
    "check_subscriptions",
    "check_proposal_reject",
    "check_proposal_accept",
    "check_discovery",
    "check_sse",
    "check_cursor",
    "check_relationships",
    "check_search",
    "check_ui_dependencies",
    "check_ui_playwright",
    "check_lsp_startup",
    "check_lsp_bridge",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run demo baseline checks")
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--project-root", default="demo/00_repo_baseline/fixture")
    parser.add_argument("--config-path", default="demo/00_repo_baseline/config/remora.yaml")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-web", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require-search", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--require-lsp-bridge", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--run-lsp-bridge", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--run-guardrails", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--require-overflow", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    return parser


def _selected_checks(args: argparse.Namespace) -> list[str]:
    if args.filter:
        unknown = [name for name in args.filter if name not in CHECKS]
        if unknown:
            raise SystemExit(f"Unknown checks: {unknown}")
        return args.filter

    order = list(DEFAULT_ORDER)
    if args.run_guardrails and "check_guardrails" not in order:
        order.append("check_guardrails")
    return order


def _print_result(result: CheckResult) -> None:
    if result.skipped:
        print(f"SKIP: {result.name} ({result.skip_reason})")
        return
    if result.passed:
        print(f"PASS: {result.name}")
        if result.detail:
            print(result.detail)
        if result.data:
            print(json.dumps(result.data, indent=2, sort_keys=True))
        return
    print(f"FAIL: {result.name}")
    if result.detail:
        print(result.detail)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config_path).resolve()

    ctx = CheckContext(
        base_url=args.base.rstrip("/"),
        project_root=project_root,
        config_path=config_path,
        strict=bool(args.strict),
        require_web=bool(args.require_web),
        require_search=bool(args.require_search),
        require_lsp_bridge=bool(args.require_lsp_bridge),
        run_lsp_bridge=bool(args.run_lsp_bridge),
        run_guardrails=bool(args.run_guardrails),
        require_overflow=bool(args.require_overflow),
        command_prefix=auto_command_prefix(),
    )

    results: list[CheckResult] = []
    failed = False

    for name in _selected_checks(args):
        print(f"==> {name}")
        result = CHECKS[name](ctx)
        results.append(result)
        _print_result(result)
        if result.passed:
            print(f"<== {name} passed")
            continue
        if result.skipped:
            print(f"<== {name} skipped")
            continue
        print(f"<== {name} failed")
        failed = True
        break

    if args.json:
        print(
            json.dumps(
                {
                    "failed": failed,
                    "results": [asdict(result) for result in results],
                },
                indent=2,
                sort_keys=True,
            )
        )

    if failed:
        return 1
    print("All demo checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
