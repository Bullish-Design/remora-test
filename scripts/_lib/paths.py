from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest import DemoConfigError

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEMO_ID = "00_repo_baseline"


def resolve_paths(manifest: dict[str, Any], profile: str, repo_root: Path = REPO_ROOT) -> dict[str, Path | str | int]:
    demo_root = repo_root / "demo" / str(manifest["demo_id"])

    project_root = Path(str(manifest["project_root"]))
    if not project_root.is_absolute():
        project_root = (repo_root / project_root).resolve()

    config_key = "config_path"
    if profile == "constrained":
        config_key = "constrained_config_path"
    elif profile == "stress":
        config_key = "stress_config_path"

    raw_config_path = manifest.get(config_key) or manifest["config_path"]
    config_path = (repo_root / str(raw_config_path)).resolve()

    workspace_root_name = str(manifest["workspace_root"])
    workspace_root = (project_root / workspace_root_name).resolve()

    raw_repo_dir = str(manifest.get("repo_dir", f"/tmp/remora-demo-{manifest['demo_id']}"))
    repo_dir = Path(raw_repo_dir)

    return {
        "demo_root": demo_root.resolve(),
        "project_root": project_root,
        "config_path": config_path,
        "repo_dir": repo_dir,
        "workspace_root": workspace_root,
        "workspace_root_name": workspace_root_name,
        "port": int(manifest["port"]),
        "base_url": str(manifest["base_url"]).rstrip("/"),
    }


def ensure_path_safe_for_delete(
    path: Path,
    *,
    allow_repo_subpaths: bool = False,
    repo_root: Path = REPO_ROOT,
) -> None:
    candidate = path
    if candidate.is_symlink():
        raise DemoConfigError(f"Refusing to delete symlink path: {candidate}")

    target = candidate.resolve(strict=False)
    root = repo_root.resolve()

    banned = {Path("/"), Path.home().resolve(), root}
    if target in banned:
        raise DemoConfigError(f"Refusing to delete unsafe path: {target}")

    if not str(target):
        raise DemoConfigError("Refusing to delete empty path")

    if str(target).startswith("/tmp/remora-demo-"):
        return

    if allow_repo_subpaths and root in target.parents:
        return

    raise DemoConfigError(f"Refusing to delete path outside allowlist: {target}")


def delete_if_exists(path: Path, *, allow_repo_subpaths: bool = False, repo_root: Path = REPO_ROOT) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    ensure_path_safe_for_delete(path, allow_repo_subpaths=allow_repo_subpaths, repo_root=repo_root)
    if path.is_symlink() or path.is_file():
        try:
            path.unlink(missing_ok=True)
        except FileNotFoundError:
            return False
        return True
    import shutil

    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return False
    return True
