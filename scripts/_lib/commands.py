from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from .http import http_json, print_json, wait_for_health
from .manifest import DemoConfigError
from .paths import REPO_ROOT, delete_if_exists, ensure_path_safe_for_delete, resolve_paths
from .runtime import (
    build_command_prefix,
    prefix_command,
    start_runtime_process,
    start_search_stack,
    stop_process,
)


def _manifest_requires(manifest: dict[str, Any], key: str) -> bool:
    requires = manifest.get("requires")
    if not isinstance(requires, dict):
        return False
    return bool(requires.get(key, False))


def _bool_flag(name: str, value: bool) -> list[str]:
    return [f"--{name}" if value else f"--no-{name}"]


def cmd_setup(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    demo_root = Path(str(paths["demo_root"]))
    project_root = Path(str(paths["project_root"]))
    config_path = Path(str(paths["config_path"]))

    if not demo_root.exists():
        raise DemoConfigError(f"Demo root missing: {demo_root}")
    if not config_path.exists():
        raise DemoConfigError(f"Config missing: {config_path}")

    repo_url = str(manifest.get("repo_url", "")).strip().lower()
    repo_dir = Path(str(paths["repo_dir"]))
    if repo_url == "local":
        if not project_root.exists():
            raise DemoConfigError(f"Project root missing: {project_root}")
    else:
        if args.force and repo_dir.exists():
            ensure_path_safe_for_delete(repo_dir, allow_repo_subpaths=True)
            shutil.rmtree(repo_dir)
        if not repo_dir.exists():
            repo_dir.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--depth", "1", str(manifest["repo_url"]), str(repo_dir)],
                check=True,
            )
        if not project_root.exists():
            raise DemoConfigError(f"Project root missing after clone: {project_root}")

    if args.clean_workspace:
        workspace_root = Path(str(paths["workspace_root"]))
        if workspace_root.exists() or workspace_root.is_symlink():
            delete_if_exists(workspace_root, allow_repo_subpaths=True)

    print("setup_complete")
    print(f"demo={manifest['demo_id']}")
    print(f"project_root={project_root}")
    print(f"config_path={config_path}")
    print(
        "start_command="
        f"python scripts/democtl.py start --demo {manifest['demo_id']} --profile {args.profile}"
    )
    return 0


def cmd_start(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    project_root = Path(str(paths["project_root"]))
    config_path = Path(str(paths["config_path"]))
    port = args.port if args.port is not None else int(paths["port"])

    prefix = build_command_prefix(args.command_prefix)
    command = prefix_command(
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
            args.bind,
            "--log-level",
            args.log_level,
        ],
    )
    if args.log_events:
        command.append("--log-events")

    return subprocess.run(command, check=False).returncode


def cmd_status(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    base_url = args.base or str(paths["base_url"])
    health = http_json(f"{base_url}/api/health")
    nodes = http_json(f"{base_url}/api/nodes")
    edges = http_json(f"{base_url}/api/edges")

    summary = {
        "base": base_url,
        "health_status": health.get("status") if isinstance(health, dict) else None,
        "nodes": len(nodes) if isinstance(nodes, list) else None,
        "edges": len(edges) if isinstance(edges, list) else None,
    }
    print_json(summary)
    return 0


def cmd_queries(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    base_url = args.base or str(paths["base_url"])

    nodes = http_json(f"{base_url}/api/nodes")
    edges = http_json(f"{base_url}/api/edges")
    events = http_json(f"{base_url}/api/events?limit=10")

    node_type_counts: dict[str, int] = {}
    for node in nodes if isinstance(nodes, list) else []:
        node_type = str(node.get("node_type", ""))
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    edge_type_counts: dict[str, int] = {}
    from_degree: dict[str, int] = {}
    for edge in edges if isinstance(edges, list) else []:
        edge_type = str(edge.get("edge_type", ""))
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
        if edge_type in {"imports", "inherits"}:
            from_id = str(edge.get("from_id", ""))
            from_degree[from_id] = from_degree.get(from_id, 0) + 1

    hotspots = sorted(from_degree.items(), key=lambda item: item[1], reverse=True)[:12]

    payload = {
        "base": base_url,
        "node_count": len(nodes) if isinstance(nodes, list) else None,
        "edge_count": len(edges) if isinstance(edges, list) else None,
        "node_type_counts": dict(sorted(node_type_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "edge_type_counts": dict(sorted(edge_type_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "semantic_hotspots": [{"from_id": node_id, "out_degree": degree} for node_id, degree in hotspots],
        "recent_events": events if isinstance(events, list) else [],
    }
    print_json(payload)
    return 0


def cmd_cleanup(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    workspace_root = Path(str(paths["workspace_root"]))
    deleted = delete_if_exists(workspace_root, allow_repo_subpaths=True)

    print("cleanup_complete")
    print(f"workspace_deleted={int(deleted)}")
    print(f"workspace_path={workspace_root}")
    return 0


def cmd_wipe(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    if not args.force:
        raise DemoConfigError("wipe is destructive; re-run with --force")

    paths = resolve_paths(manifest, args.profile)
    deleted_workspace = delete_if_exists(Path(str(paths["workspace_root"])), allow_repo_subpaths=True)

    repo_dir = Path(str(paths["repo_dir"]))
    repo_url = str(manifest.get("repo_url", "")).strip().lower()
    deleted_repo_dir = False
    if repo_url != "local" and (repo_dir.exists() or repo_dir.is_symlink()):
        deleted_repo_dir = delete_if_exists(repo_dir, allow_repo_subpaths=True)

    print("wipe_complete")
    print(f"workspace_deleted={int(deleted_workspace)}")
    print(f"repo_dir_deleted={int(deleted_repo_dir)}")
    print(f"workspace_path={paths['workspace_root']}")
    print(f"repo_dir_path={repo_dir}")
    return 0


def cmd_verify(manifest: dict[str, Any], args: argparse.Namespace) -> int:
    paths = resolve_paths(manifest, args.profile)
    base_url = args.base or str(paths["base_url"])
    port = args.port if args.port is not None else int(paths["port"])
    strict = bool(args.strict)

    require_web = args.require_web
    if require_web is None:
        require_web = strict and _manifest_requires(manifest, "web")

    require_search = args.require_search
    if require_search is None:
        require_search = strict and _manifest_requires(manifest, "search")

    require_lsp_bridge = args.require_lsp_bridge
    if require_lsp_bridge is None:
        require_lsp_bridge = strict and _manifest_requires(manifest, "lsp")

    require_overflow = args.require_overflow
    if require_overflow is None:
        require_overflow = strict and _manifest_requires(manifest, "guardrails")

    run_lsp_bridge = args.run_lsp_bridge
    if run_lsp_bridge is None:
        run_lsp_bridge = _manifest_requires(manifest, "lsp") or require_lsp_bridge

    run_guardrails = bool(args.run_guardrails)

    prefix = build_command_prefix(args.command_prefix)

    env = os.environ.copy()
    env["BASE"] = base_url
    env["PROJECT_ROOT"] = str(paths["project_root"])
    env["CONFIG_PATH"] = str(paths["config_path"])
    env["REMORA_EMBEDDY_URL"] = env.get("REMORA_EMBEDDY_URL", "http://127.0.0.1:8585")
    env["DEMO_COMMAND_PREFIX"] = " ".join(prefix)

    proc: subprocess.Popen[str] | None = None
    search_procs = None
    embeddy_temp_config: Path | None = None
    try:
        if args.start_search_stack:
            search_procs, embeddy_temp_config = start_search_stack(
                paths,
                manifest,
                env,
                timeout_s=args.health_timeout_s,
                command_prefix=prefix,
            )

        if not args.no_start_runtime:
            proc = start_runtime_process(
                Path(str(paths["project_root"])),
                Path(str(paths["config_path"])),
                port,
                args.log_level,
                log_events=bool(args.log_events),
                env=env,
                command_prefix=prefix,
            )
            if not wait_for_health(base_url, timeout_s=args.health_timeout_s):
                raise DemoConfigError(
                    f"Runtime did not become healthy at {base_url}/api/health within {args.health_timeout_s}s."
                )

        runner_path = (Path(str(paths["demo_root"])) / "checks" / "runner.py").resolve()
        if not runner_path.exists():
            raise DemoConfigError(f"Missing Python check runner: {runner_path}")

        if prefix:
            check_cmd = prefix_command(prefix, ["python", str(runner_path)])
        else:
            check_cmd = [sys.executable, str(runner_path)]

        check_cmd.extend([
            "--base",
            base_url,
            "--project-root",
            str(paths["project_root"]),
            "--config-path",
            str(paths["config_path"]),
        ])
        if strict:
            check_cmd.append("--strict")
        check_cmd.extend(_bool_flag("require-web", bool(require_web)))
        check_cmd.extend(_bool_flag("require-search", bool(require_search)))
        check_cmd.extend(_bool_flag("require-lsp-bridge", bool(require_lsp_bridge)))
        check_cmd.extend(_bool_flag("run-lsp-bridge", bool(run_lsp_bridge)))
        check_cmd.extend(_bool_flag("run-guardrails", bool(run_guardrails)))
        check_cmd.extend(_bool_flag("require-overflow", bool(require_overflow)))
        for check_name in args.filter:
            check_cmd.extend(["--filter", str(check_name)])

        check_proc = subprocess.run(check_cmd, env=env, cwd=REPO_ROOT, text=True, check=False)
        if check_proc.returncode != 0:
            return check_proc.returncode

        health = http_json(f"{base_url}/api/health")
        nodes = http_json(f"{base_url}/api/nodes")
        edges = http_json(f"{base_url}/api/edges")
        summary = {
            "verify": "passed",
            "strict": strict,
            "base": base_url,
            "health_status": health.get("status") if isinstance(health, dict) else None,
            "node_count": len(nodes) if isinstance(nodes, list) else None,
            "edge_count": len(edges) if isinstance(edges, list) else None,
        }
        print_json(summary)
        return 0
    finally:
        if proc is not None:
            stop_process(proc)
        if search_procs is not None:
            stop_process(search_procs.embeddy_proc)
            stop_process(search_procs.mock_proc)
        if embeddy_temp_config is not None:
            embeddy_temp_config.unlink(missing_ok=True)
