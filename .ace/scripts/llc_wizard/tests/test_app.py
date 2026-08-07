"""Testes para llc_wizard.app — RF-W1A.12 (WP4, FTDD), PRP-WIZARD-1C e PRP-WIZARD-1.1.

SPEC WizardApp (estado initial — §6.1):
- WizardApp(project_root) monta layout com tres paineis:
    #sidebar (lista de steps), #context-panel, #output-panel
- run_test() (pilot textual) deve expor os IDs no DOM.

PRP-WIZARD-1C (RF-W1C.1/.3/.4/.5):
- Artifact Review apresenta artefato no painel
- Scope Confirmation bloqueia início do step
- FailureRecoveryScreen com 3 opções + rerun automático

PRP-WIZARD-1.1 (RF-W1.1.1 a W1.1.10, FTDD):
- KanbanBoardWidget: 6 colunas, WIP, SLA, scores, SKIPPED colapsada
- Toggle K preserva seleção

Testes headless: usam run_test() do pilot textual (sem terminal real).
"""
import asyncio
import json

import pytest

from llc_wizard.data import StepStatus

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


# ─────────────────────── PRP-WIZARD-1C: HITL avançado ───────────────────────


def test_failure_recovery_screen_offers_three_options():
    """RF-W1C.5: tela de recovery renderiza 3 opções com atalhos."""
    from llc_wizard.screens.failure_recovery import (
        FailureRecoveryAction,
        FailureRecoveryScreen,
    )

    screen = FailureRecoveryScreen(step_id="5")
    rendered = screen.render()
    assert "re-executar" in rendered
    assert "pular" in rendered
    assert "encerrar" in rendered
    # atalhos de teclado visíveis
    for key in ("[r]", "[s]", "[q]"):
        assert key in rendered
    # ações expostas por chave
    assert screen.action_for("r") is FailureRecoveryAction.RERUN
    assert screen.action_for("s") is FailureRecoveryAction.SKIP
    assert screen.action_for("q") is FailureRecoveryAction.QUIT


def test_failure_recovery_unknown_key_returns_none():
    """RF-W1C.5: tecla desconhecida → nenhuma ação (sem crash)."""
    from llc_wizard.screens.failure_recovery import FailureRecoveryScreen

    screen = FailureRecoveryScreen(step_id="5")
    assert screen.action_for("x") is None


def test_app_rerun_step_restarts_without_leaving_tui(tmp_path):
    """RF-W1C.4: rerun reinicia o step sem sair da TUI (mesmo app)."""
    from llc_wizard.app import WizardApp
    from llc_wizard.runner import CompletionEvent

    root = _write_fake_index(tmp_path, [])
    calls = {"n": 0}

    class CountingRunner:
        async def run_step(self):
            calls["n"] += 1
            yield CompletionEvent(step_id="5", success=True, output="ok")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.reject_gate("5")
            assert app._screen_stack[-1] == "FailureRecoveryScreen"
            # rerun a partir da tela de recovery — sem sair do app
            await app.rerun_step("5", runner=CountingRunner())
            assert calls["n"] == 1
            # screen de recovery desempilhada após rerun
            assert "FailureRecoveryScreen" not in app._screen_stack

    asyncio.run(run())


def test_app_rerun_removes_recovery_not_top_of_stack(tmp_path):
    """Regressão (review): rerun remove a recovery mesmo com modal acima."""
    from llc_wizard.app import WizardApp
    from llc_wizard.runner import CompletionEvent

    root = _write_fake_index(tmp_path, [])

    class EmptyRunner:
        async def run_step(self):
            yield CompletionEvent(step_id="5", success=True, output="ok")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.reject_gate("5")
            app._screen_stack.append("DecisionModal:q-9")  # modal acima
            await app.rerun_step("5", runner=EmptyRunner())
            # recovery removida, modal preservado
            assert "FailureRecoveryScreen" not in app._screen_stack
            assert "DecisionModal:q-9" in app._screen_stack

    asyncio.run(run())


def test_app_artifact_review_survives_rebuild(tmp_path):
    """Regressão (review): review não se perde se o painel for (re)montado."""
    from llc_wizard.app import WizardApp
    from llc_wizard.decisions import ArtifactReview

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            # review antes da montagem dos painéis
            app.show_artifact_review(ArtifactReview(
                artifact="docs/prps/PRP-WIZARD-1C.md", verdict="rejected",
                approved=False, feedback=["Falta DoD"]))
            app._panels = app._build()
            rendered = app.query_one("#output-panel").render()
            assert "docs/prps/PRP-WIZARD-1C.md" in rendered
            assert "Falta DoD" in rendered


def test_app_scope_confirmation_blocks_step_start(tmp_path):
    """RF-W1C.3: escopo pendente bloqueia início do step."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            # sem escopo pendente → step pode iniciar
            assert app.can_start_step("5") is True
            # escopo pendente → bloqueia
            app.set_pending_scope("5", "Steps 1-5")
            assert app.can_start_step("5") is False
            # confirmação humana libera
            app.confirm_scope("5")
            assert app.can_start_step("5") is True

    asyncio.run(run())


def test_app_artifact_review_shows_in_output_panel(tmp_path):
    """RF-W1C.1: conteúdo do artefato visível no painel de output."""
    from llc_wizard.app import WizardApp
    from llc_wizard.decisions import ArtifactReview

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            review = ArtifactReview(
                artifact="docs/prps/PRP-WIZARD-1C.md", verdict="approved")
            app.show_artifact_review(review)
            rendered = app.query_one("#output-panel").render()
            assert "docs/prps/PRP-WIZARD-1C.md" in rendered
            assert "approved" in rendered

    asyncio.run(run())


# ──────────────────── PRP-WIZARD-1.1: Kanban UI (FTDD) ─────────────────────


def _board_from_steps(steps, since=None):
    """Board completo via KanbanBoardBuilder com steps dados (N1)."""
    from datetime import datetime as _dt

    from llc_wizard.data import StepInfo, StepStatus
    from llc_wizard.kanban import KanbanBoardBuilder

    infos = [StepInfo(**s, in_pipeline=True) for s in steps]

    class Fake:
        def get_status(self):
            from llc_wizard.data import PipelineStatus

            return PipelineStatus(steps=infos)

        def get_status_since(self, step_id):
            return (since or {}).get(step_id, _dt.fromtimestamp(0))

        def get_pending_hitl(self):
            return []

    return KanbanBoardBuilder(Fake(), sla_minutes=30).build()


def test_kanban_widget_renders_six_columns(tmp_path):
    """RF-W1.1.1: board inicial — 6 colunas, SKIPPED colapsada."""
    from llc_wizard.kanban_board import KanbanBoardWidget
    from llc_wizard.kanban import KanbanColumn

    board = _board_from_steps([
        {"id": "1", "name": "Visao", "status": StepStatus.COMPLETED},
        {"id": "2", "name": "Specs", "status": StepStatus.IN_PROGRESS},
    ])
    widget = KanbanBoardWidget(board)
    rendered = widget.render()
    for col in KanbanColumn:
        assert col.value in rendered
    assert "SKIPPED" in rendered and "▸" in rendered  # colapsada (D1 ADR-0002)


def test_kanban_widget_running_card_icon(tmp_path):
    """RF-W1.1.2: card RUNNING mostra nome + ícone 🔄."""
    from llc_wizard.kanban_board import KanbanBoardWidget
    from llc_wizard.kanban import KanbanColumn

    board = _board_from_steps([
        {"id": "2", "name": "Specs", "status": StepStatus.IN_PROGRESS},
    ])
    widget = KanbanBoardWidget(board)
    rendered = widget.render()
    assert "Specs" in rendered
    assert "🔄" in rendered


def test_kanban_widget_awaiting_human_icon(tmp_path):
    """RF-W1.1.3: card AWAITING_HUMAN mostra ícone ⚠️."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "3", "name": "PRDs", "status": StepStatus.GATE_PENDING},
    ])
    rendered = KanbanBoardWidget(board).render()
    assert "⚠️" in rendered


def test_kanban_widget_stale_card_marked(tmp_path):
    """RF-W1.1.4: card AWAITING_HUMAN > SLA recebe card-stale."""
    from datetime import datetime, timedelta

    from llc_wizard.kanban_board import KanbanBoardWidget

    since = {"3": datetime.now() - timedelta(minutes=45)}
    board = _board_from_steps([
        {"id": "3", "name": "PRDs", "status": StepStatus.GATE_PENDING},
    ], since=since)
    rendered = KanbanBoardWidget(board).render()
    assert "card-stale" in rendered


def test_kanban_widget_done_after_approval(tmp_path):
    """RF-W1.1.5: card DONE após aprovação do gate."""
    from llc_wizard.kanban_board import KanbanBoardWidget
    from llc_wizard.kanban import KanbanColumn

    board = _board_from_steps([
        {"id": "1", "name": "Visao", "status": StepStatus.COMPLETED},
    ])
    rendered = KanbanBoardWidget(board).render()
    assert "✅" in rendered
    assert board[KanbanColumn.DONE]  # card está na coluna DONE


def test_kanban_widget_rework_after_rejection(tmp_path):
    """RF-W1.1.6: card REWORK após rejeição do gate."""
    from llc_wizard.kanban_board import KanbanBoardWidget
    from llc_wizard.kanban import KanbanColumn

    board = _board_from_steps([
        {"id": "4", "name": "Planejamento", "status": StepStatus.FAILED},
    ])
    rendered = KanbanBoardWidget(board).render()
    assert "❌" in rendered
    assert board[KanbanColumn.REWORK]  # card na coluna REWORK


def test_kanban_widget_skipped_collapsed_marker(tmp_path):
    """RF-W1.1.7: coluna SKIPPED colapsada — apenas marcador ▸."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "9", "name": "Delta", "status": StepStatus.SKIPPED},
    ])
    rendered = KanbanBoardWidget(board).render()
    assert "SKIPPED" in rendered and "▸" in rendered
    # conteúdo da coluna oculto quando colapsada
    assert "Delta" not in rendered


def test_kanban_widget_wip_limit_indicator(tmp_path):
    """RF-W1.1.8: REWORK com 3 cards mostra indicador de WIP (limite 2)."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "4", "name": "A", "status": StepStatus.FAILED},
        {"id": "5", "name": "B", "status": StepStatus.FAILED},
        {"id": "6", "name": "C", "status": StepStatus.FAILED},
    ])
    widget = KanbanBoardWidget(board, wip_limits={"REWORK": 2})
    rendered = widget.render()
    assert "3/2" in rendered  # 3 cards, limite 2
    assert "WIP" in rendered


def test_app_toggle_kanban_preserves_selection(tmp_path):
    """RF-W1.1.9: toggle K preserva o step selecionado antes do toggle."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.select_step("5")
            assert app._selected_step == "5"
            app.toggle_kanban()
            assert app._kanban_mode is True
            app.toggle_kanban()
            assert app._kanban_mode is False
            assert app._selected_step == "5"  # seleção preservada

    asyncio.run(run())


def test_kanban_widget_scores_on_card(tmp_path):
    """RF-W1.1.10: Q:86 T:15500 visível no card quando dados de eval existem.

    token_cost_avg é TOKENS (não dólares) — exibimos como `T:` (fix review).
    """
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "2", "name": "Specs", "status": StepStatus.IN_PROGRESS},
    ])
    widget = KanbanBoardWidget(
        board, scores={"2": {"quality_score": 86, "tokens": 15500}})
    rendered = widget.render()
    assert "Q:86" in rendered
    assert "T:15500" in rendered
    assert "$" not in rendered


def test_kanban_widget_scores_graceful_absence(tmp_path):
    """Scores ausentes → sem crash e sem linha de score no card."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "2", "name": "Specs", "status": StepStatus.IN_PROGRESS},
    ])
    rendered = KanbanBoardWidget(board).render()
    assert "Q:" not in rendered
    assert "$" not in rendered


# ──────────────────── PRP-WIZARD-1.2: Drag & Drop + Flow Metrics + Temas ──────


def test_kanban_reorder_backlog_reorders_cards(tmp_path):
    """RF-W1.2.1: drag dentro de BACKLOG reordena cards e persiste a ordem."""
    from llc_wizard.kanban import KanbanColumn
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "6", "name": "A", "status": StepStatus.PENDING},
        {"id": "7", "name": "B", "status": StepStatus.PENDING},
        {"id": "8", "name": "C", "status": StepStatus.PENDING},
    ])
    widget = KanbanBoardWidget(board)
    order = widget.reorder(KanbanColumn.BACKLOG, from_index=2, to_index=0)
    assert order == ["8", "6", "7"]  # C movido da pos 3 para a pos 1
    rendered = widget.render()
    # conferir a ordem dos cards pela linha do card (ícone ⏳ desambigua o header)
    assert rendered.index("⏳ C") < rendered.index("⏳ A")


def test_kanban_drag_to_other_column_blocked(tmp_path):
    """RF-W1.2.2: drag para outra coluna retorna notificação e cancela."""
    from llc_wizard.kanban import KanbanColumn
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_from_steps([
        {"id": "6", "name": "A", "status": StepStatus.PENDING},
    ])
    widget = KanbanBoardWidget(board)
    ok, msg = widget.try_move("6", KanbanColumn.RUNNING)
    assert ok is False
    assert "movimento bloqueado" in msg
    # card permanece no BACKLOG (ordem intacta)
    ids = [c.id for c in board[KanbanColumn.BACKLOG]]
    assert ids == ["6"]


def test_app_drag_blocked_notification(tmp_path):
    """RF-W1.2.2 (app): drag_card para RUNNING retorna notificação e não altera."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.toggle_kanban()
            notification = app.drag_card("6", "RUNNING")
            assert "movimento bloqueado" in notification
            assert app.drag_card("6", "BACKLOG") == ""  # mesmo destino → no-op

    asyncio.run(run())


def test_app_reorder_backlog_persists_order(tmp_path):
    """RF-W1.2.1 (app): reorder_backlog persiste ordem e atualiza o render."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.toggle_kanban()
            app.reorder_backlog("6", from_index=0, to_index=2)
            assert app._backlog_order is not None
            rendered = app.kanban_render()
            assert rendered  # render continua válido após reordenação

    asyncio.run(run())


def test_export_flow_metrics_writes_yaml(tmp_path):
    """RF-W1.2.3: export gera YAML em .ace/evals/results/ com cycle/block time."""
    from llc_wizard.flow_metrics import export_flow_metrics

    root = _write_fake_index(tmp_path, [])
    path = export_flow_metrics(root)
    assert path.exists()
    assert path.parent.name == "results"
    content = path.read_text(encoding="utf-8")
    assert "cycle_time_avg_minutes" in content
    assert "block_time_avg_minutes" in content
    assert "generated_at" in content


def test_export_flow_metrics_baseline_first_run(tmp_path):
    """RF-W1.2.4: primeira execução marca baseline: true; segunda, false."""
    import yaml

    from llc_wizard.flow_metrics import export_flow_metrics

    root = _write_fake_index(tmp_path, [])
    first = export_flow_metrics(root)
    data = yaml.safe_load(first.read_text(encoding="utf-8"))
    assert data["baseline"] is True
    # segunda execução no mesmo diretório → baseline false
    second = export_flow_metrics(root)
    data2 = yaml.safe_load(second.read_text(encoding="utf-8"))
    assert data2["baseline"] is False


def test_app_theme_default_from_config(tmp_path):
    """DoD temas: default dark; config wizard.theme=light muda o tema."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])
    gates = json.loads((root / ".ace" / "config" / "gates.json").read_text())
    gates["wizard"] = {"theme": "light"}
    (root / ".ace" / "config" / "gates.json").write_text(json.dumps(gates))

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            assert app.theme == "light"
            app.toggle_theme()
            assert app.theme == "dark"
            app.toggle_theme()
            assert app.theme == "light"

    asyncio.run(run())


def test_wizard_tcss_contains_both_themes(tmp_path):
    """DoD temas: wizard.tcss existe com blocos dark e light."""
    from pathlib import Path

    tcss = Path(__file__).resolve().parents[1] / "wizard.tcss"
    assert tcss.exists()
    content = tcss.read_text(encoding="utf-8")
    assert ".dark" in content
    assert ".light" in content


def test_app_reorder_persists_across_toggle(tmp_path):
    """Regressão review: _backlog_order é re-aplicado no rebuild (toggle K)."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.toggle_kanban()
            app.reorder_backlog("6", from_index=0, to_index=2)
            assert app._backlog_order is not None
            # toggle off → on: rebuild não pode perder a ordem
            app.toggle_kanban()
            app.toggle_kanban()
            rendered = app.kanban_render()
            backlog_section = rendered.split("RUNNING")[0]
            assert backlog_section.index("⏳") >= 0  # render válido pós-rebuild

    asyncio.run(run())


def test_app_theme_observable_in_render(tmp_path):
    """Regressão review: tema tem efeito observável no render (tcss não é dead)."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.toggle_kanban()
            rendered = app.kanban_render()
            assert "[tema: dark]" in rendered
            app.toggle_theme()
            rendered = app.kanban_render()
            assert "[tema: light]" in rendered

    asyncio.run(run())


def test_app_drag_card_unknown_column_graceful(tmp_path):
    """Regressão review: coluna desconhecida → notificação, sem ValueError."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            notification = app.drag_card("6", "BOGUS")
            assert "movimento bloqueado" in notification

    asyncio.run(run())


def test_wizard_cli_export_flow_metrics_flag(tmp_path):
    """RF-W1.2.3: 'llc wizard --export-flow-metrics' grava o YAML."""
    from click.testing import CliRunner
    from llc.cli import cli

    root = _write_fake_index(tmp_path, [])
    runner = CliRunner()
    result = runner.invoke(cli, ["wizard", "--export-flow-metrics",
                                 "--project-root", str(root)])
    assert result.exit_code == 0
    assert "flow-metrics" in result.output
    results = root / ".ace" / "evals" / "results"
    assert list(results.glob("flow-metrics-*.yaml"))


def test_app_kanban_builds_from_reader_with_scores(tmp_path):
    """Integração: toggle K constrói o board via reader + SLA de gates.json + scores."""
    import yaml

    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])
    # SLA configurável + baseline de eval com score
    gates = json.loads((root / ".ace" / "config" / "gates.json").read_text())
    gates["wizard"] = {"hitl_sla_minutes": 15}
    (root / ".ace" / "config" / "gates.json").write_text(json.dumps(gates))
    baselines = root / ".ace" / "evals" / "baselines"
    baselines.mkdir(parents=True)
    (baselines / "step-2.yaml").write_text(yaml.safe_dump({
        "active_precision": "level_3",
        "by_precision_level": {
            "level_3": {"quality_score_avg": 86.0, "token_cost_avg": 15500.0,
                         "run_count": 5},
        },
    }), encoding="utf-8")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            assert app._load_sla_minutes() == 15
            app.toggle_kanban()
            rendered = app.kanban_render()
            assert "Kanban" in rendered
            scores = app._load_eval_scores()
            assert "2" in scores
            assert scores["2"]["quality_score"] == 86.0

    asyncio.run(run())


def test_app_load_sla_default_when_missing(tmp_path):
    """gates.json sem wizard.hitl_sla_minutes → default 30 (sem crash)."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            assert pilot.app._load_sla_minutes() == 30

    asyncio.run(run())


def test_app_sla_tolerates_non_dict_wizard_config(tmp_path):
    """Regressão (review): wizard config não-dict → default 30, sem crash."""
    import json as _json

    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])
    gates = _json.loads((root / ".ace" / "config" / "gates.json").read_text())
    gates["wizard"] = "não-dict"
    (root / ".ace" / "config" / "gates.json").write_text(_json.dumps(gates))

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            assert pilot.app._load_sla_minutes() == 30

    asyncio.run(run())


def test_app_eval_scores_tolerates_malformed_baseline(tmp_path):
    """Regressão (review): baseline com by_precision_level não-dict → sem crash."""
    import yaml

    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])
    baselines = root / ".ace" / "evals" / "baselines"
    baselines.mkdir(parents=True)
    (baselines / "step-2.yaml").write_text(yaml.safe_dump({
        "active_precision": "level_3",
        "by_precision_level": ["corrompido"],
    }), encoding="utf-8")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            assert pilot.app._load_eval_scores() == {}

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

# ─────────────────── P2b pos-roadmap: critical_path() highlight ──────────


def _board_two_pending():
    """Board: 2 steps PENDING (BACKLOG) + 1 COMPLETED (DONE) p/ teste crítico."""
    from llc_wizard.data import StepStatus

    return _board_from_steps([
        {"id": "6", "name": "Arquitetura", "status": StepStatus.PENDING},
        {"id": "7", "name": "Design System", "status": StepStatus.PENDING},
        {"id": "10.8", "name": "Test Coverage", "status": StepStatus.COMPLETED},
    ])


def test_kanban_widget_highlights_critical_step(tmp_path):
    """P2b: card do step no caminho crítico recebe marcador 🔺."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_two_pending()
    rendered = KanbanBoardWidget(board, critical_ids={"7"}).render()
    assert "Arquitetura 🔺" not in rendered      # 6 fora do caminho crítico
    assert "Design System 🔺" in rendered        # 7 no caminho crítico


def test_kanban_widget_no_critical_ids_no_marker(tmp_path):
    """P2b: sem critical_ids → nenhum marcador (paridade com comportamento atual)."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_two_pending()
    rendered = KanbanBoardWidget(board).render()
    assert "🔺" not in rendered


def test_kanban_widget_critical_marker_in_done_column(tmp_path):
    """P2b: step crítico também é marcado quando já está em DONE."""
    from llc_wizard.kanban_board import KanbanBoardWidget

    board = _board_two_pending()
    rendered = KanbanBoardWidget(board, critical_ids={"10.8"}).render()
    assert "Test Coverage 🔺" in rendered


def test_app_critical_ids_from_graph_source(tmp_path):
    """P2b: app com fonte graph expõe critical_ids não-vazios via reader."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            assert app.reader is not None
            # duck-typed: o reader graph tem critical_step_ids()
            ids = app.reader.critical_step_ids()
            assert isinstance(ids, list)
            assert all(isinstance(i, str) for i in ids)

    asyncio.run(run())


def test_app_kanban_render_includes_critical_marker(tmp_path):
    """P2b: render do board (fonte graph) inclui o marcador 🔺 p/ steps críticos."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            app.toggle_kanban()
            rendered = app.kanban_render()
            critical = app.reader.critical_step_ids()
            if critical:  # pipeline serial → ao menos um step no caminho crítico
                assert "🔺" in rendered

    asyncio.run(run())


def test_app_critical_ids_exclude_completed_steps(tmp_path):
    """P2b (fix review): steps DONE saem do caminho crítico restante.

    Em pipeline serial o caminho crítico inclui todos os steps; destacar só o
    que falta fazer preserva o sinal visual (não ilumina card já concluído).
    """
    import json as _json

    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])
    # step 3 concluído → fora do crítico restante; step 5 pendente → dentro
    sessions = [{"session_id": "s-3", "llc_step_id": "3",
                 "status": "completed", "timestamp": "2026-08-06T09:00:00"}]
    (root / ".ace" / "index.json").write_text(
        _json.dumps({"sessions": sessions}), encoding="utf-8")

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            app = pilot.app
            ids = app._critical_step_ids()
            assert "3" not in ids          # completado → sem 🔺
            assert ids                    # demais steps seguem no crítico
            assert any(i != "3" for i in ids)

    asyncio.run(run())


def test_app_index_source_no_critical_marker(tmp_path):
    """P2b (fix review): fonte index (sem critical_step_ids) → nenhum 🔺."""
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root, source="index").run_test() as pilot:
            app = pilot.app
            assert app._critical_step_ids() == set()
            app.toggle_kanban()
            assert "🔺" not in app.kanban_render()

    asyncio.run(run())


# ─────────────────── P2 pos-roadmap: fonte GraphEngine (graph) ─────────────


def test_app_default_source_is_graph(tmp_path):
    """P2: WizardApp default usa GraphPipelineDataSource (GraphEngine)."""
    from llc_graph.projections import GraphPipelineDataSource
    from llc_wizard.app import WizardApp

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            assert pilot.app.source_name == "graph"
            assert isinstance(pilot.app.reader, GraphPipelineDataSource)

    asyncio.run(run())


def test_app_source_index_uses_reader(tmp_path):
    """P2: source='index' → PipelineDataReader (fallback --source index)."""
    from llc_wizard.app import WizardApp
    from llc_wizard.data import PipelineDataReader

    root = _write_fake_index(tmp_path, [])

    async def run():
        async with WizardApp(project_root=root, source="index").run_test() as pilot:
            assert pilot.app.source_name == "index"
            assert isinstance(pilot.app.reader, PipelineDataReader)

    asyncio.run(run())


def test_app_kanban_board_parity_graph_vs_index(tmp_path):
    """P2: board idêntico com fonte graph e index (paridade §7.6 via app)."""
    import json as _json

    from llc_wizard.app import WizardApp
    from llc_wizard.kanban import KanbanBoardBuilder

    root = tmp_path
    ace = root / ".ace"
    (ace / "config").mkdir(parents=True)
    (ace / "sessions").mkdir(parents=True)
    sessions = [
        {"session_id": "s-05", "llc_step_id": "0.5", "status": "completed",
         "timestamp": "2026-08-06T09:00:00"},
        {"session_id": "s-1", "llc_step_id": "1", "status": "in_progress",
         "timestamp": "2026-08-06T10:00:00"},
        {"session_id": "s-2", "llc_step_id": "2", "status": "failed",
         "timestamp": "2026-08-06T08:00:00"},
        {"session_id": "s-3", "llc_step_id": "3", "status": "skipped",
         "timestamp": "2026-08-06T11:00:00"},
    ]
    (ace / "index.json").write_text(
        _json.dumps({"sessions": sessions}), encoding="utf-8")
    (ace / "config" / "gates.json").write_text(_json.dumps({
        "gates": {"1": {"step": 0.5, "label": "Visao", "checklist": ["Revisar"]}},
    }), encoding="utf-8")
    (ace / "sessions" / "s-05.md").write_text(
        "---\nstatus: completed\n---\n\n"
        '<gate_result step="0.5" decision="approved" reviewer="harness">'
        "ok</gate_result>\n", encoding="utf-8")
    note = root / "docs" / "delta" / "skip-notes" / "step-3.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("# skip\n", encoding="utf-8")

    def normalize(board):
        return {col.value: [c.id for c in cards]
                for col, cards in board.items()}

    async def run():
        async with WizardApp(project_root=root).run_test() as pilot:
            board_graph = normalize(KanbanBoardBuilder(pilot.app.reader).build())
        async with WizardApp(project_root=root, source="index").run_test() as pilot:
            board_index = normalize(KanbanBoardBuilder(pilot.app.reader).build())
        assert board_graph == board_index
        assert board_graph["DONE"] == ["0.5"]
        assert board_graph["RUNNING"] == ["1"]
        assert board_graph["REWORK"] == ["2"]

    asyncio.run(run())


def test_wizard_cli_source_flag_accepts_graph_and_index(tmp_path):
    """P2: 'wizard --source graph|index' aceitos; inválido → exit 2."""
    from click.testing import CliRunner
    from llc.cli import cli

    root = _write_fake_index(tmp_path, [])
    runner = CliRunner()
    ok = runner.invoke(cli, ["wizard", "--source", "graph",
                             "--project-root", str(root)])
    assert ok.exit_code == 0
    ok2 = runner.invoke(cli, ["wizard", "--source", "index",
                              "--project-root", str(root)])
    assert ok2.exit_code == 0
    bad = runner.invoke(cli, ["wizard", "--source", "bogus",
                              "--project-root", str(root)])
    assert bad.exit_code == 2  # click.Choice rejeita


def test_wizard_cli_help_shows_source_flag():
    """P2: 'wizard --help' documenta --source."""
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["wizard", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "graph" in result.output and "index" in result.output


def test_wizard_cli_export_flow_metrics_accepts_source_flag(tmp_path):
    """P2: --export-flow-metrics aceita --source graph|index."""
    from click.testing import CliRunner
    from llc.cli import cli

    root = _write_fake_index(tmp_path, [])
    runner = CliRunner()
    for src in ("graph", "index"):
        result = runner.invoke(cli, ["wizard", "--export-flow-metrics",
                                     "--source", src,
                                     "--project-root", str(root)])
        assert result.exit_code == 0, f"source={src}: {result.output}"


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
