"""LLC 2.0 — Delta Semantic Impact (função utilitária, Fase 3).

Usa Jev Choice (semantic_impact) + Noul (scope_creep) para avaliar o impacto
semântico de um diff quando GraphEngine.impact_of() for inconclusivo.

Question set: delta-semantic-impact (R2 — código-fonte).
  - semantic_impact: Choice (none, behavioral, contract, unknown)
  - scope_creep: Noul, raises_risk_when_true

Risk class R2 thresholds:
  - auto_min: 0.85  (alta confiança necessária para AUTO)
  - review_min: 0.70
  - R3 nunca AUTO (mas delta é R2)
"""
from __future__ import annotations

import os
from typing import Any

from llc2.contracts import (
    Automation,
    DecisionState,
    JevNoul,
    JevResult,
    PolicySpec,
    RiskClass,
    canonical_hash,
    load_policy,
    load_question_sets,
    automation_for,
)
from llc2.jev_adapter import JevAdapter, SemanticUnavailable
from llc2.llm_shim import LlmAsJevTransport

_USE_JEV = os.environ.get("LLC2_DELTA", "1").strip() not in (
    "0", "", "false", "no",
)

_QUESTION_SET_ID = "delta-semantic-impact"


def _derive_routing_delta(
    impact: str,
    result: JevResult | None,
    policy: PolicySpec,
) -> Automation:
    """Deriva nível de automação para avaliação de delta.

    Regras específicas:
      - unknown => HUMAN_REQUIRED (não sabemos o impacto)
      - contract => REVIEW_REQUIRED (mudança de contrato = alto risco)
      - scope_creep afirmativo (p_true >= 0.80) => REVIEW_REQUIRED
      - scope_creep incerto => AUTO_AUDIT
      - none/behavioral com alta confiança => AUTO
    """
    # Impacto desconhecido => humano
    if impact == "unknown":
        return Automation.HUMAN_REQUIRED

    # Mudança de contrato => revisão obrigatória
    if impact == "contract":
        return Automation.REVIEW_REQUIRED

    # Noul de risco (scope_creep) — direction antes de força (F3)
    if result is not None:
        noul = result.answers.get("scope_creep")
        if isinstance(noul, JevNoul):
            direction = noul.decided(policy.noul_hi, policy.noul_lo)
            if direction is True:
                return Automation.REVIEW_REQUIRED
            elif direction is None:
                return Automation.AUTO_AUDIT

    # none/behavioral: usa policy por confiança mínima (R2)
    if result is not None:
        min_conf = min(
            (result.confidence_of(k) for k in result.answers),
            default=0.0,
        )
        level = automation_for(policy, RiskClass.R2, min_conf)
        # R2 com confiança abaixo de review_min => HUMAN_REQUIRED
        return level

    return Automation.REVIEW_REQUIRED  # fail-closed: sem dados => revisão


def _trace_delta(
    *,
    diff: str,
    result: dict[str, Any],
    jev_result: JevResult | None,
    policy: PolicySpec,
) -> None:
    """Registra Decision Record de delta via llc_trace (Fase 0)."""
    try:
        from llc_trace import record_decision, input_hash
    except ImportError:
        return

    ih = input_hash({"diff": diff[:1000]})
    evidence: dict[str, Any] = {
        "semantic_impact": result.get("impact"),
        "routing": result.get("routing"),
    }
    if jev_result is not None:
        evidence["jev_model"] = jev_result.model
        evidence["jev_request_id"] = jev_result.request_id

    record_decision(
        "delta",
        outcome="semantic_impact",
        reason=result.get("error") or "delta_assessed",
        state="STEP_EXECUTION",
        event="DELTA_SEMANTIC",
        input_hash_value=ih,
        inputs={"diff": diff[:1000]},
        evidence=evidence,
        automation=result.get("routing"),
        config={
            "policy_version": policy.version,
            "policy_id": policy.id,
            "thresholds_hash": policy.thresholds_hash,
            "question_set_id": _QUESTION_SET_ID,
        },
    )


def delta_semantic_impact(
    diff: str,
    *,
    _transport: Any | None = None,
) -> dict[str, Any]:
    """Avalia impacto semântico de um diff via Jev Choice + Noul.

    Retorna dict com keys:
        impact, confidence, reasoning, routing,
        policy_version, question_set_hash, input_hash, error
    """
    policy = load_policy()

    # ── carrega question set uma única vez ────────────────────────────────
    qsets: Any = None
    qs: Any = None
    qs_hash = ""
    if _USE_JEV:
        try:
            qsets = load_question_sets()
            qs = qsets.get(_QUESTION_SET_ID)
            if qs is not None:
                qs_hash = qs.hash
        except Exception:
            pass

    # ── tentativa Jev ─────────────────────────────────────────────────────
    jev_result: JevResult | None = None
    impact = "unknown"
    confidence = 0.0
    reasoning = ""
    error: str | None = None

    if _USE_JEV and qs is not None:
        try:
            inputs = {"diff": diff[:3000]}  # truncado para Jev

            state = DecisionState(
                node_id="D-SEMANTIC-IMPACT",
                state_id="idle",
                decision_kind="delta",
                question_set_id=_QUESTION_SET_ID,
                question_set_version=qs.version,
                question_set_hash=qs.hash,
                inputs=inputs,
                risk_class=RiskClass.R2,
                expected_answers=qs.expected_answers,
                risk_noul_keys=qs.risk_noul_keys,
            )

            transport = _transport if _transport is not None else LlmAsJevTransport()
            adapter = JevAdapter(transport, question_sets=qsets)
            jev_result = adapter.evaluate(state)

            # Extrai Choice (semantic_impact)
            choice_ans = jev_result.answers.get("semantic_impact")
            if hasattr(choice_ans, "choice"):
                impact = choice_ans.choice
                confidence = choice_ans.confidence

            # Extrai Noul (scope_creep) para reasoning
            noul_ans = jev_result.answers.get("scope_creep")
            if isinstance(noul_ans, JevNoul):
                reasoning = (
                    f"impact={impact} ({confidence:.0%}); "
                    f"scope_creep={noul_ans.p_true:.2f}"
                )
            else:
                reasoning = f"impact={impact} ({confidence:.0%})"

        except SemanticUnavailable as exc:
            jev_result = None
            error = f"jev_unavailable: {exc}"
            reasoning = error

    # ── quando Jev indisponível ou falhou ─────────────────────────────────
    if jev_result is None and not error:
        error = "semantic_unavailable: no_jev_response"
        reasoning = error

    routing = _derive_routing_delta(impact, jev_result, policy)

    result: dict[str, Any] = {
        "impact": impact,
        "confidence": confidence,
        "reasoning": reasoning,
        "routing": routing.value,
        "policy_version": policy.version,
        "policy_id": policy.id,
        "thresholds_hash": policy.thresholds_hash,
        "question_set_hash": qs_hash,
        "input_hash": canonical_hash({"diff": diff}),
        "jev_model": jev_result.model if jev_result else None,
        "jev_request_id": jev_result.request_id if jev_result else None,
        "error": error,
    }

    _trace_delta(
        diff=diff,
        result=result,
        jev_result=jev_result,
        policy=policy,
    )

    return result
