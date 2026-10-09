"""Regressões do trailer files_touched de sessões ACE."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from finalize_session import context


def _session(text: str = "corpo") -> str:
    return (
        "---\n"
        "session_id: 't'\n"
        "status: \"in_progress\"\n"
        "---\n\n"
        f"{text}\n\n"
        "---\n"
        "duration_min: 1\n"
        "files_touched: []\n"
    )


def test_update_files_touched_populates_session_trailer(tmp_path):
    session_file = tmp_path / "session.md"
    session_file.write_text(_session(), encoding="utf-8")

    changed = context.update_files_touched(session_file, ["src/a.py", "src/b.py"])

    assert changed is True
    content = session_file.read_text(encoding="utf-8")
    assert "files_touched: [src/a.py, src/b.py]" in content
    assert "files_touched: []" not in content


def test_update_files_touched_preserves_body_and_is_idempotent(tmp_path):
    session_file = tmp_path / "session.md"
    original_body = "<action_log>\nbody with files_touched: []\n</action_log>"
    session_file.write_text(_session(original_body), encoding="utf-8")

    context.update_files_touched(session_file, ["a.py"])
    first = session_file.read_text(encoding="utf-8")
    changed = context.update_files_touched(session_file, ["a.py"])
    second = session_file.read_text(encoding="utf-8")

    assert changed is False
    assert first == second
    assert original_body in second
    assert second.count("files_touched: [a.py]") == 1


def test_update_files_touched_does_not_write_when_dry_run(tmp_path):
    session_file = tmp_path / "session.md"
    session_file.write_text(_session(), encoding="utf-8")

    changed = context.update_files_touched(session_file, ["a.py"], dry_run=True)

    assert changed is True
    assert "files_touched: []" in session_file.read_text(encoding="utf-8")
