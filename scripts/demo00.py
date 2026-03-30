#!/usr/bin/env python3
"""Pinned democtl entrypoint for demo/00_repo_baseline."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from scripts.democtl import main as democtl_main

DEMO_ID = "00_repo_baseline"


def _contains_demo_flag(args: Sequence[str]) -> bool:
    return any(arg == "--demo" or arg.startswith("--demo=") for arg in args)


def main(argv: list[str] | None = None) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    if not forwarded:
        forwarded = ["--help"]
    if _contains_demo_flag(forwarded):
        raise SystemExit(f"`--demo` is fixed for this entrypoint: {DEMO_ID}")
    return int(democtl_main([*forwarded, "--demo", DEMO_ID]))


if __name__ == "__main__":
    raise SystemExit(main())
