"""Testes do reparador histórico explicitamente autorizado para a sessão 006."""
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "repair_session", Path(__file__).parent / "repair_session.py"
)
repair = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(repair)

TARGET_ID = "2026-10-09-006"
SOURCE_ID = "2026-10-09-005"
FILES_TARGETS = {"2026-10-09-004", "2026-10-09-005"}


def _target():
    return (
        '---\nsession_id: "2026-10-09-006"\nstatus: "completed"\n---\n'
        "## Contexto\n\n**Sessão anterior:** 2026-10-09-005\n\n"
        "<context_seed>\n"
        r"\s*<\/context_seed>\s*>')` nunca casa" "\n"
        "</learning_point>\n\n"
        "## Ações\n\n<action_log>\n</action_log>\n"
        "\n## Encerramento\n<context_seed>\n"
        "state: final\npending: none\nblockers: none\nnext_action: next\n"
        "</context_seed>\n\n---\nfiles_touched: []\n"
    )


def _source():
    return (
        "---\nsession_id: \"2026-10-09-005\"\nstatus: \"completed\"\n---\n"
        "## Encerramento\n<context_seed>\n"
        "state: reparo concluído\n"
        "pending: nenhuma\n"
        "blockers: nenhum\n"
        "next_action: prosseguir\n"
        "</context_seed>\n"
    )


def test_repair_replaces_only_inherited_context_and_creates_backup(tmp_path):
    target = tmp_path / f"{TARGET_ID}.md"
    source = tmp_path / f"{SOURCE_ID}.md"
    target.write_text(_target(), encoding="utf-8")
    source.write_text(_source(), encoding="utf-8")

    result = repair.repair_session(target, source, TARGET_ID)

    assert result.changed is True
    assert result.backup.exists()
    repaired = target.read_text(encoding="utf-8")
    assert "state: reparo concluído" in repaired
    assert "<action_log>\n</action_log>" in repaired
    assert "files_touched: []" in repaired
    assert "\\s*<\\/context_seed>" not in repaired
    assert result.backup.read_text(encoding="utf-8") == _target()


def test_repair_refuses_any_session_id_other_than_allowlisted(tmp_path):
    target = tmp_path / f"{TARGET_ID}.md"
    source = tmp_path / f"{SOURCE_ID}.md"
    target.write_text(_target(), encoding="utf-8")
    source.write_text(_source(), encoding="utf-8")

    with pytest.raises(repair.RepairRefused):
        repair.repair_session(target, source, "2026-10-09-005")

    assert target.read_text(encoding="utf-8") == _target()
    assert not list(tmp_path.glob("*.bak"))


def test_repair_files_touched_allowlist_populates_trailer_and_backup(tmp_path):
    target = tmp_path / "2026-10-09-005.md"
    target.write_text(
        "---\nsession_id: \\\"2026-10-09-005\\\"\n---\n"
        "<action_log>\n"
        "<action type=\\\"file_modify\\\"><file_delta>a.py</file_delta></action>\n"
        "<action type=\\\"file_create\\\"><file_delta>b.py</file_delta></action>\n"
        "</action_log>\n---\nfiles_touched: []\n",
        encoding="utf-8",
    )

    result = repair.repair_files_touched(target, "2026-10-09-005")

    assert result.changed is True
    assert result.backup.exists()
    assert "files_touched: [a.py, b.py]" in target.read_text(encoding="utf-8")
    assert result.backup.read_text(encoding="utf-8").endswith("files_touched: []\n")


def test_repair_files_touched_refuses_non_allowlisted_id(tmp_path):
    target = tmp_path / "2026-10-09-006.md"
    target.write_text("files_touched: []\n", encoding="utf-8")

    with pytest.raises(repair.RepairRefused):
        repair.repair_files_touched(target, "2026-10-09-006")


def test_repair_is_idempotent_after_first_application(tmp_path):
    target = tmp_path / f"{TARGET_ID}.md"
    source = tmp_path / f"{SOURCE_ID}.md"
    target.write_text(_target(), encoding="utf-8")
    source.write_text(_source(), encoding="utf-8")

    first = repair.repair_session(target, source, TARGET_ID)
    repaired = target.read_text(encoding="utf-8")
    second = repair.repair_session(target, source, TARGET_ID)

    assert first.changed is True
    assert second.changed is False
    assert target.read_text(encoding="utf-8") == repaired
