"""INVARIANTES de nao-interferencia da instrumentacao (Fase 0).

Estes testes sao a razao de a Fase 0 poder ser ligada no runtime sem medo:
se algum deles falhar, a instrumentacao deixou de ser passiva e deve ser
tratada como mudanca de comportamento (com gate humano, nao como refactor).

  INV-T1  instrumentacao nunca levanta para o chamador
  INV-T2  instrumentacao nunca altera o valor de retorno
  INV-T3  desligavel por ambiente
  INV-T4  append-only
"""

import json
from pathlib import Path

import pytest

from llc_trace import decisions as dec
from llc_trace import events as ev
from llc_trace.decisions import record_decision
from llc_trace.events import log_event, reset_for_tests, trace_dir


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    # `dec.enabled` e o mesmo objeto de funcao de `ev.enabled` — basta
    # controlar a flag em events para ligar/desligar os dois.
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path))
    monkeypatch.setattr(ev, "_disabled_explicitly", False)
    reset_for_tests()
    yield
    reset_for_tests()


def _harness_function(x):
    """Simula uma funcao do runtime instrumentada."""
    log_event("step.start", step="5", value=x)
    record_decision("gate", outcome="approved", inputs={"x": x})
    return x * 2


def test_inv_t2_return_value_unchanged():
    assert _harness_function(21) == 42


def test_inv_t2_return_value_unchanged_when_instrumentation_broken(monkeypatch):
    blocker = trace_dir() / "blocker"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("LLC_TRACE_DIR", str(blocker / "sub"))
    assert _harness_function(21) == 42  # INV-T1 + INV-T2


def test_inv_t3_disabled_leaves_no_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_disabled_explicitly", True)
    assert _harness_function(1) == 2
    assert list(Path(tmp_path).iterdir()) == []


def test_inv_t4_append_only():
    for i in range(3):
        log_event("k", i=i)
    lines = [
        json.loads(x)
        for x in (trace_dir() / ev.EVENTS_FILENAME)
        .read_text(encoding="utf-8")
        .splitlines()
        if x.strip()
    ]
    assert [x["fields"]["i"] for x in lines] == [0, 1, 2]


def test_instrumentation_does_not_create_files_when_disabled_at_import(monkeypatch, tmp_path):
    """Se `LLC_TRACE=0`, nem o diretorio de log deve ser criado."""
    monkeypatch.setattr(ev, "_disabled_explicitly", True)
    log_event("nada")
    record_decision("gate", outcome="approved")
    assert not (Path(tmp_path) / ev.EVENTS_FILENAME).exists()
    assert not (Path(tmp_path) / dec.DECISIONS_FILENAME).exists()
