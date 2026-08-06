"""Testes para llc_evals.aggregate — RF-EF2.3/2.5 (PRP-EVALS-F2).

FirstPassRate(step) = gates_aprovados_1a_vez / total_gates
ReworkWaste(step)   = tokens_gastos_em_retries / TokenCost
(ADR-0005 §2.3) — persistência em .ace/evals/results/step-{id}-{date}.yaml
"""
import json
from pathlib import Path

import pytest
import yaml

from llc_evals import aggregate


def test_first_pass_rate_correct():
    """RF-EF2.5: FirstPassRate = aprovados_1a_vez / total."""
    assert aggregate.first_pass_rate(gates_first_try=3, total_gates=4) == pytest.approx(0.75)


def test_first_pass_rate_zero_total():
    assert aggregate.first_pass_rate(gates_first_try=0, total_gates=0) == 0.0


def test_rework_waste_correct():
    """RF-EF2.5: ReworkWaste = tokens_retries / TokenCost."""
    assert aggregate.rework_waste(retry_tokens=2500, token_cost=10000) == pytest.approx(0.25)


def test_rework_waste_zero_cost():
    assert aggregate.rework_waste(retry_tokens=0, token_cost=0) == 0.0


def test_aggregate_with_retry_history():
    """RF-EF2.5: aggregate() a partir do histórico de retries da sessão."""
    metrics = aggregate.aggregate(
        total_gates=4,
        gates_first_try=3,
        retry_tokens=2500,
        token_cost=10000,
    )
    assert metrics["first_pass_rate"] == pytest.approx(0.75)
    assert metrics["rework_waste"] == pytest.approx(0.25)


def test_save_result_creates_yaml(tmp_path):
    """RF-EF2.3: save_result() cria YAML em .ace/evals/results/."""
    results_dir = tmp_path / ".ace" / "evals" / "results"
    path = aggregate.save_result(
        step_id="11",
        result={"code_quality": 91.9, "first_pass_rate": 0.75},
        results_dir=results_dir,
        date="2026-08-06",
    )
    assert path.exists()
    assert path.name.startswith("step-11-")
    assert path.name.endswith(".yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["step_id"] == "11"
    assert data["code_quality"] == 91.9
    assert data["date"] == "2026-08-06"


def test_save_result_creates_dir_if_missing(tmp_path):
    results_dir = tmp_path / "novo" / "results"
    path = aggregate.save_result(
        step_id="5", result={"ok": True}, results_dir=results_dir, date="2026-08-06",
    )
    assert path.exists()
    assert path.parent == results_dir


# ── PRP-EVALS-F4: Baselines + Detecção de Regressão (ADR-0005 §2.9, D11/D12) ─
# RF-EF4.1 a EF4.6 — warm-up (collecting → warmup → stable), separação por
# nível de precisão e reset na migração level_3 → level_1.

def _warmup(n_min: int = 5, n_stable: int = 10) -> dict:
    return {"n_min": n_min, "n_stable": n_stable}


def _record_runs(manager, step_id: str, count: int, qs: float = 80.0,
                 tc: float = 10000.0, source: str = "level_1"):
    for _ in range(count):
        manager.record_run(step_id=step_id, quality_score=qs,
                           token_cost=tc, source=source)


# ── RF-EF4.1: sem alerta se run_count < N_MIN ────────────────────────────────
def test_no_alert_below_n_min(tmp_path):
    """RF-EF4.1: 3 runs (N_MIN=5) → check_regression() sem alertas."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 3)
    alerts = manager.check_regression(
        step_id="5", quality_score=70.0, token_cost=9000.0, source="level_1")
    assert alerts == []


# ── RF-EF4.2: alerta [baseline-unstable] em N_MIN ≤ run_count < N_STABLE ────
def test_alert_with_baseline_unstable_tag_in_warmup(tmp_path):
    """RF-EF4.2: 7 runs (N_STABLE=10) + delta negativo → alerta com tag."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 7, qs=85.0)
    alerts = manager.check_regression(
        step_id="5", quality_score=70.0, token_cost=9000.0, source="level_1")
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["tag"] == "baseline-unstable"
    assert alert["phase"] == "warmup"
    assert alert["regression"] is True
    assert alert["quality_delta"] < 0


# ── RF-EF4.3: alerta normal (sem tag) em run_count ≥ N_STABLE ────────────────
def test_alert_without_tag_when_stable(tmp_path):
    """RF-EF4.3: 12 runs (≥ N_STABLE) + delta negativo → alerta sem tag."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 12, qs=85.0)
    alerts = manager.check_regression(
        step_id="5", quality_score=70.0, token_cost=9000.0, source="level_1")
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["tag"] is None
    assert alert["phase"] == "stable"
    assert alert["regression"] is True


def test_no_alert_when_delta_not_negative_stable(tmp_path):
    """Sem regressão (delta ≥ 0) → nenhum alerta, mesmo estável."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 12, qs=85.0)
    alerts = manager.check_regression(
        step_id="5", quality_score=90.0, token_cost=8000.0, source="level_1")
    assert alerts == []


# ── RF-EF4.4: EfficiencyScore só compara runs do mesmo nível ─────────────────
def test_same_level_comparison_only(tmp_path):
    """RF-EF4.4: runs level_1 e level_3 em buckets separados — sem mistura.

    Discriminante: se o check misturasse os níveis (avg 75), 85 > 75 →
    nenhum alerta. Com separação (avg level_1 = 90), 85 < 90 → alerta.
    """
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 12, qs=90.0, tc=12000.0, source="level_1")
    _record_runs(manager, "5", 12, qs=60.0, tc=20000.0, source="level_3")

    # check level_1 → usa apenas bucket level_1 (qs_avg 90.0) → delta -5 → alerta
    alerts_l1 = manager.check_regression(
        step_id="5", quality_score=85.0, token_cost=10000.0, source="level_1")
    assert len(alerts_l1) == 1

    baseline = manager.load_baseline("5")
    by_level = baseline["by_precision_level"]
    assert by_level["level_1"]["quality_score_avg"] == pytest.approx(90.0)
    assert by_level["level_3"]["quality_score_avg"] == pytest.approx(60.0)
    # total = soma dos buckets, sem mistura de níveis
    assert baseline["run_count"] == 24


# ── RF-EF4.5: reset ao migrar de level_3 para level_1 ────────────────────────
def test_reset_on_level_migration(tmp_path):
    """RF-EF4.5: 8 runs level_3 → run level_1 chega → baseline resetado."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 8, qs=80.0, source="level_3")
    baseline_before = manager.load_baseline("5")
    assert baseline_before["run_count"] == 8

    manager.record_run(step_id="5", quality_score=90.0,
                       token_cost=10000.0, source="level_1")
    baseline_after = manager.load_baseline("5")
    # warm-up recomeça do zero para o novo nível (mais preciso)
    assert baseline_after["run_count"] == 1
    assert set(baseline_after["by_precision_level"].keys()) == {"level_1"}
    assert baseline_after["active_precision"] == "level_1"


def test_no_reset_on_same_level(tmp_path):
    """Mesmo nível não reseta — run_count acumula."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 3, qs=80.0, source="level_1")
    _record_runs(manager, "5", 4, qs=85.0, source="level_1")
    assert manager.load_baseline("5")["run_count"] == 7


# ── RF-EF4.6: N_MIN/N_STABLE configuráveis em gates.json ─────────────────────
def test_warmup_config_from_gates_json(tmp_path):
    """RF-EF4.6: gates.json → evals.baseline_warmup_min/stable usados."""
    gates = tmp_path / "gates.json"
    gates.write_text(json.dumps({
        "gates": {},
        "evals": {"baseline_warmup_min": 2, "baseline_warmup_stable": 4},
    }), encoding="utf-8")
    cfg = aggregate.load_warmup_config(gates_path=gates)
    assert cfg == {"n_min": 2, "n_stable": 4}

    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=cfg)
    _record_runs(manager, "5", 2, qs=85.0)   # run_count=2 == N_MIN(2)
    alerts = manager.check_regression(
        step_id="5", quality_score=70.0, token_cost=9000.0, source="level_1")
    assert len(alerts) == 1
    assert alerts[0]["phase"] == "warmup"
    assert alerts[0]["tag"] == "baseline-unstable"


def test_warmup_config_defaults_without_evals_section(tmp_path):
    """gates.json sem seção evals → defaults D11 (5/10)."""
    gates = tmp_path / "gates.json"
    gates.write_text(json.dumps({"gates": {}}), encoding="utf-8")
    assert aggregate.load_warmup_config(gates_path=gates) == _warmup()


def test_warmup_config_tolerates_non_dict_evals(tmp_path):
    """Seção evals não-dict (lista) → defaults D11, sem crash."""
    gates = tmp_path / "gates.json"
    gates.write_text(json.dumps({"gates": {}, "evals": [1, 2, 3]}),
                     encoding="utf-8")
    assert aggregate.load_warmup_config(gates_path=gates) == _warmup()


def test_warmup_config_tolerates_non_numeric_values(tmp_path):
    """Valores não-numéricos em evals → defaults D11, sem crash."""
    gates = tmp_path / "gates.json"
    gates.write_text(json.dumps({"gates": {}, "evals": {
        "baseline_warmup_min": "abc", "baseline_warmup_stable": "xyz",
    }}), encoding="utf-8")
    assert aggregate.load_warmup_config(gates_path=gates) == _warmup()


def test_warmup_config_missing_file_defaults(tmp_path):
    """gates.json ausente → defaults D11."""
    missing = tmp_path / "nao-existe.json"
    assert aggregate.load_warmup_config(gates_path=missing) == _warmup()


def test_warmup_config_bad_json_defaults(tmp_path):
    """gates.json corrompido → defaults D11, sem crash."""
    gates = tmp_path / "gates.json"
    gates.write_text("{ invalido", encoding="utf-8")
    assert aggregate.load_warmup_config(gates_path=gates) == _warmup()


# ── Regressões da revisão ────────────────────────────────────────────────────
def test_downgrade_run_does_not_reset_stable_baseline(tmp_path):
    """Run level_3 isolado NÃO reseta baseline level_1 estável (D12).

    Regressão: active_precision era sobrescrito a cada run — um único run
    level_3 após baseline level_1 estável apagava tudo no próximo level_1.
    """
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    _record_runs(manager, "5", 12, qs=90.0, source="level_1")
    # run de precisão inferior (fallback de outro cliente) → bucket próprio
    manager.record_run(step_id="5", quality_score=70.0,
                       token_cost=20000.0, source="level_3")
    baseline = manager.load_baseline("5")
    # o dono do baseline continua level_1 — NADA resetado
    assert baseline["active_precision"] == "level_1"
    assert baseline["by_precision_level"]["level_1"]["run_count"] == 12
    assert baseline["run_count"] == 13


def test_precision_field_on_buckets(tmp_path):
    """Buckets marcam precision (ADR §2.9/PRP §3): estimated/exact."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    manager.record_run(step_id="5", quality_score=80.0,
                       token_cost=10000.0, source="level_1")
    manager.record_run(step_id="5", quality_score=80.0,
                       token_cost=10000.0, source="level_3")
    baseline = manager.load_baseline("5")
    assert baseline["by_precision_level"]["level_1"]["precision"] == "exact"
    assert baseline["by_precision_level"]["level_3"]["precision"] == "estimated"


# ── Formato do baseline (PRP §3) ─────────────────────────────────────────────
def test_baseline_file_format(tmp_path):
    """Baseline persistido em .ace/evals/baselines/step-{id}.yaml no formato §3."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    manager.record_run(step_id="5", quality_score=84.2,
                       token_cost=14800.0, source="level_1")

    path = tmp_path / "baselines" / "step-5.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["step"] == "5"
    assert data["run_count"] == 1
    assert data["warmup_config"] == {"n_min": 5, "n_stable": 10}
    l1 = data["by_precision_level"]["level_1"]
    assert l1["run_count"] == 1
    assert l1["quality_score_avg"] == pytest.approx(84.2)
    assert l1["token_cost_avg"] == pytest.approx(14800.0)


def test_missing_baseline_returns_empty(tmp_path):
    """Step sem baseline → estrutura vazia (collecting), sem exceção."""
    manager = aggregate.BaselineManager(
        baselines_dir=tmp_path / "baselines", warmup_config=_warmup())
    baseline = manager.load_baseline("999")
    assert baseline["run_count"] == 0
    assert baseline["by_precision_level"] == {}
