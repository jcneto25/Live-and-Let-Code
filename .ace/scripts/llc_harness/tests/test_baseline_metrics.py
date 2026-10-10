"""Fase 6 (R-7) — baseline de métricas + contadores de replay (7.1/7.2).

- 7.1 `LLC2_BASELINE=1` grava eventos append-only em `baseline.jsonl`
  (via `trace_dir()`, mesmo padrão de `log_replay_event`) com
  `session_id/step/phase/tokens/calls/latency/replay_*`; default 0 sem impacto.
- 7.2 eventos `phase="invoke"` carregam contadores `replay_hit/miss/success/
  rollback`, `jev/llm_calls_avoided`, `tokens/cost_avoided`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from llc_harness import pipeline as pipeline_mod
from llc_harness import replay


def _baseline_path() -> Path:
    return Path(os.environ["LLC_TRACE_DIR"]) / "baseline.jsonl"


def _events():
    p = _baseline_path()
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _v2_classification(**overrides):
    base = {
        "type": "crud_endpoint",
        "confidence": 0.92,
        "reasoning": "alta confiança",
        "routing": "AUTO",
        "policy_version": "1.0.0",
        "question_set_hash": "qs-abc",
        "input_hash": "ih-123",
        "decision_id": "dec-456",
    }
    base.update(overrides)
    return base


def _drive_invoke(monkeypatch, classification, *, script=None, replay_result=None):
    """Espelha o `_run` dos testes F1; retorna o valor de `agent_invoke`."""
    monkeypatch.setattr(replay, "_USE_LLC2_REPLAY", True)
    monkeypatch.setattr(replay, "log_replay_event", lambda *a, **k: None)
    monkeypatch.setattr(
        replay, "classify_v2_routing",
        lambda td, client=None, **kw: dict(classification))
    monkeypatch.setattr(
        replay, "classify_task", lambda td, client=None: dict(classification))
    monkeypatch.setattr(replay, "find_best_script", lambda t, td: script)
    monkeypatch.setattr(
        replay, "_llm_invoke", lambda prompt, client=None: ("llm-out", 0, None))
    if script is not None:
        monkeypatch.setattr(replay, "check_target_files_stale", lambda files: False)
        monkeypatch.setattr(replay, "get_architecture_version", lambda: "1.0")
        monkeypatch.setattr(replay, "is_red_zone", lambda p: False)
        monkeypatch.setattr(
            replay, "extract_files_from_script", lambda s: s.get("target_files", []))
        monkeypatch.setattr(replay, "preflight_all_steps", lambda s, ctx: True)
        monkeypatch.setattr(replay, "gate_check", lambda step, s: "approved")
        if isinstance(replay_result, Exception):
            def boom(*a, **k):
                raise replay_result
            monkeypatch.setattr(replay, "deterministic_replay", boom)
        else:
            monkeypatch.setattr(
                replay, "deterministic_replay",
                lambda *a, **k: replay_result)
    return replay.agent_invoke(
        "prompt", task_description="Criar endpoint",
        session_id="s-9", step="3")


class TestBaselineEnabled:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("LLC2_BASELINE", raising=False)
        assert replay._baseline_enabled() is False

    @pytest.mark.parametrize("value", ["0", "", "false", "no"])
    def test_explicit_off_values(self, monkeypatch, value):
        monkeypatch.setenv("LLC2_BASELINE", value)
        assert replay._baseline_enabled() is False

    def test_on(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        assert replay._baseline_enabled() is True


class TestCaptureFlowTokens:
    def test_returns_ints_with_provenance(self):
        got = replay.capture_flow_tokens("algum prompt", "algum output")
        assert isinstance(got["tokens_in"], int) and got["tokens_in"] >= 0
        assert isinstance(got["tokens_out"], int) and got["tokens_out"] >= 0
        assert got["precision"] in ("exact", "estimated")
        assert got["source"]

    def test_fallback_without_instrument(self, monkeypatch):
        monkeypatch.setattr(replay, "capture_tokens", None)
        got = replay.capture_flow_tokens("algum prompt", "algum output")
        assert got["tokens_in"] > 0 and got["tokens_out"] >= 0
        assert got["precision"] == "estimated"
        assert got["source"] == "fallback"

    def test_no_output_means_zero_out(self, monkeypatch):
        # Sem output observado, tokens_out=0 — nunca 25% fabricados.
        # (Prompt longo: 25% da heurística daria ≥2 se fabricasse.)
        monkeypatch.setattr(replay, "capture_tokens", None)
        prompt = " ".join(f"palavra{i}" for i in range(20))
        got = replay.capture_flow_tokens(prompt, None)
        assert got["tokens_out"] == 0
        assert got["tokens_in"] > 0

    def test_usd_rate_matches_instrument(self):
        # Detector de drift: a taxa espelhada não pode divergir.
        from llc_evals import instrument
        assert replay._USD_PER_TOKEN == instrument._USD_PER_TOKEN


class TestEmitBaselineEvent:
    def test_appends_json_line(self):
        replay.emit_baseline_event({"phase": "invoke", "step": "3"})
        evs = _events()
        assert len(evs) == 1
        assert evs[0]["phase"] == "invoke"
        assert evs[0]["step"] == "3"
        assert evs[0]["timestamp"]

    def test_append_only(self):
        replay.emit_baseline_event({"n": 1})
        replay.emit_baseline_event({"n": 2})
        assert [e["n"] for e in _events()] == [1, 2]

    def test_never_raises(self, monkeypatch):
        def boom():
            raise OSError("sem disco")
        monkeypatch.setattr(replay, "trace_dir", boom)
        assert replay.emit_baseline_event({"phase": "invoke"}) is None


class TestAgentInvokeBaseline:
    def test_flag_off_writes_nothing(self, monkeypatch):
        monkeypatch.delenv("LLC2_BASELINE", raising=False)
        out, code, _seed = _drive_invoke(monkeypatch, _v2_classification())
        assert (out, code) == ("llm-out", 0)
        assert _events() == []
        assert not _baseline_path().exists()

    def test_fallback_event_has_full_schema(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        _drive_invoke(monkeypatch, _v2_classification())
        evs = _events()
        assert len(evs) == 1
        ev = evs[0]
        for key in ("timestamp", "session_id", "step", "phase", "event",
                    "reason", "latency_ms", "calls_llm", "calls_jev",
                    "tokens_in", "tokens_out", "precision", "source",
                    "replay_hit", "replay_miss", "replay_success",
                    "replay_rollback", "jev_calls_avoided",
                    "llm_calls_avoided", "tokens_avoided", "cost_avoided",
                    "exit_code"):
            assert key in ev, f"campo ausente: {key}"
        assert (ev["session_id"], ev["step"], ev["phase"]) == ("s-9", "3", "invoke")
        assert ev["event"] == "llm_fallback"
        assert ev["reason"] == "cache_miss"
        assert ev["calls_llm"] == 1 and ev["calls_jev"] == 1
        assert ev["latency_ms"] >= 0
        assert ev["replay_hit"] == 0 and ev["replay_miss"] == 1
        assert ev["llm_calls_avoided"] == 0 and ev["tokens_avoided"] == 0
        assert ev["exit_code"] == 0

    def test_reason_passthrough(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        _drive_invoke(monkeypatch, _v2_classification(routing="HUMAN_REQUIRED"))
        assert _events()[0]["reason"] == "human_required"

    def test_replay_success_counts_avoided(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        script = {"id": "s1", "usage_count": 3, "target_files": ["app.py"],
                  "architecture_version": "1.0"}
        result = _drive_invoke(monkeypatch, _v2_classification(), script=script,
                               replay_result={"status": "success"})
        # Contrato normalizado (reparo pós-review): sempre 3-tupla.
        assert result == ("replay:s1", 0, None)
        ev = _events()[0]
        assert ev["event"] == "replay_success"
        assert ev["replay_hit"] == 1 and ev["replay_success"] == 1
        assert ev["replay_rollback"] == 0
        assert ev["calls_llm"] == 0 and ev["calls_jev"] == 1
        assert ev["llm_calls_avoided"] == 1
        assert ev["jev_calls_avoided"] == 0  # Jev rodou p/ classificar
        assert ev["tokens_avoided"] > 0 and ev["cost_avoided"] > 0
        assert ev["tokens_out"] == 0  # sem LLM, sem saída fabricada
        assert ev["exit_code"] == 0

    def test_rollback_counts_llm(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        script = {"id": "s1", "usage_count": 3, "target_files": ["app.py"],
                  "architecture_version": "1.0"}
        # deterministic_replay cai no llm_fallback_fn após rollback → tupla.
        out, code, _seed = _drive_invoke(
            monkeypatch, _v2_classification(), script=script,
            replay_result=("llm-out", 0, None))
        assert (out, code) == ("llm-out", 0)
        ev = _events()[0]
        assert ev["event"] == "replay_rollback"
        assert ev["replay_hit"] == 1 and ev["replay_rollback"] == 1
        assert ev["replay_success"] == 0
        assert ev["calls_llm"] == 1
        assert ev["llm_calls_avoided"] == 0

    def test_error_still_emits_and_reraises(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        script = {"id": "s1", "usage_count": 3, "target_files": ["app.py"],
                  "architecture_version": "1.0"}
        with pytest.raises(RuntimeError):
            _drive_invoke(monkeypatch, _v2_classification(), script=script,
                          replay_result=RuntimeError("replay explodiu"))
        ev = _events()[0]
        assert ev["event"] == "error"
        assert ev["exit_code"] is None  # sem resultado, sem exit code

    def test_replayed_classification_avoids_jev(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        _drive_invoke(monkeypatch,
                      _v2_classification(replayed=True, reasoning="replay_hit"))
        ev = _events()[0]
        assert ev["calls_jev"] == 0
        assert ev["jev_calls_avoided"] == 1


class TestRealReplayContract:
    """O teste que faltou desde a F1: replay REAL ponta a ponta.

    `deterministic_replay` sem mock com script mínimo (`steps: []`).
    Antes do reparo: dict cru atravessa `agent_invoke` e `step_run`
    quebra com ValueError no unpack.
    """

    def _script(self):
        return {"id": "s1", "usage_count": 0, "target_files": [],
                "steps": [],
                "architecture_version": replay.get_architecture_version()}

    def _mock_env(self, monkeypatch, script):
        monkeypatch.setattr(replay, "_USE_LLC2_REPLAY", True)
        monkeypatch.setattr(
            replay, "classify_v2_routing",
            lambda td, client=None, **kw: _v2_classification())
        monkeypatch.setattr(replay, "find_best_script", lambda t, td: script)
        monkeypatch.setattr(replay, "check_target_files_stale",
                            lambda files: False)
        monkeypatch.setattr(replay, "preflight_all_steps",
                            lambda s, ctx: True)
        monkeypatch.setattr(
            replay, "_llm_invoke", lambda prompt, client=None: ("llm", 0, None))

    def test_agent_invoke_normalizes_real_replay(self, monkeypatch):
        monkeypatch.setenv("LLC2_BASELINE", "1")
        script = self._script()
        self._mock_env(monkeypatch, script)
        result = replay.agent_invoke("prompt", task_description="tarefa")
        assert result == ("replay:s1", 0, None)
        assert script["usage_count"] == 1  # replay REAL executou
        ev = _events()[0]
        assert ev["event"] == "replay_success"
        assert ev["replay_success"] == 1

    @pytest.mark.parametrize("baseline", ["1", None])
    def test_step_run_survives_real_replay(self, monkeypatch, baseline):
        if baseline is None:
            monkeypatch.delenv("LLC2_BASELINE", raising=False)
        else:
            monkeypatch.setenv("LLC2_BASELINE", baseline)
        script = self._script()
        self._mock_env(monkeypatch, script)
        monkeypatch.setattr(
            pipeline_mod, "session_start",
            lambda *a, **k: {"session_id": "s-1", "context_seed": "seed"})
        monkeypatch.setattr(
            pipeline_mod, "skill_load", lambda *a, **k: ("sk.md", "prompt"))
        # agent_invoke REAL (rebind) — nada de mock no caminho medido.
        monkeypatch.setattr(pipeline_mod, "agent_invoke", replay.agent_invoke)
        assert pipeline_mod.step_run("5", task="tarefa") == "s-1"
        if baseline == "1":
            evs = [e for e in _events() if e["phase"] == "invoke"]
            assert len(evs) == 1
            assert evs[0]["event"] == "replay_success"
        else:
            assert _events() == []


class TestStepRunBaseline:
    def _run_step(self, monkeypatch, *, baseline="1", invoke=None):
        if baseline is None:
            monkeypatch.delenv("LLC2_BASELINE", raising=False)
        else:
            monkeypatch.setenv("LLC2_BASELINE", baseline)
        monkeypatch.setattr(
            pipeline_mod, "session_start",
            lambda *a, **k: {"session_id": "s-1", "context_seed": "seed"})
        monkeypatch.setattr(
            pipeline_mod, "skill_load", lambda *a, **k: ("sk.md", "prompt"))
        calls = {}
        def fake_invoke(*a, **k):
            calls.update(k)
            return ("out", 0, None) if invoke is None else invoke
        monkeypatch.setattr(pipeline_mod, "agent_invoke", fake_invoke)
        assert pipeline_mod.step_run("5", task="tarefa teste") == "s-1"
        return calls

    def test_single_writer_no_step_phase(self, monkeypatch):
        # Reparo pós-review: evento único (invoke); step foi consolidado
        # para não duplicar tokens na agregação "por sessão".
        self._run_step(monkeypatch, baseline="1")
        assert _events() == []  # agent_invoke mockado → nenhum evento real

    def test_flag_off_writes_nothing(self, monkeypatch):
        self._run_step(monkeypatch, baseline=None)
        assert _events() == []

    def test_session_passthrough_to_invoke(self, monkeypatch):
        calls = self._run_step(monkeypatch, baseline="1")
        assert calls.get("session_id") == "s-1"
        assert calls.get("step") == "5"
