#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable

import check_graph_boot
import check_ui_dependencies
import check_ui_playwright
from _harness import CheckContext, CheckResult, auto_command_prefix


RunFn = Callable[[CheckContext], CheckResult]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "demo/01-clone-to-knowledge-graph/config/remora.yaml"
DEFAULT_PROJECT_ROOT = REPO_ROOT / "demo/01-clone-to-knowledge-graph/repo/blinker"

CHECKS: dict[str, RunFn] = {
    "check_graph_boot": check_graph_boot.run,
    "check_ui_dependencies": check_ui_dependencies.run,
    "check_ui_playwright": check_ui_playwright.run,
}

DEFAULT_ORDER = [
    "check_graph_boot",
    "check_ui_dependencies",
    "check_ui_playwright",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Idea #6 clone-to-knowledge-graph checks (reference: blinker)"
    )
    parser.add_argument("--base", default="http://127.0.0.1:8081")
    parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
    )
    parser.add_argument(
        "--project-root",
        default=str(DEFAULT_PROJECT_ROOT),
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-web", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require-search", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--require-lsp-bridge", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--run-lsp-bridge", action=argparse.BooleanOptionalAction, default=False)
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
    return list(DEFAULT_ORDER)


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
