#!/usr/bin/env python3
"""CLI entrypoint for demo setup, cleanup, execution, and verification."""

from __future__ import annotations

import argparse

from _lib.commands import (
    cmd_cleanup,
    cmd_queries,
    cmd_setup,
    cmd_start,
    cmd_status,
    cmd_verify,
    cmd_wipe,
)
from _lib.manifest import DemoConfigError, load_manifest
from _lib.paths import DEFAULT_DEMO_ID, REPO_ROOT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage remora demos")
    parser.add_argument(
        "command",
        choices=["setup", "start", "status", "queries", "cleanup", "wipe", "verify"],
        help="Command to run",
    )
    parser.add_argument("--demo", default=DEFAULT_DEMO_ID, help="Demo id under demo/")
    parser.add_argument("--profile", choices=["default", "constrained", "stress"], default="default")
    parser.add_argument("--force", action="store_true", help="Required for destructive commands")
    parser.add_argument("--clean-workspace", action="store_true", help="Used by setup")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int)
    parser.add_argument("--base", help="Override base URL")

    parser.add_argument("--strict", action="store_true", help="Strict verification mode")
    parser.add_argument(
        "--command-prefix",
        help="Optional command prefix, e.g. 'devenv shell --'. Auto-detected when omitted.",
    )
    parser.add_argument(
        "--no-start-runtime",
        action="store_true",
        help="Run verify against an existing runtime",
    )
    parser.add_argument(
        "--start-search-stack",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Start mock embedder + embeddy before verify (default: true)",
    )
    parser.add_argument(
        "--require-web",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Require web/API checks during verify (default: strict + manifest requires.web)",
    )
    parser.add_argument(
        "--require-search",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Require search checks during verify (default: strict + manifest requires.search)",
    )
    parser.add_argument(
        "--require-lsp-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Require LSP bridge checks during verify (default: strict + manifest requires.lsp)",
    )
    parser.add_argument(
        "--run-lsp-bridge",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run LSP bridge checks during verify (default: manifest requires.lsp)",
    )
    parser.add_argument(
        "--run-guardrails",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run runtime overflow/guardrail checks during verify (default: false)",
    )
    parser.add_argument(
        "--require-overflow",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Require overflow growth in guardrail check",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        help="Verify-only: run only selected check names (repeatable)",
    )

    parser.add_argument("--health-timeout-s", type=float, default=60.0)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--log-events", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    manifest = load_manifest(args.demo, REPO_ROOT)

    if args.command == "setup":
        return cmd_setup(manifest, args)
    if args.command == "start":
        return cmd_start(manifest, args)
    if args.command == "status":
        return cmd_status(manifest, args)
    if args.command == "queries":
        return cmd_queries(manifest, args)
    if args.command == "cleanup":
        return cmd_cleanup(manifest, args)
    if args.command == "wipe":
        return cmd_wipe(manifest, args)
    if args.command == "verify":
        return cmd_verify(manifest, args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DemoConfigError as exc:
        raise SystemExit(f"democtl error: {exc}") from exc
