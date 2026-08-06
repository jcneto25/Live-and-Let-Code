"""llc_evals.evaluators.doc_judge — LLM-as-judge com rubric estruturado.

PRP-EVALS-F3 (ADR-0005 §2.7): steps documentais/arquiteturais não são
avaliáveis por testes ou fitness; o DocJudge avalia contra rubrics YAML
versionados, com saída JSON determinística. O LLM é injetado (tool-agnostic,
D9) — nunca chamado diretamente aqui; nos testes é sempre mockado.

Restrição de custo (D10): o judge roda apenas em gates/amostragem
(should_run), nunca a cada geração.
"""
from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

# Steps roteados para DocJudge (ADR-0005 §2.6): documentais + arquiteturais + UX.
_DOC_STEPS = {"0.5", "1", "2", "3", "5", "5a", "5b", "5c", "5d", "7", "7a"}

# Fases em que o judge pode rodar (D10): gate ou amostragem humana.
_GATE_PHASES = {"gate", "sampling"}

_DEFAULT_RUBRICS_DIR = Path(__file__).resolve().parent.parent / "rubrics"

_PROMPT_TEMPLATE = """\
Você é um avaliador técnico rigoroso. Avalie o artefato contra a rubrica.
Para cada dimensão, atribua 0-100 e justifique em 1 frase.
Retorne APENAS JSON: {{"<dimensao>": {{"score": X, "reason": "..."}}, ...}}

[RUBRICA]
{rubric_yaml}

[ARTEFATO A AVALIAR]
{artifact_content}

[ARTEFATOS DE REFERÊNCIA / CONTEXTO UPSTREAM]
{upstream_artifacts}
"""


def load_rubric(step_id: str, rubrics_dir: Path | str | None = None) -> dict:
    """Carrega o rubric YAML do step (RF-EF3.4). KeyError se não existir."""
    base = Path(rubrics_dir) if rubrics_dir else _DEFAULT_RUBRICS_DIR
    path = base / f"rubric-step-{step_id}.yaml"
    if not path.exists():
        raise KeyError(f"Rubric não encontrado para step {step_id}: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def build_prompt(
    rubric: dict,
    artifact_content: str,
    upstream_artifacts: str | None = None,
) -> str:
    """Prompt padrão que instrui o judge a retornar APENAS JSON (ADR-0005 §8.1).

    RF-EF3.5: o artefato e os artefatos upstream (rastreabilidade) entram no prompt.
    """
    rubric_yaml = yaml.safe_dump(rubric, sort_keys=False)
    upstream = upstream_artifacts or "(nenhum)"
    return _PROMPT_TEMPLATE.format(
        rubric_yaml=rubric_yaml,
        artifact_content=artifact_content,
        upstream_artifacts=upstream,
    )


def parse_response(raw: str) -> tuple[dict | None, str | None]:
    """Converte a resposta do judge em dict; erro descritivo se não-JSON.

    RF-EF3.6: saída livre/estranha → (None, erro) — nunca crash. Tolerante a
    code fences markdown (```json) e a blocos JSON embutidos em texto.
    """
    if not raw or not raw.strip():
        return None, "resposta vazia do judge"
    text = raw.strip()
    # remove code fences markdown (```json ... ```), mesmo com prosa ao redor
    text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None, "saída não-JSON do judge"
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None, "saída não-JSON do judge"
    if not isinstance(data, dict):
        return None, "saída do judge não é um objeto JSON"
    return data, None


def aggregate_score(scores: dict, dimensions: list[dict]) -> float | None:
    """QualityScore agregado: média ponderada pelos pesos do rubric (RF-EF3.2).

    Dimensões ausentes no JSON do judge não inflam o denominador. Resultado
    ∈ [0,100]; None se não houver dimensões pontuáveis.
    """
    total_weight = 0.0
    acc = 0.0
    for dim in dimensions:
        name = dim.get("name")
        weight = float(dim.get("weight", 0))
        if weight <= 0 or name not in scores:
            continue
        entry = scores[name]
        score = entry.get("score") if isinstance(entry, dict) else entry
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            continue  # score malformado (ex.: "n/a") — ignorado, sem crash (RF-EF3.6)
        acc += weight * float(score)
        total_weight += weight
    if total_weight <= 0:
        return None
    result = acc / total_weight
    return round(min(100.0, max(0.0, result)), 2)  # clamp ∈ [0,100] (RF-EF3.2)


class DocJudge:
    """LLM-as-judge com rubric estruturado (RF-EF3.1/3.3/3.5)."""

    def __init__(
        self,
        llm_call: Callable[[str], str] | None = None,
        rubrics_dir: Path | str | None = None,
    ):
        self.llm_call = llm_call
        self.rubrics_dir = rubrics_dir

    def evaluate(
        self,
        *,
        step_id: str,
        artifact_content: str,
        upstream_artifacts: str | None = None,
        llm_call: Callable[[str], str] | None = None,
    ) -> dict:
        """Avalia o artefato contra o rubric do step (RF-EF3.1/3.5).

        Retorna {step_id, scores, aggregate, error}. Em erro de parse,
        scores/aggregate são None e o erro é registrado (RF-EF3.6).
        """
        try:
            rubric = load_rubric(step_id, self.rubrics_dir)
        except KeyError as exc:
            return {
                "step_id": step_id, "scores": None, "aggregate": None,
                "error": str(exc),
            }
        caller = llm_call or self.llm_call
        if caller is None:
            return {
                "step_id": step_id, "scores": None, "aggregate": None,
                "error": "llm_call não fornecido (judge é tool-agnostic, D9)",
            }
        prompt = build_prompt(rubric, artifact_content, upstream_artifacts)
        try:
            raw = caller(prompt)
        except Exception as exc:  # noqa: BLE001 — degradação graciosa (RF-EF3.6)
            return {
                "step_id": step_id, "scores": None, "aggregate": None,
                "error": f"falha na chamada do LLM: {exc}",
            }
        scores, error = parse_response(raw)
        if error or scores is None:
            return {
                "step_id": step_id, "scores": None, "aggregate": None,
                "error": error,
            }
        aggregate = aggregate_score(scores, rubric.get("dimensions", []))
        return {
            "step_id": step_id, "scores": scores,
            "aggregate": aggregate, "error": None,
        }

    def routes_to(self, step_id: str) -> bool:
        """True para steps documentais/arquiteturais/UX (ADR-0005 §2.6)."""
        return step_id in _DOC_STEPS

    def should_run(self, phase: str) -> bool:
        """Judge roda apenas em gates/amostragem (RF-EF3.3 / D10)."""
        return phase in _GATE_PHASES


@dataclass(frozen=True)
class JudgmentSample:
    """Amostra de calibração judge↔humano (ADR-0005 §2.7)."""

    step_id: str
    judge_score: float
    human_score: float


class HumanSampling:
    """Estrutura para registrar calibração judge↔humano (PRP-EVALS-F3 §1.2).

    Correlação de Pearson entre judge e humano (meta ADR-0005 §7: ≥ 0.8).
    """

    def __init__(self) -> None:
        self._samples: list[JudgmentSample] = []

    def record(self, *, step_id: str, judge_score: float, human_score: float) -> None:
        self._samples.append(
            JudgmentSample(step_id=step_id, judge_score=judge_score,
                           human_score=human_score)
        )

    def correlation(self) -> float | None:
        """Pearson(judge, human); None com < 2 amostras ou variância zero."""
        if len(self._samples) < 2:
            return None
        judge = [s.judge_score for s in self._samples]
        human = [s.human_score for s in self._samples]
        try:
            return round(statistics.correlation(judge, human), 4)
        except statistics.StatisticsError:
            return None

    def count(self) -> int:
        return len(self._samples)
