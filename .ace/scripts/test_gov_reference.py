#!/usr/bin/env python3
"""Testes para emissão de <gov_reference> no contexto da sessão.

Cobre R3 (PRP-GOV-004): quando --files casa GOVs, o contexto deve incluir
uma tag parseável por GOV casado. Sem --files (injeção global), os
gov_reference são emitidos para todos os GOVs abertos.
"""

import re
from io import StringIO

import initialize_session.cli as cli_mod
import initialize_session.session as session_mod


def build_gov_lines(gov_dir, monkeypatch):
    """Cria 2 GOVs open + 1 addressed e carrega via load_open_govs."""
    gov_dir.mkdir(parents=True, exist_ok=True)
    (gov_dir / "GOV-001-auth.md").write_text(
        "**Status**: open\n## Área Afetada\nsrc/auth\n## Sintoma\nbug\n\n"
        "## Classe de Falha\nFalha Estrutural\n", encoding="utf-8")
    (gov_dir / "GOV-002-ui.md").write_text(
        "**Status**: open\n## Área Afetada\nsrc/ui\n## Sintoma\nbug ui\n\n"
        "## Classe de Falha\nDefeito Local\n", encoding="utf-8")
    (gov_dir / "GOV-003-done.md").write_text(
        "**Status**: addressed\n## Área Afetada\nsrc/api\n## Sintoma\nbug api\n\n",
        encoding="utf-8")
    monkeypatch.setattr(cli_mod, "GOV_DIR", gov_dir)


def test_gov_reference_emitted(gov_workspace):
    """Cada GOV open gera um <gov_reference> no contexto."""
    out = session_mod.build_context_block(
        prev_session=None, context_seed=None, gov_context=gov_workspace.load_open_govs())
    refs = re.findall(r'<gov_reference id="([^"]+)"', out)
    assert len(refs) == 2
    assert "GOV-001-auth" in refs and "GOV-002-ui" in refs


def test_gov_reference_excludes_addressed(gov_workspace):
    """GOVs addressed NÃO geram <gov_reference> (só open)."""
    out = session_mod.build_context_block(
        prev_session=None, context_seed=None, gov_context=gov_workspace.load_open_govs())
    assert "GOV-003-done" not in out


def test_gov_reference_status_open(gov_workspace):
    """Atributo status= open nos gov_reference."""
    out = session_mod.build_context_block(
        prev_session=None, context_seed=None, gov_context=gov_workspace.load_open_govs())
    assert out.count('status="open"') == 2


def test_gov_reference_inside_govs_block(gov_workspace):
    """<gov_reference> fica DENTRO de <govs>...</govs>."""
    out = session_mod.build_context_block(
        prev_session=None, context_seed=None, gov_context=gov_workspace.load_open_govs())
    govs_block = re.search(r"<govs>(.*?)</govs>", out, re.DOTALL).group(1)
    assert "<gov_reference" in govs_block


def test_no_govs_no_reference(session_fixture):
    """Sem GOVs open → nenhum <gov_reference> no contexto."""
    out = session_mod.build_context_block(
        prev_session=None, context_seed=None, gov_context="")
    assert "<gov_reference" not in out


# ── fixtures locais ──

import pytest
from pathlib import Path


@pytest.fixture
def gov_workspace(tmp_path, monkeypatch):
    build_gov_lines(tmp_path / "docs" / "governance", monkeypatch)
    return cli_mod


@pytest.fixture
def session_fixture():
    return None
