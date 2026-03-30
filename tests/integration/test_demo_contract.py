from __future__ import annotations

from pathlib import Path

DEMO_ROOT = Path("demo/00_repo_baseline")


def test_required_paths_exist() -> None:
    required = [
        DEMO_ROOT,
        Path("tests"),
        DEMO_ROOT / "demo.yaml",
        Path("scripts/democtl.py"),
        Path("scripts/playwright_screenshot.py"),
        Path("scripts/_lib/playwright_ui.py"),
        DEMO_ROOT / "config/remora.yaml",
        DEMO_ROOT / "config/remora.constrained.yaml",
        DEMO_ROOT / "config/remora.stress.yaml",
        DEMO_ROOT / "bundles/demo-code-agent/bundle.yaml",
        DEMO_ROOT / "bundles/demo-code-agent/tools/demo_echo.pym",
        DEMO_ROOT / "bundles/demo-code-agent/tools/rewrite_to_magic.pym",
        DEMO_ROOT / "bundles/demo-directory-agent/bundle.yaml",
        DEMO_ROOT / "checks/runner.py",
        DEMO_ROOT / "checks/_harness.py",
        DEMO_ROOT / "checks/check_runtime.py",
        DEMO_ROOT / "checks/check_virtual_agents.py",
        DEMO_ROOT / "checks/check_reflection.py",
        DEMO_ROOT / "checks/check_subscriptions.py",
        DEMO_ROOT / "checks/check_proposal_reject.py",
        DEMO_ROOT / "checks/check_proposal_accept.py",
        DEMO_ROOT / "checks/check_discovery.py",
        DEMO_ROOT / "checks/check_sse.py",
        DEMO_ROOT / "checks/check_cursor.py",
        DEMO_ROOT / "checks/check_relationships.py",
        DEMO_ROOT / "checks/check_search.py",
        DEMO_ROOT / "checks/check_lsp_startup.py",
        DEMO_ROOT / "checks/check_lsp_bridge.py",
        DEMO_ROOT / "checks/check_guardrails.py",
        DEMO_ROOT / "checks/check_smoke.py",
        DEMO_ROOT / "checks/check_ui_dependencies.py",
        DEMO_ROOT / "checks/check_ui_playwright.py",
        DEMO_ROOT / "scripts/mock_embedder_server.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing required demo paths: {missing}"


def test_python_entrypoints_use_python_shebangs() -> None:
    for path in [Path("scripts/democtl.py"), DEMO_ROOT / "checks/runner.py"]:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env python3"), f"Missing Python shebang: {path}"


def test_legacy_shell_check_scripts_removed() -> None:
    legacy = sorted((DEMO_ROOT / "scripts").glob("test_*.sh"))
    assert not legacy, f"Legacy shell checks should be removed: {legacy}"
    assert not (DEMO_ROOT / "scripts/run_demo_checks.sh").exists()
    assert not (DEMO_ROOT / "scripts/lsp_event_bridge_probe.py").exists()
    assert not (DEMO_ROOT / "scripts/install_local_ui_assets.py").exists()


def test_demo_config_modern_keys_and_no_legacy_keys() -> None:
    text = (DEMO_ROOT / "config/remora.yaml").read_text(encoding="utf-8")

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
