"""Fase 5 (R-6) — wiring de capabilities no pipeline.

- 5.2: perfil por cliente detectado sob LLC2_APPLY_CAPABILITY_PROFILE=1;
- 5.3: detecção post-hoc após o agente (warn-only, nunca bloqueia).
"""
from __future__ import annotations

import json
from pathlib import Path

from llc_harness import pipeline as pipeline_mod


def _run_step(monkeypatch, tmp_path, **env):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLC2_STATECHART", "1")
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        pipeline_mod, "session_start",
        lambda *a, **k: {"session_id": "s-1", "context_seed": "seed"})
    monkeypatch.setattr(
        pipeline_mod, "skill_load", lambda *a, **k: ("sk.md", "prompt"))
    monkeypatch.setattr(
        pipeline_mod, "agent_invoke", lambda *a, **k: ("out", 0, None))
    return pipeline_mod.step_run("5", task="tarefa teste")


class TestApplyCapabilityProfile:
    """5.2 — gera perfil para o cliente detectado (opt-in)."""

    def test_writes_profile_for_detected_client(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            pipeline_mod, "detect_agent_client", lambda: "opencode")
        assert _run_step(monkeypatch, tmp_path,
                         LLC2_APPLY_CAPABILITY_PROFILE="1") == "s-1"
        path = tmp_path / ".llc2" / "permissions" / "opencode.json"
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["client"] == "opencode"
        assert payload["allowed"]

    def test_no_profile_when_flag_off(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            pipeline_mod, "detect_agent_client", lambda: "opencode")
        _run_step(monkeypatch, tmp_path, LLC2_APPLY_CAPABILITY_PROFILE="0")
        assert not (tmp_path / ".llc2").exists()

    def test_no_profile_by_default(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            pipeline_mod, "detect_agent_client", lambda: "opencode")
        _run_step(monkeypatch, tmp_path, LLC2_APPLY_CAPABILITY_PROFILE=None)
        assert not (tmp_path / ".llc2").exists()

    def test_unknown_client_falls_back_gracefully(self, monkeypatch, tmp_path):
        monkeypatch.setattr(pipeline_mod, "detect_agent_client", lambda: None)
        _run_step(monkeypatch, tmp_path, LLC2_APPLY_CAPABILITY_PROFILE="1")
        path = tmp_path / ".llc2" / "permissions" / "generic.json"
        assert path.exists()

    def test_missing_llc2_degrades_gracefully(self, monkeypatch, tmp_path):
        monkeypatch.setattr(pipeline_mod, "detect_agent_client",
                            lambda: "opencode")
        monkeypatch.setattr(pipeline_mod, "generate_permission_profile", None)
        assert _run_step(monkeypatch, tmp_path,
                         LLC2_APPLY_CAPABILITY_PROFILE="1") == "s-1"


class TestPostHocDetection:
    """5.3 — detecção pós-agente roda sempre, sem bloquear."""

    def test_red_zone_write_warns_but_completes(
            self, monkeypatch, tmp_path, capsys):
        calls = iter([[], ["src/auth/guard.ts"]])
        monkeypatch.setattr(
            pipeline_mod, "_git_modified_files", lambda: next(calls))
        assert _run_step(monkeypatch, tmp_path) == "s-1"
        assert "guard.ts" in capsys.readouterr().out

    def test_preexisting_dirt_does_not_warn(
            self, monkeypatch, tmp_path, capsys):
        """Sujeira pré-agente não é atribuída ao agente (snapshot antes)."""
        calls = iter([["src/auth/guard.ts"], ["src/auth/guard.ts"]])
        monkeypatch.setattr(
            pipeline_mod, "_git_modified_files", lambda: next(calls))
        _run_step(monkeypatch, tmp_path)
        assert "Post-hoc" not in capsys.readouterr().out

    def test_clean_diff_is_silent(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(pipeline_mod, "_git_modified_files", lambda: [])
        _run_step(monkeypatch, tmp_path)
        assert "Post-hoc" not in capsys.readouterr().out

    def test_git_failure_never_blocks(self, monkeypatch, tmp_path):
        def boom():
            raise OSError("sem git")
        monkeypatch.setattr(pipeline_mod, "_git_modified_files", boom)
        assert _run_step(monkeypatch, tmp_path) == "s-1"

    def test_git_unavailable_warns_in_repo(self, monkeypatch, tmp_path, capsys):
        """None (não verificado) avisa com .git presente; sem .git, silêncio."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setattr(pipeline_mod, "_git_modified_files",
                            lambda: None)
        _run_step(monkeypatch, tmp_path)
        assert "indisponível" in capsys.readouterr().out
