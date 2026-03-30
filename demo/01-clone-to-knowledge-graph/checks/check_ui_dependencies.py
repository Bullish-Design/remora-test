from __future__ import annotations

import time
import urllib.request

from _harness import CheckContext, CheckFailure, CheckResult


NAME = "check_ui_dependencies"
EXPECTED_VENDOR_PATHS = (
    "/static/vendor/graphology.umd.min.js",
    "/static/vendor/sigma.min.js",
)


def _fetch_text(url: str, timeout_s: float) -> str:
    with urllib.request.urlopen(url, timeout=timeout_s) as response:
        return response.read().decode("utf-8", errors="replace")


def _fetch_bytes(url: str, timeout_s: float) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout_s) as response:
        return response.read()


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    info: dict[str, object] = {}

    try:
        index_html = _fetch_text(f"{ctx.base_url}/", timeout_s=5.0)
        has_unpkg = any(
            token in index_html
            for token in ("unpkg.com/graphology", "unpkg.com/sigma", "unpkg.com/graphology-layout-forceatlas2")
        )
        info["uses_unpkg_cdn"] = has_unpkg
        if has_unpkg:
            raise CheckFailure("UI index references unpkg CDN; expected upstream packaged /static/vendor assets only")

        missing_refs = [path for path in EXPECTED_VENDOR_PATHS if path not in index_html]
        info["expected_vendor_refs"] = list(EXPECTED_VENDOR_PATHS)
        info["missing_vendor_refs"] = missing_refs
        if missing_refs:
            raise CheckFailure(f"UI index missing expected vendor script refs: {missing_refs}")

        vendor_sizes: dict[str, int] = {}
        for path in EXPECTED_VENDOR_PATHS:
            body = _fetch_bytes(f"{ctx.base_url}{path}", timeout_s=5.0)
            vendor_sizes[path] = len(body)
            if len(body) < 1000:
                raise CheckFailure(f"Vendor asset appears unexpectedly small: {path} ({len(body)} bytes)")
        info["vendor_asset_sizes"] = vendor_sizes

        return CheckResult(name=NAME, passed=True, duration_s=time.time() - started, data=info)
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc), data=info)
