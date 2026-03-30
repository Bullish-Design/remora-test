#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _lib.playwright_ui import (
    extract_title,
    fetch_html,
    take_playwright_screenshot,
    timestamped_screenshot_path,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture a Playwright UI screenshot with demo-aware artifact paths.")
    parser.add_argument("--url", required=True, help="Target URL, e.g. http://127.0.0.1:8080/")
    parser.add_argument("--project-root", default=".", help="Repository project root")
    parser.add_argument("--config-path", default="demo/00_repo_baseline/config/remora.yaml", help="Demo config path")
    parser.add_argument("--output-dir", help="Override screenshot output directory")
    parser.add_argument("--prefix", default="ui-playwright", help="Screenshot filename prefix")
    parser.add_argument("--timeout-ms", type=int, default=20000, help="Playwright navigation/screenshot timeout")
    parser.add_argument("--wait-for-selector", default="#graph canvas", help="Selector to wait for before capture")
    parser.add_argument("--wait-for-timeout-ms", type=int, default=2500, help="Extra render settle time before capture")
    parser.add_argument("--no-full-page", action="store_true", help="Capture viewport only instead of full page")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config_path)
    if not config_path.is_absolute():
        config_path = (project_root / config_path).resolve()

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    screenshot_path = timestamped_screenshot_path(
        project_root=project_root,
        config_path=config_path,
        output_dir=output_dir,
        prefix=args.prefix,
    )

    html = fetch_html(args.url, timeout_s=10.0)
    if "<html" not in html.lower():
        raise SystemExit(f"error: target did not return HTML content: {args.url}")

    result = take_playwright_screenshot(
        url=args.url,
        output_path=screenshot_path,
        timeout_ms=int(args.timeout_ms),
        wait_for_selector=str(args.wait_for_selector),
        wait_for_timeout_ms=int(args.wait_for_timeout_ms),
        full_page=not bool(args.no_full_page),
        cwd=project_root,
    )
    if result.returncode != 0:
        detail = f"{result.stdout}\n{result.stderr}".strip()[-2000:]
        raise SystemExit(f"error: playwright screenshot failed:\n{detail}")
    if not screenshot_path.exists():
        raise SystemExit(f"error: screenshot file missing after playwright success: {screenshot_path}")

    payload = {
        "url": args.url,
        "title": extract_title(html),
        "screenshot_path": str(screenshot_path),
        "screenshot_size_bytes": screenshot_path.stat().st_size,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(str(screenshot_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
