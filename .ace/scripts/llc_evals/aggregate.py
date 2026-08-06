"""llc_evals.aggregate — agregação de métricas por step + persistência.

PRP-EVALS-F2 (ADR-0005 §2.3, §2.9):
    FirstPassRate(step) = gates_aprovados_1a_vez / total_gates
    ReworkWaste(step)   = tokens_gastos_em_retries / TokenCost

save_result() persiste em .ace/evals/results/step-{id}-{date}.yaml (RF-EF2.3).

PRP-EVALS-F4 (ADR-0005 §2.9, D11/D12):
    BaselineManager — baseline histórico por step em
    `.ace/evals/baselines/step-{id}.yaml`, com política de warm-up
    (collecting → warmup → stable), separação por nível de precisão
    (level_1/level_2/level_3) e reset automático na migração para um
    nível mais preciso (level_3 → level_1).

Regressão: cada run compara-se ao baseline do MESMO step e MESMO nível
(D6/D12); deltas negativos de qualidade disparam alerta.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

from llc_evals.evaluators.efficiency_meter import efficiency_score as _eff

# ── PRP-EVALS-F4: política de warm-up (D11) ──────────────────────────────────
DEFAULT_WARMUP = {"n_min": 5, "n_stable": 10}

# Precisão por nível: level_1 (log nativo) > level_2 (usage block) > level_3
# (estimativa). A migração para um nível MAIS preciso reseta o baseline (D12).
_PRECISION_ORDER = {"level_1": 1, "level_2": 2, "level_3": 3}


def load_warmup_config(gates_path: Path | str | None = None) -> dict:
    """Lê N_MIN/N_STABLE de `gates.json → evals` (RF-EF4.6).

    Defaults D11 (5/10) se gates.json ausente ou sem seção `evals`.
    Chaves: `evals.baseline_warmup_min` e `evals.baseline_warmup_stable`.
    """
    cfg = dict(DEFAULT_WARMUP)
    if gates_path is None:
        return cfg
    path = Path(gates_path)
    if not path.exists():
        return cfg
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return cfg
    evals_cfg = data.get("evals", {}) if isinstance(data, dict) else {}
    if not isinstance(evals_cfg, dict):
        return cfg  # seção evals inválida (ex.: lista) → defaults D11
    try:
        cfg["n_min"] = int(evals_cfg.get("baseline_warmup_min", cfg["n_min"]))
        cfg["n_stable"] = int(evals_cfg.get("baseline_warmup_stable", cfg["n_stable"]))
    except (ValueError, TypeError):
        return cfg  # valor não-numérico → defaults D11
    return cfg


def _precision_rank(source: str) -> int:
    """Ranking numérico de precisão (1 = mais preciso). Nível desconhecido → pior."""
    return _PRECISION_ORDER.get(source, 99)


class BaselineManager:
    """Baseline histórico por step com política de warm-up (RF-EF4.1-4.6).

    Fases (D11):
      collecting — run_count < N_MIN   → NENHUM alerta de regressão
      warmup     — N_MIN ≤ run_count < N_STABLE → alertas com tag
                   `[baseline-unstable]` (informativo, não bloqueante)
      stable     — run_count ≥ N_STABLE → alertas normais

    Separação por nível (D12): cada nível de precisão mantém bucket próprio
    (`by_precision_level`); `check_regression()` compara apenas runs do mesmo
    nível. Migração para nível mais preciso reseta o baseline e o warm-up
    recomeça (RF-EF4.5).
    """

    def __init__(self, baselines_dir: Path | str, warmup_config: dict | None = None):
        self.baselines_dir = Path(baselines_dir)
        self.cfg = dict(DEFAULT_WARMUP)
        if warmup_config:
            self.cfg.update(warmup_config)

    # ── Persistência ────────────────────────────────────────────────────────
    def _path(self, step_id: str) -> Path:
        return self.baselines_dir / f"step-{step_id}.yaml"

    def load_baseline(self, step_id: str) -> dict:
        """Carrega baseline do step; estrutura vazia se ausente (sem exceção)."""
        path = self._path(step_id)
        if not path.exists():
            return self._empty(step_id)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            return self._empty(step_id)
        data.setdefault("by_precision_level", {})
        return data

    def _empty(self, step_id: str) -> dict:
        return {
            "step": str(step_id),
            "run_count": 0,
            "baseline_phase": "collecting",
            "warmup_config": dict(self.cfg),
            "active_precision": None,
            "by_precision_level": {},
        }

    # ── Fase (D11) ──────────────────────────────────────────────────────────
    def phase_for(self, run_count: int) -> str:
        """collecting | warmup | stable a partir do run_count do nível ativo."""
        if run_count < self.cfg["n_min"]:
            return "collecting"
        if run_count < self.cfg["n_stable"]:
            return "warmup"
        return "stable"

    # ── Registro (RF-EF4.5) ─────────────────────────────────────────────────
    def record_run(self, *, step_id: str, quality_score: float,
                   token_cost: float, source: str) -> dict:
        """Registra run no bucket do nível; reseta baseline se nível mais preciso.

        A média móvel de QualityScore/TokenCost por nível usa o run_count
        anterior do bucket — dados de níveis diferentes nunca se misturam
        (D12/RF-EF4.4).
        """
        baseline = self.load_baseline(step_id)
        active = baseline.get("active_precision")
        # RF-EF4.5: migração para nível MAIS preciso (level_3 → level_1/2)
        # reseta o baseline — o warm-up recomeça para os dados exatos.
        if active is not None and _precision_rank(source) < _precision_rank(active):
            baseline = self._empty(step_id)

        by_level = baseline.setdefault("by_precision_level", {})
        bucket = by_level.setdefault(source, {
            "run_count": 0,
            "quality_score_avg": 0.0,
            "token_cost_avg": 0.0,
            "efficiency_score_avg": 0.0,
            "precision": "estimated" if source == "level_3" else "exact",
        })
        prev_n = bucket["run_count"]
        bucket["run_count"] = prev_n + 1
        bucket["quality_score_avg"] = round(
            (bucket["quality_score_avg"] * prev_n + quality_score) / bucket["run_count"], 4)
        bucket["token_cost_avg"] = round(
            (bucket["token_cost_avg"] * prev_n + token_cost) / bucket["run_count"], 4)
        try:
            eff = _eff(quality_score, token_cost)
        except ValueError:
            eff = 0.0  # custo inválido → sem eficiência no bucket
        bucket["efficiency_score_avg"] = round(
            (bucket["efficiency_score_avg"] * prev_n + eff) / bucket["run_count"], 4)

        total = sum(b["run_count"] for b in by_level.values())
        baseline["run_count"] = total
        # active_precision = nível DONO do baseline (definido no 1º run ou no
        # reset) — NUNCA sobrescrito por run de precisão inferior: um run
        # level_3 isolado não pode apagar um baseline level_1 estável (D12:
        # "não são excluídos, mas identificados").
        if baseline.get("active_precision") is None:
            baseline["active_precision"] = source
        active_bucket = by_level.get(baseline["active_precision"], bucket)
        baseline["baseline_phase"] = self.phase_for(active_bucket["run_count"])
        baseline["warmup_config"] = dict(self.cfg)

        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self._path(step_id).write_text(
            yaml.safe_dump(baseline, sort_keys=False), encoding="utf-8")
        return baseline

    # ── Regressão (RF-EF4.1-4.4) ────────────────────────────────────────────
    def check_regression(self, *, step_id: str, quality_score: float,
                         token_cost: float, source: str) -> list[dict]:
        """Compara run contra o baseline do MESMO nível; retorna alertas.

        - collecting → [] (RF-EF4.1: sem alerta se run_count < N_MIN)
        - warmup + delta negativo → alerta com tag `baseline-unstable`
          (RF-EF4.2)
        - stable + delta negativo → alerta sem tag (RF-EF4.3)
        - delta não-negativo → [] (sem regressão)
        """
        baseline = self.load_baseline(step_id)
        by_level = baseline.get("by_precision_level", {})
        bucket = by_level.get(source)
        if bucket is None or bucket["run_count"] == 0:
            return []
        run_count = bucket["run_count"]
        phase = self.phase_for(run_count)
        if phase == "collecting":
            return []

        q_delta = round(quality_score - bucket["quality_score_avg"], 4)
        t_delta = round(token_cost - bucket["token_cost_avg"], 4)
        if q_delta >= 0:
            return []  # sem regressão de qualidade

        alert = {
            "step_id": str(step_id),
            "phase": phase,
            "tag": "baseline-unstable" if phase == "warmup" else None,
            "quality_delta": q_delta,
            "token_delta": t_delta,
            "regression": True,
        }
        return [alert]


def first_pass_rate(*, gates_first_try: int, total_gates: int) -> float:
    """Gates aprovados de primeira / total (ADR-0005 §2.3)."""
    if total_gates <= 0:
        return 0.0
    return round(gates_first_try / total_gates, 4)


def rework_waste(*, retry_tokens: float, token_cost: float) -> float:
    """Fração de tokens desperdiçada em retries (ADR-0005 §2.3)."""
    if token_cost <= 0:
        return 0.0
    return round(retry_tokens / token_cost, 4)


def aggregate(
    *,
    total_gates: int,
    gates_first_try: int,
    retry_tokens: float,
    token_cost: float,
) -> dict:
    """Métricas agregadas da sessão a partir do histórico de retries (RF-EF2.5)."""
    return {
        "first_pass_rate": first_pass_rate(
            gates_first_try=gates_first_try, total_gates=total_gates,
        ),
        "rework_waste": rework_waste(
            retry_tokens=retry_tokens, token_cost=token_cost,
        ),
    }


def save_result(
    *,
    step_id: str,
    result: dict,
    results_dir: Path,
    date: str | None = None,
) -> Path:
    """Persiste resultado em `.ace/evals/results/step-{id}-{date}.yaml` (RF-EF2.3)."""
    day = date or str(date.today())
    path = Path(results_dir) / f"step-{step_id}-{day}.yaml"
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "step_id": step_id,
        "date": day,
        **result,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path
