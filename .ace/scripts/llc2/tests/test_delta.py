"""Testes do Delta Semantic Impact LLC 2.0 (Fase 3).

Foco: Jev Choice (semantic_impact) + Noul (scope_creep) no diff.
"""
from __future__ import annotations

import pytest

from llc2.contracts import Automation, JevNoul, JevResult, load_policy
from llc2.delta import (
    _derive_routing_delta,
    delta_semantic_impact,
)
from llc2.jev_adapter import FakeJevTransport


@pytest.fixture
def policy():
    return load_policy()


@pytest.fixture
def transport_none_safe():
    """Impacto nenhum, sem scope creep. Alta confiança em todas as dimensões."""
    return FakeJevTransport({
        "semantic_impact": {
            "choice": "none",
            "probabilities": {"none": 0.90, "behavioral": 0.05,
                              "contract": 0.03, "unknown": 0.02},
            "confidence": 0.95,
        },
        "scope_creep": {"noul": 0.02},  # decision_strength = 0.96 >= R2 auto_min
    })


@pytest.fixture
def transport_contract():
    """Mudança de contrato — alto risco."""
    return FakeJevTransport({
        "semantic_impact": {
            "choice": "contract",
            "probabilities": {"none": 0.02, "behavioral": 0.05,
                              "contract": 0.88, "unknown": 0.05},
            "confidence": 0.90,
        },
        "scope_creep": {"noul": 0.15},
    })


@pytest.fixture
def transport_scope_creep():
    """Scope creep afirmativo — eleva piso."""
    return FakeJevTransport({
        "semantic_impact": {
            "choice": "behavioral",
            "probabilities": {"none": 0.10, "behavioral": 0.75,
                              "contract": 0.10, "unknown": 0.05},
            "confidence": 0.85,
        },
        "scope_creep": {"noul": 0.92},  # afirmativo => REVIEW_REQUIRED
    })


@pytest.fixture
def transport_unknown():
    """Impacto desconhecido."""
    return FakeJevTransport({
        "semantic_impact": {
            "choice": "unknown",
            "probabilities": {"none": 0.15, "behavioral": 0.20,
                              "contract": 0.15, "unknown": 0.50},
            "confidence": 0.60,
        },
        "scope_creep": {"noul": 0.30},
    })


# ── Testes de _derive_routing_delta ───────────────────────────────────────

def test_routing_unknown_always_human(policy):
    """impact='unknown' => HUMAN_REQUIRED."""
    assert _derive_routing_delta("unknown", None, policy) is Automation.HUMAN_REQUIRED


def test_routing_contract_always_review(policy):
    """impact='contract' => REVIEW_REQUIRED."""
    assert _derive_routing_delta("contract", None, policy) is Automation.REVIEW_REQUIRED


def test_routing_scope_creep_affirmative(policy):
    """scope_creep afirmativo eleva para REVIEW_REQUIRED."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r1",
        answers={"scope_creep": JevNoul(0.92)},
    )
    assert _derive_routing_delta("behavioral", result, policy) is Automation.REVIEW_REQUIRED


def test_routing_scope_creep_uncertain(policy):
    """scope_creep incerto => AUTO_AUDIT."""
    result = JevResult(
        model="jev-1.13.0",
        request_id="r2",
        answers={"scope_creep": JevNoul(0.50)},
    )
    assert _derive_routing_delta("behavioral", result, policy) is Automation.AUTO_AUDIT


def test_routing_none_high_conf_auto(policy):
    """impact='none', sem scope creep, alta confiança => AUTO (R2)."""
    from llc2.contracts import JevChoice
    result = JevResult(
        model="jev-1.13.0",
        request_id="r3",
        answers={
            "semantic_impact": JevChoice("none", {"none": 0.95}, 0.95),
            "scope_creep": JevNoul(0.02),  # decision_strength = 0.96
        },
    )
    # R2 auto_min=0.85; min_conf = min(0.95, 0.96) = 0.95 >= 0.85 => AUTO
    level = _derive_routing_delta("none", result, policy)
    assert level is Automation.AUTO


def test_routing_no_data_fail_closed(policy):
    """Sem Jev result => REVIEW_REQUIRED (fail-closed)."""
    assert _derive_routing_delta("none", None, policy) is Automation.REVIEW_REQUIRED


# ── Testes de delta_semantic_impact ───────────────────────────────────────

def test_delta_none_safe(transport_none_safe, policy):
    """Diff seguro: impact=none, routing=AUTO."""
    result = delta_semantic_impact(
        "diff simples de refatoracao",
        _transport=transport_none_safe,
    )

    assert result["error"] is None
    assert result["impact"] == "none"
    assert result["routing"] == "AUTO"
    assert result["policy_version"] == policy.version
    assert result.get("jev_model") is not None


def test_delta_contract(transport_contract, policy):
    """Mudança de contrato: routing=REVIEW_REQUIRED."""
    result = delta_semantic_impact(
        "diff altera API publica",
        _transport=transport_contract,
    )

    assert result["error"] is None
    assert result["impact"] == "contract"
    assert result["routing"] == "REVIEW_REQUIRED"


def test_delta_scope_creep(transport_scope_creep, policy):
    """Scope creep: routing=REVIEW_REQUIRED mesmo sendo behavioral."""
    result = delta_semantic_impact(
        "diff adiciona funcionalidade nao solicitada",
        _transport=transport_scope_creep,
    )

    assert result["error"] is None
    assert result["impact"] == "behavioral"
    assert result["routing"] == "REVIEW_REQUIRED"


def test_delta_unknown(transport_unknown, policy):
    """Impacto desconhecido: routing=HUMAN_REQUIRED."""
    result = delta_semantic_impact(
        "diff ambiguo",
        _transport=transport_unknown,
    )

    assert result["error"] is None
    assert result["impact"] == "unknown"
    assert result["routing"] == "HUMAN_REQUIRED"


# ── Teste de nunca retorna None ───────────────────────────────────────────

def test_delta_never_returns_none(policy):
    """Mesmo com transport que falha, retorna dict com error."""
    failing = FakeJevTransport({}, fail_times=3)
    result = delta_semantic_impact(
        "qualquer diff",
        _transport=failing,
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "impact" in result
    assert "routing" in result
    assert result["error"] is not None
