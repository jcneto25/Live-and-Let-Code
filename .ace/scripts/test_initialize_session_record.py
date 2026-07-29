#!/usr/bin/env python3
"""Testes de regressão: get_previous_session deve tolerar campos extras
gravados no index.json por finalize_session.py (completed_at) e
update_index (prp) — construção de SessionInfo não pode explodir com
chaves desconhecidas. Bug exposto em 2026-07-27 (sessão 003 finalizada)."""

import json

import pytest

from initialize_session import session as session_mod
from initialize_session.session import SessionInfo, get_previous_session


def _write_index(tmp_path, records):
    index_file = tmp_path / "index.json"
    index_file.write_text(
        json.dumps({"project": "LLC", "sessions": records}, ensure_ascii=False),
        encoding="utf-8",
    )
    return index_file


BASE_RECORD = {
    "session_id": "2026-07-27-003",
    "file": "2026-07-27-003.md",
    "status": "completed",
    "llc_step": 10.0,
    "llc_step_id": "10",
    "tags": ["AGENTS.md"],
    "timestamp": "2026-07-27T21:30:01",
}


def test_tolerates_completed_at(tmp_path, monkeypatch):
    """Registro finalizado (com completed_at) não pode quebrar a construção."""
    record = {**BASE_RECORD, "completed_at": "2026-07-27T21:35:29"}
    monkeypatch.setattr(session_mod, "INDEX_FILE", _write_index(tmp_path, [record]))

    info = get_previous_session()

    assert isinstance(info, SessionInfo)
    assert info.session_id == "2026-07-27-003"
    assert info.status == "completed"


def test_tolerates_prp_and_unknown_future_keys(tmp_path, monkeypatch):
    """update_index grava 'prp'; campos futuros também não podem quebrar."""
    record = {**BASE_RECORD, "prp": "PRP-001", "campo_futuro": {"x": 1}}
    monkeypatch.setattr(session_mod, "INDEX_FILE", _write_index(tmp_path, [record]))

    info = get_previous_session()

    assert isinstance(info, SessionInfo)
    assert info.llc_step_id == "10"


def test_known_fields_preserved(tmp_path, monkeypatch):
    """Filtragem não pode descartar campos conhecidos do dataclass."""
    record = {**BASE_RECORD, "completed_at": "2026-07-27T21:35:29"}
    monkeypatch.setattr(session_mod, "INDEX_FILE", _write_index(tmp_path, [record]))

    info = get_previous_session()

    assert info.file == "2026-07-27-003.md"
    assert info.llc_step == 10.0
    assert info.tags == ["AGENTS.md"]
    assert info.timestamp == "2026-07-27T21:30:01"


def test_skips_records_not_completed_nor_in_progress(tmp_path, monkeypatch):
    """Varredura reversa continua respeitando o filtro de status."""
    older = {**BASE_RECORD, "session_id": "2026-07-27-001", "completed_at": "x"}
    aborted = {**BASE_RECORD, "session_id": "2026-07-27-002", "status": "aborted"}
    monkeypatch.setattr(
        session_mod, "INDEX_FILE", _write_index(tmp_path, [older, aborted])
    )

    info = get_previous_session()

    assert info is not None
    assert info.session_id == "2026-07-27-001"
