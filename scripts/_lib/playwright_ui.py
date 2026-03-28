from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request


def playwright_executable() -> str:
    raw = os.getenv("PLAYWRIGHT_CLI_PATH", "").strip()
    if raw:
        return raw
    return "playwright"


def fetch_html(url: str, *, timeout_s: float = 10.0) -> str:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to load UI root {url}: {exc}") from exc

    if status != 200:
        raise RuntimeError(f"UI root returned HTTP {status} for {url}")
    return body


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def demo_dir_from_config(project_root: Path, config_path: Path) -> Path:
    resolved = config_path.resolve()
    for candidate in [resolved.parent, *resolved.parents]:
        if candidate.parent.name == "demo":
            return candidate
    return (project_root / "demo" / "unknown_demo").resolve()


def timestamped_screenshot_path(
    *,
    project_root: Path,
    config_path: Path,
    output_dir: Path | None = None,
    prefix: str = "ui-playwright",
) -> Path:
    if output_dir is None:
        demo_dir = demo_dir_from_config(project_root, config_path)
        output_dir = demo_dir / "artifacts" / "ui_screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    millis = int((time.time() % 1.0) * 1000)
    safe_prefix = prefix.strip() or "ui-playwright"
    return output_dir / f"{safe_prefix}-{stamp}-{millis:03d}.png"


def take_playwright_screenshot(
    *,
    url: str,
    output_path: Path,
    timeout_ms: int = 20000,
    wait_for_selector: str = "#graph canvas",
    wait_for_timeout_ms: int = 2500,
    full_page: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [playwright_executable(), "screenshot"]
    if wait_for_selector:
        cmd.extend(["--wait-for-selector", wait_for_selector])
    if wait_for_timeout_ms > 0:
        cmd.extend(["--wait-for-timeout", str(wait_for_timeout_ms)])
    if full_page:
        cmd.append("--full-page")
    cmd.extend(["--timeout", str(timeout_ms), url, str(output_path)])
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=cwd,
        check=False,
    )
