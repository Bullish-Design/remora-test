from __future__ import annotations

import json
import time
from typing import Any
import urllib.request


def http_json(url: str, timeout_s: float = 5.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_health(base_url: str, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            payload = http_json(f"{base_url}/api/health", timeout_s=2.0)
            if isinstance(payload, dict) and payload.get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def wait_for_raw_json(url: str, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            payload = http_json(url, timeout_s=2.0)
            if isinstance(payload, dict):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))
