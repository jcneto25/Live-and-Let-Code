"""Testes para llc_evals.evaluators.doc_judge — RF-EF3.1 a EF3.6 (PRP-EVALS-F3).

DocJudge: LLM-as-judge com rubric estruturado (ADR-0005 §2.7). LLM sempre
mockado nos testes — o judge é tool-agnostic (D9), recebe o callable injetado.
"""
import json

import pytest

from llc_evals.evaluators import doc_judge
from llc_evals.evaluators.doc_judge import (
    DocJudge,
    HumanSampling,
    aggregate_score,
    build_prompt,
    load_rubric,
    parse_response,
)

# Resposta JSON válida no formato {dimensao: {score, reason}} (RF-EF3.1)
VALID_JSON = json.dumps({
    "completude": {"score": 80, "reason": "Seções do template preenchidas"},
    "rastreabilidade": {"score": 90, "reason": "Requisitos traçam à Visão"},
    "testabilidade": {"score": 70, "reason": "Verificável"},
    "clareza": {"score": 85, "reason": "Sem ambiguidade"},
    "alinhamento_negocio": {"score": 75, "reason": "Alinhado à Visão"},
})


# ── RF-EF3.1: evaluate() retorna score por dimensão ──────────────────────────

def test_evaluate_returns_per_dimension_scores():
    """RF-EF3.1: judge (mockado) → JSON {dimensao: {score, reason}}."""
    judge = DocJudge(llm_call=lambda prompt: VALID_JSON)
    result = judge.evaluate(step_id="2", artifact_content="# PRD de exemplo")
    assert result["error"] is None
    scores = result["scores"]
    assert scores["completude"] == {"score": 80, "reason": "Seções do template preenchidas"}
    assert scores["rastreabilidade"]["score"] == 90
    assert all("score" in v and "reason" in v for v in scores.values())


# ── RF-EF3.2: aggregate_score ponderado ∈ [0,100] ────────────────────────────

def test_aggregate_score_weighted_average():
    """RF-EF3.2: média ponderada pelos pesos do rubric ∈ [0,100]."""
    rubric = load_rubric("2")
    scores = {
        "completude": {"score": 80},
        "rastreabilidade": {"score": 90},
        "testabilidade": {"score": 70},
        "clareza": {"score": 85},
        "alinhamento_negocio": {"score": 75},
    }
    total = aggregate_score(scores, rubric["dimensions"])
    # 0.25*80 + 0.25*90 + 0.20*70 + 0.15*85 + 0.15*75 = 80.5
    assert total == pytest.approx(80.5, abs=0.01)
    assert 0.0 <= total <= 100.0


def test_aggregate_score_missing_dimension_skipped():
    """Dimensão ausente no JSON do judge não quebra nem infla o agregado."""
    rubric = load_rubric("2")
    scores = {"completude": {"score": 50}}  # só 1 das 5 dimensões
    total = aggregate_score(scores, rubric["dimensions"])
    # só a dimensão presente entra no denominador
    assert total == pytest.approx(50.0, abs=0.01)


def test_aggregate_score_malformed_score_skipped_no_crash():
    """RF-EF3.6: score malformado (não-numérico) é ignorado, sem crash."""
    rubric = load_rubric("2")
    scores = {
        "completude": {"score": "n/a"},       # string inválida
        "rastreabilidade": {"score": [80]},    # lista
        "testabilidade": {"score": 70},
    }
    total = aggregate_score(scores, rubric["dimensions"])
    assert total == pytest.approx(70.0, abs=0.01)  # só a válida entra


def test_aggregate_score_clamped_to_100():
    """RF-EF3.2: score fora de faixa é clampado ∈ [0,100]."""
    rubric = load_rubric("2")
    scores = {
        "completude": {"score": 150},          # acima de 100
        "rastreabilidade": {"score": 90},
        "testabilidade": {"score": 70},
        "clareza": {"score": 85},
        "alinhamento_negocio": {"score": 75},
    }
    total = aggregate_score(scores, rubric["dimensions"])
    assert total <= 100.0


def test_evaluate_llm_exception_graceful():
    """RF-EF3.6: exceção do LLM (rede/timeout) → erro registrado, sem crash."""
    def broken_llm(prompt: str) -> str:
        raise TimeoutError("timeout")

    judge = DocJudge(llm_call=broken_llm)
    result = judge.evaluate(step_id="2", artifact_content="# PRD")
    assert result["error"] is not None
    assert "timeout" in result["error"]
    assert result["scores"] is None
    assert result["aggregate"] is None


# ── RF-EF3.3: judge roda apenas em gates/amostragem ──────────────────────────

def test_judge_not_called_mid_execution():
    """RF-EF3.3: mid-execution → should_run False (judge não é chamado)."""
    judge = DocJudge()
    assert not judge.should_run("execution")
    assert not judge.should_run("generation")
    assert judge.should_run("gate")
    assert judge.should_run("sampling")


# ── RF-EF3.4: rubrics YAML existem para 0.5, 1, 2, 3, 5 ──────────────────────

def test_load_rubric_exists_for_all_steps():
    """RF-EF3.4: load_rubric() sem KeyError para steps documentais/arquiteturais."""
    for step_id in ("0.5", "1", "2", "3", "5"):
        rubric = load_rubric(step_id)
        assert rubric["step"] == step_id
        assert rubric["dimensions"]
        weights = [d["weight"] for d in rubric["dimensions"]]
        assert sum(weights) == 100  # pesos normalizados


def test_load_rubric_missing_step_raises():
    with pytest.raises(KeyError):
        load_rubric("999")


# ── RF-EF3.5: judge recebe artefato upstream (rastreabilidade) ───────────────

def test_evaluate_includes_upstream_artifact():
    """RF-EF3.5: artefato + upstream entram no prompt (rastreabilidade)."""
    captured: dict = {}

    def fake_llm(prompt: str) -> str:
        captured["prompt"] = prompt
        return VALID_JSON

    judge = DocJudge(llm_call=fake_llm)
    judge.evaluate(
        step_id="2",
        artifact_content="# PRD do módulo X",
        upstream_artifacts="# Visão Estratégica (Step 0.5)",
    )
    assert "[ARTEFATO A AVALIAR]" in captured["prompt"]
    assert "# PRD do módulo X" in captured["prompt"]
    assert "# Visão Estratégica (Step 0.5)" in captured["prompt"]


# ── RF-EF3.6: saída não-JSON tratada graciosamente ───────────────────────────

def test_non_json_output_handled_gracefully():
    """RF-EF3.6: LLM devolve texto livre → erro registrado, score=None, sem crash."""
    judge = DocJudge(llm_call=lambda prompt: "Este artefato está ótimo! Parabéns.")
    result = judge.evaluate(step_id="2", artifact_content="# PRD")
    assert result["error"] is not None
    assert result["scores"] is None
    assert result["aggregate"] is None


def test_parse_response_free_text_returns_error():
    scores, error = parse_response("texto livre sem JSON nenhum")
    assert scores is None
    assert error is not None


def test_parse_response_strips_markdown_fences():
    raw = '```json\n{"a": {"score": 1, "reason": "ok"}}\n```'
    scores, error = parse_response(raw)
    assert error is None
    assert scores == {"a": {"score": 1, "reason": "ok"}}


def test_parse_response_empty_returns_error():
    scores, error = parse_response("")
    assert scores is None
    assert error is not None


# ── Roteamento (ADR-0005 §2.6): steps documentais/arquiteturais ──────────────

def test_routes_to_documental_and_architectural_steps():
    judge = DocJudge()
    assert judge.routes_to("0.5")
    assert judge.routes_to("2")
    assert judge.routes_to("5")
    assert judge.routes_to("5a")
    assert not judge.routes_to("11")  # código → CodeEvaluator
    assert not judge.routes_to("10.8")


# ── Amostragem humana (calibração judge↔humano, ADR-0005 §7) ────────────────

def test_human_sampling_correlation():
    """Registra calibração e computa correlação judge↔humano (meta ≥ 0.8)."""
    store = HumanSampling()
    store.record(step_id="2", judge_score=80, human_score=85)
    store.record(step_id="2", judge_score=90, human_score=92)
    store.record(step_id="2", judge_score=60, human_score=58)
    corr = store.correlation()
    assert corr is not None
    assert -1.0 <= corr <= 1.0
    assert store.count() == 3


def test_human_sampling_requires_two_samples():
    store = HumanSampling()
    store.record(step_id="2", judge_score=80, human_score=85)
    assert store.correlation() is None  # < 2 amostras


# ── Prompt padrão (ADR-0005 §8.1): JSON-only ─────────────────────────────────

def test_build_prompt_requires_json_only():
    rubric = load_rubric("2")
    prompt = build_prompt(rubric, artifact_content="# PRD", upstream_artifacts=None)
    assert "Retorne APENAS JSON" in prompt
    assert "[RUBRICA]" in prompt
    assert "[ARTEFATO A AVALIAR]" in prompt
    assert "[ARTEFATOS DE REFERÊNCIA" in prompt
