"""LLC 2.0 — Adapter da camada semântica (Jev).

Responsabilidades deste módulo:
  - montar UMA chamada fan-out por Decision State (nunca N chamadas);
  - validar o contrato da resposta (schema, opções, faixas);
  - pinar o modelo e recusar "latest";
  - cachear por (question_set.hash, input_hash) — base do replay;
  - falhar FECHADO: indisponível => exceção, nunca "decisão otimista".

O adapter NÃO decide e NÃO transiciona. Ele devolve `JevResult` tipado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from llc2.contracts import (
    DecisionState, JevChoice, JevNoul, JevResult, JevScore, QuestionSet,
    canonical_hash, load_question_sets,
)


class SemanticUnavailable(Exception):
    """Jev indisponível / timeout / schema inválido / modelo divergente.

    Quem chama (`Decision Engine`) converte isso em
    `Automation.HUMAN_REQUIRED` com reason="semantic_unavailable".
    """


@dataclass(frozen=True)
class JevRequest:
    model: str
    question_set_id: str
    question_set_version: str
    question_set_hash: str
    inputs: Mapping[str, Any]
    questions: Mapping[str, Any]
    timeout_s: int = 30
    idempotency_key: str = ""


@dataclass(frozen=True)
class JevRawResponse:
    model: str
    request_id: str | None
    answers: Mapping[str, Mapping[str, Any]]
    usage: Mapping[str, int] = field(default_factory=dict)


class JevTransport(Protocol):
    """Fronteira de rede. Único ponto que toca a API do Jev."""

    def call(self, request: JevRequest) -> JevRawResponse: ...


class DecisionCache(Protocol):
    def get(self, key: tuple[str, str]) -> JevResult | None: ...
    def put(self, key: tuple[str, str], value: JevResult) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], JevResult] = {}

    def get(self, key: tuple[str, str]) -> JevResult | None:
        return self._data.get(key)

    def put(self, key: tuple[str, str], value: JevResult) -> None:
        self._data[key] = value

    def __len__(self) -> int:
        return len(self._data)


# ── validação ──────────────────────────────────────────────────────────────

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SemanticUnavailable(msg)


def _build_answer(name: str, spec: Any, raw: Mapping[str, Any]) -> Any:
    kind = spec.kind
    if kind == "choice":
        choice = raw.get("choice")
        _require(isinstance(choice, str), f"{name}: 'choice' ausente")
        _require(choice in spec.options,
                 f"{name}: opção '{choice}' fora de {spec.options}")
        probs = raw.get("probabilities", {})
        conf = raw.get("confidence")
        _require(isinstance(conf, (int, float)), f"{name}: confidence ausente")
        return JevChoice(choice, dict(probs), float(conf))

    if kind == "score":
        score = raw.get("score")
        _require(isinstance(score, int) and not isinstance(score, bool),
                 f"{name}: 'score' deve ser int (índice do nível)")
        _require(0 <= score < len(spec.levels),
                 f"{name}: score {score} fora de 0..{len(spec.levels) - 1}")
        probs = raw.get("probabilities", {})
        conf = raw.get("confidence")
        _require(isinstance(conf, (int, float)), f"{name}: confidence ausente")
        return JevScore(score, spec.levels, dict(probs), float(conf))

    if kind == "noul":
        p = raw.get("noul", raw.get("p_true"))
        _require(isinstance(p, (int, float)), f"{name}: 'noul' ausente")
        _require(0.0 <= float(p) <= 1.0, f"{name}: noul {p} fora de 0..1")
        return JevNoul(float(p))

    raise SemanticUnavailable(f"{name}: tipo desconhecido '{kind}'")


# ── adapter ────────────────────────────────────────────────────────────────

class JevAdapter:
    """Avalia um Decision State. Uma chamada fan-out. Falha fechada."""

    def __init__(self, transport: JevTransport,
                 question_sets: Mapping[str, QuestionSet] | None = None,
                 cache: DecisionCache | None = None,
                 timeout_s: int = 30, max_retries: int = 2) -> None:
        self.transport = transport
        self.question_sets = question_sets if question_sets is not None \
            else load_question_sets()
        self.cache = cache
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.calls = 0        # contador observável (métrica: Jev calls/sessão)

    # -- chaves ------------------------------------------------------------
    @staticmethod
    def _qkey(state: DecisionState) -> str:
        _require(state.question_set_id is not None,
                 "DecisionState sem question_set_id")
        return str(state.question_set_id)

    def _resolve(self, state: DecisionState) -> QuestionSet:
        qs = self.question_sets.get(self._qkey(state))
        _require(qs is not None, f"question set desconhecido: {state.question_set_id}")
        _require(not qs.model.endswith("latest") and not qs.model.endswith("-latest"),
                 f"modelo não pinado em '{qs.id}': {qs.model}")
        _require(state.question_set_hash in (None, qs.hash),
                 f"hash do question set divergente para '{qs.id}'")
        return qs

    # -- avaliação ---------------------------------------------------------
    def evaluate(self, state: DecisionState) -> JevResult:
        qs = self._resolve(state)
        key = (qs.hash, state.input_hash)

        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                return hit

        request = JevRequest(
            model=qs.model, question_set_id=qs.id,
            question_set_version=qs.version, question_set_hash=qs.hash,
            inputs=dict(state.inputs),
            questions={n: {"type": s.kind, "criteria": s.criteria,
                           "instructions": s.instructions}
                       for n, s in qs.questions.items()},
            timeout_s=self.timeout_s,
            idempotency_key=canonical_hash({"qs": qs.hash, "in": state.input_hash}),
        )

        raw: JevRawResponse | None = None
        last_err: Exception | None = None
        for _ in range(self.max_retries + 1):
            self.calls += 1
            try:
                raw = self.transport.call(request)
                break
            except Exception as exc:            # timeout, rede, 5xx
                last_err = exc
                raw = None
        _require(raw is not None,
                 f"Jev indisponível após {self.max_retries + 1} tentativas: {last_err}")
        assert raw is not None

        _require(raw.model == qs.model,
                 f"modelo divergente do pin: {raw.model} != {qs.model}")

        answers: dict[str, Any] = {}
        for name, spec in qs.questions.items():
            got = raw.answers.get(name)
            # ausência de UMA pergunta = parcial; a Policy rebaixa um nível.
            # ausência de TODAS = indisponível.
            if got is None:
                continue
            answers[name] = _build_answer(name, spec, got)
        _require(bool(answers), "Jev retornou zero respostas válidas")

        result = JevResult(model=raw.model, request_id=raw.request_id,
                           answers=answers, usage=dict(raw.usage))
        if self.cache is not None:
            self.cache.put(key, result)
        return result


# ── transport fake (testes) ────────────────────────────────────────────────

class FakeJevTransport:
    """Transport determinístico para testes. Não é mock de rede: é scriptado."""

    def __init__(self, answers: Mapping[str, Mapping[str, Any]],
                 model: str = "jev-1.13.0", usage: Mapping[str, int] | None = None,
                 fail_times: int = 0, drop: tuple[str, ...] = ()) -> None:
        self._answers = dict(answers)
        self.model = model
        self.usage = dict(usage or {"input_tokens": 1200, "output_tokens": 40})
        self.fail_times = fail_times
        self.drop = drop
        self.seen: list[JevRequest] = []

    def call(self, request: JevRequest) -> JevRawResponse:
        self.seen.append(request)
        if self.fail_times > 0:
            self.fail_times -= 1
            raise TimeoutError("jev timeout")
        payload = {k: v for k, v in self._answers.items() if k not in self.drop}
        return JevRawResponse(model=self.model, request_id="req-fake",
                              answers=payload, usage=self.usage)


def record_payload(result: JevResult) -> dict[str, Any]:
    """Projeção do JevResult para o Decision Record.

    Guarda `probabilities` SEMPRE — qualquer medida de confiança pode ser
    recomputada a partir delas, inclusive em drift analysis.
    """
    answers: dict[str, Any] = {}
    for name, a in result.answers.items():
        if isinstance(a, JevChoice):
            answers[name] = {"type": "choice", "choice": a.choice,
                             "probabilities": dict(a.probabilities),
                             "confidence": a.confidence}
        elif isinstance(a, JevScore):
            answers[name] = {"type": "score", "score": a.score,
                             "levels": list(a.levels),
                             "probabilities": dict(a.probabilities),
                             "confidence": a.confidence}
        else:
            answers[name] = {"type": "noul", "p_true": a.p_true,
                             "decision_strength": a.decision_strength}
    return {"model": result.model, "request_id": result.request_id,
            "answers": answers, "usage": dict(result.usage)}
