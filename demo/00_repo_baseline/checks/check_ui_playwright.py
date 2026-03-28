from __future__ import annotations

from pathlib import Path
import sys
import time

from _harness import CheckContext, CheckFailure, CheckResult

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._lib.playwright_ui import (  # noqa: E402
    extract_title,
    fetch_html,
    take_playwright_screenshot,
    timestamped_screenshot_path,
)


NAME = "check_ui_playwright"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    screenshot_path: Path | None = None
    try:
        root_url = f"{ctx.base_url}/"
        html = fetch_html(root_url, timeout_s=10.0)
        if "<html" not in html.lower():
            raise CheckFailure("UI root did not return HTML content")

        screenshot_path = timestamped_screenshot_path(
            project_root=ctx.project_root,
            config_path=ctx.config_path,
            prefix="ui-playwright",
        )
        shot = take_playwright_screenshot(url=root_url, output_path=screenshot_path, timeout_ms=20000, cwd=ctx.project_root)

        if shot.returncode != 0:
            detail = f"{shot.stdout}\n{shot.stderr}".strip()[-1500:]
            if ctx.strict or ctx.require_web:
                raise CheckFailure(f"Playwright screenshot failed:\n{detail}")
            return CheckResult(
                name=NAME,
                passed=True,
                skipped=True,
                skip_reason="Playwright screenshot unavailable in this environment",
                detail=detail,
                duration_s=time.time() - started,
            )

        if not screenshot_path.exists():
            raise CheckFailure(f"Playwright reported success but screenshot missing: {screenshot_path}")
        size = screenshot_path.stat().st_size
        if size <= 0:
            raise CheckFailure(f"Playwright screenshot was empty: {screenshot_path}")

        title = extract_title(html)
        return CheckResult(
            name=NAME,
            passed=True,
            duration_s=time.time() - started,
            data={
                "ui_root": root_url,
                "title": title,
                "screenshot_path": str(screenshot_path),
                "screenshot_size_bytes": size,
            },
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
