from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal host envs
    yaml = None  # type: ignore[assignment]


class DemoConfigError(RuntimeError):
    pass


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse a constrained YAML subset used by demo manifests."""
    root: dict[str, Any] = {}
    section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  ") and section is not None:
            key, _, value = line.strip().partition(":")
            if not key:
                continue
            child = root.get(section)
            if not isinstance(child, dict):
                child = {}
                root[section] = child
            child[key.strip()] = _parse_scalar(value.strip())
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if value == "":
            root[key] = {}
            section = key
        else:
            root[key] = _parse_scalar(value)
            section = None

    return root


def _parse_scalar(value: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def _is_local_repo(manifest: dict[str, Any]) -> bool:
    return str(manifest.get("repo_url", "")).strip().lower() == "local"


def _validate_manifest(manifest: dict[str, Any], *, manifest_path: Path, expected_demo_id: str) -> None:
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
    if not _is_local_repo(manifest):
        required.add("repo_dir")

    missing = sorted(required - set(manifest))
    if missing:
        raise DemoConfigError(f"Manifest missing keys {missing}: {manifest_path}")

    demo_id = str(manifest.get("demo_id", ""))
    if demo_id != expected_demo_id:
        raise DemoConfigError(
            f"Manifest demo_id mismatch: expected {expected_demo_id}, got {demo_id}"
        )


def load_manifest(demo_id: str, repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / "demo" / demo_id / "demo.yaml"
    if not manifest_path.exists():
        raise DemoConfigError(f"Manifest not found: {manifest_path}")

    payload: dict[str, Any] | None = None
    if yaml is not None:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            payload = loaded
    if payload is None:
        payload = _parse_simple_yaml(manifest_path)

    if not isinstance(payload, dict):
        raise DemoConfigError(f"Invalid manifest format: {manifest_path}")

    _validate_manifest(payload, manifest_path=manifest_path, expected_demo_id=demo_id)
    return payload
