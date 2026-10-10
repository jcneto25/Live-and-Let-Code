"""LLC Replay Verification — Phase 7.

Consome DecisionRecords do llc_trace e usa contracts.replay_decision /
verify_replay para reproduzir decisões sem re-inferência.

F7: replay verifica input_hash antes de reavaliar.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# ── Carrega DecisionRecords do llc_trace ────────────────────────────────────

def load_decision_records() -> list[dict[str, Any]]:
    """Carrega todos os Decision Records de .ace/logs/decisions.jsonl."""
    from llc_trace import decisions_path

    log_path = decisions_path()
    if not log_path.exists():
        return []
    
    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def find_matching_record(
    input_hash: str,
    kind: str | None = None,
    outcome: str | None = None,
) -> dict[str, Any] | None:
    """Encontra DecisionRecord com input_hash correspondente.

    Retorna o mais recente (último no arquivo).
    `outcome` (F3/3.3) desambigua records do mesmo input: records de
    cache (replay_hit/miss) não devem sombrear o record do classificador.
    """
    records = load_decision_records()
    for record in reversed(records):
        if record.get("input_hash") == input_hash:
            if kind is None or record.get("kind") == kind:
                if outcome is None or record.get("outcome") == outcome:
                    return record
    return None


# ── Integração com contracts.replay_decision / verify_replay ────────────────

def replay_decision_from_record(
    record: dict[str, Any],
    semantic_result: Any = None,  # JevResult | None
    policy: Any = None,  # PolicySpec | None
) -> Any:  # Decision
    """Reproduz decisão a partir de DecisionRecord usando contracts.replay_decision.
    
    Não faz inferência — apenas recomputa usando a política e hard_eval do registro.
    """
    try:
        from llc2.contracts import (
            DecisionRecord,
            Decision,
            HardEvalResult,
            Check,
            RiskClass,
            JevResult,
            JevChoice,
            JevScore,
            JevNoul,
            load_policy,
            replay_decision as contracts_replay_decision,
        )
    except ImportError:
        return None
    
    # Converte dict para DecisionRecord (dataclass)
    decision_record = _dict_to_decision_record(record)
    
    # Evidência semântica: a do chamador ou a GRAVADA no registro
    # (Passagem 3 §12: decide(record.hard_eval, record.jev, policy@version)).
    jev_result = _effective_semantic(record, semantic_result)
    
    # Usa policy do registro ou carrega padrão
    policy_spec = policy or load_policy()
    
    return contracts_replay_decision(decision_record, jev_result, policy_spec)


def verify_replay_from_record(
    record: dict[str, Any],
    input_hash: str,
    semantic_result: Any = None,  # JevResult | None
    policy: Any = None,  # PolicySpec | None
    ctx_builder: Any = None,  # callable(Decision) -> GuardContext
) -> dict[str, Any]:
    """Verifica replay completo: hash -> decisão -> transição.
    
    Retorna dict com:
      - ok: bool (todos os checks passaram)
      - input_hash_match: bool
      - decision_match: bool
      - expected_transition: str | None
      - errors: list[str]
      - drift: dict | None
    """
    try:
        from llc2.contracts import (
            DecisionRecord,
            ReplayVerification,
            load_policy,
            verify_replay as contracts_verify_replay,
            DriftReport,
            l1_distance,
        )
    except ImportError:
        return {
            "ok": False,
            "input_hash_match": False,
            "decision_match": False,
            "expected_transition": None,
            "errors": ["llc2.contracts não disponível"],
            "drift": None,
        }
    
    decision_record = _dict_to_decision_record(record)
    jev_result = _effective_semantic(record, semantic_result)
    policy_spec = policy or load_policy()
    
    # Chama verify_replay do contracts
    verification = contracts_verify_replay(
        record=decision_record,
        semantic=jev_result,
        input_hash=input_hash,
        policy=policy_spec,
        ctx_builder=ctx_builder,
    )
    
    # Calcula drift se houver Jev result
    drift = None
    if jev_result and record.get("jev_result"):
        drift = _compute_drift(record["jev_result"], jev_result)
    
    return {
        "ok": verification.ok,
        "input_hash_match": verification.input_hash_match,
        "decision_match": verification.decision_match,
        "expected_transition": verification.expected_transition,
        "errors": list(verification.errors),
        "drift": drift,
    }


def _dict_to_decision_record(record: dict[str, Any]) -> Any:  # DecisionRecord
    """Converte dict do JSONL para DecisionRecord dataclass."""
    from llc2.contracts import DecisionRecord, Decision, HardEvalResult, Check, Action, Automation

    dec = record.get("decision") or {}
    action_value = dec.get("action") or record.get("action") or "CONTINUE"
    automation_value = dec.get("automation") or record.get("automation") or "AUTO"

    try:
        action = Action(action_value)
    except ValueError:
        action = Action.CONTINUE

    try:
        automation = Automation(automation_value)
    except ValueError:
        automation = Automation.AUTO

    config = record.get("config") or {}
    policy_version = config.get("policy_version") or record.get("policy_version") or "1.0.0"
    policy_id = config.get("policy_id") or record.get("policy_id") or "llc-default"
    thresholds_hash = config.get("thresholds_hash") or record.get("thresholds_hash") or "sha256:unknown"

    # `DecisionRecord.is_replayable()` exige `policy["version"]`, mas o JSONL
    # grava `policy_version`. Sem este mapeamento TODO registro aparece como
    # "não replayável" e o replay nunca reproduz nada.
    policy_mapping = {
        **config,
        "id": policy_id,
        "version": policy_version,
        "thresholds_hash": thresholds_hash,
    }

    decision = Decision(
        action=action,
        automation=automation,
        reason=dec.get("reason") or record.get("reason") or "",
        policy_id=policy_id,
        policy_version=policy_version,
        thresholds_hash=thresholds_hash,
        confidence=dec.get("confidence") or record.get("confidence"),
        evidence_refs=tuple(dec.get("evidence_refs", ()) or ()),
    )

    he = record.get("hard_eval")
    hard_eval = None
    if he and he.get("checks"):
        hard_eval = HardEvalResult(tuple(
            Check(
                name=c.get("name", "?"),
                passed=bool(c.get("passed", False)),
                blocking=bool(c.get("blocking", True)),
            )
            for c in he["checks"]
        ))

    qs = record.get("question_set")
    if qs is None:
        qs = {
            "id": config.get("question_set_id"),
            "version": config.get("question_set_version"),
            "hash": config.get("question_set_hash"),
            "expected_answers": [],
            "risk_noul_keys": [],
        }

    return DecisionRecord(
        decision_id=record.get("decision_id", ""),
        timestamp=record.get("ts", ""),
        node_id=record.get("node_id", record.get("step", "")),
        state_id=record.get("state_id", record.get("state", "")),
        event=record.get("event", ""),
        input_hash=record.get("input_hash", ""),
        state_hash=record.get("state_hash", ""),
        policy=policy_mapping,
        decision=decision,
        decision_kind=record.get("kind", ""),
        risk_class=record.get("risk_class", "R0"),
        question_set=qs,
        jev=record.get("jev") or record.get("jev_result"),
        hard_eval=record.get("hard_eval"),
        statechart=record.get("statechart"),
        action=record.get("action"),
        human=record.get("human_approval"),
        artifact_hashes=tuple(record.get("artifact_hashes", [])),
    )


def _dict_to_jev_result(semantic: dict[str, Any] | None) -> Any | None:  # JevResult | None
    """Converte dict para JevResult dataclass."""
    if not semantic:
        return None
    
    try:
        from llc2.contracts import JevResult, JevChoice, JevScore, JevNoul
    except ImportError:
        return None
    
    # Assinaturas canônicas (contracts.py):
    #   JevChoice(choice, probabilities, confidence)
    #   JevScore(score, levels, probabilities, confidence)
    #   JevNoul(p_true)  -> NÃO tem `confidence`
    answers = {}
    for k, v in semantic.get("answers", {}).items():
        if isinstance(v, dict):
            if "choice" in v:
                answers[k] = JevChoice(
                    choice=v["choice"],
                    probabilities=dict(v.get("probabilities") or {}),
                    confidence=float(v.get("confidence", 0.0)),
                )
            elif "score" in v or "index" in v:
                answers[k] = JevScore(
                    score=int(v.get("score", v.get("index", 0))),
                    levels=tuple(v.get("levels") or ()),
                    probabilities=dict(v.get("probabilities") or {}),
                    confidence=float(v.get("confidence", 0.0)),
                )
            elif "p_true" in v:
                answers[k] = JevNoul(p_true=float(v["p_true"]))
            else:
                answers[k] = v
        else:
            answers[k] = v
    
    # `JevResult(model, request_id, answers, usage)` — não existe campo
    # `probabilities` no topo (as probabilidades vivem em cada resposta).
    return JevResult(
        model=semantic.get("model", "unknown"),
        request_id=semantic.get("request_id", ""),
        answers=answers,
        usage=dict(semantic.get("usage") or {}),
    )


def _effective_semantic(record: dict[str, Any], semantic_result: Any = None) -> Any:
    """Evidência semântica efetiva do replay.

    Prioriza a fornecida pelo chamador; na ausência, usa a JÁ REGISTRADA no
    próprio registro (`jev` / `jev_result`). O replay nunca infere — apenas
    reutiliza a evidência gravada (Passagem 3 §12).
    """
    if semantic_result is not None:
        return semantic_result
    payload = record.get("jev") or record.get("jev_result")
    if not payload:
        return None
    return _dict_to_jev_result(payload)


def _compute_drift(original_jev: dict[str, Any], new_jev: Any) -> dict[str, Any] | None:
    """Computa drift entre resultado Jev original e novo."""
    try:
        from llc2.contracts import l1_distance, DriftReport
    except ImportError:
        return None
    
    # Extrai probabilidades dos answers
    def extract_probs(jev: Any) -> dict[str, float]:
        probs = {}
        if hasattr(jev, "probabilities") and jev.probabilities:
            return dict(jev.probabilities)
        if isinstance(jev, dict) and jev.get("probabilities"):
            return dict(jev["probabilities"])
        # Fallback: extrai de answers
        for k, v in (jev.answers if hasattr(jev, "answers") else jev.get("answers", {})).items():
            if hasattr(v, "confidence"):
                probs[k] = float(v.confidence)
            elif isinstance(v, dict) and "confidence" in v:
                probs[k] = float(v["confidence"])
        return probs
    
    old_probs = extract_probs(original_jev)
    new_probs = extract_probs(new_jev)
    
    max_l1 = l1_distance(old_probs, new_probs)
    
    # Verifica se decisão mudou
    old_decision = original_jev.get("routing") if isinstance(original_jev, dict) else getattr(original_jev, "routing", None)
    new_decision = new_jev.routing if hasattr(new_jev, "routing") else None
    decision_changed = old_decision != new_decision if old_decision and new_decision else False
    
    # Automation changed
    old_auto = original_jev.get("automation") if isinstance(original_jev, dict) else getattr(original_jev, "automation", None)
    new_auto = new_jev.automation if hasattr(new_jev, "automation") else None
    automation_changed = old_auto != new_auto if old_auto and new_auto else False
    
    return {
        "decision_changed": decision_changed,
        "automation_changed": automation_changed,
        "max_l1": max_l1,
        "kind": "DECISION_DRIFT" if decision_changed 
                else "CONFIDENCE_DRIFT" if max_l1 > 0.0
                else "STABLE",
    }


# ── Função principal para pipeline: tenta replay antes de chamar Jev ────────

def attempt_replay(
    input_hash: str,
    kind: str = "early_commitment",
    semantic_result: Any = None,
    policy: Any = None,
    ctx_builder: Any = None,
    outcome: str | None = None,
) -> dict[str, Any] | None:
    """Tenta replay determinístico para o input_hash.

    Retorna:
      - None: sem registro correspondente ou replay não aplicável
      - dict: resultado do replay com keys:
          * "replayed": True
          * "decision": Decision reproduzida
          * "verification": dict de verify_replay_from_record
          * "drift": DriftReport se houver
          * "record": DecisionRecord original

    `outcome` (F3/3.3, default None = comportamento legado): restringe
    a busca a records com aquele outcome — records de cache
    (replay_hit/miss) não sombreiam o record do classificador.
    """
    records = load_decision_records()
    exact = None
    latest_same_kind = None
    for record in reversed(records):
        if kind is not None and record.get("kind") != kind:
            continue
        if outcome is not None and record.get("outcome") != outcome:
            continue
        if latest_same_kind is None:
            latest_same_kind = record
        if record.get("input_hash") == input_hash:
            exact = record
            break

    record = exact or latest_same_kind
    if not record:
        return None

    config = record.get("config") or {}
    if not config.get("policy_version") or \
       not config.get("thresholds_hash") or \
       not (record.get("statechart") or {}).get("to"):
        if record.get("input_hash") != input_hash:
            return {
                "replayed": False,
                "reason": "input_hash_mismatch",
                "verification": {
                    "ok": False,
                    "input_hash_match": False,
                    "decision_match": False,
                    "expected_transition": None,
                    "errors": [f"input_hash divergente: {record.get('input_hash')} != {input_hash}"],
                    "drift": None,
                },
                "record": record,
            }
        return None

    if record.get("input_hash") != input_hash:
        return {
            "replayed": False,
            "reason": "input_hash_mismatch",
            "verification": {
                "ok": False,
                "input_hash_match": False,
                "decision_match": False,
                "expected_transition": None,
                "errors": [f"input_hash divergente: {record.get('input_hash')} != {input_hash}"],
                "drift": None,
            },
            "record": record,
        }

    reproduced = replay_decision_from_record(record, semantic_result, policy)
    if reproduced is None:
        return None

    verification = verify_replay_from_record(record, input_hash, semantic_result, policy, ctx_builder)

    # Passagem 2 §1.5: hit com `input_hash` igual devolve a DECISÃO DO REGISTRO,
    # sem inferência. A decisão recomputada serve apenas à verificação (drift).
    return {
        "replayed": True,
        "decision": _dict_to_decision_record(record).decision,
        "reproduced": reproduced,
        "verification": verification,
        "record": record,
    }


# ── Logging de eventos de replay ────────────────────────────────────────────

def log_replay_attempt(
    input_hash: str,
    result: dict[str, Any] | None,
    kind: str = "early_commitment",
) -> None:
    """Registra tentativa de replay em .ace/logs/replay.jsonl."""
    from datetime import datetime
    
    from llc_trace import trace_dir

    log_path = trace_dir() / "replay.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "event": "replay_attempt",
        "input_hash": input_hash,
        "kind": kind,
        "replayed": result["replayed"] if result else False,
        "reason": result.get("reason") if result else "no_record",
        "verification_ok": result["verification"]["ok"] if result and result.get("verification") else False,
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")