"""LLC 2.0 — Contratos executáveis v2 (Passagem 4).

Mudanças normativas em relação à v1 (Passagem 3):

  F1  Thresholds saem do código e passam a ser carregados de
      `decision-policy.v1.yaml`; `thresholds_hash` é calculado de verdade.
  F2  `decide()` fecha o fail-open: semântica ESPERADA e ausente =>
      HUMAN_REQUIRED ("semantic_unavailable"), nunca AUTO.
  F3  Noul passa a ser avaliado por DIREÇÃO antes de força
      (`raises_risk_when_true`), não só por |2p-1|.
  F4  `Classification` é sempre populada e nunca descartada (§14).
  F5  Regiões paralelas entram na tabela de transições e na matriz de
      capacidade (resolução por prefixo); join explícito via
      `VERIFICATION_COMPLETE`.
  F6  Guards recebem um único `GuardContext` (assinatura uniforme).
  F7  Replay verifica `input_hash` antes de reproduzir.

Regra permanente: nada aqui executa efeito, rede, LLM ou Jev.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_POLICY_PATH = HERE / "decision-policy.v1.yaml"
DEFAULT_QUESTION_SETS_PATH = HERE / "question-sets.v1.yaml"


# ══════════════════════════════════════════════════════════════════════════
# 1. ENUMS
# ══════════════════════════════════════════════════════════════════════════

class RiskClass(str, Enum):
    R0 = "R0"  # leitura / informacional — sem efeito
    R1 = "R1"  # escrita de artefato reversível (docs, PRP, ADR)
    R2 = "R2"  # mudança de código-fonte
    R3 = "R3"  # irreversível: migration, schema, auth, CI, secrets, deploy


class Automation(str, Enum):
    AUTO = "AUTO"
    AUTO_AUDIT = "AUTO_AUDIT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


AUTOMATION_ORDER: tuple[Automation, ...] = (
    Automation.AUTO,
    Automation.AUTO_AUDIT,
    Automation.REVIEW_REQUIRED,
    Automation.HUMAN_REQUIRED,
)


def _index(level: Automation) -> int:
    return AUTOMATION_ORDER.index(level)


def raise_to(level: Automation, floor: Automation) -> Automation:
    """Eleva `level` até, no mínimo, `floor`. Nunca reduz."""
    return AUTOMATION_ORDER[max(_index(level), _index(floor))]


def downgrade(level: Automation, steps: int = 1) -> Automation:
    """Rebaixa um nível de automação (fail-closed)."""
    return AUTOMATION_ORDER[min(_index(level) + steps, len(AUTOMATION_ORDER) - 1)]


class Action(str, Enum):
    CONTINUE = "CONTINUE"
    IMPLEMENT = "IMPLEMENT"
    IMPLEMENT_WITH_REVIEW = "IMPLEMENT_WITH_REVIEW"
    RETRY = "RETRY"
    SKIP = "SKIP"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"


class EventType(str, Enum):
    START = "START"
    AGENT_RETURNED = "AGENT_RETURNED"
    HARD_EVAL_DONE = "HARD_EVAL_DONE"
    SEMANTIC_NOT_NEEDED = "SEMANTIC_NOT_NEEDED"
    SEMANTIC_READY = "SEMANTIC_READY"
    VERIFICATION_COMPLETE = "VERIFICATION_COMPLETE"  # join das regiões paralelas
    DECIDED = "DECIDED"
    APPLIED = "APPLIED"
    RETRY = "RETRY"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    SKIP = "SKIP"
    FAIL = "FAIL"


# ══════════════════════════════════════════════════════════════════════════
# 2. PRIMITIVAS JEV
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class JevChoice:
    choice: str
    probabilities: Mapping[str, float]
    confidence: float


@dataclass(frozen=True)
class JevScore:
    """`score` é o ÍNDICE do nível (0..len(levels)-1), não uma nota livre."""
    score: int
    levels: tuple[str, ...]
    probabilities: Mapping[str, float]
    confidence: float

    @property
    def level_label(self) -> str:
        return self.levels[self.score]


@dataclass(frozen=True)
class JevNoul:
    """Probabilidade de a afirmação ser verdadeira.

    `p_true` é o valor primário. `decision_strength` = |2p-1| é uma
    estatística derivada por NÓS e NÃO é probabilidade de estar correto.
    O modelo não devolve `confidence` para Noul.
    """
    p_true: float

    @property
    def decision_strength(self) -> float:
        return abs(2.0 * self.p_true - 1.0)

    def decided(self, hi: float = 0.80, lo: float = 0.20) -> bool | None:
        if self.p_true >= hi:
            return True
        if self.p_true <= lo:
            return False
        return None


@dataclass(frozen=True)
class JevResult:
    model: str                      # ex. "jev-1.13.0" — PINADO, nunca "latest"
    request_id: str | None
    answers: Mapping[str, JevChoice | JevScore | JevNoul]
    usage: Mapping[str, int] = field(default_factory=dict)

    def confidence_of(self, key: str) -> float:
        """Eixo comparável entre primitivas (para thresholds).

        Choice/Score -> `confidence` do modelo. Noul -> `decision_strength`.
        ATENÇÃO: isto serve SOMENTE para comparar com thresholds. A direção
        da resposta Noul é avaliada por `direction_of()`.
        """
        a = self.answers[key]
        if isinstance(a, JevNoul):
            return a.decision_strength
        return a.confidence

    def direction_of(self, key: str, hi: float = 0.80,
                     lo: float = 0.20) -> bool | None:
        """Direção de um Noul. Levanta TypeError se a chave não for Noul."""
        a = self.answers[key]
        if not isinstance(a, JevNoul):
            raise TypeError(f"{key} não é Noul: {type(a).__name__}")
        return a.decided(hi, lo)


# ══════════════════════════════════════════════════════════════════════════
# 3. HARD EVAL
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    blocking: bool = True


@dataclass(frozen=True)
class HardEvalResult:
    checks: tuple[Check, ...] = ()

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.blocking)

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.checks if c.blocking and not c.passed)


# ══════════════════════════════════════════════════════════════════════════
# 4. HASH CANÔNICO
# ══════════════════════════════════════════════════════════════════════════

def canonical_hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ══════════════════════════════════════════════════════════════════════════
# 5. QUESTION SETS
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class QuestionSpec:
    kind: str                       # choice | score | noul
    instructions: str
    criteria: Any = None            # choice: {opt: desc} | score: [níveis] | noul: None
    raises_risk_when_true: bool = False   # só para Noul

    @property
    def options(self) -> tuple[str, ...]:
        if self.kind != "choice" or self.criteria is None:
            raise TypeError(f"{self.kind} não tem options")
        return tuple(self.criteria)

    @property
    def levels(self) -> tuple[str, ...]:
        if self.kind != "score" or self.criteria is None:
            raise TypeError(f"{self.kind} não tem levels")
        return tuple(self.criteria)


@dataclass(frozen=True)
class QuestionSet:
    id: str
    version: str
    model: str                      # PINADO
    applies_to: tuple[str, ...]
    risk_class: RiskClass
    questions: Mapping[str, QuestionSpec]
    hash: str

    @property
    def expected_answers(self) -> tuple[str, ...]:
        return tuple(self.questions)

    @property
    def risk_noul_keys(self) -> tuple[str, ...]:
        return tuple(k for k, q in self.questions.items()
                     if q.kind == "noul" and q.raises_risk_when_true)

    @classmethod
    def from_mapping(cls, d: Mapping[str, Any]) -> "QuestionSet":
        qs: dict[str, QuestionSpec] = {}
        for name, spec in (d.get("questions") or {}).items():
            qs[name] = QuestionSpec(
                kind=spec["type"],
                instructions=str(spec.get("instructions", "")).strip(),
                criteria=spec.get("criteria"),
                raises_risk_when_true=bool(
                    spec.get("raises_risk_when_true", False)),
            )
        body = {
            "id": d["id"], "version": d["version"], "model": d["model"],
            "questions": {k: {"type": q.kind, "criteria": q.criteria,
                              "raises_risk_when_true": q.raises_risk_when_true}
                          for k, q in qs.items()},
        }
        return cls(id=d["id"], version=d["version"], model=d["model"],
                   applies_to=tuple(d.get("applies_to", ())),
                   risk_class=RiskClass(d.get("risk_class", "R1")),
                   questions=qs, hash=canonical_hash(body))


def load_question_sets(path: Path | str | None = None) -> dict[str, QuestionSet]:
    p = Path(path or DEFAULT_QUESTION_SETS_PATH)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {d["id"]: QuestionSet.from_mapping(d) for d in raw}


# ══════════════════════════════════════════════════════════════════════════
# 6. DECISION POLICY — carregada do YAML, com hash real
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PolicySpec:
    id: str
    version: str
    risk: Mapping[str, Mapping[str, Any]]
    noul: Mapping[str, float]
    fallback: Mapping[str, str]
    routing: Mapping[str, bool]
    limits: Mapping[str, int]
    thresholds_hash: str

    @property
    def noul_hi(self) -> float:
        return float(self.noul.get("true_at", 0.80))

    @property
    def noul_lo(self) -> float:
        return float(self.noul.get("false_at", 0.20))

    @property
    def max_retries(self) -> int:
        return int(self.limits.get("max_retries", 3))


def load_policy(path: Path | str | None = None) -> PolicySpec:
    p = Path(path or DEFAULT_POLICY_PATH)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    core = {
        "risk": raw.get("risk", {}),
        "noul": raw.get("noul", {}),
        "fallback": raw.get("fallback", {}),
        "routing": raw.get("routing", {}),
        "limits": raw.get("limits", {}),
    }
    return PolicySpec(
        id=str(raw.get("id", "llc-default")),
        version=str(raw.get("version", "1.0.0")),
        risk=core["risk"], noul=core["noul"], fallback=core["fallback"],
        routing=core["routing"], limits=core["limits"],
        thresholds_hash=canonical_hash(core),
    )


def automation_for(policy: PolicySpec, risk: RiskClass,
                   confidence: float) -> Automation:
    """Determinação pura do nível de automação a partir do YAML. Fail-closed."""
    cfg = policy.risk[risk.value]
    for key, level in (("auto_min", Automation.AUTO),
                       ("audit_min", Automation.AUTO_AUDIT),
                       ("review_min", Automation.REVIEW_REQUIRED)):
        bound = cfg.get(key)
        if bound is not None and confidence >= float(bound):
            return level
    return Automation.HUMAN_REQUIRED


# ══════════════════════════════════════════════════════════════════════════
# 7. DECISION STATE
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DecisionState:
    node_id: str
    state_id: str
    decision_kind: str
    question_set_id: str | None
    question_set_version: str | None
    question_set_hash: str | None
    inputs: Mapping[str, Any]
    risk_class: RiskClass
    retry_count: int = 0
    derived: Mapping[str, Any] = field(default_factory=dict)
    expected_answers: tuple[str, ...] = ()
    risk_noul_keys: tuple[str, ...] = ()

    @property
    def input_hash(self) -> str:
        return canonical_hash(self.inputs)

    @classmethod
    def from_question_set(cls, qs: QuestionSet | None, **kw) -> "DecisionState":
        if qs is None:
            return cls(**kw)
        return cls(question_set_id=qs.id, question_set_version=qs.version,
                   question_set_hash=qs.hash,
                   expected_answers=qs.expected_answers,
                   risk_noul_keys=qs.risk_noul_keys, **kw)


# ══════════════════════════════════════════════════════════════════════════
# 8. DECISION
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Classification:
    """O que provavelmente é. Preservada SEMPRE, qualquer que seja a confiança."""
    label: str
    probabilities: Mapping[str, float]
    confidence: float


@dataclass(frozen=True)
class Decision:
    action: Action
    automation: Automation
    reason: str
    policy_id: str
    policy_version: str
    thresholds_hash: str
    classification: Classification | None = None
    confidence: float | None = None
    evidence_refs: tuple[str, ...] = ()

    @property
    def requires_human(self) -> bool:
        return self.automation in (Automation.REVIEW_REQUIRED,
                                   Automation.HUMAN_REQUIRED)


def _risk_floor(state: DecisionState, semantic: JevResult,
                policy: PolicySpec) -> Automation | None:
    """Noul de risco afirmativo eleva o piso de automação (F3).

    Um Noul `needs_human_review` com p_true=0.97 é uma RESPOSTA de risco,
    não um sinal de confiança. Sem isto, `|2p-1| = 0.94` empurraria a
    decisão para AUTO — invertendo o significado da pergunta.
    """
    floor: Automation | None = None
    for key in state.risk_noul_keys:
        ans = semantic.answers.get(key)
        if not isinstance(ans, JevNoul):
            continue
        direction = ans.decided(policy.noul_hi, policy.noul_lo)
        if direction is True:
            want = (Automation.HUMAN_REQUIRED if state.risk_class is RiskClass.R3
                    else Automation.REVIEW_REQUIRED)
            floor = want if floor is None else raise_to(floor, want)
        elif direction is None:
            floor = (Automation.AUTO_AUDIT if floor is None
                     else raise_to(floor, Automation.AUTO_AUDIT))
    return floor


def _classification_from(semantic: JevResult) -> Classification | None:
    for ans in semantic.answers.values():
        if isinstance(ans, JevChoice):
            return Classification(ans.choice, ans.probabilities, ans.confidence)
    return None


def decide(state: DecisionState, hard: HardEvalResult,
           semantic: JevResult | None,
           policy: PolicySpec | None = None,
           *, semantic_expected: bool | None = None) -> Decision:
    """DECISION POLICY — pura, sem rede, sem IO. Fail-closed.

    Ordem de autoridade:
      1. Hard EVAL falhou              -> BLOCK / HUMAN_REQUIRED (Jev não override)
      2. Semântica esperada e ausente  -> ESCALATE / HUMAN_REQUIRED
      3. Noul de risco afirmativo      -> piso REVIEW_REQUIRED (HUMAN em R3)
      4. Resposta parcial              -> rebaixa um nível
      5. Risco x confiança             -> tabela do YAML
    """
    policy = policy or load_policy()
    ev: list[str] = [c.name for c in hard.checks]

    # (1) INV-004 — falha de Hard EVAL nunca é overridden por Jev
    if not hard.passed:
        return Decision(Action.BLOCK, Automation.HUMAN_REQUIRED,
                        "hard_eval_failed", policy.id, policy.version,
                        policy.thresholds_hash, confidence=None,
                        evidence_refs=tuple(ev))

    expected = tuple(state.expected_answers)
    if semantic_expected is None:
        semantic_expected = bool(expected)

    # (2) F2 — semântica esperada e ausente é HUMAN_REQUIRED, nunca AUTO
    if semantic_expected and semantic is None:
        return Decision(Action.ESCALATE, Automation.HUMAN_REQUIRED,
                        "semantic_unavailable", policy.id, policy.version,
                        policy.thresholds_hash, confidence=None,
                        evidence_refs=tuple(ev))

    # Sem semântica prevista e Hard EVAL passou: decisão estrutural explícita
    if semantic is None:
        return Decision(Action.CONTINUE, Automation.AUTO,
                        "resolved_deterministically", policy.id, policy.version,
                        policy.thresholds_hash, confidence=None,
                        evidence_refs=tuple(ev))

    ev += [f"jev:{k}" for k in semantic.answers]
    missing = tuple(k for k in expected if k not in semantic.answers)

    min_conf = min((semantic.confidence_of(k) for k in semantic.answers),
                   default=0.0)
    level = automation_for(policy, state.risk_class, min_conf)

    # (3) F3 — direção do Noul de risco
    floor = _risk_floor(state, semantic, policy)
    reason_floor = False
    if floor is not None and _index(level) < _index(floor):
        level = raise_to(level, floor)
        reason_floor = True

    # INV-005 — R3 nunca AUTO (a tabela já garante; reforço explícito)
    if state.risk_class is RiskClass.R3 and level is Automation.AUTO:
        level = Automation.REVIEW_REQUIRED

    # (4) resposta parcial rebaixa um nível
    if missing:
        level = downgrade(level)

    if missing:
        reason = "semantic_partial"
    elif reason_floor:
        reason = "risk_noul_affirmative"
    elif level is Automation.AUTO:
        reason = "semantic_confident"
    else:
        reason = "semantic_uncertain"

    action = {
        Automation.AUTO: Action.CONTINUE,
        Automation.AUTO_AUDIT: Action.CONTINUE,
        Automation.REVIEW_REQUIRED: Action.IMPLEMENT_WITH_REVIEW,
        Automation.HUMAN_REQUIRED: Action.ESCALATE,
    }[level]

    return Decision(action, level, reason, policy.id, policy.version,
                    policy.thresholds_hash,
                    classification=_classification_from(semantic),
                    confidence=min_conf, evidence_refs=tuple(ev))


# ══════════════════════════════════════════════════════════════════════════
# 9. DECISION RECORD (append-only)
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    timestamp: str
    node_id: str
    state_id: str
    event: str
    input_hash: str
    state_hash: str
    policy: Mapping[str, Any]
    decision: Decision
    decision_kind: str = ""
    risk_class: str = "R0"
    question_set: Mapping[str, Any] | None = None
    jev: Mapping[str, Any] | None = None
    hard_eval: Mapping[str, Any] | None = None
    statechart: Mapping[str, Any] | None = None
    action: Mapping[str, Any] | None = None
    human: Mapping[str, Any] | None = None
    artifact_hashes: tuple[str, ...] = ()

    def is_replayable(self) -> bool:
        return bool(self.policy.get("version")
                    and self.policy.get("thresholds_hash")
                    and (self.statechart or {}).get("to"))


# ══════════════════════════════════════════════════════════════════════════
# 10. EVENT
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Event:
    event_id: str
    type: EventType
    node_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════
# 11. INTERFACES (Protocol) — fronteiras de autoridade
# ══════════════════════════════════════════════════════════════════════════

@runtime_checkable
class DagView(Protocol):
    """llc_graph como ADVISOR. Read-only. Nunca executa transição."""

    def deps_satisfied(self, node_id: str) -> bool: ...
    def requires_human(self, node_id: str) -> bool: ...
    def risk_class(self, node_id: str) -> RiskClass: ...
    def impact_of(self, node_id: str) -> frozenset[str]: ...
    def frontier(self) -> tuple[str, ...]: ...


@runtime_checkable
class SemanticEvaluator(Protocol):
    """Jev. Avalia. Nunca executa, nunca escreve estado."""

    def evaluate(self, state: DecisionState) -> JevResult: ...


@runtime_checkable
class HardEvaluator(Protocol):
    def run(self, node_id: str) -> HardEvalResult: ...


@runtime_checkable
class Policy(Protocol):
    def decide(self, state: DecisionState, hard: HardEvalResult,
               semantic: JevResult | None) -> Decision: ...


@runtime_checkable
class EventBus(Protocol):
    def publish(self, event: Event) -> None: ...
    def subscribe(self, handler: Callable[[Event], None]) -> None: ...
    def history(self, node_id: str) -> tuple[Event, ...]: ...


class ToolBroker(Protocol):
    """Ponto ÚNICO de mediação de efeito (INV-008).

    Se um tool call não passa por aqui, a matriz de capacidade não existe.
    """

    def authorize(self, state_id: str, tool: str) -> bool: ...


# ══════════════════════════════════════════════════════════════════════════
# 12. CAPABILITY MATRIX — declarativa, com resolução por prefixo
# ══════════════════════════════════════════════════════════════════════════

CAPABILITY_MATRIX: dict[str, frozenset[str]] = {
    "idle": frozenset({"read_index", "read_artifacts"}),
    "active.preparing": frozenset({"read_index", "read_artifacts",
                                   "build_decision_state", "jev_eval"}),
    "active.agent_running": frozenset({"read_index", "read_artifacts",
                                       "write_artifacts", "run_tests"}),
    "active.verifying": frozenset({"read_index", "read_artifacts",
                                   "run_hard_eval", "jev_eval"}),
    "active.verifying.hard": frozenset({"read_index", "run_hard_eval"}),
    "active.verifying.semantic": frozenset({"read_index", "jev_eval"}),
    "active.deciding": frozenset({"read_index", "apply_policy"}),
    "active.applying": frozenset({"read_index", "apply_changes",
                                  "git_commit", "rollback"}),
    "governance.auto_approved": frozenset({"read_index", "apply_changes"}),
    "governance.awaiting_human": frozenset({"read_index", "show_evidence",
                                            "request_approval"}),
    "governance.rework": frozenset({"read_index", "build_decision_state"}),
    "done": frozenset({"read_index", "read_artifacts"}),
    "failed": frozenset({"read_index", "read_artifacts"}),
    "skipped": frozenset({"read_index", "read_artifacts"}),
}

FORBIDDEN_EVERYWHERE = frozenset({"deploy", "force_push", "delete_session"})


def capabilities_for_state(state_id: str) -> frozenset[str]:
    """Resolve por prefixo mais longo: `active.verifying.hard.passed`
    herda de `active.verifying.hard`. Estado desconhecido => KeyError."""
    key = state_id
    while True:
        if key in CAPABILITY_MATRIX:
            return CAPABILITY_MATRIX[key] - FORBIDDEN_EVERYWHERE
        if "." not in key:
            break
        key = key.rsplit(".", 1)[0]
    raise KeyError(f"estado sem matriz de capacidade: {state_id}")


class DefaultToolBroker:
    """Broker mínimo sobre a matriz declarativa."""

    def authorize(self, state_id: str, tool: str) -> bool:
        return tool in capabilities_for_state(state_id)


# ══════════════════════════════════════════════════════════════════════════
# 13. GUARDS — puras, assinatura uniforme (F6)
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardContext:
    node_id: str = ""
    dag: Any = None                      # DagView (consulta read-only)
    hard: HardEvalResult | None = None
    decision: Decision | None = None
    retries: int = 0
    max_retries: int = 3
    has_question_set: bool = False
    regions: Mapping[str, str] = field(default_factory=dict)


def guard_deps_satisfied(ctx: GuardContext) -> bool:
    return bool(ctx.dag is not None and ctx.dag.deps_satisfied(ctx.node_id))


def guard_hard_eval_passed(ctx: GuardContext) -> bool:
    return bool(ctx.hard is not None and ctx.hard.passed)


def guard_hard_eval_failed(ctx: GuardContext) -> bool:
    return bool(ctx.hard is not None and not ctx.hard.passed)


def guard_semantic_not_needed(ctx: GuardContext) -> bool:
    return bool(ctx.hard is not None and ctx.hard.passed
                and not ctx.has_question_set)


def guard_verification_complete(ctx: GuardContext) -> bool:
    """Join das regiões ortogonais: hard terminou E semântica terminou."""
    return (ctx.regions.get("hard") == "passed"
            and ctx.regions.get("semantic") in ("ready", "not_needed"))


def guard_is_auto(ctx: GuardContext) -> bool:
    return bool(ctx.decision is not None
                and ctx.decision.automation in (Automation.AUTO,
                                                Automation.AUTO_AUDIT))


def guard_is_review(ctx: GuardContext) -> bool:
    return bool(ctx.decision is not None
                and ctx.decision.automation is Automation.REVIEW_REQUIRED)


def guard_is_human(ctx: GuardContext) -> bool:
    return bool(ctx.decision is not None
                and ctx.decision.automation is Automation.HUMAN_REQUIRED)


def guard_retries_left(ctx: GuardContext) -> bool:
    return ctx.retries < ctx.max_retries


def guard_gate_has_evidence(ctx: GuardContext) -> bool:
    """INV-009 — auto-aprovação sem evidência é rejeitada."""
    return bool(ctx.decision is not None and ctx.decision.evidence_refs)


GUARD_REGISTRY: dict[str, Callable[[GuardContext], bool]] = {
    "deps_satisfied": guard_deps_satisfied,
    "hard_eval_passed": guard_hard_eval_passed,
    "hard_eval_failed": guard_hard_eval_failed,
    "semantic_not_needed": guard_semantic_not_needed,
    "verification_complete": guard_verification_complete,
    "is_auto": guard_is_auto,
    "is_review": guard_is_review,
    "is_human": guard_is_human,
    "retries_left": guard_retries_left,
    "gate_has_evidence": guard_gate_has_evidence,
}


# ══════════════════════════════════════════════════════════════════════════
# 14. TABELA DE TRANSIÇÕES — STATE + EVENT + GUARD = NEXT
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Transition:
    state: str
    event: EventType
    guard: str | None
    next: str
    action: str | None = None


TRANSITIONS: tuple[Transition, ...] = (
    Transition("idle", EventType.START, "deps_satisfied", "active.preparing",
               "build_decision_state"),
    Transition("idle", EventType.SKIP, None, "skipped", "write_decision_record"),

    Transition("active.preparing", EventType.AGENT_RETURNED, None,
               "active.agent_running", "invoke_agent"),
    Transition("active.agent_running", EventType.HARD_EVAL_DONE, None,
               "active.verifying", "run_hard_eval"),

    # região ortogonal HARD
    Transition("active.verifying.hard", EventType.HARD_EVAL_DONE,
               "hard_eval_passed", "active.verifying.hard.passed",
               "run_hard_eval"),
    Transition("active.verifying.hard", EventType.HARD_EVAL_DONE, None,
               "active.verifying.hard.failed", None),

    # região ortogonal SEMANTIC
    Transition("active.verifying.semantic", EventType.SEMANTIC_NOT_NEEDED,
               "semantic_not_needed", "active.verifying.semantic.not_needed",
               None),
    Transition("active.verifying.semantic", EventType.SEMANTIC_READY, None,
               "active.verifying.semantic.ready", "call_jev"),

    # join — ordem importa: completo primeiro, falho depois
    Transition("active.verifying", EventType.VERIFICATION_COMPLETE,
               "verification_complete", "active.deciding", None),
    Transition("active.verifying", EventType.VERIFICATION_COMPLETE,
               "hard_eval_failed", "governance.awaiting_human", "open_gate"),

    Transition("active.deciding", EventType.DECIDED, "is_auto",
               "governance.auto_approved", "apply_policy"),
    Transition("active.deciding", EventType.DECIDED, "is_review",
               "governance.awaiting_human", "open_gate"),
    Transition("active.deciding", EventType.DECIDED, "is_human",
               "governance.awaiting_human", "open_gate"),

    Transition("governance.auto_approved", EventType.APPLIED,
               "gate_has_evidence", "active.applying", "apply_changes"),
    Transition("governance.awaiting_human", EventType.HUMAN_APPROVED, None,
               "governance.auto_approved", None),
    # INV-010 — rejeição gera rework, não aborta
    Transition("governance.awaiting_human", EventType.HUMAN_REJECTED,
               "retries_left", "governance.rework", "increment_retries"),
    Transition("governance.awaiting_human", EventType.HUMAN_REJECTED, None,
               "failed", "write_decision_record"),
    Transition("governance.rework", EventType.RETRY, None, "active.preparing",
               "rollback"),

    Transition("active.applying", EventType.APPLIED, "hard_eval_passed",
               "done", "write_decision_record"),
    Transition("active.applying", EventType.FAIL, "retries_left",
               "governance.rework", "rollback"),
    Transition("active.applying", EventType.FAIL, None, "failed", "rollback"),
)


def next_state(state: str, event: EventType, ctx: GuardContext) -> str | None:
    """Resolve em ORDEM DE DECLARAÇÃO. Estado sem transição => None (sem efeito)."""
    for t in TRANSITIONS:
        if t.state != state or t.event != event:
            continue
        if t.guard is None or GUARD_REGISTRY[t.guard](ctx):
            return t.next
    return None


# ══════════════════════════════════════════════════════════════════════════
# 15. REPLAY — sem Jev, sem LLM (F7: verifica input_hash)
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ReplayVerification:
    ok: bool
    input_hash_match: bool
    decision_match: bool
    expected_transition: str | None
    errors: tuple[str, ...] = ()


def _hard_from_record(record: DecisionRecord) -> HardEvalResult:
    return HardEvalResult(tuple(
        Check(name=c.get("name", "?"), passed=bool(c.get("passed")),
              blocking=bool(c.get("blocking", True)))
        for c in (record.hard_eval or {}).get("checks", [])
    ))


def _state_from_record(record: DecisionRecord) -> DecisionState:
    qs = record.question_set or {}
    return DecisionState(
        node_id=record.node_id, state_id=record.state_id,
        decision_kind=record.decision_kind,
        question_set_id=qs.get("id"), question_set_version=qs.get("version"),
        question_set_hash=qs.get("hash"),
        inputs={},  # o replay compara por `input_hash`, não reenvia inputs
        risk_class=RiskClass(record.risk_class),
        expected_answers=tuple(qs.get("expected_answers", ())),
        risk_noul_keys=tuple(qs.get("risk_noul_keys", ())),
    )


def replay_decision(record: DecisionRecord, semantic: JevResult | None,
                    policy: PolicySpec | None = None) -> Decision:
    """Recomputa a decisão a partir do registro. PURA. Não infere."""
    state = _state_from_record(record)
    semantic_expected = bool((record.question_set or {}).get("expected_answers"))
    return decide(state, _hard_from_record(record), semantic,
                  policy or load_policy(), semantic_expected=semantic_expected)


def verify_replay(record: DecisionRecord, semantic: JevResult | None,
                  input_hash: str, policy: PolicySpec | None = None,
                  ctx_builder=None) -> ReplayVerification:
    """Replay completo: hash -> decisão -> transição. Zero inferência."""
    errors: list[str] = []
    if not record.is_replayable():
        errors.append("registro não replayável (falta policy.version/"
                      "thresholds_hash/statechart.to)")

    hash_ok = record.input_hash == input_hash
    if not hash_ok:
        errors.append(f"input_hash divergente: {record.input_hash} != {input_hash}")

    reproduced = replay_decision(record, semantic, policy)
    decision_ok = (reproduced.action == record.decision.action
                   and reproduced.automation == record.decision.automation
                   and reproduced.reason == record.decision.reason)
    if not decision_ok:
        errors.append(f"decisão divergente: {reproduced.automation.value}/"
                      f"{reproduced.reason} != {record.decision.automation.value}"
                      f"/{record.decision.reason}")

    expected = None
    if ctx_builder is not None:
        sc = record.statechart or {}
        expected = next_state(sc.get("from", ""),
                              EventType(sc.get("event", "DECIDED")),
                              ctx_builder(reproduced))
        if expected != sc.get("to"):
            errors.append(f"transição divergente: {expected} != {sc.get('to')}")

    return ReplayVerification(ok=not errors, input_hash_match=hash_ok,
                              decision_match=decision_ok,
                              expected_transition=expected,
                              errors=tuple(errors))


# ══════════════════════════════════════════════════════════════════════════
# 16. DRIFT
# ══════════════════════════════════════════════════════════════════════════

def l1_distance(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


@dataclass(frozen=True)
class DriftReport:
    decision_changed: bool
    automation_changed: bool
    max_l1: float

    @property
    def kind(self) -> str:
        if self.decision_changed:
            return "DECISION_DRIFT"
        if self.automation_changed or self.max_l1 > 0.0:
            return "CONFIDENCE_DRIFT"
        return "STABLE"
