"""Fase 3 (R-5) — DecisionRecord versionado em 100% dos caminhos v2.

Tarefas 3.1–3.5 do plano `docs/llc2-complementacao-plano.md`:
- 3.1 replay.py grava metadados completos (config + routing + refs);
- 3.2 pipeline step_run registra estado NodeMachine sob LLC2_RECORD=1;
- 3.3 verificação usa o DecisionRecord real (não o stub sintético);
- 3.4 gates populam evidence_refs em todos os ramos;
- 3.5 LLC2_RECORD default 0 (só os writes novos são gated).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from llc_harness import gates as gates_mod
from llc_harness import pipeline as pipeline_mod
from llc_harness import replay


def _trace_lines(name: str) -> list[dict]:
    p = Path(os.environ["LLC_TRACE_DIR"]) / name
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()
            if x.strip()]


def _decisions() -> list[dict]:
    return _trace_lines("decisions.jsonl")


def _events() -> list[dict]:
    return _trace_lines("events.jsonl")


def _v2_classification(**overrides):
    base = {
        "type": "crud_endpoint",
        "confidence": 0.92,
        "reasoning": "alta confiança",
        "routing": "REVIEW_REQUIRED",
        "policy_version": "1.0.0",
        "policy_id": "llc-default",
        "thresholds_hash": "sha256:abc",
        "question_set_hash": "sha256:qs",
        "input_hash": "sha256:ih",
        "decision_id": "dec-1",
    }
    base.update(overrides)
    return base


# ── 3.4: gates com evidence_refs ─────────────────────────────────────────────

class TestGateEvidenceRefs:
    def test_gate_with_checklist_has_refs(self, monkeypatch):
        monkeypatch.setattr(
            gates_mod, "load_gates_config",
            lambda: {"gates": {"G-T": {"checklist": ["item a", "item b"]}}})
        assert gates_mod.gate_check("G-T", auto_approve=True) == "approved"
        recs = [r for r in _decisions() if r["kind"] == "gate"]
        assert len(recs) == 1
        assert recs[0]["evidence"]["evidence_refs"] == ["gates.json#G-T"]

    def test_gate_without_gate_has_empty_refs(self, monkeypatch):
        monkeypatch.setattr(
            gates_mod, "load_gates_config", lambda: {"gates": {}})
        # step "0" resolve no registry com gate=None (Caminho 1, sem gate).
        assert gates_mod.gate_check("0", auto_approve=True) == "approved"
        recs = [r for r in _decisions() if r["kind"] == "gate"]
        assert len(recs) == 1
        assert recs[0]["evidence"]["evidence_refs"] == []


# ── 3.1: metadados completos no early commitment ──────────────────────────────

class TestEarlyCommitmentMetadata:
    def test_replay_hit_carries_full_config(self):
        replay._trace_early_commitment(
            "replay_hit", classification=_v2_classification(),
            script={"id": "s1", "usage_count": 2}, task_description="T")
        recs = [r for r in _decisions() if r["kind"] == "early_commitment"]
        assert len(recs) == 1
        rec = recs[0]
        assert rec["config"] == {
            "policy_version": "1.0.0",
            "policy_id": "llc-default",
            "thresholds_hash": "sha256:abc",
            "question_set_hash": "sha256:qs",
        }
        assert rec["automation"] == "REVIEW_REQUIRED"
        assert rec["evidence"]["evidence_refs"] == ["dec-1"]
        assert rec["input_hash"].startswith("sha256:")

    def test_legacy_classification_keeps_null_config(self):
        replay._trace_early_commitment(
            "llm_fallback",
            classification={"type": "x", "confidence": 0.5},
            fallback_reason="no_cache", task_description="T")
        recs = [r for r in _decisions() if r["kind"] == "early_commitment"]
        assert len(recs) == 1
        assert recs[0]["config"] is None
        assert recs[0]["automation"] == "AUTO"
        assert recs[0]["evidence"]["evidence_refs"] == []


# ── 3.3: verificação contra o DecisionRecord real ─────────────────────────────

class TestVerifyAgainstRealRecord:
    def test_replay_verify_uses_record_from_trace(self, monkeypatch):
        from llc2.classifier import classify_task_v2
        from llc2.jev_adapter import FakeJevTransport

        task = "Criar endpoint de usuarios"
        seed = classify_task_v2(
            task, client=None, _transport=FakeJevTransport({
                "task_type": {
                    "choice": "crud_endpoint",
                    "probabilities": {"crud_endpoint": 0.92},
                    "confidence": 0.92},
                "complexity": {
                    "score": 1, "probabilities": {"1": 0.7},
                    "confidence": 0.85},
                "needs_human_review": {"noul": 0.15},
            }))
        assert seed["replayed"] is False

        events = []
        monkeypatch.setattr(replay, "_USE_LLC2_REPLAY", True)
        monkeypatch.setattr(
            replay, "classify_v2_routing",
            lambda td, client=None, **kw: dict(seed))
        monkeypatch.setattr(replay, "log_replay_event",
                            lambda ev, sid=None, **kw: events.append(
                                {"event": ev, "script_id": sid, **kw}))
        script = {"id": "s1", "usage_count": 3, "target_files": ["app.py"],
                  "architecture_version": "1.0"}
        monkeypatch.setattr(replay, "find_best_script", lambda t, td: script)
        monkeypatch.setattr(replay, "check_target_files_stale",
                            lambda files: False)
        monkeypatch.setattr(replay, "get_architecture_version", lambda: "1.0")
        monkeypatch.setattr(replay, "is_red_zone", lambda p: False)
        monkeypatch.setattr(replay, "extract_files_from_script",
                            lambda s: s.get("target_files", []))
        monkeypatch.setattr(replay, "preflight_all_steps",
                            lambda s, ctx: True)
        monkeypatch.setattr(replay, "gate_check",
                            lambda step, s: "approved")
        monkeypatch.setattr(replay, "deterministic_replay",
                            lambda s, ctx, g, llm, p, c: ("replay", 0, None))

        replay.agent_invoke("prompt", task_description=task)
        verify = next(e for e in events if e["event"] == "replay_verify")
        assert verify["ok"] == "True"


# ── 3.3b: replay de classificação sobrevive a records de cache ────────────────

class TestClassificationReplayNotShadowed:
    def test_miss_record_does_not_shadow_classification(self, monkeypatch):
        """classify → replay_miss → classify: 2ª ainda é replay_hit (Jev 1x).

        Regressão: records de cache (mesmo input_hash, outcome replay_miss)
        sombreavam o record do classificador no lookup reverso.
        """
        from llc2.classifier import classify_task_v2
        from llc2.jev_adapter import FakeJevTransport

        monkeypatch.setenv("LLC2_REPLAY", "1")
        task = "Criar endpoint de usuarios"
        fake = FakeJevTransport({
            "task_type": {
                "choice": "crud_endpoint",
                "probabilities": {"crud_endpoint": 0.92},
                "confidence": 0.92},
            "complexity": {
                "score": 1, "probabilities": {"1": 0.7},
                "confidence": 0.85},
            "needs_human_review": {"noul": 0.15},
        })
        first = classify_task_v2(task, client=None, _transport=fake)
        assert first["replayed"] is False
        replay._trace_early_commitment(
            "replay_miss", classification=first,
            fallback_reason="no_cache", task_description=task)
        second = classify_task_v2(task, client=None, _transport=fake)
        assert second["replayed"] is True
        assert second["reasoning"] == "replay_hit"
        assert len(fake.seen) == 1


# ── 3.2 + 3.5: estado NodeMachine sob LLC2_RECORD ──────────────────────────────

class TestNodeStateRecords:
    def _run_step(self, monkeypatch, *, record="1"):
        monkeypatch.setenv("LLC2_STATECHART", "1")
        if record is not None:
            monkeypatch.setenv("LLC2_RECORD", record)
        else:
            monkeypatch.delenv("LLC2_RECORD", raising=False)
        monkeypatch.setattr(
            pipeline_mod, "session_start",
            lambda *a, **k: {"session_id": "s-1", "context_seed": "seed"})
        monkeypatch.setattr(
            pipeline_mod, "skill_load", lambda *a, **k: ("sk.md", "prompt"))
        monkeypatch.setattr(
            pipeline_mod, "agent_invoke", lambda *a, **k: ("out", 0, None))
        return pipeline_mod.step_run("5", task="tarefa teste")

    def test_records_written_with_full_metadata(self, monkeypatch):
        assert self._run_step(monkeypatch, record="1") == "s-1"
        recs = [r for r in _decisions() if r["kind"] == "step_execution"]
        assert {r["outcome"] for r in recs} == {"node_start", "node_end"}
        for rec in recs:
            assert rec["config"]["policy_version"] == "1.0.0"
            assert rec["config"]["thresholds_hash"].startswith("sha256:")
            assert rec["config"]["question_set_hash"].startswith("sha256:")
            assert rec["input_hash"].startswith("sha256:")
            assert rec["state_hash"].startswith("sha256:")
            assert rec["evidence"]["evidence_refs"]
            assert rec["decision_id"]

    def test_no_records_when_flag_off(self, monkeypatch):
        self._run_step(monkeypatch, record="0")
        assert [r for r in _decisions()
                if r["kind"] == "step_execution"] == []

    def test_no_records_by_default(self, monkeypatch):
        self._run_step(monkeypatch, record=None)
        assert [r for r in _decisions()
                if r["kind"] == "step_execution"] == []

    def test_single_start_end_events_with_machine(self, monkeypatch):
        """Dedup 3.2: com NodeMachine, 1 step.start + 1 step.end (era 2+2)."""
        self._run_step(monkeypatch, record="1")
        kinds = [e["kind"] for e in _events()]
        assert kinds.count("step.start") == 1
        assert kinds.count("step.end") == 1
        # log_event aninha o kwarg fields (forma pré-existente do record).
        starts = [e for e in _events() if e["kind"] == "step.start"]
        assert "statechart_state" in starts[0]["fields"]["fields"]
