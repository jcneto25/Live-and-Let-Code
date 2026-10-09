"""Regressões da extração do context_seed anterior."""
from pathlib import Path

from initialize_session.session import extract_context_seed


def test_extracts_ending_seed_after_literal_context_tag_in_learning_point(tmp_path):
    session = tmp_path / "previous.md"
    session.write_text(
        "## Contexto\n"
        "<context_seed>\n"
        "state: antigo\n"
        "pending: none\n"
        "blockers: none\n"
        "next_action: continuar\n"
        "</context_seed>\n\n"
        "## Aprendizados\n"
        "<learning_point priority=\"high\">O texto cita `</context_seed>` "
        "sem fechar o bloco atual.</learning_point>\n\n"
        "## Encerramento\n"
        "<context_seed>\n"
        "state: final\n"
        "pending: nenhuma\n"
        "blockers: nenhum\n"
        "next_action: proximo\n"
        "</context_seed>\n",
        encoding="utf-8",
    )

    assert extract_context_seed(session) == (
        "state: final\n"
        "pending: nenhuma\n"
        "blockers: nenhum\n"
        "next_action: proximo"
    )


def test_extract_context_seed_uses_structural_closing_line(tmp_path):
    session = tmp_path / "previous.md"
    session.write_text(
        "## Encerramento\n"
        "<context_seed>\n"
        "state: contém `</context_seed>` em prosa\n"
        "pending: nenhuma\n"
        "blockers: nenhum\n"
        "next_action: proximo\n"
        "</context_seed>\n",
        encoding="utf-8",
    )

    assert "state: contém `</context_seed>` em prosa" in extract_context_seed(session)
