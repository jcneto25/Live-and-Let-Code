#!/usr/bin/env python3
"""Testes para gov-tools.py close (R5 — transição addressed→closed).

Cobre:
  - close exige status addressed
  - close exige contagem 3/3 no campo Status da Reincidência
  - close exige --confirm (sem confirmação é dry-run)
  - close preenche Status e Data de fechamento
  - close em GOV open/closed falha
"""

import subprocess
import sys
from pathlib import Path

import pytest

GOV_TOOLS = Path(__file__).parent / "gov-tools.py"


def _make_gov(tmp_path, name, status, recurrence="3/3"):
    gov_dir = tmp_path / "docs" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / name).write_text(
        f"**Status**: {status}\n"
        f"**Data de abertura**: 2026-07-01\n"
        f"## Sintoma\nX\n"
        f"## Área Afetada\nsrc/x\n"
        f"## Status da Reincidência\n{recurrence} PRPs sem reincidência desde a instalação\n",
        encoding="utf-8",
    )
    return gov_dir


def _run_close(tmp_path, gov_file, extra=()):
    return subprocess.run(
        [sys.executable, str(GOV_TOOLS), "close", gov_file] + list(extra),
        cwd=tmp_path, capture_output=True, text=True,
    )


def test_close_requires_addressed(tmp_path):
    _make_gov(tmp_path, "GOV-009-x.md", "open")
    r = _run_close(tmp_path, "GOV-009-x.md", ["--confirm"])
    assert r.returncode != 0
    assert "addressed" in r.stdout + r.stderr


def test_close_requires_3_prps(tmp_path):
    _make_gov(tmp_path, "GOV-010-x.md", "addressed", recurrence="1/3")
    r = _run_close(tmp_path, "GOV-010-x.md", ["--confirm"])
    assert r.returncode != 0
    assert "3" in r.stdout + r.stderr


def test_close_without_confirm_is_dryrun(tmp_path):
    _make_gov(tmp_path, "GOV-011-x.md", "addressed", recurrence="3/3")
    gov_file = tmp_path / "docs/governance/GOV-011-x.md"
    before = gov_file.read_text()
    r = _run_close(tmp_path, "GOV-011-x.md")
    assert r.returncode == 0
    assert "dry-run" in (r.stdout + r.stderr).lower() or "confirme" in (r.stdout + r.stderr).lower()
    # arquivo não modificado
    assert gov_file.read_text() == before


def test_close_with_confirm_updates_file(tmp_path):
    _make_gov(tmp_path, "GOV-012-x.md", "addressed", recurrence="3/3")
    r = _run_close(tmp_path, "GOV-012-x.md", ["--confirm"])
    assert r.returncode == 0
    content = (tmp_path / "docs/governance/GOV-012-x.md").read_text()
    assert "**Status**: closed" in content
    assert "**Data de fechamento**" in content


def test_close_already_closed_fails(tmp_path):
    _make_gov(tmp_path, "GOV-013-x.md", "closed", recurrence="3/3")
    r = _run_close(tmp_path, "GOV-013-x.md", ["--confirm"])
    assert r.returncode != 0


def test_close_missing_file_fails(tmp_path):
    _make_gov(tmp_path, "GOV-014-x.md", "addressed")
    r = _run_close(tmp_path, "GOV-999-inexistente.md", ["--confirm"])
    assert r.returncode != 0
