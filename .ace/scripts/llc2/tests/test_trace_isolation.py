"""Isolamento dos logs de trace (`llc_trace`) nos testes de `llc2`.

Motivo (sessão `2026-10-09-005`): a suíte `.ace/scripts/llc2/tests/` escrevia
em `.ace/logs/decisions.jsonl` e `.ace/logs/replay.jsonl` — arquivos
**rastreados pelo git**. Cada execução de `python -m pytest
.ace/scripts/llc2/tests/` adicionava ~19 linhas ao working tree, sujando a
árvore sem nenhuma mudança de código real.

Isso fura o rollback por fase do plano `docs/llc2-complementacao-plano.md`
(§2.3/§3.3/§5.3), que pressupõe árvore limpa para estancar regressão.

A suíte `llc_replay/tests/test_verify.py` já resolve o mesmo problema com um
fixture `autouse` que aponta `LLC_TRACE_DIR` para `tmp_path`. Estes testes
verificam que `llc2/tests/` faz o mesmo.

O isolamento vive em `conftest.py` deste diretório (não neste arquivo): se
estivesse aqui, isolaria apenas a si mesmo e os outros módulos da suíte
continuariam sujando `.ace/logs/`.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
TRACKED_LOGS = ("decisions.jsonl", "replay.jsonl", "events.jsonl")


def _tracked_log_state() -> dict[str, int]:
    """Número de linhas de cada log rastreado em `.ace/logs/`."""
    logs_dir = REPO_ROOT / ".ace" / "logs"
    state: dict[str, int] = {}
    for name in TRACKED_LOGS:
        path = logs_dir / name
        if path.exists():
            state[name] = len(path.read_bytes().splitlines())
    return state


def test_trace_dir_is_redirected_out_of_repo():
    """O fixture `autouse` do conftest precisa tirar o trace de dentro do repo."""
    from llc_trace import trace_dir

    resolved = trace_dir().resolve()
    assert str(REPO_ROOT) not in str(resolved), (
        f"trace_dir() aponta para dentro do repo ({resolved}); "
        "os testes vao escrever em .ace/logs/ e sujar o working tree"
    )


def test_record_decision_does_not_touch_tracked_logs():
    """Gravar um Decision Record nao pode alterar os logs rastreados."""
    from llc_trace import record_decision

    before = _tracked_log_state()
    record_decision("gate", outcome="approved", reason="teste de isolamento")
    after = _tracked_log_state()

    assert before == after, (
        "record_decision escreveu em .ace/logs/ (arquivos rastreados pelo git). "
        f"antes={before} depois={after}"
    )


def test_log_event_does_not_touch_tracked_logs():
    """Registrar um evento nao pode alterar os logs rastreados."""
    from llc_trace import log_event

    before = _tracked_log_state()
    log_event("teste_isolamento", detail="x")
    after = _tracked_log_state()

    assert before == after, (
        "log_event escreveu em .ace/logs/ (arquivos rastreados pelo git). "
        f"antes={before} depois={after}"
    )


def test_classifier_does_not_touch_tracked_logs():
    """Classificar tasks nao pode acumular linhas nos logs rastreados."""
    from llc2.classifier import classify_task_v2

    before = _tracked_log_state()
    for task in ("Criar endpoint de usuarios", "Criar um componente de UI"):
        classify_task_v2(task)
    after = _tracked_log_state()

    assert before == after, (
        "classify_task_v2 acumulou linhas em .ace/logs/: "
        f"antes={before} depois={after}"
    )


def test_log_replay_event_honors_trace_dir():
    """`execute.log_replay_event` deve respeitar `LLC_TRACE_DIR`.

    Ele usava `LOGS_DIR` de `llc_replay/constants.py`, que e
    `Path(".ace/logs")` — **relativo ao cwd** e alheio ao `LLC_TRACE_DIR`.
    Resultado: escapava do isolamento (escrevia no repo durante os testes) e
    tornava `TestReplayRoutingHandling` dependente do cwd.
    """
    import os

    from llc_trace import trace_dir
    from llc_replay.execute import log_replay_event

    target = trace_dir() / "replay.jsonl"
    existed = target.exists()
    before = target.read_text(encoding="utf-8") if existed else ""

    log_replay_event("teste_isolamento", script_id="x")

    assert target.exists(), (
        f"log_replay_event nao escreveu em trace_dir() ({target}); "
        "provavelmente ainda usa LOGS_DIR (relativo ao cwd)"
    )
    after = target.read_text(encoding="utf-8")
    assert len(after) > len(before), "log_replay_event nao anexou linha"

    # E nao pode ter tocado o log do repo
    repo_log = REPO_ROOT / ".ace" / "logs" / "replay.jsonl"
    repo_before = _tracked_log_state().get("replay.jsonl", 0)
    assert os.path.exists(repo_log)
    now = len(repo_log.read_bytes().splitlines())
    assert now == repo_before, "log_replay_event escreveu no log do repo"


def test_isolation_fixture_is_not_local_to_this_module():
    """Guard contra regressao: o fixture deve vir do conftest, nao daqui.

    Se alguem mover o fixture para dentro deste arquivo, ele isola so a si
    mesmo e os demais modulos da suite voltam a sujar `.ace/logs/`.
    """
    conftest = Path(__file__).with_name("conftest.py")
    assert conftest.is_file(), (
        "falta llc2/tests/conftest.py com o fixture de isolamento "
        "(LLC_TRACE_DIR -> tmp_path)"
    )
    source = conftest.read_text(encoding="utf-8")
    assert "LLC_TRACE_DIR" in source and "autouse" in source, (
        "conftest.py existe mas nao define o fixture autouse de LLC_TRACE_DIR"
    )