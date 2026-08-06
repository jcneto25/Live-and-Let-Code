"""Testes para finalize_session.extract — extração de tags de sessão ACE.

Cobre os dois bugs de harness descobertos em 2026-08-06:
1. `<action_log>` casava no regex `<action([^>]*)>` — fantasma [type=?].
2. Texto com tags literais dentro de `<context_seed>` (metadados) poluía
   a extração — fantasma [type=?] que engolia o 1º <action> real.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from finalize_session.extract import extract_actions, extract_all_tags


def _session_with_actions(actions: list[str]) -> str:
    return (
        "---\nsession_id: 't'\n---\n\n## Ações\n\n<action_log>\n"
        + "\n".join(actions)
        + "\n</action_log>\n"
    )


def test_extract_actions_ignores_action_log_container():
    """<action_log> não é <action>: só as actions reais são extraídas."""
    content = _session_with_actions([
        '<action type="file_modify"><file_delta>x.py</file_delta>'
        '<description>fix</description></action>',
    ])
    actions = extract_actions(content)
    assert len(actions) == 1
    assert actions[0]["attrs"]["type"] == "file_modify"


def test_extract_actions_multiple_actions():
    content = _session_with_actions([
        '<action type="file_create"><file_delta>a.py</file_delta>'
        '<description>novo</description></action>',
        '<action type="file_modify"><file_delta>b.py</file_delta>'
        '<description>alterado</description></action>',
    ])
    actions = extract_actions(content)
    assert [a["attrs"]["type"] for a in actions] == ["file_create", "file_modify"]


def test_extract_actions_ignores_context_seed_with_literal_tags():
    """Metadados <context_seed> com tags literais NÃO geram fantasma.

    Regressão (sessão 2026-08-06-018): o seed copiado da sessão anterior
    citava `<action_log>`/`<action>` em texto — sem o strip, virava um
    action fantasma [type=?] que engolia o primeiro <action> real.
    """
    seed = (
        "<context_seed>\n"
        "state: [file_modify] bug: <action_log> casa no regex de <action>\n"
        "pending: nenhuma\nblockers: nenhum\nnext_action: seguir\n"
        "</context_seed>"
    )
    content = (
        "## Contexto\n\n" + seed + "\n\n## Ações\n\n<action_log>\n"
        '<action type="file_modify"><file_delta>engine.py</file_delta>'
        "<description>parallel_frontier</description></action>\n"
        "</action_log>\n"
    )
    actions = extract_actions(content)
    assert len(actions) == 1
    assert actions[0]["attrs"]["type"] == "file_modify"
    assert "parallel_frontier" in actions[0]["content"]


def test_extract_all_tags_strips_placeholders():
    """Placeholders em comentários HTML não são tags reais."""
    content = (
        "<!-- <gate_result step=\"1\" decision=\"approved\">ph</gate_result> -->\n"
        '<gate_result step="2" decision="approved" reviewer="h">real</gate_result>\n'
    )
    gates = extract_all_tags(content, "gate_result")
    assert len(gates) == 1
    assert gates[0]["attrs"]["decision"] == "approved"
    assert "real" in gates[0]["content"]


def test_extract_actions_empty_log():
    content = "<action_log>\n</action_log>\n"
    assert extract_actions(content) == []
