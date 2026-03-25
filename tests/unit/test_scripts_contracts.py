from pathlib import Path


def _script_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_search_script_enforces_index_error_thresholds() -> None:
    text = _script_text("scripts/test_search.sh")
    assert "MAX_INDEX_ERRORS" in text
    assert "Unable to parse index error count" in text
    assert "Indexing reported too many errors" in text


def test_proposal_scripts_assert_chat_send_status() -> None:
    reject_text = _script_text("scripts/test_proposal_flow.sh")
    accept_text = _script_text("scripts/test_proposal_accept_flow.sh")
    assert '.status // empty' in reject_text
    assert '.status // empty' in accept_text
    assert "Chat send failed for proposal-flow trigger." in reject_text
    assert "Chat send failed for proposal-accept trigger." in accept_text


def test_lsp_bridge_wrapper_invokes_probe_with_strict_flag() -> None:
    text = _script_text("scripts/test_lsp_event_bridge.sh")
    assert "lsp_event_bridge_probe.py" in text
    assert "--require-lsp-bridge" in text
