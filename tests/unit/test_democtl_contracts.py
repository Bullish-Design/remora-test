from pathlib import Path


def test_democtl_exposes_required_commands() -> None:
    text = Path("scripts/democtl.py").read_text(encoding="utf-8")
    for command in ["setup", "start", "status", "queries", "cleanup", "wipe", "verify"]:
        assert f'"{command}"' in text


def test_democtl_verify_supports_strict_mode_and_lsp_search_checks() -> None:
    text = Path("scripts/democtl.py").read_text(encoding="utf-8")
    for flag in ["--strict", "--require-web", "--require-search", "--require-lsp-bridge", "--filter"]:
        assert flag in text


def test_democtl_wipe_requires_force() -> None:
    text = Path("scripts/_lib/commands.py").read_text(encoding="utf-8")
    assert 'wipe is destructive; re-run with --force' in text


def test_democtl_uses_refactored_library_modules() -> None:
    text = Path("scripts/democtl.py").read_text(encoding="utf-8")
    assert "from scripts._lib.commands import" in text
    assert "from scripts._lib.manifest import DemoConfigError, load_manifest" in text
