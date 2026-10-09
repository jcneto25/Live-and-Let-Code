"""Testes do DocJudge LLC 2.0 (Fase 2).

Foco: Jev Score/Noul no doc_judge, preservando aggregate ∈ [0,100].
"""
from __future__ import annotations

import pytest

from llc2.contracts import Automation, JevNoul, JevResult, JevScore, load_policy
from llc2.doc_judge import (
    _aggregate,
    _derive_routing_doc,
    _score_from_jev,
    doc_judge_v2,
)
from llc2.jev_adapter import FakeJevTransport


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def policy():
    return load_policy()


@pytest.fixture
def transport_prd_excellent():
    """Transport que responde PRD excelente."""
    return FakeJevTransport({
        "prd_quality": {
            "score": 3,
            "probabilities": {"0": 0.01, "1": 0.02, "2": 0.10, "3": 0.87},
            "confidence": 0.92,
        },
        "executivo_comunica_valor": {"noul": 0.92},
        "tecnico_cobre_requisitos": {"noul": 0.88},
        "ambos_consistentes": {"noul": 0.95},
    })


@pytest.fixture
def transport_prd_poor():
    """Transport que responde PRD de baixa qualidade."""
    return FakeJevTransport({
        "prd_quality": {
            "score": 0,
            "probabilities": {"0": 0.75, "1": 0.15, "2": 0.07, "3": 0.03},
            "confidence": 0.80,
        },
        "executivo_comunica_valor": {"noul": 0.15},
        "tecnico_cobre_requisitos": {"noul": 0.10},
        "ambos_consistentes": {"noul": 0.20},
    })


@pytest.fixture
def transport_prd_uncertain():
    """Transport com Noul incerto (zona cinzenta)."""
    return FakeJevTransport({
        "prd_quality": {
            "score": 2,
            "probabilities": {"0": 0.05, "1": 0.15, "2": 0.50, "3": 0.30},
            "confidence": 0.65,
        },
        "executivo_comunica_valor": {"noul": 0.50},  # incerto
        "tecnico_cobre_requisitos": {"noul": 0.55},  # incerto
        "ambos_consistentes": {"noul": 0.48},        # incerto
    })


# ── Testes de _score_from_jev ─────────────────────────────────────────────

def test_score_from_jev_score():
    """JevScore mapeia índice para 0-100."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r1",
        answers={"q": JevScore(3, ("A", "B", "C", "D"),
                              {"0": 0.1, "1": 0.1, "2": 0.1, "3": 0.7}, 0.9)},
    )
    score, reason = _score_from_jev("q", result)
    assert score == 100.0  # índice 3 / (4-1) * 100
    assert "D" in reason


def test_score_from_jev_score_mid():
    """JevScore índice 1 de 4 níveis => 33.33%."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r2",
        answers={"q": JevScore(1, ("A", "B", "C", "D"),
                              {"0": 0.1, "1": 0.6, "2": 0.2, "3": 0.1}, 0.7)},
    )
    score, _ = _score_from_jev("q", result)
    assert score == pytest.approx(33.33, abs=0.01)


def test_score_from_jev_noul():
    """JevNoul mapeia p_true para 0-100."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r3",
        answers={"q": JevNoul(0.85)},
    )
    score, reason = _score_from_jev("q", result)
    assert score == 85.0
    assert "0.85" in reason


def test_score_from_jev_missing():
    """Resposta ausente => None."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r4",
        answers={},
    )
    assert _score_from_jev("q", result) is None


# ── Testes de _aggregate ──────────────────────────────────────────────────

def test_aggregate_all_dimensions():
    """Todas as dimensões presentes => média ponderada correta."""
    scores = {
        "prd_quality": {"score": 100.0},
        "executivo_comunica_valor": {"score": 90.0},
        "tecnico_cobre_requisitos": {"score": 85.0},
        "ambos_consistentes": {"score": 95.0},
    }
    # 0.4*100 + 0.2*90 + 0.2*85 + 0.2*95 = 40 + 18 + 17 + 19 = 94
    assert _aggregate(scores) == pytest.approx(94.0, abs=0.01)


def test_aggregate_partial():
    """Dimensão ausente não infla denominador."""
    scores = {
        "prd_quality": {"score": 100.0},
        "executivo_comunica_valor": {"score": 50.0},
    }
    # 0.4*100 + 0.2*50 = 40 + 10 = 50; peso total = 60; aggregate = 50/0.6 = 83.33
    assert _aggregate(scores) == pytest.approx(83.33, abs=0.01)


def test_aggregate_empty():
    """Nenhuma dimensão => None."""
    assert _aggregate({}) is None


def test_aggregate_clamped():
    """Score fora de faixa é clampado."""
    scores = {"prd_quality": {"score": 150.0}}
    assert _aggregate(scores) == 100.0


# ── Testes de _derive_routing_doc ─────────────────────────────────────────

def test_routing_low_aggregate_review(policy):
    """Aggregate < 50 => REVIEW_REQUIRED."""
    assert _derive_routing_doc(40.0, None, policy) is Automation.REVIEW_REQUIRED


def test_routing_noul_negative_review(policy):
    """Noul negativo (p_true baixo) => REVIEW_REQUIRED."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r5",
        answers={"executivo_comunica_valor": JevNoul(0.10)},
    )
    assert _derive_routing_doc(80.0, result, policy) is Automation.REVIEW_REQUIRED


def test_routing_noul_uncertain_auto_audit(policy):
    """Noul incerto => AUTO_AUDIT."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r6",
        answers={"executivo_comunica_valor": JevNoul(0.50)},
    )
    assert _derive_routing_doc(80.0, result, policy) is Automation.AUTO_AUDIT


def test_routing_high_quality_auto(policy):
    """Alta qualidade, Noul positivo => AUTO."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r7",
        answers={
            "executivo_comunica_valor": JevNoul(0.92),
            "tecnico_cobre_requisitos": JevNoul(0.88),
            "ambos_consistentes": JevNoul(0.95),
        },
    )
    assert _derive_routing_doc(90.0, result, policy) is Automation.AUTO


# ── Testes de doc_judge_v2 com FakeJevTransport ───────────────────────────

def test_doc_judge_v2_excellent(transport_prd_excellent, policy):
    """PRD excelente: aggregate alto, routing=AUTO."""
    result = doc_judge_v2(
        step_id="2",
        artifact_content="# PRD excelente",
        _transport=transport_prd_excellent,
    )

    assert result["error"] is None
    assert result["scores"] is not None
    assert result["aggregate"] is not None
    assert result["aggregate"] > 80.0
    assert result["routing"] == "AUTO"
    assert result["policy_version"] == policy.version
    assert result["jev_model"] is not None


def test_doc_judge_v2_poor(transport_prd_poor, policy):
    """PRD ruim: aggregate baixo, routing=REVIEW_REQUIRED."""
    result = doc_judge_v2(
        step_id="2",
        artifact_content="# PRD ruim",
        _transport=transport_prd_poor,
    )

    assert result["error"] is None
    assert result["scores"] is not None
    assert result["aggregate"] is not None
    assert result["aggregate"] < 50.0
    assert result["routing"] == "REVIEW_REQUIRED"


def test_doc_judge_v2_uncertain(transport_prd_uncertain, policy):
    """Noul incerto: routing=AUTO_AUDIT."""
    result = doc_judge_v2(
        step_id="2",
        artifact_content="# PRD incerto",
        _transport=transport_prd_uncertain,
    )

    assert result["error"] is None
    assert result["routing"] == "AUTO_AUDIT"


# ── Teste de nunca retorna None ───────────────────────────────────────────

def test_doc_judge_v2_never_returns_none(policy):
    """Mesmo com transport que falha, retorna dict com error."""
    failing = FakeJevTransport({}, fail_times=3)
    result = doc_judge_v2(
        step_id="2",
        artifact_content="# PRD qualquer",
        _transport=failing,
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "scores" in result
    assert "aggregate" in result
    assert "routing" in result
