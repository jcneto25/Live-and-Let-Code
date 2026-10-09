"""Replay interno do classificador (solução A — "gravar mais").

A 2ª classificação da mesma task deve resolver por replay determinístico
(zero tokens) em vez de rodar o Jev de novo. Caminhos sem insumos de
verificação (legado, `unknown`) permanecem safe miss.
"""
from __future__ import annotations

import shutil

import pytest

from llc2.classifier import classify_task_v2
from llc2.jev_adapter import FakeJevTransport


@pytest.fixture
def replay_env(monkeypatch):
    monkeypatch.setenv("LLC2_REPLAY", "1")


@pytest.fixture
def transport_crud_high():
    """Transport que responde crud_endpoint com alta confiança."""
    return FakeJevTransport({
        "task_type": {
            "choice": "crud_endpoint",
            "probabilities": {"crud_endpoint": 0.92, "ui_component": 0.03,
                              "validation_rule": 0.03, "test_write": 0.01,
                              "unknown": 0.01},
            "confidence": 0.92,
        },
        "complexity": {
            "score": 1,
            "probabilities": {"0": 0.1, "1": 0.7, "2": 0.15, "3": 0.05},
            "confidence": 0.85,
        },
        "needs_human_review": {"noul": 0.15},
    })


def test_second_classification_hits_replay(replay_env, transport_crud_high):
    """2ª classificação com input_hash igual: replay_hit, Jev 1x."""
    first = classify_task_v2(
        "Criar endpoint de usuarios", client=None, _transport=transport_crud_high)
    assert first["replayed"] is False

    second = classify_task_v2(
        "Criar endpoint de usuarios", client=None, _transport=transport_crud_high)
    assert second["replayed"] is True
    assert second["reasoning"] == "replay_hit"
    assert second["type"] == first["type"] == "crud_endpoint"
    assert second["routing"] == first["routing"]
    assert second["confidence"] == first["confidence"]
    assert len(transport_crud_high.seen) == 1


def test_replay_disabled_by_default_runs_jev_twice(
        monkeypatch, transport_crud_high):
    """Sem LLC2_REPLAY: sem replay (default 0 mantém produção segura)."""
    monkeypatch.delenv("LLC2_REPLAY", raising=False)
    classify_task_v2(
        "Criar endpoint de usuarios", client=None, _transport=transport_crud_high)
    second = classify_task_v2(
        "Criar endpoint de usuarios", client=None, _transport=transport_crud_high)
    assert second["replayed"] is False
    assert len(transport_crud_high.seen) == 2


def test_legacy_path_is_safe_miss(replay_env, monkeypatch):
    """Sem Jev e sem client LLM: nunca hit, nunca exceção."""
    monkeypatch.setattr("llc2.classifier._USE_JEV", False)
    monkeypatch.setattr(shutil, "which", lambda _: None)
    first = classify_task_v2("Criar endpoint de usuarios", client=None)
    assert first["replayed"] is False
    second = classify_task_v2("Criar endpoint de usuarios", client=None)
    assert second["replayed"] is False
    assert second["type"] == first["type"]


def test_unknown_label_is_safe_miss(replay_env):
    """Rótulo unknown via Jev: nunca hit (sem insumos p/ recompute)."""
    transport = FakeJevTransport({
        "task_type": {
            "choice": "unknown",
            "probabilities": {"crud_endpoint": 0.1, "ui_component": 0.1,
                              "validation_rule": 0.1, "test_write": 0.1,
                              "unknown": 0.6},
            "confidence": 0.6,
        },
        "complexity": {
            "score": 0,
            "probabilities": {"0": 0.6, "1": 0.2, "2": 0.1, "3": 0.1},
            "confidence": 0.6,
        },
        "needs_human_review": {"noul": 0.5},
    })
    first = classify_task_v2(
        "Tarefa enigmática", client=None, _transport=transport)
    assert first["type"] == "unknown"
    second = classify_task_v2(
        "Tarefa enigmática", client=None, _transport=transport)
    assert second["replayed"] is False
    assert second["type"] == "unknown"
