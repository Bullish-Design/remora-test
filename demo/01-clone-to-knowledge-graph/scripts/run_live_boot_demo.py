#!/usr/bin/env python3
"""Run Idea #6 in progressive mode so nodes/edges appear while clone writes files."""

from __future__ import annotations

import argparse
import os
import json
from pathlib import Path
import signal
import shlex
import shutil
import subprocess
import threading
import time
from typing import Any
import urllib.error
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "demo/01-clone-to-knowledge-graph/config/remora.live_boot.yaml"
DEFAULT_PROJECT_ROOT = REPO_ROOT / "demo/01-clone-to-knowledge-graph/repo/blinker"
DEFAULT_WORKSPACE_ROOT = (
    REPO_ROOT / "demo/01-clone-to-knowledge-graph/repo/.remora-01-clone-to-knowledge-graph-live-boot"
)
DEFAULT_REPO_URL = "https://github.com/pallets-eco/blinker.git"
DEFAULT_BASE_URL = "http://127.0.0.1:8081"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run progressive clone-to-knowledge-graph demo (reference: blinker)"
    )
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--project-root", default=str(DEFAULT_PROJECT_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG))
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--clone-depth", type=int, default=1)
    parser.add_argument("--health-timeout-s", type=float, default=60.0)
    parser.add_argument("--poll-interval-s", type=float, default=1.0)
    parser.add_argument("--settle-s", type=float, default=15.0)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument(
        "--command-prefix",
        default="",
        help="Optional command prefix, e.g. 'devenv shell --'",
    )
    parser.add_argument(
        "--keep-running",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep runtime open after clone for live UI inspection",
    )
    return parser.parse_args()


def _safe_delete(path: Path) -> None:
    local_demo_root = (REPO_ROOT / "demo/01-clone-to-knowledge-graph").resolve()
    prefixes = ("/tmp/remora-demo-", "/tmp/remora-workspaces/")
    resolved = path.resolve(strict=False)
    in_tmp_allowlist = any(str(resolved).startswith(prefix) for prefix in prefixes)
    in_local_demo = local_demo_root == resolved or local_demo_root in resolved.parents
    if not in_tmp_allowlist and not in_local_demo:
        raise SystemExit(f"Refusing to delete unsafe path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def _request_json(url: str, timeout_s: float = 3.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout_s) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _wait_for_health(base_url: str, timeout_s: float, proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + timeout_s
    url = f"{base_url.rstrip('/')}/api/health"
    while time.time() < deadline:
        if proc.poll() is not None:
            raise SystemExit(f"remora start exited early with code {proc.returncode}")
        try:
            payload = _request_json(url)
            if isinstance(payload, dict) and payload.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit(f"Runtime did not become healthy at {url} within {timeout_s}s")


def _graph_counts(base_url: str) -> tuple[int | None, int | None]:
    try:
        nodes = _request_json(f"{base_url.rstrip('/')}/api/nodes")
        edges = _request_json(f"{base_url.rstrip('/')}/api/edges")
        node_count = len(nodes) if isinstance(nodes, list) else None
        edge_count = len(edges) if isinstance(edges, list) else None
        return node_count, edge_count
    except Exception:
        return None, None


def _start_count_monitor(base_url: str, interval_s: float) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()

    def _run() -> None:
        last: tuple[int | None, int | None] = (-1, -1)
        while not stop_event.is_set():
            counts = _graph_counts(base_url)
            if counts != last:
                nodes, edges = counts
                print(f"[graph] nodes={nodes} edges={edges}")
                last = counts
            stop_event.wait(interval_s)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return stop_event, thread


def _terminate_runtime(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return

    def _kill_group(sig: int) -> None:
        if os.name == "nt":
            if sig == signal.SIGTERM:
                proc.terminate()
            else:
                proc.kill()
            return
        os.killpg(proc.pid, sig)

    try:
        _kill_group(signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        proc.wait(timeout=10.0)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        _kill_group(signal.SIGKILL)
    except ProcessLookupError:
        return
    proc.wait(timeout=5.0)


def main() -> int:
    args = _parse_args()

    project_root = Path(args.project_root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    config_path = Path(args.config_path).resolve()
    base_url = args.base.rstrip("/")

    if not config_path.exists():
        raise SystemExit(f"Config path not found: {config_path}")

    print("Preparing clean live-boot directories...")
    _safe_delete(project_root)
    _safe_delete(workspace_root)
    project_root.mkdir(parents=True, exist_ok=True)
    workspace_root.parent.mkdir(parents=True, exist_ok=True)

    if any(project_root.iterdir()):
        raise SystemExit(f"Project root must be empty before clone: {project_root}")

    prefix = shlex.split(args.command_prefix) if args.command_prefix.strip() else []
    runtime_cmd = [
        *prefix,
        "remora",
        "start",
        "--project-root",
        str(project_root),
        "--config",
        str(config_path),
        "--port",
        str(args.port),
        "--bind",
        args.bind,
        "--log-level",
        args.log_level,
        "--log-events",
    ]
    print(f"Starting runtime: {' '.join(runtime_cmd)}")
    runtime_env = os.environ.copy()
    runtime_env["REMORA_WORKSPACE_ROOT"] = str(workspace_root)
    runtime_proc = subprocess.Popen(
        runtime_cmd,
        text=True,
        env=runtime_env,
        start_new_session=True,
    )

    monitor_stop: threading.Event | None = None
    monitor_thread: threading.Thread | None = None
    try:
        _wait_for_health(base_url, timeout_s=args.health_timeout_s, proc=runtime_proc)
        print(f"Runtime healthy at {base_url}/api/health")
        print(f"Open UI now: {base_url}/")

        monitor_stop, monitor_thread = _start_count_monitor(base_url, interval_s=args.poll_interval_s)
        time.sleep(1.0)

        clone_cmd = [
            "git",
            "clone",
            f"--depth={args.clone_depth}",
            args.repo_url,
            str(project_root),
        ]
        print(f"Cloning repository into live project root: {' '.join(clone_cmd)}")
        clone_proc = subprocess.run(clone_cmd, text=True, check=False)
        if clone_proc.returncode != 0:
            raise SystemExit(f"git clone failed with exit code {clone_proc.returncode}")

        print(f"Clone finished. Waiting {args.settle_s:.1f}s for graph to settle...")
        time.sleep(max(args.settle_s, 0.0))

        nodes, edges = _graph_counts(base_url)
        print(f"Final graph counts: nodes={nodes} edges={edges}")
        print("Tip: verify SSE replay with:")
        print(f"  curl -sN '{base_url}/sse?replay=80&once=true'")

        if args.keep_running:
            print("Runtime kept alive for UI observation. Press Ctrl+C to stop.")
            while True:
                time.sleep(1.0)
        return 0
    except KeyboardInterrupt:
        print("Interrupted, shutting down.")
        return 130
    finally:
        if monitor_stop is not None:
            monitor_stop.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=2.0)
        _terminate_runtime(runtime_proc)


if __name__ == "__main__":
    raise SystemExit(main())
