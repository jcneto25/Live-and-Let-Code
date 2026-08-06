"""Testes para llc_wizard.app — RF-W1A.12 (WP4, FTDD).

SPEC WizardApp (estado initial — §6.1):
- WizardApp(project_root) monta layout com tres paineis:
    #sidebar (lista de steps), #context-panel, #output-panel
- run_test() (pilot textual) deve expor os IDs no DOM.

Testes headless: usam run_test() do pilot textual (sem terminal real).
"""
import asyncio
import json

import pytest

textual = pytest.importorskip("textual")


def _write_fake_index(tmp_path, steps):
    """Cria .ace com index.json e config/gates.json falsos p/ o app montar."""
    ace = tmp_path / ".ace"
    config = ace / "config"
    config.mkdir(parents=True)
    idx = {
        "specs": [],
        "steps": steps,
        "sessions": [{"id": 5, "status": "in_progress", "title": "Arquitetura"}],
    }
    (ace / "index.json").write_text(json.dumps(idx))
    (config / "gates.json").write_text(json.dumps({"gates": {"1": {"checklist": []}}}))
    return tmp_path


def test_wizardapp_mounts_three_panels(tmp_path):
    """SPEC 6.1 initial: #sidebar, #context-panel e #output-panel no DOM."""
    steps = [{"id": "1", "name": "Glossario", "status": "pending"}]
    root = _write_fake_index(tmp_path, steps)

    from llc_wizard.app import WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            assert pilot.app.query_one("#sidebar")
            assert pilot.app.query_one("#context-panel")
            assert pilot.app.query_one("#output-panel")

    asyncio.run(run())


def test_wizard_app_sidebar_lists_steps(tmp_path):
    """SPEC-1.1: sidebar lista os steps do index.json."""
    steps = [
        {"id": "1", "name": "Glossario", "status": "pending"},
        {"id": "2", "name": "RF", "status": "in_progress"},
    ]
    root = _write_fake_index(tmp_path, steps)

    from llc_wizard.app import WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            sidebar = pilot.app.query_one("#sidebar")
            assert str(sidebar.render())

    asyncio.run(run())


def test_wizard_app_shows_progress_count(tmp_path):
    """SPEC-1.1: barra de progresso mostra 'done/total' no estado inicial."""
    root = _write_fake_index(tmp_path, [])

    from llc_wizard.app import WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            progress = pilot.app.query_one("#progress-bar")
            label = progress.render() if hasattr(progress, "render") else str(progress)
            import re

            assert re.search(r"\d+/\d+", str(label))

    asyncio.run(run())


def test_sidebar_uses_status_icons(tmp_path):
    """WP4.2: sidebar renderiza icone por status do step."""
    root = _write_fake_index(tmp_path, [])

    from llc_wizard.app import STATUS_ICON, StepStatus, WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            sidebar = pilot.app.query_one("#sidebar")
            rendered = str(sidebar.render())
            assert STATUS_ICON[StepStatus.PENDING] in rendered

    asyncio.run(run())


def test_gate_checklist_renders_items(tmp_path):
    """SPEC 6.2: GateChecklist renderiza itens do gate com checkbox."""
    root = _write_fake_index(tmp_path, [])
    (root / ".ace" / "config" / "gates.json").write_text(json.dumps(
        {"gates": {"1": {"checklist": ["Verificar RF", "Revisar glossario"]}}}))

    from llc_wizard.app import GateChecklist

    checklist = GateChecklist("1", ["Verificar RF", "Revisar glossario"])
    rendered = str(checklist.render())
    assert "Verificar RF" in rendered
    assert "[ ]" in rendered


def test_gate_checklist_unchecked_disables_approve(tmp_path):
    """SPEC 6.2 unchecked_required: itens obrigatorios nao marcados bloqueiam Aprovar."""
    root = _write_fake_index(tmp_path, [])

    from llc_wizard.app import GateChecklist

    checklist = GateChecklist("1", ["Item obrigatorio"], required_all=True)
    assert checklist.can_approve() is False


def test_gate_checklist_all_checked_enables_approve():
    """SPEC 6.2 all_required_checked: todos obrigatorios marcados habilitam Aprovar."""
    from llc_wizard.app import GateChecklist

    checklist = GateChecklist("1", ["Item obrigatorio"], required_all=True)
    checklist.toggle(0)
    assert checklist.can_approve() is True


def test_approve_gate_advances_step(tmp_path):
    """SPEC 6.1 gate_approved: Aprovar avanca o step (gate passa)."""
    root = _write_fake_index(tmp_path, [])

    from llc_wizard.app import WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            before = pilot.app._gate_approved
            pilot.app.approve_gate("5")
            assert pilot.app._gate_approved is True
            assert pilot.app._gate_approved != before

    asyncio.run(run())


def test_reject_gate_stacks_failure_screen(tmp_path):
    """SPEC 6.1 gate_rejected: Rejeitar empilha FailureRecoveryScreen."""
    root = _write_fake_index(tmp_path, [])

    from llc_wizard.app import WizardApp

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            pilot.app.reject_gate("5")
            assert pilot.app._screen_stack[-1] == "FailureRecoveryScreen"

    asyncio.run(run())


def test_wizard_cli_help_shows_flags():
    """RF-W1A.13: 'llc wizard --help' exit 0 e flags --from e --auto-approve."""
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["wizard", "--help"])
    assert result.exit_code == 0
    assert "--from" in result.output
    assert "--auto-approve" in result.output


def test_wizard_cli_without_textual_asks_to_install(monkeypatch):
    """RF-W1A.14: sem Textual exibe 'pip install textual'."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "textual":
            raise ImportError("No module named 'textual'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["wizard"])
    assert "pip install textual" in result.output


def test_wizard_cli_uses_fallback_prompt_when_no_agent(monkeypatch, tmp_path):
    """RF-W1A.14: fallback (sem Textual + sem agente) gera prompt copy-paste."""
    import builtins
    import shutil

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "textual":
            raise ImportError("No module named 'textual'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    from click.testing import CliRunner
    from llc.cli import cli

    root = tmp_path
    (root / ".ace").mkdir()
    runner = CliRunner()
    result = runner.invoke(cli, ["wizard", "--project-root", str(root)])
    assert "llc run" in result.output or "copie" in result.output


def test_wizard_does_not_write_to_sessions_dir():
    """RF-W1A.15: nenhum open('w') em llc_wizard/ aponta para .ace/sessions/."""
    import ast
    from pathlib import Path

    wizard_dir = Path(__file__).resolve().parent.parent
    violations = []
    for src in (wizard_dir).rglob("*.py"):
        if "tests" in src.parts:
            continue
        tree = ast.parse(src.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "open":
                    args = [a for a in node.args]
                    if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                        mode_args = [k.value for k in node.keywords if k.arg == "mode"]
                        mode = mode_args[0] if mode_args else ""
                        if "w" in mode and "sessions" in args[0].value:
                            violations.append((str(src), args[0].value))
                if isinstance(func, ast.Attribute):
                    if func.attr in ("write_text", "write") and isinstance(node.func.value, ast.Call):
                        pass

    # Checagem adicional: caminho contendo 'sessions' nunca em write_text/open 'w'
    import re

    for src in wizard_dir.rglob("*.py"):
        if "tests" in src.parts:
            continue
        content = src.read_text(encoding="utf-8")
        if re.search(r"(open\s*\(\s*['\"][^'\"]*sessions|write_text\s*\(\s*['\"][^'\"]*sessions)",
                     content):
            violations.append(str(src))

    assert not violations, f"Escrita em sessions/ detectada: {violations}"

# ─────────────────────── PRP-WIZARD-1B: HITL Widgets ───────────────────────


def test_decision_modal_renders_prompt_and_accepts_response():
    """RF-W1B.6: DecisionModal renderiza prompt e aceita resposta."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector
    from llc_wizard.widgets.decision_modal import DecisionModal

    collector = RealtimePromptCollector()
    prompt = PromptRequest(prompt_id="q-1", text="Qual escopo?", step_id="5")
    modal = DecisionModal(prompt=prompt, collector=collector)

    rendered = modal.render()
    assert "Qual escopo?" in rendered

    modal.set_response("Apenas steps 1-5")
    modal.confirm()
    assert collector.pending_prompts == []  # prompt respondido/liberado


def test_decision_modal_shows_options():
    """RF-W1B.6: modal exibe opções quando o prompt as define."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector
    from llc_wizard.widgets.decision_modal import DecisionModal

    collector = RealtimePromptCollector()
    prompt = PromptRequest(
        prompt_id="q-2", text="Metodo de deploy?", step_id="3",
        options=["docker", "kubernetes", "bare-metal"],
    )
    modal = DecisionModal(prompt=prompt, collector=collector)
    rendered = modal.render()
    for opt in ("docker", "kubernetes", "bare-metal"):
        assert opt in rendered


def test_prompt_widget_lists_pending_prompts():
    """RF: prompt_widgets renderiza prompts pendentes do collector."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector
    from llc_wizard.widgets.prompt_widgets import PendingPromptsWidget

    collector = RealtimePromptCollector()
    import asyncio

    async def run():
        asyncio.create_task(collector.request_input(
            PromptRequest(prompt_id="p1", text="Pergunta A", step_id="5")))
        asyncio.create_task(collector.request_input(
            PromptRequest(prompt_id="p2", text="Pergunta B", step_id="6")))
        await asyncio.sleep(0.02)
        widget = PendingPromptsWidget(collector)
        rendered = str(widget.render())
        assert "Pergunta A" in rendered
        assert "Pergunta B" in rendered

    asyncio.run(run())


def test_wizard_app_routes_prompt_during_step_execution(tmp_path):
    """RF-W1B (integração): WizardApp roteia prompt HITL durante execução do step."""
    from llc_wizard.decisions import PromptRequest
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            prompt = PromptRequest(prompt_id="q-5", text="Pergunta do step 5",
                                   step_id="5")
            # coletor registra o prompt (task em background)
            task = asyncio.create_task(app.collector.request_input(prompt))
            await asyncio.sleep(0.02)
            # app abre modal para o prompt pendente e roteia a resposta
            modal = app.open_prompt_modal(app.collector.pending_prompts[0])
            rendered = modal.render()
            assert "Pergunta do step 5" in rendered
            modal.set_response("respondido")
            modal.confirm()
            result = await task
            assert result == "respondido"

    asyncio.run(run())


def test_wizard_app_executes_step_with_hitl(tmp_path):
    """RF-W1B (integração): run_step_with_hitl captura output e completa o step."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    from llc_wizard.runner import CompletionEvent, OutputEvent

    class FakeRunner:
        async def run_step(self):
            yield OutputEvent(text="step 5 iniciado")
            yield CompletionEvent(step_id="5", success=True, output="ok")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            events = [ev async for ev in app.run_step_with_hitl("5", "tarefa",
                                                                runner=FakeRunner())]
            has_output = any(isinstance(e, OutputEvent) for e in events)
            has_done = any(isinstance(e, CompletionEvent) and e.success
                           for e in events)
            assert has_output and has_done

    asyncio.run(run())
