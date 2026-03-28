from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _manifest_paths() -> list[Path]:
    return sorted((REPO_ROOT / "demo").glob("*/demo.yaml"))


def _load_manifest(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"Manifest must be a mapping: {path}"
    return payload


def test_demo_isolation_unique_demo_ids_ports_workspace_roots_and_repo_dirs() -> None:
    demo_ids: list[str] = []
    ports: list[int] = []
    workspace_roots: list[str] = []
    repo_dirs: list[str] = []

    for path in _manifest_paths():
        manifest = _load_manifest(path)
        demo_id = str(manifest["demo_id"])
        port = int(manifest["port"])
        workspace_root = str(manifest["workspace_root"])
        repo_url = str(manifest.get("repo_url", "")).strip().lower()
        repo_dir = str(manifest.get("repo_dir", "")).strip()

        demo_ids.append(demo_id)
        ports.append(port)
        workspace_roots.append(workspace_root)
        if repo_url != "local":
            assert repo_dir, f"Missing repo_dir for non-local manifest: {path}"
            repo_dirs.append(repo_dir)

    assert len(demo_ids) == len(set(demo_ids)), "Duplicate demo_id across manifests"
    assert len(ports) == len(set(ports)), "Duplicate port across manifests"
    assert len(workspace_roots) == len(set(workspace_roots)), "Duplicate workspace_root across manifests"
    assert len(repo_dirs) == len(set(repo_dirs)), "Duplicate repo_dir across manifests"


def test_demo_repo_dirs_use_tmp_prefix() -> None:
    for path in _manifest_paths():
        manifest = _load_manifest(path)
        repo_url = str(manifest.get("repo_url", "")).strip().lower()
        if repo_url == "local":
            continue
        repo_dir = str(manifest["repo_dir"])
        assert repo_dir.startswith("/tmp/remora-demo-"), (
            f"repo_dir must use /tmp/remora-demo- prefix for safety: {path} -> {repo_dir}"
        )


def test_demo_project_roots_are_not_remora_v2() -> None:
    for path in _manifest_paths():
        manifest = _load_manifest(path)
        project_root = str(manifest["project_root"])
        assert "remora-v2" not in project_root, (
            f"Demo project_root should not target remora-v2 directly: {path} -> {project_root}"
        )
