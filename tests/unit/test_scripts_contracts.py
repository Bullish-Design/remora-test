from pathlib import Path

DEMO_CHECK_ROOT = Path("demo/00_repo_baseline/checks")


def _check_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_search_check_enforces_index_error_thresholds() -> None:
    text = _check_text(str(DEMO_CHECK_ROOT / "check_search.py"))
    assert "max_index_errors" in text
    assert "Unable to parse index error count" in text
    assert "Indexing reported too many errors" in text


def test_proposal_checks_assert_chat_send_status() -> None:
    reject_text = _check_text(str(DEMO_CHECK_ROOT / "check_proposal_reject.py"))
    accept_text = _check_text(str(DEMO_CHECK_ROOT / "check_proposal_accept.py"))
    assert "ensure_chat_sent(chat" in reject_text
    assert "ensure_chat_sent(chat" in accept_text
    assert "Chat send failed for proposal-flow trigger" in reject_text
    assert "Chat send failed for proposal-accept trigger" in accept_text


def test_runner_exposes_lsp_bridge_strict_flags() -> None:
    text = _check_text(str(DEMO_CHECK_ROOT / "runner.py"))
    assert "--require-lsp-bridge" in text
    assert "--run-lsp-bridge" in text
    assert "check_lsp_bridge" in text


def test_runner_includes_playwright_ui_check() -> None:
    text = _check_text(str(DEMO_CHECK_ROOT / "runner.py"))
    assert "check_ui_playwright" in text


def test_repo_level_playwright_script_uses_timestamped_artifacts() -> None:
    lib_text = _check_text("scripts/_lib/playwright_ui.py")
    script_text = _check_text("scripts/playwright_screenshot.py")
    assert "ui-playwright" in lib_text
    assert "safe_prefix" in lib_text
    assert "artifacts" in lib_text
    assert "timestamped_screenshot_path" in script_text
