"""Testes do log de eventos (append-only, fail-silent)."""

import json
import os

import pytest

from llc_trace import events as ev
from llc_trace.events import (
    clear_context,
    enabled,
    event_from_payload,
    events_path,
    get_context,
    log_event,
    reset_for_tests,
    set_context,
    trace_dir,
)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Todo teste escreve em tmp_path e comeca com estado limpo."""
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path))
    monkeypatch.setattr(ev, "_disabled_explicitly", False)
    reset_for_tests()
    yield
    reset_for_tests()


def _lines():
    p = events_path()
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_trace_dir_respects_env(tmp_path):
    assert trace_dir() == tmp_path


def test_log_event_writes_one_line():
    log_event("step.start", step="5", session_id="2026-10-07-005")
    lines = _lines()
    assert len(lines) == 1
    assert lines[0]["kind"] == "step.start"
    assert lines[0]["step"] == "5"
    assert lines[0]["session_id"] == "2026-10-07-005"
    assert lines[0]["schema"] == ev.SCHEMA


def test_log_event_seq_is_monotonic():
    log_event("a")
    log_event("b")
    seqs = [x["seq"] for x in _lines()]
    assert seqs == sorted(seqs) and len(set(seqs)) == 2


def test_log_event_appends_never_overwrites():
    log_event("first")
    log_event("second")
    assert [x["kind"] for x in _lines()] == ["first", "second"]


def test_context_is_injected_when_field_omitted():
    set_context(session_id="S1", step="7")
    log_event("gate.open")
    rec = _lines()[0]
    assert rec["session_id"] == "S1"
    assert rec["step"] == "7"


def test_explicit_field_wins_over_context():
    set_context(step="7")
    log_event("gate.open", step="9")
    assert _lines()[0]["step"] == "9"


def test_clear_context():
    set_context(session_id="S1")
    clear_context()
    assert get_context() == {}


def test_disabled_by_env_writes_nothing(monkeypatch):
    monkeypatch.setattr(ev, "_disabled_explicitly", True)
    assert enabled() is False
    assert log_event("nope") is None
    assert _lines() == []


def test_long_strings_are_truncated():
    log_event("prompt", text="x" * 5000)
    field = _lines()[0]["fields"]["text"]
    assert len(field) < 600 and field.endswith("…[truncated]")


def test_none_fields_are_dropped():
    log_event("k", a=None, b=1)
    assert _lines()[0]["fields"] == {"b": 1}


def test_log_event_never_raises_on_unwritable_dir(tmp_path, monkeypatch):
    blocker = tmp_path / "blocking-file"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("LLC_TRACE_DIR", str(blocker / "sub"))
    assert log_event("boom") is None  # INV-T1


def test_event_from_payload_computes_input_hash():
    rec = event_from_payload("step.start", {"step": "5", "task": "x"})
    assert rec["input_hash"].startswith("sha256:")


def test_event_record_pid_present():
    log_event("k")
    assert _lines()[0]["pid"] == os.getpid()
