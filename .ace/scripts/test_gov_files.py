#!/usr/bin/env python3
"""Testes para load_open_govs (injeção cirúrgica — artigo LLC Prioridade 4).

Cobre:
  - ausência de docs/governance/ (retorna "")
  - filtro por status (só GOVs open)
  - filtro cirúrgico por --files (área afetada)
  - retrocompatibilidade: sem files retorna todos os GOVs open
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent.parent


@pytest.fixture
def gov_workspace(tmp_path, monkeypatch):
    """Cria docs/governance com 3 GOVs sintéticos e aponta GOV_DIR para tmp."""
    gov_dir = tmp_path / "docs" / "governance"
    gov_dir.mkdir(parents=True)

    (gov_dir / "GOV-001-auth-bypass.md").write_text(
        "**Status**: open\n**Data de abertura**: 2026-07-30\n"
        "## Sintoma\nLogin bypass via header\n"
        "## Área Afetada\nsrc/auth, middleware/auth.py\n",
        encoding="utf-8",
    )
    (gov_dir / "GOV-002-silent-failure.md").write_text(
        "**Status**: addressed\n**Data de abertura**: 2026-07-28\n"
        "## Sintoma\nExcept pass swallowing\n"
        "## Área Afetada\n.ace/scripts, src/users\n",
        encoding="utf-8",
    )
    (gov_dir / "GOV-003-stub-backend.md").write_text(
        "**Status**: open\n**Data de abertura**: 2026-07-29\n"
        "## Sintoma\nUI criada sobre service stub return []\n"
        "## Área Afetada\nsrc/dashboard, services/dashboard.ts\n",
        encoding="utf-8",
    )
    (gov_dir / "GOV-TEMPLATE.md").write_text("**Status**: open\n", encoding="utf-8")

    # Patch GOV_DIR no módulo carregado
    import initialize_session.cli as cli_mod

    monkeypatch.setattr(cli_mod, "GOV_DIR", gov_dir)
    return cli_mod


def test_no_gov_dir_returns_empty(tmp_path, monkeypatch):
    """Sem docs/governance/, retorna string vazia."""
    import initialize_session.cli as cli_mod

    monkeypatch.setattr(cli_mod, "GOV_DIR", tmp_path / "nonexistent")
    assert cli_mod.load_open_govs() == ""


def test_returns_only_open_govs(gov_workspace):
    """Só GOVs open entram (GOV-002 addressed excluído; TEMPLATE excluído)."""
    out = gov_workspace.load_open_govs()
    assert "GOV-001" in out
    assert "GOV-002" not in out
    assert "GOV-003" in out
    assert "GOV-TEMPLATE" not in out


def test_default_includes_all_open(gov_workspace):
    """Retrocompatível: sem --files retorna todos os abertos."""
    out = gov_workspace.load_open_govs()
    assert "GOV-001" in out and "GOV-003" in out


def test_files_filter_matches_area(gov_workspace):
    """Injeção cirúrgica: --files 'src/auth' retorna apenas GOV-001."""
    out = gov_workspace.load_open_govs(files=["src/auth"])
    assert "GOV-001" in out
    assert "GOV-003" not in out


def test_files_filter_no_match_returns_empty(gov_workspace):
    """--files sem correspondência em nenhuma área retorna vazio."""
    out = gov_workspace.load_open_govs(files=["src/payments"])
    assert out == ""


def test_files_filter_multiple_targets(gov_workspace):
    """Múltiplos alvos: união de matches."""
    out = gov_workspace.load_open_govs(files=["src/auth", "src/dashboard"])
    assert "GOV-001" in out
    assert "GOV-003" in out


def test_files_filter_case_insensitive(gov_workspace):
    """Match de área é case-insensitive."""
    out = gov_workspace.load_open_govs(files=["SRC/AUTH"])
    assert "GOV-001" in out
