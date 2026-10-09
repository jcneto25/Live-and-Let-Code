"""conftest da suíte `llc_harness/tests`.

Mesmo padrão de `llc2/tests/conftest.py`: isola o trace (`llc_trace`) em
`tmp_path` para que os testes do replay harness não escrevam em
`.ace/logs/*.jsonl` (arquivos rastreados). `LLC_TRACE_DIR` tem precedência
sobre o default em `llc_trace.events.trace_dir()`; `monkeypatch` restaura ao
fim de cada teste.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_llc_trace_dir(monkeypatch, tmp_path):
    """Redireciona o trace para `tmp_path` — nenhum teste toca `.ace/logs/`."""
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path / "trace"))
