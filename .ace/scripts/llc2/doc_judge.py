"""LLC 2.0 — DocJudge com Jev Score/Noul (Fase 2).

Substitui JSON+regex por Jev fan-out (Score + 3×Noul).
Preserva interface externa: {step_id, scores, aggregate, error}.
Aggregate ∈ [0,100] (RF-EF3.2).

Mapeamento Jev → score:
  - JevScore (prd_quality):  (score / (n_levels-1)) * 100
  - JevNoul:  p_true * 100

Pesos default das dimensões (somam 100):
  - prd_quality: 40
  - executivo_comunica_valor: 20
  - tecnico_cobre_requisitos: 20
  - ambos_consistentes: 20
"""
from __future__ import annotations

import os
from typing import Any, Callable

from llc2.contracts import (
    Automation,
    DecisionState,
    JevNoul,
    JevResult,
    JevScore,
    PolicySpec,
    RiskClass,
    canonical_hash,
    load_policy,
    load_question_sets,
    automation_for,
)
from llc2.jev_adapter import JevAdapter, SemanticUnavailable
from llc2.llm_shim import LlmAsJevTransport

_USE_JEV = os.environ.get("LLC2_DOC_JUDGE", "1").strip() not in (
    "0", "", "false", "no",
)

_QUESTION_SET_ID = "prd-gate"

# Pesos default (fallback quando policy não tem o campo)
_DEFAULT_WEIGHTS: dict[str, float] = {
    "prd_quality": 40.0,
    "executivo_comunica_valor": 20.0,
    "tecnico_cobre_requisitos": 20.0,
    "ambos_consistentes": 20.0,
}


def _score_from_jev(name: str, result: JevResult) -> tuple[float, str] | None:
    """Extrai (score_0_100, reason) de uma resposta Jev.

    Score: (índice / (n-1)) * 100
    Noul: p_true * 100
    """
    ans = result.answers.get(name)
    if ans is None:
        return None

    if isinstance(ans, JevScore):
        n = len(ans.levels)
        if n <= 1:
            return None
        score = (ans.score / (n - 1)) * 100.0
        reason = f"{ans.level_label} (confiança {ans.confidence:.0%})"
        return round(score, 2), reason

    if isinstance(ans, JevNoul):
        score = ans.p_true * 100.0
        reason = f"p_true={ans.p_true:.2f}"
        return round(score, 2), reason

    return None


def _aggregate(
    scores: dict[str, dict],
    weights: Mapping[str, float] | None = None,
) -> float | None:
    """Média ponderada ∈ [0,100]; None se nenhuma dimensão pontuável."""
    w = dict(weights) if weights else _DEFAULT_WEIGHTS
    total_weight = 0.0
    acc = 0.0
    for name, entry in scores.items():
        weight = float(w.get(name, 0))
        if weight <= 0:
            continue
        score = entry.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            continue
        acc += weight * float(score)
        total_weight += weight
    if total_weight <= 0:
        return None
    result = acc / total_weight
    return round(min(100.0, max(0.0, result)), 2)


def _derive_routing_doc(
    aggregate: float | None,
    result: JevResult | None,
    policy: PolicySpec,
) -> Automation:
    """Deriva nível de automação para avaliação de documento.

    Regras específicas:
      - aggregate < 50 => REVIEW_REQUIRED (documento de baixa qualidade)
      - Noul negativo (p_true < 0.20) em qualquer dimensão => REVIEW_REQUIRED
      - Noul incerto (0.20 < p_true < 0.80) => AUTO_AUDIT no mínimo
    """
    if aggregate is not None and aggregate < 50.0:
        return Automation.REVIEW_REQUIRED

    # Avalia Noul de qualidade (sem raises_risk_when_true)
    if result is not None:
        for name in ("executivo_comunica_valor", "tecnico_cobre_requisitos",
                     "ambos_consistentes"):
            noul = result.answers.get(name)
            if isinstance(noul, JevNoul):
                direction = noul.decided(policy.noul_hi, policy.noul_lo)
                if direction is False:
                    return Automation.REVIEW_REQUIRED
                elif direction is None:
                    # Incerteza em qualidade => eleva para AUTO_AUDIT
                    return Automation.AUTO_AUDIT

    # Padrão: usa policy por confiança mínima
    if result is not None:
        min_conf = min(
            (result.confidence_of(k) for k in result.answers),
            default=0.0,
        )
        return automation_for(policy, RiskClass.R1, min_conf)

    return Automation.AUTO


def _trace_doc_judge(
    *,
    step_id: str,
    result: dict[str, Any],
    jev_result: JevResult | None,
    policy: PolicySpec,
) -> None:
    """Registra Decision Record de doc_judge via llc_trace (Fase 0)."""
    try:
        from llc_trace import record_decision, input_hash
    except ImportError:
        return

    ih = input_hash({"step": step_id})
    evidence: dict[str, Any] = {
        "doc_judge_aggregate": result.get("aggregate"),
        "doc_judge_routing": result.get("routing"),
    }
    if jev_result is not None:
        evidence["jev_model"] = jev_result.model
        evidence["jev_request_id"] = jev_result.request_id

    record_decision(
        "doc_judge",
        outcome="doc_judge",
        reason=result.get("error") or "doc_quality_assessed",
        state="STEP_EXECUTION",
        event="DOC_JUDGE",
        input_hash_value=ih,
        inputs={"step": step_id},
        evidence=evidence,
        automation=result.get("routing"),
        config={
            "policy_version": policy.version,
            "policy_id": policy.id,
            "thresholds_hash": policy.thresholds_hash,
            "question_set_id": _QUESTION_SET_ID,
        },
    )


def doc_judge_v2(
    *,
    step_id: str,
    artifact_content: str,
    upstream_artifacts: str | None = None,
    llm_call: Callable[[str], str] | None = None,
    _transport: Any | None = None,
) -> dict[str, Any]:
    """Avalia documento via Jev Score/Noul. Retorna formato compatível com v1.

    Retorna dict com keys:
        step_id, scores, aggregate, error, routing,
        policy_version, input_hash, decision_id
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
    scores: dict[str, dict] = {}
    error: str | None = None

    if _USE_JEV and qs is not None:
        try:
            inputs: dict[str, Any] = {
                "artifact": artifact_content[:2000],  # truncado para Jev
                "step_id": step_id,
            }
            if upstream_artifacts:
                inputs["upstream"] = upstream_artifacts[:1000]

            state = DecisionState(
                node_id=f"D-DOC-QUALITY-{step_id}",
                state_id="idle",
                decision_kind="doc_judge",
                question_set_id=_QUESTION_SET_ID,
                question_set_version=qs.version,
                question_set_hash=qs.hash,
                inputs=inputs,
                risk_class=RiskClass.R1,
                expected_answers=qs.expected_answers,
                risk_noul_keys=qs.risk_noul_keys,
            )

            transport = _transport if _transport is not None else LlmAsJevTransport()
            adapter = JevAdapter(transport, question_sets=qsets)
            jev_result = adapter.evaluate(state)

            for name in qs.questions:
                extracted = _score_from_jev(name, jev_result)
                if extracted:
                    score, reason = extracted
                    scores[name] = {"score": score, "reason": reason}

        except SemanticUnavailable as exc:
            jev_result = None
            error = f"jev_unavailable: {exc}"

    # ── fallback: se Jev não respondeu nada, usa llm_call legado ──────────
    if not scores:
        if llm_call is not None:
            # Chama o judge legado e converte para novo formato
            from llc_evals.evaluators.doc_judge import (
                DocJudge, build_prompt, load_rubric, parse_response, aggregate_score,
            )
            try:
                rubric = load_rubric(step_id)
                prompt = build_prompt(rubric, artifact_content, upstream_artifacts)
                raw = llm_call(prompt)
                parsed, parse_err = parse_response(raw)
                if parse_err or parsed is None:
                    error = parse_err or "parse_error"
                else:
                    # Converte formato legado para novo
                    for dim_name, entry in parsed.items():
                        if isinstance(entry, dict) and "score" in entry:
                            scores[dim_name] = {
                                "score": entry["score"],
                                "reason": entry.get("reason", ""),
                            }
            except Exception as exc:
                error = f"legacy_fallback_error: {exc}"
        else:
            # Nem Jev nem llm_call disponível — não pode avaliar
            error = error or "no_evaluator_available: jev_failed_and_no_llm_call"

    aggregate = _aggregate(scores, policy.doc_judge_weights) if scores else None
    routing = _derive_routing_doc(aggregate, jev_result, policy)

    # input_hash do conteúdo COMPLETO (não truncado) para replay determinístico
    artifact_hash = canonical_hash(artifact_content)
    result: dict[str, Any] = {
        "step_id": step_id,
        "scores": scores if scores else None,
        "aggregate": aggregate,
        "error": error,
        "routing": routing.value,
        "policy_version": policy.version,
        "policy_id": policy.id,
        "thresholds_hash": policy.thresholds_hash,
        "question_set_hash": qs_hash,
        "input_hash": artifact_hash,
        "jev_model": jev_result.model if jev_result else ("llm-legacy-json" if scores else None),
        "jev_request_id": jev_result.request_id if jev_result else None,
    }

    _trace_doc_judge(
        step_id=step_id,
        result=result,
        jev_result=jev_result,
        policy=policy,
    )

    return result
