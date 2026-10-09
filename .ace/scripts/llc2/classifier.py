"""LLC 2.0 — Classificador de tarefas com Jev Choice (Fase 1).

Mudança normativa (§14 / F4 / G1):
  ANTES: if confidence < 0.80: return None  # descarta rótulo
  DEPOIS: rótulo SEMPRE preservado; baixa confiança rebaixa AUTOMATION.

O classificador retorna um dict com:
  - type: rótulo (crud_endpoint, ui_component, validation_rule, test_write, unknown)
  - confidence: float [0,1]
  - reasoning: str
  - routing: AUTO | REVIEW_REQUIRED | HUMAN_REQUIRED
  - policy_version, question_set_hash, input_hash, decision_id

NUNCA retorna None. Quando Jev está indisponível, fallback para LLM com a
mesma interface (não a interface antiga de XML/regex).
"""
from __future__ import annotations

import os
import uuid
from typing import Any

from llc2.contracts import (
    Automation,
    DecisionState,
    JevChoice,
    JevNoul,
    JevResult,
    PolicySpec,
    RiskClass,
    canonical_hash,
    load_policy,
    load_question_sets,
    automation_for,
)
from llc2.jev_adapter import JevAdapter, SemanticUnavailable, record_payload
from llc2.llm_shim import LlmAsJevTransport

# ── Feature flag ──────────────────────────────────────────────────────────
_USE_JEV = os.environ.get("LLC2_CLASSIFY", "1").strip() not in ("0", "", "false", "no")

# Replay determinístico (Fase 1/7) — cascata §21: Hard EVAL -> Replay -> Jev.
#
# Default **`0`**, alinhado ao §9 do plano e a `llc_harness/replay.py`
# (`os.environ.get('LLC2_REPLAY','0')`). A env é lida **por chamada**, não no
# import: uma leitura em nível de módulo vira dependência da ordem de
# importação dos testes e quebra quando outra suíte importa `llc2.classifier`
# antes de setar a flag.
REPLAY_ENV = "LLC2_REPLAY"
REPLAY_DEFAULT = "0"

# ── Question set fixo para classificação ──────────────────────────────────
_QUESTION_SET_ID = "task-classification"


def _make_state(task_description: str) -> DecisionState:
    """Monta DecisionState para classificação de tarefa."""
    inputs = {"task": task_description}
    return DecisionState(
        node_id="D-CLASSIFY-TASK",
        state_id="idle",
        decision_kind="classification",
        question_set_id=_QUESTION_SET_ID,
        question_set_version="2.0.0",
        question_set_hash="",  # preenchido após load
        inputs=inputs,
        risk_class=RiskClass.R1,
    )


def _extract_reasoning(result: JevResult) -> str:
    """Deriva reasoning textual do JevResult (para UX e debug)."""
    parts: list[str] = []
    for name, ans in result.answers.items():
        if isinstance(ans, JevChoice):
            parts.append(f"{name}={ans.choice} ({ans.confidence:.0%})")
        elif isinstance(ans, JevNoul):
            parts.append(f"{name}={ans.p_true:.2f}")
    return "; ".join(parts)


def _classification_from(result: JevResult) -> tuple[str, float] | None:
    """Extrai (label, confidence) do primeiro JevChoice no resultado."""
    for ans in result.answers.values():
        if isinstance(ans, JevChoice):
            return ans.choice, ans.confidence
    return None


def _derive_routing(
    label: str,
    confidence: float,
    result: JevResult | None,
    policy: PolicySpec,
) -> Automation:
    """Deriva nível de automação a partir da policy.

    Regras específicas de classificação:
      - unknown => HUMAN_REQUIRED (não sabemos o que é)
      - R1 (classificação é sempre R1) com confiança abaixo do review_min
        => REVIEW_REQUIRED
      - acima de auto_min => AUTO
      - no meio => REVIEW_REQUIRED
    """
    if label == "unknown":
        return Automation.HUMAN_REQUIRED

    level = automation_for(policy, RiskClass.R1, confidence)

    # Noul de risco (needs_human_review) pode elevar o piso
    if result is not None:
        noul = result.answers.get("needs_human_review")
        if isinstance(noul, JevNoul):
            direction = noul.decided(policy.noul_hi, policy.noul_lo)
            if direction is True:
                level = Automation.REVIEW_REQUIRED
            elif direction is None:
                # incerteza no Noul de risco => eleva para AUTO_AUDIT no mínimo
                if level in (Automation.AUTO,):
                    level = Automation.AUTO_AUDIT

    return level


def _trace_classification(
    *,
    task_description: str,
    result: dict[str, Any],
    jev_result: JevResult | None,
    policy: PolicySpec,
    state: DecisionState | None = None,
) -> None:
    """Registra Decision Record de classificação via llc_trace (Fase 0).

    Solução A: grava também os insumos da verificação §12 (statechart,
    jev_result, risk_class, question_set) para que o replay possa
    reproduzir a decisão sem re-inferência. `statechart` só é gravado
    com evidência semântica presente — sem ela o replay cai no portão 1
    (safe miss), nunca num hit de verificação fraca.
    """
    try:
        from llc_trace import record_decision, input_hash
    except ImportError:
        return

    ih = input_hash({"task": task_description})
    evidence: dict[str, Any] = {
        "classification_type": result["type"],
        "classification_confidence": result["confidence"],
        "routing": result["routing"],
    }
    if jev_result is not None:
        evidence["jev_model"] = jev_result.model
        evidence["jev_request_id"] = jev_result.request_id

    # `reason` precisa ser reproduzível por `decide()` para o hit: AUTO
    # limpo recomputa `semantic_confident`; demais routings recebem um
    # marcador que nunca coincide (miss seguro, valor ao vivo preservado).
    routing = result["routing"]
    reason = ("semantic_confident" if routing == Automation.AUTO.value
              else f"live_{routing}")

    qs_payload: dict[str, Any] | None = None
    if state is not None:
        qs_payload = {
            "id": state.question_set_id,
            "version": state.question_set_version,
            "hash": state.question_set_hash,
            "expected_answers": list(state.expected_answers),
            "risk_noul_keys": list(state.risk_noul_keys),
        }

    record_decision(
        "early_commitment",
        outcome="classify",
        reason=reason,
        state="STEP_EXECUTION",
        event="CLASSIFY",
        input_hash_value=ih,
        inputs={"task": task_description},
        evidence=evidence,
        automation=result["routing"],
        hard_eval={"checks": []},  # classificação não roda Hard EVAL
        config={
            "policy_version": policy.version,
            "policy_id": policy.id,
            "thresholds_hash": policy.thresholds_hash,
            "question_set_hash": result.get("question_set_hash"),
            "question_set_version": "2.0.0",
        },
        statechart=({"from": "idle", "to": "classified", "event": "DECIDED"}
                    if jev_result is not None else None),
        jev_result=(record_payload(jev_result)
                    if jev_result is not None else None),
        risk_class=RiskClass.R1.value,  # classificação é sempre R1
        question_set=qs_payload,
    )


def _try_replay_classification(input_hash: str) -> dict[str, Any] | None:
    """Tenta resolver a classificação por replay determinístico (zero tokens).

    Retorna o dict de classificação quando há registro com `input_hash` igual
    E a verificação do replay passa; caso contrário `None` (segue para o Jev).
    Nunca levanta: qualquer falha degrada para o caminho normal.
    """
    replay_enabled = os.environ.get(REPLAY_ENV, REPLAY_DEFAULT).strip().lower() \
        not in ("0", "", "false", "no")
    if not replay_enabled:
        return None
    try:
        from llc_replay.verify import attempt_replay
    except Exception:
        return None
    try:
        replay = attempt_replay(input_hash, kind="early_commitment")
    except Exception:
        return None
    if not replay or not replay.get("replayed"):
        return None
    if not (replay.get("verification") or {}).get("ok"):
        return None

    record = replay.get("record") or {}
    decision = replay.get("decision")
    evidence = record.get("evidence") or {}
    config = record.get("config") or {}
    return {
        "type": evidence.get("classification_type", "unknown"),
        "confidence": evidence.get("classification_confidence", 0.0),
        "reasoning": "replay_hit",
        "routing": (decision.automation.value if decision is not None
                    else record.get("automation")),
        "policy_version": config.get("policy_version"),
        "policy_id": config.get("policy_id"),
        "thresholds_hash": config.get("thresholds_hash"),
        "question_set_hash": config.get("question_set_hash"),
        "input_hash": input_hash,
        "decision_id": record.get("decision_id"),
        "jev_model": record.get("jev_model"),
        "jev_request_id": record.get("jev_request_id"),
        "replayed": True,
    }


def classify_task_v2(
    task_description: str,
    client: str | None = None,
    *,
    _transport: Any | None = None,
) -> dict[str, Any]:
    """Classifica uma tarefa via Jev Choice. NUNCA retorna None.

    Retorna dict com keys:
        type, confidence, reasoning, routing,
        policy_version, question_set_hash, input_hash, decision_id

    `_transport` é injetável para testes (FakeJevTransport).
    """
    policy = load_policy()
    decision_id = str(uuid.uuid4())

    # ── Replay antes do Jev: hit com input_hash igual não gasta tokens ────
    input_hash_value = canonical_hash({"task": task_description})
    replayed_result = _try_replay_classification(input_hash_value)
    if replayed_result is not None:
        return replayed_result

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
            pass  # qsets/qs ficam None; cai no fallback legado

    # ── tentativa Jev (ou shim LLM) ───────────────────────────────────────
    jev_result: JevResult | None = None
    classify_state: DecisionState | None = None
    label = "unknown"
    confidence = 0.0
    reasoning = ""

    if _USE_JEV and qs is not None:
        try:
            state = _make_state(task_description)
            # atualiza hash do question set no state
            state = DecisionState(
                **{**state.__dict__, "question_set_hash": qs.hash,
                   "expected_answers": qs.expected_answers,
                   "risk_noul_keys": qs.risk_noul_keys}
            )
            classify_state = state

            transport = _transport if _transport is not None else LlmAsJevTransport(client=client)
            adapter = JevAdapter(transport, question_sets=qsets)
            jev_result = adapter.evaluate(state)

            extracted = _classification_from(jev_result)
            if extracted:
                label, confidence = extracted
            reasoning = _extract_reasoning(jev_result)

        except SemanticUnavailable as exc:
            # Fallback: usar LLM direto com nova interface (preserva rótulo)
            jev_result = None
            reasoning = f"jev_unavailable: {exc}"
            # continua para fallback abaixo

    # ── fallback direto para LLM quando Jev indisponível ─────────────────
    if jev_result is None:
        # Fallback: usa o classificador legado mas com nova interface
        # (preserva rótulo, nunca retorna None)
        label, confidence, reasoning = _legacy_classify_with_preserve(
            task_description, client
        )

    routing = _derive_routing(label, confidence, jev_result, policy)

    result: dict[str, Any] = {
        "type": label,
        "confidence": confidence,
        "reasoning": reasoning,
        "routing": routing.value,
        "policy_version": policy.version,
        "policy_id": policy.id,
        "thresholds_hash": policy.thresholds_hash,
        "question_set_hash": qs_hash,
        "input_hash": input_hash_value,
        "decision_id": decision_id,
        "jev_model": jev_result.model if jev_result else "llm-legacy-xml",
        "jev_request_id": jev_result.request_id if jev_result else None,
        "replayed": False,
    }

    _trace_classification(
        task_description=task_description,
        result=result,
        jev_result=jev_result,
        policy=policy,
        state=classify_state,
    )

    return result


# ── Fallback legado (nova interface, mesmo parser) ────────────────────────

def _legacy_classify_with_preserve(
    task_description: str, client: str | None
) -> tuple[str, float, str]:
    """Fallback usando LLM subprocess com XML/regex.

    Diferença crucial do legado: NUNCA retorna None.
    Rótulo é sempre preservado, inclusive 'unknown'.
    """
    import shutil
    import subprocess
    import re

    if client is None:
        for c in ["claude", "opencode", "codex", "cursor"]:
            if shutil.which(c):
                client = c
                break

    if not client:
        return "unknown", 0.0, "no_llm_client_available"

    categories = {
        "crud_endpoint": "criar/alterar/deletar/listar endpoints de API",
        "ui_component": "criar/alterar componentes de interface (form, tabela, modal)",
        "validation_rule": "adicionar/alterar validacao em schema, campo ou sanitizacao",
        "test_write": "escrever testes unitarios, integracao ou E2E",
    }
    cats_text = "\n".join(f"- {t}: {d}" for t, d in categories.items())
    prompt = f"""Classifique a tarefa abaixo em uma destas 4 categorias.
Se a tarefa envolver multiplos aspectos, escolha o tipo que representa a MAIOR PARTE do esforco.

Categorias:
{cats_text}

Se nao se encaixar em nenhuma, retorne type="unknown".

Tarefa: {task_description}

Responda APENAS com XML:
<task_classification><type>...</type><confidence>0.XX</confidence>
<reasoning>...</reasoning></task_classification>"""

    try:
        # Usa STDIN (como replay.py) — compatível com todos os CLIs
        process = subprocess.Popen(
            [client],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output, _ = process.communicate(input=prompt, timeout=30)
    except Exception as exc:
        return "unknown", 0.0, f"llm_error: {exc}"

    type_match = re.search(r"<type>(.*?)</type>", output)
    confidence_match = re.search(r"<confidence>(.*?)</confidence>", output)
    reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", output)

    if not type_match:
        return "unknown", 0.0, "parse_error: no type tag"

    task_type = type_match.group(1).strip()
    confidence = 0.0
    reasoning = reasoning_match.group(1) if reasoning_match else ""

    try:
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
    except ValueError:
        confidence = 0.0

    if task_type not in categories and task_type != "unknown":
        task_type = "unknown"
        confidence = 0.0
        reasoning = f"parse_error: unrecognized type '{task_type}'"

    return task_type, confidence, reasoning
