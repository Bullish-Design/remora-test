from __future__ import annotations

from pathlib import Path
import os


def test_required_paths_exist() -> None:
    required = [
        Path("bundles"),
        Path("queries"),
        Path("tests"),
        Path("bundles/demo-code-agent/bundle.yaml"),
        Path("bundles/demo-code-agent/tools/demo_echo.pym"),
        Path("bundles/demo-code-agent/tools/rewrite_to_magic.pym"),
        Path("bundles/demo-directory-agent/bundle.yaml"),
        Path("scripts/test_demo_runtime.sh"),
        Path("scripts/test_virtual_agents.sh"),
        Path("scripts/test_proposal_flow.sh"),
        Path("scripts/run_demo_checks.sh"),
        Path("scripts/test_lsp_startup.sh"),
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing required demo paths: {missing}"


def test_required_scripts_executable() -> None:
    for script in [
        Path("scripts/test_demo_runtime.sh"),
        Path("scripts/test_virtual_agents.sh"),
        Path("scripts/test_proposal_flow.sh"),
        Path("scripts/run_demo_checks.sh"),
        Path("scripts/test_search.sh"),
        Path("scripts/test_lsp_startup.sh"),
    ]:
        assert script.exists(), f"Missing script: {script}"
        assert os.access(script, os.X_OK), f"Script not executable: {script}"


def test_remora_yaml_modern_keys_and_no_legacy_keys() -> None:
    text = Path("remora.yaml").read_text(encoding="utf-8")

    for required_key in [
        "query_search_paths",
        "bundle_search_paths",
        "bundle_overlays",
        "workspace_root",
        "virtual_agents",
    ]:
        assert required_key in text, f"Missing modern key: {required_key}"

    for legacy_key in ["swarm_root", "bundle_root", "bundle_mapping"]:
        assert legacy_key not in text, f"Legacy key should not exist: {legacy_key}"
