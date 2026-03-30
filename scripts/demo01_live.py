#!/usr/bin/env python3
"""Entry point wrapper for the demo/01 live boot script."""

from __future__ import annotations

import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "demo/01-clone-to-knowledge-graph/scripts/run_live_boot_demo.py"
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = [sys.executable, str(SCRIPT_PATH), *args]
    os.execv(sys.executable, cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
