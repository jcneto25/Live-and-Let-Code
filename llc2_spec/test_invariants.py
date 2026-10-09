"""LLC 2.0 — Testes executáveis dos invariantes (Passagem 4).

Validam a ESPECIFICAÇÃO (`contracts.py`, `jev_adapter.py`,
`macro_projection.py`) e as correções F1..F7. A implementação do runtime
deve satisfazê-los sem alterá-los.

Execução:  pytest llc2_spec/test_invariants.py -q
"""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from contracts import (
    FORBIDDEN_EVERYWHERE, GUARD_REGISTRY, TRANSITIONS, Action, Automation,
    CAPABILITY_MATRIX, Check, Classification, Decision, DecisionRecord,
    DecisionState, DriftReport, EventType, GuardContext, HardEvalResult,
    JevChoice, JevNoul, JevResult, JevScore, PolicySpec, RiskClass,
    automation_for, canonical_hash, capabilities_for_state, decide,
    downgrade, guard_gate_has_evidence, guard_retries_left,
    l1_distance, load_policy, load_question_sets, next_state,
    raise_to, replay_decision, verify_replay,
)
from jev_adapter import (
    FakeJevTransport, JevAdapter, MemoryCache, SemanticUnavailable,
    record_payload,
)
from macro_projection import divergences, macro_view, phase_of

HERE = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════════
# fixtures
# ══════════════════════════════════════════════════════════════════════════

def policy() -> PolicySpec:
    return load_policy(HERE / "decision-policy.v1.yaml")


def question_sets():
    return load_question_sets(HERE / "question-sets.v1.yaml")


def hard_ok() -> HardEvalResult:
    return HardEvalResult((Check("fitness", True), Check("coverage", True)))


def hard_bad() -> HardEvalResult:
    return HardEvalResult((Check("fitness", True), Check("security", False)))


def jev_high() -> JevResult:
    """Alta confiança, sem Noul de risco afirmativo."""
    return JevResult(
        model="jev-1.13.0", request_id="r1",
        answers={
            "task_type": JevChoice("crud_endpoint",
                                   {"crud_endpoint": 0.95, "test_write": 0.05},
                                   0.90),
            "complexity": JevScore(1, ("Trivial", "Pequena", "Média", "Grande"),
                                   {"1": 0.92, "2": 0.08}, 0.88),
            "needs_human_review": JevNoul(0.03),
        },
        usage={"input_tokens": 1200, "output_tokens": 40},
    )


def jev_risky() -> JevResult:
    """Noul de risco AFIRMATIVO: p_true=0.97 => 'sim, precisa de humano'.

    Completo (3/3) para isolar o efeito da direção do Noul do efeito de
    resposta parcial.
    """
    return JevResult(
        model="jev-1.13.0", request_id="r2",
        answers={
            "task_type": JevChoice("crud_endpoint", {"crud_endpoint": 0.96}, 0.95),
            "complexity": JevScore(1, ("Trivial", "Pequena", "Média", "Grande"),
                                   {"1": 0.9}, 0.95),
            "needs_human_review": JevNoul(0.97),
        },
    )


def classify_state(risk: RiskClass = RiskClass.R1,
                   with_risk_noul: bool = True) -> DecisionState:
    qs = question_sets()["task-classification"]
    return DecisionState.from_question_set(
        qs, node_id="step-2", state_id="active.verifying.semantic",
        decision_kind="D-CLASSIFY-TASK",
        inputs={"task": "criar endpoint de usuario"}, risk_class=risk,
    )


def structural_state(risk: RiskClass = RiskClass.R0) -> DecisionState:
    """Sem question set => semântica não é esperada."""
    return DecisionState(node_id="step-11", state_id="active.verifying",
                         decision_kind="D-HARD-ONLY", question_set_id=None,
                         question_set_version=None, question_set_hash=None,
                         inputs={"checks": "fitness"}, risk_class=risk)


def ctx(**kw) -> GuardContext:
    return GuardContext(**kw)


# ══════════════════════════════════════════════════════════════════════════
# F1 — thresholds são DADOS, não literais no código
# ══════════════════════════════════════════════════════════════════════════

def test_f1_policy_comes_from_yaml_with_real_hash():
    p = policy()
    assert p.id == "llc-default" and p.version == "1.0.0"
    assert p.thresholds_hash.startswith("sha256:")
    assert len(p.thresholds_hash) == 71


def test_f1_thresholds_hash_is_stable_and_content_bound():
    a = policy()
    b = load_policy(HERE / "decision-policy.v1.yaml")
    assert a.thresholds_hash == b.thresholds_hash
    other = dataclasses.replace(a, risk={"R2": {"auto_min": 0.99}})
    assert PolicySpec(**{**other.__dict__,
                         "thresholds_hash": canonical_hash(
                             {"risk": {"R2": {"auto_min": 0.99}},
                              "noul": a.noul, "fallback": a.fallback,
                              "routing": a.routing, "limits": a.limits})
                         }).thresholds_hash != a.thresholds_hash


def test_f1_changing_yaml_changes_automation(tmp_path):
    """Se o limiar estivesse no código, isto falharia."""
    strict = tmp_path / "strict.yaml"
    strict.write_text((HERE / "decision-policy.v1.yaml").read_text(encoding="utf-8")
                      .replace("auto_min: 0.85", "auto_min: 0.99"),
                      encoding="utf-8")
    p = load_policy(strict)
    assert automation_for(p, RiskClass.R2, 0.90) is not Automation.AUTO
    assert automation_for(policy(), RiskClass.R2, 0.90) is Automation.AUTO


def test_f1_risk_scales_monotonically():
    for c in (0.0, 0.55, 0.75, 0.95):
        levels = [automation_for(policy(), r, c) for r in RiskClass]
        idx = [__import__("contracts").AUTOMATION_ORDER.index(x) for x in levels]
        assert idx == sorted(idx), f"thresholds não escalam com risco em conf={c}"


# ══════════════════════════════════════════════════════════════════════════
# F2 — semântica esperada e ausente => HUMAN_REQUIRED (fecha fail-open)
# ══════════════════════════════════════════════════════════════════════════

def test_f2_semantic_expected_and_missing_is_human_required():
    d = decide(classify_state(), hard_ok(), None)
    assert d.automation is Automation.HUMAN_REQUIRED
    assert d.reason == "semantic_unavailable"
    assert d.action is Action.ESCALATE


def test_f2_semantic_expected_and_missing_even_in_r0():
    d = decide(classify_state(RiskClass.R0), hard_ok(), None)
    assert d.automation is Automation.HUMAN_REQUIRED


def test_f2_semantic_not_expected_is_structural_auto():
    d = decide(structural_state(), hard_ok(), None)
    assert d.automation is Automation.AUTO
    assert d.reason == "resolved_deterministically"


def test_f2_partial_answer_downgrades_one_level():
    partial = JevResult("jev-1.13.0", "r3", {
        "task_type": JevChoice("crud_endpoint", {"crud_endpoint": 0.95}, 0.95),
    })  # falta complexity e needs_human_review
    d = decide(classify_state(), hard_ok(), partial)
    assert d.reason == "semantic_partial"
    # min_conf 0.95 em R1 => AUTO; parcial rebaixa para AUTO_AUDIT
    assert d.automation is Automation.AUTO_AUDIT


# ══════════════════════════════════════════════════════════════════════════
# F3 — Noul: direção antes de força
# ══════════════════════════════════════════════════════════════════════════

def test_f3_risk_noul_affirmative_does_not_become_auto():
    d = decide(classify_state(RiskClass.R2), hard_ok(), jev_risky())
    assert d.automation is Automation.REVIEW_REQUIRED
    assert d.reason == "risk_noul_affirmative"


def test_f3_risk_noul_affirmative_in_r3_is_human():
    d = decide(classify_state(RiskClass.R3), hard_ok(), jev_risky())
    assert d.automation is Automation.HUMAN_REQUIRED


def test_f3_non_risk_noul_high_stays_auto():
    """Noul de QUALIDADE positivo não é risco: confiança alta segue AUTO."""
    st = structural_state(RiskClass.R2)
    st = dataclasses.replace(st, expected_answers=(), risk_noul_keys=())
    good = JevResult("jev-1.13.0", "r4", {
        "task_type": JevChoice("crud_endpoint", {"crud_endpoint": 0.96}, 0.95),
        "tecnico_cobre_requisitos": JevNoul(0.97),
    })
    d = decide(st, hard_ok(), good, semantic_expected=True)
    assert d.automation is Automation.AUTO


def test_f3_uncertain_risk_noul_collapses_to_human():
    """Noul de risco em zona incerta => decision_strength 0 => eixo de
    confiança vai a zero. O piso AUTO_AUDIT é segunda linha de defesa; aqui
    a primeira (confiança mínima) já resolve, e fail-closed."""
    uncertain = JevResult("jev-1.13.0", "r5", {
        "task_type": JevChoice("crud_endpoint", {"crud_endpoint": 0.96}, 0.95),
        "complexity": JevScore(1, ("Trivial", "Pequena", "Média", "Grande"),
                               {"1": 0.9}, 0.95),
        "needs_human_review": JevNoul(0.5),
    })
    d = decide(classify_state(RiskClass.R0), hard_ok(), uncertain)
    assert d.automation is Automation.HUMAN_REQUIRED
    assert d.confidence == pytest.approx(0.0)


def test_noul_semantics_p_true_vs_decision_strength():
    n = JevNoul(0.90)
    assert n.p_true == 0.90 and n.decision_strength == 0.80
    assert not hasattr(n, "confidence")
    assert JevNoul(0.50).decided() is None
    assert JevNoul(0.85).decided() is True
    assert JevNoul(0.10).decided() is False


def test_confidence_of_normalizes_noul_on_same_axis_only():
    r = jev_high()
    assert r.confidence_of("needs_human_review") == pytest.approx(0.94)
    assert r.confidence_of("task_type") == pytest.approx(0.90)


# ══════════════════════════════════════════════════════════════════════════
# F4 — classificação preservada, roteamento rebaixado (§14)
# ══════════════════════════════════════════════════════════════════════════

def test_f4_low_confidence_preserves_label_and_downgrades():
    low = JevResult("jev-1.13.0", "r6", {
        "task_type": JevChoice("BUG_FIX", {"BUG_FIX": 0.61, "FEATURE": 0.39},
                               0.22),
    })
    d = decide(classify_state(RiskClass.R1), hard_ok(), low)
    assert isinstance(d.classification, Classification)
    assert d.classification.label == "BUG_FIX"       # rótulo preservado
    assert d.classification.confidence == pytest.approx(0.22)
    assert d.automation is Automation.HUMAN_REQUIRED  # roteamento caiu
    assert d.reason == "semantic_partial"             # faltaram 2 perguntas


def test_f4_label_never_becomes_unknown_by_threshold():
    """`unknown` só existe como opção do modelo, nunca como punição de limiar."""
    c = JevChoice("BUG_FIX", {"BUG_FIX": 0.61}, 0.22)
    assert "unknown" in question_sets()["task-classification"].questions[
        "task_type"].options
    assert c.choice == "BUG_FIX"


def test_f4_classification_is_none_only_when_no_choice_answer():
    no_choice = JevResult("jev-1.13.0", "r7", {"needs_human_review": JevNoul(0.1)})
    d = decide(classify_state(), hard_ok(), no_choice)
    assert d.classification is None


# ══════════════════════════════════════════════════════════════════════════
# F5 — regiões paralelas, join explícito, capacidades por prefixo
# ══════════════════════════════════════════════════════════════════════════

def test_f5_substates_resolve_capabilities_by_prefix():
    assert capabilities_for_state("active.verifying.hard.passed") == \
        capabilities_for_state("active.verifying.hard")
    assert "jev_eval" in capabilities_for_state("active.verifying.semantic.ready")
    assert "run_hard_eval" not in capabilities_for_state(
        "active.verifying.semantic.ready")


def test_f5_join_requires_both_regions_final():
    assert next_state("active.verifying", EventType.VERIFICATION_COMPLETE,
                      ctx(regions={"hard": "passed", "semantic": "ready"})) == \
        "active.deciding"
    assert next_state("active.verifying", EventType.VERIFICATION_COMPLETE,
                      ctx(regions={"hard": "passed",
                                   "semantic": "running"})) is None
    assert next_state("active.verifying", EventType.VERIFICATION_COMPLETE,
                      ctx(regions={"semantic": "ready"})) is None


def test_f5_hard_failure_routes_to_human_not_auto():
    nxt = next_state("active.verifying", EventType.VERIFICATION_COMPLETE,
                     ctx(hard=hard_bad(),
                         regions={"hard": "failed", "semantic": "ready"}))
    assert nxt == "governance.awaiting_human"


def test_f5_hard_region_transitions():
    assert next_state("active.verifying.hard", EventType.HARD_EVAL_DONE,
                      ctx(hard=hard_ok())) == "active.verifying.hard.passed"
    assert next_state("active.verifying.hard", EventType.HARD_EVAL_DONE,
                      ctx(hard=hard_bad())) == "active.verifying.hard.failed"


def test_f5_semantic_not_needed_guard():
    assert next_state("active.verifying.semantic",
                      EventType.SEMANTIC_NOT_NEEDED,
                      ctx(hard=hard_ok(), has_question_set=False)) == \
        "active.verifying.semantic.not_needed"
    assert next_state("active.verifying.semantic",
                      EventType.SEMANTIC_NOT_NEEDED,
                      ctx(hard=hard_ok(), has_question_set=True)) is None


# ══════════════════════════════════════════════════════════════════════════
# INV-004 — falha de Hard EVAL não é overridden por Jev
# ══════════════════════════════════════════════════════════════════════════

def test_inv004_hard_failure_never_overridden():
    d = decide(classify_state(), hard_bad(), jev_high())
    assert d.automation is Automation.HUMAN_REQUIRED
    assert d.action is Action.BLOCK
    assert d.reason == "hard_eval_failed"


def test_inv004_hard_failure_blocks_even_in_r0():
    assert decide(classify_state(RiskClass.R0), hard_bad(),
                  jev_high()).automation is Automation.HUMAN_REQUIRED


# ══════════════════════════════════════════════════════════════════════════
# INV-005 — R3 nunca AUTO
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("conf", [0.0, 0.5, 0.9, 0.99, 1.0])
def test_inv005_r3_never_auto(conf):
    assert automation_for(policy(), RiskClass.R3, conf) is not Automation.AUTO


def test_inv005_helpers_are_monotonic():
    assert raise_to(Automation.AUTO, Automation.REVIEW_REQUIRED) is \
        Automation.REVIEW_REQUIRED
    assert raise_to(Automation.HUMAN_REQUIRED, Automation.AUTO) is \
        Automation.HUMAN_REQUIRED
    assert downgrade(Automation.AUTO) is Automation.AUTO_AUDIT
    assert downgrade(Automation.HUMAN_REQUIRED) is Automation.HUMAN_REQUIRED


# ══════════════════════════════════════════════════════════════════════════
# INV-006 / F7 — replay sem inferência e com verificação de hash
# ══════════════════════════════════════════════════════════════════════════

def _record(decision: Decision, state: DecisionState,
            input_hash: str) -> DecisionRecord:
    qs = question_sets()["task-classification"]
    return DecisionRecord(
        decision_id="d1", timestamp="2026-10-07T00:00:00Z",
        node_id=state.node_id, state_id="active.deciding", event="DECIDED",
        input_hash=input_hash, state_hash="sha256:y",
        decision_kind=state.decision_kind, risk_class=state.risk_class.value,
        policy={"id": "llc-default", "version": "1.0.0",
                "thresholds_hash": policy().thresholds_hash},
        decision=decision,
        question_set={"id": qs.id, "version": qs.version, "hash": qs.hash,
                      "expected_answers": list(qs.expected_answers),
                      "risk_noul_keys": list(qs.risk_noul_keys)},
        hard_eval={"checks": [{"name": "fitness", "passed": True,
                               "blocking": True}]},
        statechart={"version": "1.0.0", "from": "active.deciding",
                    "to": "governance.auto_approved", "guard": "is_auto",
                    "guard_result": True},
    )


def test_inv006_replay_reproduces_decision_without_inference():
    st = classify_state()
    original = decide(st, hard_ok(), jev_high())
    rec = _record(original, st, st.input_hash)
    reproduced = replay_decision(rec, jev_high())
    assert (reproduced.action, reproduced.automation, reproduced.reason) == \
        (original.action, original.automation, original.reason)


def test_inv006_replay_is_pure_no_network():
    src = inspect.getsource(replay_decision)
    for banned in ("requests", "urllib", "subprocess", "open("):
        assert banned not in src


def test_f7_verify_replay_ok_on_matching_hash():
    st = classify_state()
    original = decide(st, hard_ok(), jev_high())
    rec = _record(original, st, st.input_hash)
    v = verify_replay(rec, jev_high(), st.input_hash,
                      ctx_builder=lambda d: ctx(decision=d))
    assert v.ok and v.input_hash_match and v.decision_match
    assert v.expected_transition == "governance.auto_approved"
    assert v.errors == ()


def test_f7_verify_replay_detects_hash_mismatch():
    st = classify_state()
    original = decide(st, hard_ok(), jev_high())
    rec = _record(original, st, st.input_hash)
    v = verify_replay(rec, jev_high(), "sha256:outro",
                      ctx_builder=lambda d: ctx(decision=d))
    assert not v.ok and not v.input_hash_match
    assert any("input_hash divergente" in e for e in v.errors)


def test_f7_record_without_policy_version_is_not_replayable():
    st = classify_state()
    rec = _record(decide(st, hard_ok(), jev_high()), st, st.input_hash)
    rec = DecisionRecord(**{**rec.__dict__, "policy": {"id": "x"}})
    assert not rec.is_replayable()


def test_f7_replay_never_reinfers():
    st = classify_state()
    original = decide(st, hard_ok(), jev_high())
    rec = _record(original, st, st.input_hash)
    # replay SEM JevResult e com semântica esperada => HUMAN_REQUIRED,
    # provando que não há "inferência silenciosa" caindo para AUTO.
    assert replay_decision(rec, None).automation is Automation.HUMAN_REQUIRED


# ══════════════════════════════════════════════════════════════════════════
# INV-007 — Decision Record versionado
# ══════════════════════════════════════════════════════════════════════════

def test_inv007_decision_carries_policy_identity():
    d = decide(classify_state(), hard_ok(), jev_high())
    assert d.policy_id and d.policy_version and d.thresholds_hash


def test_inv007_record_requires_versioned_fields():
    required = {"decision_id", "node_id", "state_id", "event",
                "input_hash", "state_hash", "policy", "decision"}
    fields = {f.name for f in dataclasses.fields(DecisionRecord)
              if f.default is dataclasses.MISSING
              and f.default_factory is dataclasses.MISSING}
    assert required <= fields


def test_inv007_hashes_are_deterministic():
    assert canonical_hash({"b": 1, "a": 2}) == canonical_hash({"a": 2, "b": 1})
    assert classify_state().input_hash == classify_state().input_hash


# ══════════════════════════════════════════════════════════════════════════
# INV-008 — capacidades limitadas pelo estado
# ══════════════════════════════════════════════════════════════════════════

def test_inv008_every_state_in_transitions_has_capability_matrix():
    states = {t.state for t in TRANSITIONS} | {t.next for t in TRANSITIONS}
    missing = []
    for s in sorted(states):
        try:
            capabilities_for_state(s)
        except KeyError:
            missing.append(s)
    assert not missing, f"estados sem matriz: {missing}"


def test_inv008_awaiting_human_cannot_write_or_deploy():
    caps = capabilities_for_state("governance.awaiting_human")
    for bad in ("apply_changes", "git_commit", "deploy", "jev_eval"):
        assert bad not in caps


def test_inv008_deploy_is_forbidden_everywhere():
    for st in CAPABILITY_MATRIX:
        assert "deploy" not in capabilities_for_state(st)
    for bad in ("deploy", "force_push", "delete_session"):
        assert bad in FORBIDDEN_EVERYWHERE


def test_inv008_unknown_state_raises():
    with pytest.raises(KeyError):
        capabilities_for_state("estado.inexistente")


# ══════════════════════════════════════════════════════════════════════════
# INV-009 — gate consome evidência
# ══════════════════════════════════════════════════════════════════════════

def test_inv009_decision_always_carries_evidence():
    d = decide(classify_state(), hard_ok(), jev_high())
    assert d.evidence_refs
    assert any(r.startswith("jev:") for r in d.evidence_refs)


def test_inv009_auto_approved_to_applying_requires_evidence():
    d = decide(classify_state(), hard_ok(), jev_high())
    assert next_state("governance.auto_approved", EventType.APPLIED,
                      ctx(decision=d)) == "active.applying"
    empty = Decision(Action.CONTINUE, Automation.AUTO, "r", "p", "1", "h")
    assert next_state("governance.auto_approved", EventType.APPLIED,
                      ctx(decision=empty)) is None
    assert not guard_gate_has_evidence(ctx(decision=empty))


# ══════════════════════════════════════════════════════════════════════════
# INV-010 — rejeição gera rework, não aborta
# ══════════════════════════════════════════════════════════════════════════

def test_inv010_rejection_with_retries_goes_to_rework():
    assert next_state("governance.awaiting_human", EventType.HUMAN_REJECTED,
                      ctx(retries=0, max_retries=3)) == "governance.rework"


def test_inv010_rejection_without_retries_fails():
    assert next_state("governance.awaiting_human", EventType.HUMAN_REJECTED,
                      ctx(retries=3, max_retries=3)) == "failed"


def test_inv010_rework_returns_to_preparing():
    assert next_state("governance.rework", EventType.RETRY, ctx()) == \
        "active.preparing"
    assert guard_retries_left(ctx(retries=0, max_retries=3))
    assert not guard_retries_left(ctx(retries=3, max_retries=3))


# ══════════════════════════════════════════════════════════════════════════
# INV-002 / INV-003 / INV-011 — eventos, guards puras, sem Jev em guard
# ══════════════════════════════════════════════════════════════════════════

def test_inv002_every_transition_has_event():
    assert all(isinstance(t.event, EventType) and t.event.value
               for t in TRANSITIONS)


def test_inv003_all_guards_registered_and_pure():
    for t in TRANSITIONS:
        if t.guard:
            assert t.guard in GUARD_REGISTRY
    for name, fn in GUARD_REGISTRY.items():
        src = inspect.getsource(fn)
        for banned in ("requests", "urllib", "subprocess", "open(", "socket"):
            assert banned not in src, f"{name} faz IO"
        ann = inspect.signature(fn).return_annotation
        assert ann in (bool, "bool", inspect.Signature.empty), name


def test_inv003_guards_return_bool():
    assert guard_gate_has_evidence(ctx(decision=Decision(
        Action.CONTINUE, Automation.AUTO, "r", "p", "1", "h",
        evidence_refs=("fitness",)))) is True


def test_f6_guards_have_uniform_single_argument():
    for name, fn in GUARD_REGISTRY.items():
        params = list(inspect.signature(fn).parameters)
        assert params == ["ctx"], f"guard {name} tem assinatura {params}"


def test_inv011_no_guard_receives_evaluator():
    banned = {"client", "evaluator", "jev", "llm", "semantic_client",
              "policy_client", "http", "transport"}
    for name, fn in GUARD_REGISTRY.items():
        assert not (set(inspect.signature(fn).parameters) & banned)
    assert "decide" not in GUARD_REGISTRY


# ══════════════════════════════════════════════════════════════════════════
# INV-001 — LLM não muta estado de workflow
# ══════════════════════════════════════════════════════════════════════════

def test_inv001_no_capability_writes_state_directly():
    for st, caps in CAPABILITY_MATRIX.items():
        for forbidden in ("write_session", "mutate_state", "set_state",
                          "delete_session"):
            assert forbidden not in caps, st


def test_inv001_rollback_never_moves_forward():
    for t in TRANSITIONS:
        if t.action == "rollback":
            assert t.next in {"active.preparing", "governance.rework", "failed"}


# ══════════════════════════════════════════════════════════════════════════
# ADAPTER JEV — contrato
# ══════════════════════════════════════════════════════════════════════════

_RAW_OK = {
    "task_type": {"choice": "crud_endpoint",
                  "probabilities": {"crud_endpoint": 0.95}, "confidence": 0.9},
    "complexity": {"score": 1, "probabilities": {"1": 0.9}, "confidence": 0.9},
    "needs_human_review": {"noul": 0.03},
}


def _adapter(**kw) -> JevAdapter:
    return JevAdapter(FakeJevTransport(_RAW_OK, **kw),
                      question_sets=question_sets(),
                      cache=MemoryCache(), **({"max_retries": 1} | {})
                      if False else {})


def test_adapter_fanout_is_one_call():
    a = JevAdapter(FakeJevTransport(_RAW_OK), question_sets=question_sets(),
                   cache=MemoryCache())
    st = classify_state()
    r1 = a.evaluate(st)
    assert a.calls == 1
    assert set(r1.answers) == set(question_sets()[
        "task-classification"].expected_answers)
    r2 = a.evaluate(st)          # cache hit
    assert a.calls == 1 and r2 == r1


def test_adapter_types_are_correct():
    a = _adapter()
    r = a.evaluate(classify_state())
    assert isinstance(r.answers["task_type"], JevChoice)
    assert isinstance(r.answers["complexity"], JevScore)
    assert isinstance(r.answers["needs_human_review"], JevNoul)
    assert r.model == "jev-1.13.0"


def test_adapter_rejects_option_outside_criteria():
    bad = dict(_RAW_OK)
    bad["task_type"] = {"choice": "OUTRA", "confidence": 0.9}
    a = JevAdapter(FakeJevTransport(bad), question_sets=question_sets())
    with pytest.raises(SemanticUnavailable):
        a.evaluate(classify_state())


def test_adapter_rejects_score_out_of_range():
    bad = dict(_RAW_OK)
    bad["complexity"] = {"score": 9, "confidence": 0.9}
    a = JevAdapter(FakeJevTransport(bad), question_sets=question_sets())
    with pytest.raises(SemanticUnavailable):
        a.evaluate(classify_state())


def test_adapter_rejects_noul_out_of_range():
    bad = dict(_RAW_OK)
    bad["needs_human_review"] = {"noul": 1.7}
    a = JevAdapter(FakeJevTransport(bad), question_sets=question_sets())
    with pytest.raises(SemanticUnavailable):
        a.evaluate(classify_state())


def test_adapter_missing_answer_is_partial_not_failure():
    a = JevAdapter(FakeJevTransport(_RAW_OK, drop=("complexity",)),
                   question_sets=question_sets())
    r = a.evaluate(classify_state())
    assert "complexity" not in r.answers
    d = decide(classify_state(), hard_ok(), r)
    assert d.reason == "semantic_partial"


def test_adapter_unavailable_fails_closed():
    a = JevAdapter(FakeJevTransport(_RAW_OK, fail_times=99),
                   question_sets=question_sets(), max_retries=2)
    with pytest.raises(SemanticUnavailable):
        a.evaluate(classify_state())
    assert a.calls == 3      # 1 + 2 retries


def test_adapter_rejects_unpinned_model():
    qs = question_sets()["task-classification"]
    unpinned = dataclasses.replace(qs, model="jev-latest")
    a = JevAdapter(FakeJevTransport(_RAW_OK),
                   question_sets={"task-classification": unpinned})
    with pytest.raises(SemanticUnavailable):
        a.evaluate(dataclasses.replace(
            classify_state(), question_set_hash=unpinned.hash))


def test_adapter_rejects_model_drift_from_pin():
    a = JevAdapter(FakeJevTransport(_RAW_OK, model="jev-9.9.9"),
                   question_sets=question_sets())
    with pytest.raises(SemanticUnavailable):
        a.evaluate(classify_state())


def test_adapter_request_is_idempotent_and_hashed():
    a = JevAdapter(FakeJevTransport(_RAW_OK), question_sets=question_sets())
    st = classify_state()
    a.evaluate(st)
    a.evaluate(st)
    assert len(a.transport.seen) == 2
    assert a.transport.seen[0].idempotency_key == \
        a.transport.seen[1].idempotency_key
    assert a.transport.seen[0].model == "jev-1.13.0"


def test_record_payload_always_keeps_probabilities():
    r = _adapter().evaluate(classify_state())
    payload = record_payload(r)
    assert payload["model"] == "jev-1.13.0"
    assert "probabilities" in payload["answers"]["task_type"]
    assert payload["answers"]["needs_human_review"]["p_true"] == 0.03
    assert "decision_strength" in payload["answers"]["needs_human_review"]


# ══════════════════════════════════════════════════════════════════════════
# DRIFT
# ══════════════════════════════════════════════════════════════════════════

def test_drift_kinds():
    assert DriftReport(True, True, 0.4).kind == "DECISION_DRIFT"
    assert DriftReport(False, True, 0.1).kind == "CONFIDENCE_DRIFT"
    assert DriftReport(False, False, 0.0).kind == "STABLE"


def test_l1_distance():
    assert l1_distance({"a": 1.0}, {"a": 1.0}) == 0.0
    assert abs(l1_distance({"a": 1.0}, {"a": 0.6}) - 0.4) < 1e-9


# ══════════════════════════════════════════════════════════════════════════
# PROJEÇÃO MACRO — uma fonte de verdade
# ══════════════════════════════════════════════════════════════════════════

def test_macro_phase_mapping():
    assert phase_of("0.5") == "discovery"
    assert phase_of("2") == "discovery"
    assert phase_of("3") == "planning"
    assert phase_of("5.3") == "planning"
    assert phase_of("9") == "implementation"
    assert phase_of("99") == "unmapped"


def test_macro_view_is_deterministic():
    configs = {"0.5": "done", "2": "active.preparing", "3": "idle"}
    assert macro_view(configs) == macro_view(configs)


def test_macro_view_precedence():
    assert macro_view({"2": "done", "3": "done"}).phase == "terminal"
    assert macro_view({"2": "governance.awaiting_human",
                       "3": "active.deciding"}).phase == "governance"
    assert macro_view({"2": "done", "3": "active.deciding"}).phase == "planning"


def test_macro_view_reports_failures_and_human_blocks():
    v = macro_view({"2": "governance.awaiting_human", "3": "failed"})
    assert v.blocked_by_human == ("2",) and v.failed == ("3",)


def test_macro_divergences_are_declared_not_silent():
    d = divergences()
    assert any("use_cases" in x for x in d)
    assert any("deploy" in x for x in d)
