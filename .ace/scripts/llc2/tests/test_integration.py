"""Testes de integração Fase 1: llc_classify + llc_harness/replay.

Garante que a interface externa dos módulos modificados continua válida.
"""
from __future__ import annotations

import pytest


# ── llc_classify.py ───────────────────────────────────────────────────────

class TestClassifyTaskInterface:
    """O classificador deve retornar dict com routing quando llc2 disponível."""

    def test_classify_task_returns_dict_with_routing(self, monkeypatch):
        """classify_task com llc2 ativo retorna dict nunca None."""
        from llc_classify import classify_task
        # Força modo llc2 (se disponível)
        monkeypatch.setenv("LLC2_CLASSIFY", "1")
        # Usa transport fake via classify_task_v2
        from llc2.jev_adapter import FakeJevTransport
        fake = FakeJevTransport({
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

        # classify_task não aceita _transport diretamente; precisamos
        # mockar internamente ou chamar classify_task_v2 direto
        from llc2.classifier import classify_task_v2
        result = classify_task_v2(
            "Criar endpoint de usuarios", client=None, _transport=fake,
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["type"] == "crud_endpoint"
        assert "routing" in result
        assert result["routing"] in ("AUTO", "REVIEW_REQUIRED", "HUMAN_REQUIRED")

    def test_classify_task_legacy_mode(self, monkeypatch):
        """LLC2_CLASSIFY=0 usa legado (pode retornar None ou levantar)."""
        monkeypatch.setenv("LLC2_CLASSIFY", "0")
        # Recarrega o módulo para pegar a flag desativada
        import importlib
        import llc_classify
        importlib.reload(llc_classify)

        # O legado não captura FileNotFoundError do subprocess
        with pytest.raises(FileNotFoundError):
            llc_classify.classify_task("Criar endpoint", client="__no_such_client__")


# ── llc_harness/replay.py ─────────────────────────────────────────────────

class TestReplayRoutingHandling:
    """O replay deve tratar routing HUMAN_REQUIRED e REVIEW_REQUIRED."""

    def test_replay_skips_when_human_required(self, monkeypatch):
        """routing=HUMAN_REQUIRED => não tenta replay, vai para fallback."""
        from llc_harness import replay

        classification = {
            "type": "crud_endpoint",
            "confidence": 0.95,
            "reasoning": "alta confiança",
            "routing": "HUMAN_REQUIRED",
        }

        # Simula que classify_task retornou o dict acima
        monkeypatch.setattr(
            replay, "classify_task", lambda td, client=None: classification,
        )
        # Mock de find_best_script para garantir que NÃO é chamado
        calls = []
        monkeypatch.setattr(
            replay, "find_best_script",
            lambda t, td: calls.append((t, td)) or None,
        )
        # Mock _llm_invoke para capturar o fallback
        llm_calls = []
        monkeypatch.setattr(
            replay, "_llm_invoke",
            lambda prompt, client=None: llm_calls.append(prompt) or ("ok", 0, None),
        )

        # Chama agent_invoke com task_description
        replay.agent_invoke("prompt", task_description="Criar endpoint")

        # find_best_script NÃO deve ser chamado quando routing=HUMAN_REQUIRED
        assert len(calls) == 0
        # _llm_invoke DEVE ser chamado (fallback)
        assert len(llm_calls) == 1

    def test_replay_uses_gate_when_review_required(self, monkeypatch):
        """routing=REVIEW_REQUIRED => tenta replay mas gate é obrigatório."""
        from llc_harness import replay
        from llc_steps import canonical_id

        classification = {
            "type": "crud_endpoint",
            "confidence": 0.60,
            "reasoning": "média confiança",
            "routing": "REVIEW_REQUIRED",
        }

        monkeypatch.setattr(
            replay, "classify_task", lambda td, client=None: classification,
        )

        # Mock find_best_script para retornar um script
        fake_script = {
            "id": "script-123",
            "usage_count": 5,
            "target_files": ["app.py"],
            "architecture_version": "1.0",
        }
        monkeypatch.setattr(
            replay, "find_best_script",
            lambda t, td: fake_script if t == "crud_endpoint" else None,
        )

        # Desativa checks que rejeitariam o replay
        monkeypatch.setattr(replay, "check_target_files_stale", lambda files: False)
        monkeypatch.setattr(replay, "get_architecture_version", lambda: "1.0")
        monkeypatch.setattr(replay, "is_red_zone", lambda p: False)
        monkeypatch.setattr(replay, "extract_files_from_script", lambda s: s.get("target_files", []))
        monkeypatch.setattr(replay, "preflight_all_steps", lambda s, ctx: True)

        # Mock gate_check — deve ser chamado porque REVIEW_REQUIRED ativa gate
        gate_calls = []
        monkeypatch.setattr(
            replay, "gate_check",
            lambda step, script: gate_calls.append((step, script)) or "approved",
        )

        # Mock deterministic_replay
        replay_calls = []
        monkeypatch.setattr(
            replay, "deterministic_replay",
            lambda script, ctx, gate, llm, prompt, client: replay_calls.append(script) or ("replay", 0, None),
        )

        # Mock _llm_invoke
        monkeypatch.setattr(
            replay, "_llm_invoke",
            lambda prompt, client=None: ("llm", 0, None),
        )

        replay.agent_invoke("prompt", task_description="Criar endpoint")

        # Gate deve ser chamado (porque REVIEW_REQUIRED ativa gate)
        assert len(gate_calls) >= 1
        # deterministic_replay deve ser chamado (gate aprovou)
        assert len(replay_calls) == 1
