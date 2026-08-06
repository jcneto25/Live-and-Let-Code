#!/usr/bin/env python3
"""R7 (GOV-002 Decisão item 2 / GOV-003): sessões-placeholder proibidas.

session_start (harness) e initialize_session devem falhar explicitamente
pedindo --task real em vez de criar sessão com task manufaturada
("Step N" literal) — padrão exato das sessões órfãs GOV-002:
task_context="Step 0.5" + project="" + zero actions + in_progress eterno.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from initialize_session.session import is_placeholder_task
from llc_harness import session as harness_session


class TestIsPlaceholderTask:
    @pytest.mark.parametrize("task", ["Step 0.5", "Step 11", "Step 11.4",
                                      "", "   ", None,
                                      # GOV-002 reincidência 3.3 (2026-08-06):
                                      # "tarefa"/"task"/"smoke" passaram pelo sentinel
                                      # antigo (só pegava "Step N"). Endurecer:
                                      "tarefa", "Tarefa", "task", "TODO",
                                      "smoke", "placeholder", "x", "tbd"])
    def test_placeholders_detected(self, task):
        assert is_placeholder_task(task)

    @pytest.mark.parametrize("task", [
        "Auditoria factory-evolution: GOV-003",
        "Implementar Step 5 do pipeline",   # contém "Step", mas não é o sentinel
        "step 0.5 greenfield",               # case diferente não é o padrão f"Step {step}"
        "Step",                              # sem número — não é o padrão manufaturado
        "Implementar autenticação de usuários",  # descritivo: não é placeholder
        "Refatorar módulo de pagamentos",
        "task runner do pipeline",           # contém "task" mas é descritivo
    ])
    def test_real_tasks_accepted(self, task):
        assert not is_placeholder_task(task)


class TestHarnessSessionStartGuard:
    def test_refuses_missing_task(self, monkeypatch, capsys):
        called = []
        monkeypatch.setattr(subprocess, "run",
                            lambda *a, **k: called.append((a, k)))
        with pytest.raises(SystemExit) as exc:
            harness_session.session_start("0.5", task=None)
        assert exc.value.code != 0
        assert called == []  # não chega a invocar initialize_session
        assert "--task" in capsys.readouterr().out

    def test_refuses_placeholder_task(self, monkeypatch):
        def _boom(*a, **k):
            raise AssertionError("não deveria invocar initialize_session")
        monkeypatch.setattr(subprocess, "run", _boom)
        with pytest.raises(SystemExit):
            harness_session.session_start("0.5", task="Step 0.5")

    def test_accepts_real_task(self, monkeypatch):
        class R:
            returncode = 0
            stdout = json.dumps({"session_id": "2026-08-05-099",
                                 "context_seed": "", "worktree": None})
            stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
        out = harness_session.session_start("0.5", task="Tarefa real de teste")
        assert out["session_id"] == "2026-08-05-099"


class TestInitializeSessionCliGuard:
    def test_main_rejects_placeholder(self, monkeypatch, capsys):
        from initialize_session import cli as init_cli
        monkeypatch.setattr(sys, "argv",
                            ["initialize_session.py", "--step", "0.5",
                             "--task", "Step 0.5", "--json"])
        with pytest.raises(SystemExit) as exc:
            init_cli.main()
        assert exc.value.code != 0
        err = capsys.readouterr().err
        assert "--task" in err or "placeholder" in err.lower()

    def test_main_rejects_whitespace_task(self, monkeypatch):
        from initialize_session import cli as init_cli
        monkeypatch.setattr(sys, "argv",
                            ["initialize_session.py", "--step", "0.5",
                             "--task", "   ", "--json"])
        with pytest.raises(SystemExit):
            init_cli.main()
