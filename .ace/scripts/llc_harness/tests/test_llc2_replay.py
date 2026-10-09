"""Fase 1 (R-2) — integração llc_harness/replay.py → Decision Engine llc2.

Tarefas 1.3–1.7 do plano `docs/llc2-complementacao-plano.md`:

- 1.3 `classify_v2_routing()` retorna dict versionado e nunca None;
- 1.4 com `LLC2_REPLAY=1`, o fluxo usa a classificação v2 (routing respeitado);
- 1.5 `verify_replay_from_record` recebe o caminho versionado (input_hash);
- 1.6 hits/misses/fallbacks logam `decision_id`/`input_hash`/
  `question_set_hash`/`policy_version`;
- 1.7 com flag off ou exceção no ramo v2, o legado roda idêntico, com razão
  clara (`llc2_replay_error`) quando a exceção ocorre.
"""
from __future__ import annotations

import json

import pytest

from llc_harness import replay
from llc2.jev_adapter import FakeJevTransport


def _fake_transport():
    return FakeJevTransport({
        "task_type": {
            "choice": "crud_endpoint",
            "probabilities": {"crud_endpoint": 0.92, "ui_component": 0.03,
                              "validation_rule": 0.03, "test_write": 0.01,
                              "unknown": 0.01},
            "confidence": 0.92,
        },
        "complexity": {
            "score": 1,
            "probabilities": {"0": 0.1, "1": 0.7, "2": 0.15, "3": 0.05},
            "confidence": 0.85,
        },
        "needs_human_review": {"noul": 0.15},
    })


V2_FIELDS = ("decision_id", "input_hash", "question_set_hash", "policy_version")


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


class TestClassifyV2Routing:
    """Tarefa 1.3 — helper encapsula classify_task_v2."""

    def test_returns_all_versioned_fields(self):
        result = replay.classify_v2_routing(
            "Criar endpoint de usuarios", _transport=_fake_transport()
        )
        assert isinstance(result, dict)
        for key in ("type", "confidence", "reasoning", "routing", *V2_FIELDS):
            assert key in result, f"campo versionado ausente: {key}"

    def test_respects_transport_choice(self):
        result = replay.classify_v2_routing(
            "Criar endpoint de usuarios", _transport=_fake_transport()
        )
        assert result["type"] == "crud_endpoint"

    def test_raises_when_llc2_unavailable(self, monkeypatch):
        monkeypatch.setattr(replay, "classify_task_v2", None)
        with pytest.raises(RuntimeError):
            replay.classify_v2_routing("qualquer tarefa")


class TestAgentInvokeV2:
    """Tarefas 1.4/1.6/1.7 — fluxo sob LLC2_REPLAY."""

    def _run(self, monkeypatch, classification, *, script=None, flag="1"):
        events = []
        monkeypatch.setattr(replay, "_USE_LLC2_REPLAY", flag == "1")
        monkeypatch.setattr(replay, "log_replay_event",
                            lambda ev, sid=None, **kw: events.append({"event": ev, "script_id": sid, **kw}))
        if classification is None:
            monkeypatch.delattr(replay, "classify_v2_routing", raising=False)
        else:
            monkeypatch.setattr(replay, "classify_v2_routing",
                                lambda td, client=None, **kw: dict(classification))
        legacy_calls = []
        monkeypatch.setattr(replay, "classify_task",
                            lambda td, client=None: legacy_calls.append(td) or _v2_classification())
        monkeypatch.setattr(replay, "find_best_script",
                            lambda t, td: script)
        monkeypatch.setattr(replay, "_llm_invoke",
                            lambda prompt, client=None: ("llm", 0, None))
        if script is not None:
            monkeypatch.setattr(replay, "check_target_files_stale", lambda files: False)
            monkeypatch.setattr(replay, "get_architecture_version", lambda: "1.0")
            monkeypatch.setattr(replay, "is_red_zone", lambda p: False)
            monkeypatch.setattr(replay, "extract_files_from_script", lambda s: s.get("target_files", []))
            monkeypatch.setattr(replay, "preflight_all_steps", lambda s, ctx: True)
            monkeypatch.setattr(replay, "gate_check", lambda step, s: "approved")
            monkeypatch.setattr(replay, "deterministic_replay",
                                lambda s, ctx, gate, llm, prompt, client: ("replay", 0, None))
        replay.agent_invoke("prompt", task_description="Criar endpoint")
        return events, legacy_calls

    def test_v2_classification_is_used_and_logs_versioned_fields(self, monkeypatch):
        events, legacy_calls = self._run(monkeypatch, _v2_classification())

        assert legacy_calls == []                       # legado não é consultado
        classify = next(e for e in events if e["event"] == "classify")
        for key in V2_FIELDS:
            assert classify.get(key), f"classify sem {key}"

    def test_replay_hit_logs_versioned_fields_and_verifies_record(self, monkeypatch):
        script = {"id": "s1", "usage_count": 3, "target_files": ["app.py"],
                  "architecture_version": "1.0"}
        verifies = []
        monkeypatch.setattr(replay, "verify_replay_from_record",
                            lambda record, ih, **kw: verifies.append((record, ih)) or {"ok": True})
        events, _ = self._run(monkeypatch, _v2_classification(), script=script)

        hit = next(e for e in events if e["event"] == "replay_hit")
        for key in V2_FIELDS:
            assert hit.get(key), f"replay_hit sem {key}"
        assert verifies, "verify_replay_from_record não foi chamado"
        record, ih = verifies[0]
        assert ih == _v2_classification()["input_hash"]
        assert record.get("decision_id") == _v2_classification()["decision_id"]

    def test_exception_in_v2_falls_back_to_legacy_with_reason(self, monkeypatch):
        def boom(td, client=None, **kw):
            raise RuntimeError("llc2 explodiu")
        events, legacy_calls = self._run(monkeypatch, boom)

        assert legacy_calls == ["Criar endpoint"]        # legado assumiu
        assert any(e["event"] == "llm_fallback" and e.get("reason") == "llc2_replay_error"
                   for e in events)

    def test_flag_off_keeps_legacy_identical(self, monkeypatch):
        events, legacy_calls = self._run(monkeypatch, _v2_classification(), flag="0")

        assert legacy_calls == ["Criar endpoint"]        # caminho legado original
        assert not any(str(e.get("reason", "")).startswith("llc2_replay") for e in events)

    def test_human_required_under_v2_skips_cache(self, monkeypatch):
        classification = _v2_classification(routing="HUMAN_REQUIRED")
        events, _ = self._run(monkeypatch, classification)

        assert not any(e["event"] == "replay_hit" for e in events)
        assert any(e["event"] == "llm_fallback" and e.get("reason") == "human_required"
                   for e in events)
