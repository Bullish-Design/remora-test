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


def test_demo_manifests_exist() -> None:
    manifests = _manifest_paths()
    assert manifests, "No demo manifests found under demo/*/demo.yaml"


def test_demo_manifest_required_keys_present() -> None:
    required = {
        "demo_id",
        "name",
        "repo_url",
        "project_root",
        "config_path",
        "workspace_root",
        "port",
        "base_url",
    }
    for manifest_path in _manifest_paths():
        manifest = _load_manifest(manifest_path)
        missing = required - set(manifest)
        assert not missing, f"Missing keys {sorted(missing)} in {manifest_path}"
        repo_url = str(manifest.get("repo_url", "")).strip().lower()
        if repo_url != "local":
            assert "repo_dir" in manifest, f"Missing repo_dir for non-local demo: {manifest_path}"
