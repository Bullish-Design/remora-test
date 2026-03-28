from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import signal
import shutil
import subprocess
import tempfile
import time
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal host envs
    yaml = None  # type: ignore[assignment]

from .http import wait_for_raw_json
from .manifest import DemoConfigError
from .paths import REPO_ROOT


@dataclass(frozen=True)
class SearchStackConfig:
    embeddy_url: str
    mock_embedder_url: str


@dataclass
class SearchStackProcesses:
    mock_proc: subprocess.Popen[str]
    embeddy_proc: subprocess.Popen[str]


def build_command_prefix(command_prefix: str | None) -> list[str]:
    if command_prefix:
        return shlex.split(command_prefix)
    if shutil.which("devenv"):
        return ["devenv", "shell", "--"]
    return []


def prefix_command(prefix: list[str], command: list[str]) -> list[str]:
    return [*prefix, *command]


def start_runtime_process(
    project_root: Path,
    config_path: Path,
    port: int,
    log_level: str,
    *,
    env: dict[str, str] | None = None,
    command_prefix: list[str] | None = None,
) -> subprocess.Popen[str]:
    prefix = command_prefix or []
    cmd = prefix_command(
        prefix,
        [
            "remora",
            "start",
            "--project-root",
            str(project_root),
            "--config",
            str(config_path),
            "--port",
            str(port),
            "--bind",
            "127.0.0.1",
            "--log-level",
            log_level,
            "--log-events",
        ],
    )
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )


def _resolve_url_template(raw: str, env: dict[str, str]) -> str:
    value = raw.strip()
    if value.startswith("${") and value.endswith("}") and ":-" in value:
        inner = value[2:-1]
        name, _, default = inner.partition(":-")
        return env.get(name, default)
    if value.startswith("${") and value.endswith("}"):
        name = value[2:-1]
        return env.get(name, "")
    return value


def _parse_search_stack_config(config_path: Path, env: dict[str, str], manifest: dict[str, Any]) -> SearchStackConfig:
    if yaml is None:
        raise DemoConfigError("PyYAML is required for search-stack config parsing. Install pyyaml.")
    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config_payload, dict):
        raise DemoConfigError(f"Invalid config format: {config_path}")

    search_block = config_payload.get("search")
    if not isinstance(search_block, dict):
        raise DemoConfigError(f"Config missing search block: {config_path}")

    raw_embeddy_url = str(search_block.get("embeddy_url", "http://127.0.0.1:8585"))
    embeddy_url = _resolve_url_template(raw_embeddy_url, env)
    if not embeddy_url:
        embeddy_url = "http://127.0.0.1:8585"

    mock_embedder_url = str(manifest.get("mock_embedder_url", "http://127.0.0.1:8586"))
    mock_embedder_url = _resolve_url_template(mock_embedder_url, env)
    if not mock_embedder_url:
        mock_embedder_url = "http://127.0.0.1:8586"

    return SearchStackConfig(embeddy_url=embeddy_url, mock_embedder_url=mock_embedder_url)


def _url_host_port(raw_url: str, fallback_host: str, fallback_port: int) -> tuple[str, int]:
    parsed = urlparse(raw_url)
    host = parsed.hostname or fallback_host
    port = parsed.port or fallback_port
    return host, port


def _build_embeddy_config(
    embeddy_template_path: Path,
    stack_config: SearchStackConfig,
) -> Path:
    if yaml is None:
        raise DemoConfigError("PyYAML is required for embeddy config generation. Install pyyaml.")
    payload = yaml.safe_load(embeddy_template_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DemoConfigError(f"Invalid embeddy config format: {embeddy_template_path}")

    emb_host, emb_port = _url_host_port(stack_config.embeddy_url, "127.0.0.1", 8585)
    mock_host, mock_port = _url_host_port(stack_config.mock_embedder_url, "127.0.0.1", 8586)

    server = payload.get("server")
    if not isinstance(server, dict):
        server = {}
        payload["server"] = server
    server["host"] = emb_host
    server["port"] = emb_port

    embedder = payload.get("embedder")
    if not isinstance(embedder, dict):
        embedder = {}
        payload["embedder"] = embedder
    embedder["remote_url"] = f"http://{mock_host}:{mock_port}"

    fd, temp_path = tempfile.mkstemp(prefix="democtl-embeddy-config-", suffix=".yaml", dir="/tmp")
    os.close(fd)
    out_path = Path(temp_path)
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return out_path


def start_search_stack(
    paths: dict[str, Path | str | int],
    manifest: dict[str, Any],
    env: dict[str, str],
    timeout_s: float,
    *,
    command_prefix: list[str] | None = None,
) -> tuple[SearchStackProcesses, Path]:
    prefix = command_prefix or []
    demo_script_dir = (paths["demo_root"] / "scripts").resolve()  # type: ignore[operator]
    mock_script = demo_script_dir / "mock_embedder_server.py"
    embeddy_template = (REPO_ROOT / "configs/embeddy.remote.yaml").resolve()
    config_path = Path(str(paths["config_path"]))

    if not mock_script.exists():
        raise DemoConfigError(f"Missing mock embedder server script: {mock_script}")
    if not embeddy_template.exists():
        raise DemoConfigError(f"Missing embeddy config: {embeddy_template}")

    stack_config = _parse_search_stack_config(config_path, env, manifest)
    embedy_cfg = _build_embeddy_config(embeddy_template, stack_config)

    mock_host, mock_port = _url_host_port(stack_config.mock_embedder_url, "127.0.0.1", 8586)

    mock_env = env.copy()
    mock_env["MOCK_EMBED_HOST"] = mock_host
    mock_env["MOCK_EMBED_PORT"] = str(mock_port)

    embeddy_cmd = prefix_command(prefix, ["embeddy", "serve", "--config", str(embedy_cfg)])
    mock_cmd = prefix_command(prefix, ["python", str(mock_script)])

    mock_log = Path(tempfile.gettempdir()) / f"democtl-mock-embedder-{int(time.time())}.log"
    embeddy_log = Path(tempfile.gettempdir()) / f"democtl-embeddy-{int(time.time())}.log"

    mock_handle = mock_log.open("w", encoding="utf-8")
    embeddy_handle = embeddy_log.open("w", encoding="utf-8")

    embeddy_proc = subprocess.Popen(
        embeddy_cmd,
        stdout=embeddy_handle,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    embeddy_handle.close()

    if not wait_for_raw_json(f"{stack_config.embeddy_url.rstrip('/')}/api/v1/health", timeout_s=timeout_s):
        stop_process(embeddy_proc)
        mock_handle.close()
        emb_tail = embeddy_log.read_text(encoding="utf-8", errors="replace")[-2000:] if embeddy_log.exists() else ""
        raise DemoConfigError(
            "Embeddy did not become healthy on "
            f"{stack_config.embeddy_url.rstrip('/')}/api/v1/health\n"
            f"embeddy_pid={embeddy_proc.pid} returncode={embeddy_proc.poll()} log={embeddy_log}\n{emb_tail}"
        )

    mock_proc = subprocess.Popen(
        mock_cmd,
        stdout=mock_handle,
        stderr=subprocess.STDOUT,
        text=True,
        env=mock_env,
    )
    mock_handle.close()

    if not wait_for_raw_json(f"{stack_config.mock_embedder_url.rstrip('/')}/health", timeout_s=timeout_s):
        stop_process(embeddy_proc)
        stop_process(mock_proc)
        mock_tail = mock_log.read_text(encoding="utf-8", errors="replace")[-2000:] if mock_log.exists() else ""
        emb_tail = embeddy_log.read_text(encoding="utf-8", errors="replace")[-2000:] if embeddy_log.exists() else ""
        raise DemoConfigError(
            "Mock embedder did not become healthy on "
            f"{stack_config.mock_embedder_url.rstrip('/')}/health\n"
            f"mock_pid={mock_proc.pid} returncode={mock_proc.poll()} log={mock_log}\n{mock_tail}\n"
            f"embeddy_pid={embeddy_proc.pid} returncode={embeddy_proc.poll()} log={embeddy_log}\n{emb_tail}"
        )

    return SearchStackProcesses(mock_proc=mock_proc, embeddy_proc=embeddy_proc), embedy_cfg


def stop_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
