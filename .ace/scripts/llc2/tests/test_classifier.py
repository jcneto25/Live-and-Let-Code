"""Testes do classificador LLC 2.0 (Fase 1).

Foco: G1 destravado — rótulo preservado, routing derivado, nunca None.
"""
from __future__ import annotations

import os
from typing import Any

import pytest

from llc2.classifier import (
    _derive_routing,
    _legacy_classify_with_preserve,
    classify_task_v2,
)
from llc2.contracts import Automation, JevChoice, JevNoul, JevResult, load_policy
from llc2.jev_adapter import FakeJevTransport


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def policy():
    return load_policy()


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


@pytest.fixture
def transport_ui_low():
    """Transport que responde ui_component com baixa confiança."""
    return FakeJevTransport({
        "task_type": {
            "choice": "ui_component",
            "probabilities": {"crud_endpoint": 0.30, "ui_component": 0.35,
                              "validation_rule": 0.20, "test_write": 0.10,
                              "unknown": 0.05},
            "confidence": 0.35,
        },
        "complexity": {
            "score": 2,
            "probabilities": {"0": 0.05, "1": 0.20, "2": 0.50, "3": 0.25},
            "confidence": 0.40,
        },
        "needs_human_review": {"noul": 0.10},
    })


@pytest.fixture
def transport_human_review():
    """Transport que sinaliza necessidade de revisão humana."""
    return FakeJevTransport({
        "task_type": {
            "choice": "crud_endpoint",
            "probabilities": {"crud_endpoint": 0.85, "ui_component": 0.05,
                              "validation_rule": 0.05, "test_write": 0.03,
                              "unknown": 0.02},
            "confidence": 0.85,
        },
        "complexity": {
            "score": 3,
            "probabilities": {"0": 0.02, "1": 0.08, "2": 0.20, "3": 0.70},
            "confidence": 0.80,
        },
        "needs_human_review": {"noul": 0.92},  # afirmativo => eleva piso
    })


# ── Testes de derive_routing ──────────────────────────────────────────────

def test_derive_routing_unknown_always_human(policy):
    """Rótulo 'unknown' => HUMAN_REQUIRED independente de confiança."""
    assert _derive_routing("unknown", 0.99, None, policy) is Automation.HUMAN_REQUIRED


def test_derive_routing_high_confidence_auto(policy):
    """Alta confiança em R1 => AUTO."""
    assert _derive_routing("crud_endpoint", 0.95, None, policy) is Automation.AUTO


def test_derive_routing_mid_confidence_auto_audit(policy):
    """Confiança entre audit_min (0.50) e auto_min (0.70) em R1 => AUTO_AUDIT."""
    assert _derive_routing("crud_endpoint", 0.60, None, policy) is Automation.AUTO_AUDIT


def test_derive_routing_low_confidence_human(policy):
    """Confiança abaixo de review_min (0.50) em R1 => HUMAN_REQUIRED."""
    assert _derive_routing("crud_endpoint", 0.40, None, policy) is Automation.HUMAN_REQUIRED


def test_derive_routing_human_review_noul(policy):
    """Noul needs_human_review afirmativo eleva para REVIEW_REQUIRED."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r1",
        answers={"needs_human_review": JevNoul(0.92)},
    )
    level = _derive_routing("crud_endpoint", 0.95, result, policy)
    assert level is Automation.REVIEW_REQUIRED


def test_derive_routing_noul_uncertain_downgrades(policy):
    """Noul incerto (0.50) em risco não deixa ficar em AUTO."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r2",
        answers={"needs_human_review": JevNoul(0.50)},
    )
    level = _derive_routing("crud_endpoint", 0.95, result, policy)
    # 0.50 está entre false_at (0.20) e true_at (0.80) => incerto
    # deveria elevar de AUTO para AUTO_AUDIT no mínimo
    assert level in (Automation.AUTO_AUDIT, Automation.REVIEW_REQUIRED)


# ── Testes de classify_task_v2 com FakeJevTransport ───────────────────────

def test_classify_v2_preserves_label_high_conf(transport_crud_high, policy):
    """Alta confiança: rótulo preservado, routing=AUTO."""
    result = classify_task_v2(
        "Criar endpoint de usuarios", client=None, _transport=transport_crud_high,
    )

    # NUNCA None
    assert result is not None
    assert isinstance(result, dict)
    assert result["type"] == "crud_endpoint"
    assert result["confidence"] == pytest.approx(0.92, abs=0.01)
    assert result["routing"] == "AUTO"
    assert "decision_id" in result
    assert "input_hash" in result
    assert result["policy_version"] == policy.version
    assert result.get("jev_model") is not None


def test_classify_v2_preserves_label_low_conf(transport_ui_low):
    """Baixa confiança: rótulo preservado, routing rebaixado (não None!)."""
    result = classify_task_v2(
        "Criar um componente de UI", client=None, _transport=transport_ui_low,
    )

    assert result is not None
    assert result["type"] == "ui_component"
    # confidence 0.35 em R1 => abaixo de review_min (0.50) => HUMAN_REQUIRED
    assert result["routing"] == "HUMAN_REQUIRED"


def test_classify_v2_human_review_noul(transport_human_review):
    """Noul afirmativo eleva routing mesmo com confiança alta."""
    result = classify_task_v2(
        "Criar endpoint complexo", client=None, _transport=transport_human_review,
    )

    assert result is not None
    assert result["type"] == "crud_endpoint"
    assert result["routing"] == "REVIEW_REQUIRED"


# ── Testes de fallback legado ─────────────────────────────────────────────

def test_legacy_classify_with_preserve_no_client():
    """Sem cliente LLM: retorna unknown com reasoning."""
    label, conf, reason = _legacy_classify_with_preserve(
        "Criar endpoint", client="__nonexistent_llm_client__",
    )
    assert label == "unknown"
    assert conf == 0.0
    # Quando o client não existe no PATH, subprocess falha com FileNotFound
    assert "llm_error" in reason or "no_llm_client" in reason


# ── Testes de campos do Decision Record ───────────────────────────────────

def test_classify_v2_populates_all_fields(transport_crud_high, policy):
    """O dict retornado contém todos os campos esperados pelo replay.py."""
    result = classify_task_v2(
        "Criar endpoint", client=None, _transport=transport_crud_high,
    )

    required_keys = {
        "type", "confidence", "reasoning", "routing",
        "policy_version", "policy_id", "thresholds_hash",
        "question_set_hash", "input_hash", "decision_id",
        "jev_model", "jev_request_id",
    }
    assert required_keys.issubset(result.keys())


# ── Teste de invariante: nunca retorna None ───────────────────────────────

def test_classify_v2_never_returns_none(policy):
    """G1: mesmo com transport que falha, classify_task_v2 nunca retorna None."""
    failing = FakeJevTransport({}, fail_times=3)
    result = classify_task_v2(
        "qualquer coisa", client=None, _transport=failing,
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "type" in result
    assert "routing" in result
