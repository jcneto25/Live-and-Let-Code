"""Testes do Decision Record — formato que a Fase 7 (replay) vai consumir."""

import json

import pytest

from llc_trace import decisions as dec
from llc_trace.decisions import (
    EARLY_COMMITMENT,
    GATE,
    RUNTIME_VERSION,
    decisions_path,
    record_decision,
)
from llc_trace.events import reset_for_tests, set_context


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path))
    monkeypatch.setattr(dec, "enabled", lambda: True)
    reset_for_tests()
    yield
    reset_for_tests()


def _lines():
    p = decisions_path()
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


# ── Campos obrigatorios ─────────────────────────────────────────────────────

REQUIRED_2_0_FIELDS = [
    "policy_version", "statechart_version",
    "jev_model", "jev_request_id", "jev_result",
    "hard_eval", "human_approval",
]


def test_record_has_all_forward_compatible_fields():
    record_decision(EARLY_COMMITMENT, outcome="llm_fallback", reason="no_classify")
    rec = _lines()[0]
    for field in REQUIRED_2_0_FIELDS:
        assert field in rec, f"campo {field} deve existir (mesmo nulo) no schema"
        assert rec[field] is None


def test_record_core_fields():
    record_decision(
        GATE, outcome="approved", reason="human",
        state="GATE_11", event="GATE_DECIDED", step="11",
    )
    rec = _lines()[0]
    assert rec["schema"] == dec.SCHEMA
    assert rec["kind"] == GATE
    assert rec["outcome"] == "approved"
    assert rec["reason"] == "human"
    assert rec["state"] == "GATE_11"
    assert rec["event"] == "GATE_DECIDED"
    assert rec["step"] == "11"
    assert rec["runtime_version"] == RUNTIME_VERSION


def test_decision_id_is_unique():
    record_decision(GATE, outcome="approved")
    record_decision(GATE, outcome="approved")
    ids = [x["decision_id"] for x in _lines()]
    assert len(set(ids)) == 2


def test_input_hash_derived_from_inputs():
    rec = record_decision(EARLY_COMMITMENT, inputs={"task": "criar endpoint"})
    assert rec["input_hash"].startswith("sha256:")
    # mesmo payload -> mesmo hash (base do replay)
    rec2 = record_decision(EARLY_COMMITMENT, inputs={"task": "criar endpoint"})
    assert rec["input_hash"] == rec2["input_hash"]


def test_explicit_input_hash_wins():
    rec = record_decision(GATE, inputs={"a": 1}, input_hash_value="sha256:fixed")
    assert rec["input_hash"] == "sha256:fixed"


def test_inputs_are_recorded_but_truncated():
    rec = record_decision(GATE, outcome="approved", inputs={"blob": "y" * 5000})
    assert rec["inputs"]["blob"].endswith("…[truncated]")


# ── Não-interferência ───────────────────────────────────────────────────────

def test_record_decision_never_raises_on_unwritable_dir(tmp_path, monkeypatch):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("LLC_TRACE_DIR", str(blocker / "sub"))
    assert record_decision(GATE, outcome="approved") is None  # INV-T1


def test_record_decision_handles_non_serializable_inputs():
    rec = record_decision(GATE, outcome="approved", inputs={"obj": object()})
    assert rec is not None


def test_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(dec, "enabled", lambda: False)
    assert record_decision(GATE, outcome="approved") is None
    assert _lines() == []


def test_session_id_from_context():
    set_context(session_id="2026-10-07-005")
    rec = record_decision(GATE, outcome="approved")
    assert rec["session_id"] == "2026-10-07-005"
