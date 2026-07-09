#!/usr/bin/env python3
"""Characterization tests for the clean-code refactor (Fase 1 — módulos-folha).

Protege o comportamento das funções puras extraídas/refatoradas, para que o
deep restructure não altere semântica.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from learning_points import (
    extract_learning_points,
    load_existing_learning_points,
    normalize_text,
)
from session_sequence import get_next_session_id


def _load_hyphenated(module_name: str):
    """Carrega módulo cujo arquivo tem hífen no nome (ex: dependency-graph-generator)."""
    path = Path(__file__).parent / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_dgg = _load_hyphenated("dependency-graph-generator")
extract_prp_dependencies = _dgg.extract_prp_dependencies
generate_dependency_graph = _dgg.generate_dependency_graph


# ── learning_points (extraído de promote-learning-points) ──


def test_extract_learning_points_basic():
    content = (
        '<learning_point priority="high">Faça X</learning_point>\n'
        '<learning_point priority="medium">Faça Y</learning_point>'
    )
    pts = extract_learning_points(content)
    assert [p["priority"] for p in pts] == ["high", "medium"]
    assert pts[0]["content"] == "Faça X"


def test_extract_learning_points_default_priority():
    content = "<learning_point>Sem prioridade</learning_point>"
    pts = extract_learning_points(content)
    assert pts[0]["priority"] == "medium"
    assert pts[0]["content"] == "Sem prioridade"


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  Foo   BAR\nbaz ") == "foo bar baz"


def test_load_existing_learning_points_empty(tmp_path):
    f = tmp_path / "learning_points.md"
    assert load_existing_learning_points(f) == {}


def test_load_existing_learning_points_parses_sections(tmp_path):
    f = tmp_path / "learning_points.md"
    f.write_text("## src1\n\nAlgum texto aqui\n\n## src2\n\nOutro texto\n", encoding="utf-8")
    existing = load_existing_learning_points(f)
    assert normalize_text("Algum texto aqui") in existing
    assert normalize_text("Outro texto") in existing


# ── session_sequence (compartilhado validate-session-write / initialize_session) ──


def test_get_next_session_id_first_when_no_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("session_sequence.SESSIONS_DIR", tmp_path)
    assert get_next_session_id("2026-07-09") == "2026-07-09-001"


def test_get_next_session_id_max_plus_one(tmp_path, monkeypatch):
    monkeypatch.setattr("session_sequence.SESSIONS_DIR", tmp_path)
    (tmp_path / "2026-07-09-001.md").write_text("")
    (tmp_path / "2026-07-09-003.md").write_text("")
    assert get_next_session_id("2026-07-09") == "2026-07-09-004"


def test_get_next_session_id_skips_existing(tmp_path, monkeypatch):
    monkeypatch.setattr("session_sequence.SESSIONS_DIR", tmp_path)
    (tmp_path / "2026-07-09-005.md").write_text("")
    assert get_next_session_id("2026-07-09") == "2026-07-09-006"


# ── dependency-graph-generator ──


def test_extract_prp_dependencies():
    content = "Depende de PRP-001 e PRP-002, também PRP-001 repetido."
    deps = extract_prp_dependencies(content)
    assert deps == ["PRP-001", "PRP-002"]


def test_generate_dependency_graph_structure(tmp_path):
    prp = tmp_path / "PRP-001.md"
    prp.write_text("# PRP-001\nRef PRP-002\n", encoding="utf-8")
    graph = generate_dependency_graph([prp])
    assert graph["version"] == "1.2.0"
    assert "prp_001" in graph["artifacts"]
    # extract_prp_dependencies captura toda referência PRP no conteúdo,
    # incluindo o próprio ID do PRP (comportamento pré-existente).
    assert graph["artifacts"]["prp_001"]["depends_on"] == ["PRP-001", "PRP-002"]
    assert "execution_waves" in graph["artifacts"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
