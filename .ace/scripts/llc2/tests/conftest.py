"""conftest da suíte `llc2/tests`.

Isola o trace (`llc_trace`) em `tmp_path`, para que rodar esta suíte **não**
escreva em `.ace/logs/*.jsonl` — arquivos rastreados pelo git.

Sem isto, `python -m pytest .ace/scripts/llc2/tests/` adicionava ~19 linhas a
`.ace/logs/decisions.jsonl` a cada execução, sujando o working tree sem
nenhuma mudança de código. Isso quebra o rollback por fase do plano
`docs/llc2-complementacao-plano.md` (§2.3/§3.3/§5.3), que pressupõe árvore
limpa para estancar regressão.

Mesmo padrão já adotado em `llc_replay/tests/test_verify.py`:
`LLC_TRACE_DIR` tem precedência sobre o diretório default em
`llc_trace.events.trace_dir()`.

`monkeypatch` restaura a variável ao fim de cada teste — nada vaza para as
demais suítes, e não há dependência da ordem de importação.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_llc_trace_dir(monkeypatch, tmp_path):
    """Redireciona o trace para `tmp_path` — nenhum teste toca `.ace/logs/`."""
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path / "trace"))