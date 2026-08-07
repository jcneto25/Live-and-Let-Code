"""llc_wizard.app — WizardApp (Textual TUI) RF-W1A.12.

Monta o layout com tres paineis: #sidebar (steps), #context-panel (gate) e
#output-panel. Nesta fase (WP4) o app e somente-leitura de apresentacao:
le o estado via PipelineDataSource (default: GraphPipelineDataSource sobre o
GraphEngine; fallback PipelineDataReader com --source index) e deriva o
progresso via PipelineStatus.
Nunca escreve frontmatter em .ace/sessions/ (RF-W1A.15).

PRP-WIZARD-1B: integra HITL real — o app possui um RealtimePromptCollector,
roteia prompts pendentes para um DecisionModal e executa steps com feedback.

PRP-WIZARD-1C: fecha o ciclo HITL avançado — Artifact Review apresenta o
artefato no painel de output (RF-W1C.1), Scope Confirmation bloqueia o início
do step até confirmação humana (RF-W1C.3) e a FailureRecoveryScreen real
(3 opções) suporta rerun automático sem sair da TUI (RF-W1C.4/5).
"""
from __future__ import annotations

from pathlib import Path

from llc_wizard.data import GateInfo, GateItem, StepStatus, build_data_source
from llc_wizard.decisions import (
    ArtifactReview,
    PromptRequest,
    RealtimePromptCollector,
)
from llc_wizard.flow_metrics import export_flow_metrics
from llc_wizard.kanban_board import KanbanBoardWidget
from llc_wizard.kanban import KanbanBoardBuilder, KanbanColumn
from llc_wizard.screens import FailureRecoveryScreen
from llc_wizard.widgets.decision_modal import DecisionModal

STATUS_ICON = {
    StepStatus.PENDING: "⏳",
    StepStatus.IN_PROGRESS: "🔄",
    StepStatus.GATE_PENDING: "⛔",
    StepStatus.COMPLETED: "✅",
    StepStatus.FAILED: "❌",
    StepStatus.SKIPPED: "⏭️",
    StepStatus.EXCLUDED: "🚫",
}


class WizardApp:
    """App Textual minimo — expoe #sidebar, #context-panel e #output-panel.

    Nota: para manter o teste headless (run_test) simples e nao acoplar os
    testes a Textual 0.x, a montagem usa um pseudo-DOM proprio. A integracao
    real com Textual App entra no WP4.2+ com a mesma API de IDs.
    """

    def __init__(self, project_root: Path, source: str = "graph"):
        self.project_root = Path(project_root)
        self.source_name = source
        self.reader = build_data_source(self.project_root, source)
        self.collector = RealtimePromptCollector()
        self._panels = {}
        self._gate_approved = False
        self._screen_stack: list[str] = []
        self._pending_scopes: dict[str, str] = {}  # step_id → escopo proposto
        self._recovery_screens: dict[str, FailureRecoveryScreen] = {}
        self._selected_step: str | None = None
        self._kanban_mode: bool = False
        self._kanban_widget: KanbanBoardWidget | None = None
        self._backlog_order: list[str] | None = None
        self.theme = self._load_theme()
        # P3 (PRP-WIZARD-2.0): ondas + mapa step→onda para swimlanes. Carregado
        # uma vez no init (dado de repo, não do reader); degrada para board
        # plano quando EXECUTION_WAVES.md não existe.
        self._waves, self._step_wave = self._load_wave_data()

    def _build(self):
        status = self.reader.get_status()
        icons = "\n".join(STATUS_ICON[s.status] for s in status.steps)
        self._sidebar = SimpleWidget("sidebar", icons, has_flow=False)
        self._sidebar_text = " / ".join(s.id for s in status.steps)
        self._progress = SimpleWidget("progress-bar",
                                      f"{status.progress_percent:.0f}% ({status.progress_percent:.0f}/{len(status.steps)})")
        self._context = SimpleWidget("context-panel", "Contexto vazio")
        self._output = SimpleWidget(
            "output-panel",
            getattr(self, "_output_text", None) or "Aguardando execucao",
        )
        return {"sidebar": self._sidebar, "context-panel": self._context,
                "output-panel": self._output, "progress-bar": self._progress}

    def run_test(self):
        """Retorna um contexto piloto usando asyncio (contrato de teste)."""
        return _WizardPilot(self)

    def query_one(self, node_id):
        """Retorna o widget com o ID dado (contrato do pilot)."""
        return self._panels[node_id.lstrip("#")]

    def approve_gate(self, step_id: str) -> None:
        """Registra aprovacao do gate (SPEC 6.1 gate_approved)."""
        self._gate_approved = True
        self._screen_stack.append("GateApprovedScreen")

    def reject_gate(self, step_id: str) -> None:
        """Registra rejeicao e empilha FailureRecoveryScreen real (SPEC 6.1).

        PRP-WIZARD-1C: a tela agora é o objeto concreto com 3 opções
        (re-executar / pular / encerrar) e atalhos de teclado (RF-W1C.5).
        Mantém o nome no stack por compatibilidade com o contrato do 1A.
        """
        screen = FailureRecoveryScreen(step_id=step_id)
        self._recovery_screens[step_id] = screen
        self._screen_stack.append("FailureRecoveryScreen")

    # ── PRP-WIZARD-1.1: Kanban UI (toggle K) ───────────────────────────────
    def select_step(self, step_id: str) -> None:
        """Seleciona um step (preservado entre toggles Pipeline ↔ Kanban)."""
        self._selected_step = step_id

    def toggle_kanban(self) -> None:
        """Toggle K: alterna modo Pipeline ↔ Kanban sem perder a seleção.

        RF-W1.1.9: o step selecionado antes do toggle é mantido.
        """
        self._kanban_mode = not self._kanban_mode
        if self._kanban_mode:
            self._build_kanban()

    def _load_sla_minutes(self) -> int:
        """SLA humano do Kanban: gates.json → wizard.hitl_sla_minutes (default 30)."""
        import json

        path = self.project_root / ".ace" / "config" / "gates.json"
        if not path.exists():
            return 30
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 30
        wizard_cfg = data.get("wizard", {}) if isinstance(data, dict) else {}
        if not isinstance(wizard_cfg, dict):  # config não-dict → default
            return 30
        value = wizard_cfg.get("hitl_sla_minutes", 30)
        return int(value) if isinstance(value, (int, float)) else 30

    def _load_eval_scores(self) -> dict[str, dict]:
        """Scores de eval por step (PRP-EVALS-F1/F2) — gracefoso se ausentes.

        Lê .ace/evals/baselines/step-*.yaml (quality_score_avg) e estima o
        custo via token_cost_avg. Nunca lança: dados ausentes → {}.
        """
        import yaml

        baselines_dir = self.project_root / ".ace" / "evals" / "baselines"
        scores: dict[str, dict] = {}
        if not baselines_dir.is_dir():
            return scores
        for path in sorted(baselines_dir.glob("step-*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except (yaml.YAMLError, OSError, AttributeError, TypeError):
                continue
            if not isinstance(data, dict):
                continue
            step_id = path.stem[len("step-"):]
            active = data.get("active_precision") or ""
            levels = data.get("by_precision_level")
            if not isinstance(levels, dict):
                continue
            bucket = levels.get(active)
            if not isinstance(bucket, dict):
                continue
            q = bucket.get("quality_score_avg")
            if q is None:
                continue
            tokens = bucket.get("token_cost_avg")
            scores[step_id] = {
                "quality_score": float(q),
                # token_cost_avg é TOKENS, não dólares — exibimos como T:
                "tokens": float(tokens) if tokens is not None else 0.0,
            }
        return scores

    def _critical_step_ids(self) -> set[str]:
        """Steps no caminho crítico RESTANTE (P2b) — duck-typed sobre a fonte.

        A fonte graph (`GraphPipelineDataSource`) expõe `critical_step_ids()`;
        a fonte index não — retorna vazio (sem marcador 🔺). Filtra apenas
        steps TERMINAIS não concluídos (não-DONE/SKIPPED/EXCLUDED): em pipeline
        serial o caminho crítico inclui todos os steps; destacar apenas o que
        falta fazer preserva o sinal visual (fix review P2b).
        """
        fn = getattr(self.reader, "critical_step_ids", None)
        if not callable(fn):
            return set()
        try:
            critical = set(fn())
        except ValueError:  # ciclo no grafo violaria ADR-0004 §2.5 — degradação
            return set()
        if not critical:
            return set()
        remaining = {
            s.id for s in self.reader.get_status().steps
            if s.status is not StepStatus.COMPLETED
            and s.status is not StepStatus.SKIPPED
            and s.status is not StepStatus.EXCLUDED
        }
        return critical & remaining

    def _load_wave_data(self) -> tuple[list, dict[str, int]]:
        """Ondas + mapa step→onda (P3 swimlanes) — degradação graciosa.

        Fonte: `EXECUTION_WAVES.md` real (gerado no Step 4) via
        `parse_execution_waves()`, cruzado com as sessões do `index.json`
        (`llc_step_id` + `prp`) via `build_step_wave_map()`. Arquivo ausente,
        vazio ou malformado → `([], {})` — o Kanban renderiza sem swimlanes
        (comportamento anterior), nunca quebra a TUI (convenção do P2).
        """
        waves_file = (self.project_root / "docs" / "planning"
                      / "EXECUTION_WAVES.md")
        if not waves_file.exists():
            return [], {}
        try:
            from llc_wave import parse_execution_waves
            from llc_wave.parsing import build_step_wave_map

            waves = parse_execution_waves(waves_file)
            if not waves:
                return [], {}
            import json

            try:
                data = json.loads(
                    (self.project_root / ".ace" / "index.json")
                    .read_text(encoding="utf-8"))
                sessions = data.get("sessions", []) if isinstance(data, dict) else []
            except (json.JSONDecodeError, OSError, AttributeError):
                sessions = []
            return waves, build_step_wave_map(sessions, waves)
        except ImportError:
            return [], {}

    def _next_step_ids(self) -> set[str]:
        """Steps elegíveis p/ execução agora (P2b-rest) — duck-typed.

        A fonte graph expõe `ready_step_ids()` (steps READY, sem espera
        humana); a fonte index não — retorna vazio (sem marcador ➤).

        Sem filtro extra de status: no adapter, READY→PENDING (paridade
        §7.6), logo todo step ready está na coluna BACKLOG por construção
        (fix review P2b-rest — interseção PENDING era lógica morta).
        """
        fn = getattr(self.reader, "ready_step_ids", None)
        if not callable(fn):
            return set()
        return set(fn())

    def _build_kanban(self) -> None:
        """Constrói o board Kanban a partir da fonte ativa (graph | index)."""
        sla = self._load_sla_minutes()
        builder = KanbanBoardBuilder(self.reader, sla_minutes=sla)
        board = builder.build()
        # RF-W1.2.1: reordenação de prioridade persistida é re-aplicada no
        # rebuild (toggle K não perde o drag & drop — fix review)
        if self._backlog_order:
            backlog = board.get(KanbanColumn.BACKLOG, [])
            by_id = {c.id: c for c in backlog}
            ordered = [by_id[cid] for cid in self._backlog_order if cid in by_id]
            ordered += [c for c in backlog if c.id not in self._backlog_order]
            board[KanbanColumn.BACKLOG] = ordered
        self._kanban_widget = KanbanBoardWidget(
            board,
            sla_minutes=sla,
            scores=self._load_eval_scores(),
            theme=self.theme,
            critical_ids=self._critical_step_ids(),
            next_ids=self._next_step_ids(),
            waves=self._waves,
            step_wave=self._step_wave,
        )
        self._panels["kanban-board"] = SimpleWidget(
            "kanban-board", self._kanban_widget.render()
        )

    def kanban_render(self) -> str:
        """Render do board Kanban (vazio se o modo ainda não foi ativado)."""
        if self._kanban_widget is None:
            self._build_kanban()
        return self._kanban_widget.render()

    # ── PRP-WIZARD-1.2: Drag & Drop (RF-W1.2.1/.2) ──────────────────────────
    def drag_card(self, card_id: str, target_column: str) -> str:
        """Tenta arrastar um card para outra coluna (RF-W1.2.2).

        Retorna notificação de bloqueio ("movimento bloqueado...") quando o
        destino está fora do BACKLOG — o board permanece intacto. BACKLOG →
        BACKLOG é no-op (retorna ""). Coluna desconhecida também é bloqueada
        (graceful — fix review).
        """
        try:
            target = KanbanColumn(target_column)
        except ValueError:
            return f"movimento bloqueado: coluna desconhecida '{target_column}'"
        if self._kanban_widget is None:
            self._build_kanban()
        ok, msg = self._kanban_widget.try_move(card_id, target)
        if ok:
            self._sync_kanban_panel()
            return ""
        return msg

    def reorder_backlog(self, card_id: str, from_index: int,
                        to_index: int) -> list[str]:
        """Reordena um card dentro do BACKLOG (RF-W1.2.1).

        Persiste a nova ordem na sessão do app (`_backlog_order`) e atualiza o
        painel. Retorna a nova ordem de ids.
        """
        if self._kanban_widget is None:
            self._build_kanban()
        order = self._kanban_widget.reorder(
            KanbanColumn.BACKLOG, from_index, to_index)
        self._backlog_order = order
        self._sync_kanban_panel()
        return order

    # ── PRP-WIZARD-2.0: Swimlanes por wave (P3) ────────────────────────────
    def toggle_wave(self, wave_number: int | None) -> str:
        """Colapsa/expande a swimlane de uma onda (RF-W2.0.4/.5).

        Delega ao widget e re-sincroniza o painel. Sem ondas definidas → no-op
        (graceful). Retorna o render atualizado.
        """
        if self._kanban_widget is None:
            self._build_kanban()
        if not self._waves:
            return self.kanban_render()
        self._kanban_widget.toggle_wave(wave_number)
        self._sync_kanban_panel()
        return self.kanban_render()

    def _sync_kanban_panel(self) -> None:
        """Atualiza o painel kanban-board após uma mutação do board."""
        self._panels["kanban-board"]._text = self._kanban_widget.render()

    # ── PRP-WIZARD-1.2: Export de métricas de fluxo (RF-W1.2.3/.4) ───────────
    def export_flow_metrics(self, results_dir=None) -> Path:
        """Exporta flow metrics para .ace/evals/results/ (RF-W1.2.3).

        Baseline é marcado apenas na primeira execução (RF-W1.2.4).
        """
        return export_flow_metrics(
            self.project_root, source=self.reader, results_dir=results_dir)

    # ── PRP-WIZARD-1.2: Temas dark/light (DoD) ───────────────────────────────
    def _load_theme(self) -> str:
        """Tema inicial: gates.json → wizard.theme (default "dark")."""
        import json

        path = self.project_root / ".ace" / "config" / "gates.json"
        if not path.exists():
            return "dark"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "dark"
        wizard_cfg = data.get("wizard", {}) if isinstance(data, dict) else {}
        if not isinstance(wizard_cfg, dict):
            return "dark"
        theme = wizard_cfg.get("theme", "dark")
        return theme if theme in ("dark", "light") else "dark"

    def toggle_theme(self) -> str:
        """Alterna tema dark ↔ light (DoD temas). Retorna o novo tema.

        O tema é aplicado ao widget Kanban (render reflete o tema ativo) e o
        painel é re-sincronizado se já montado (fix review — tcss não é dead).
        """
        self.theme = "light" if self.theme == "dark" else "dark"
        if self._kanban_widget is not None:
            self._kanban_widget.theme = self.theme
            self._sync_kanban_panel()
        return self.theme

    # ── PRP-WIZARD-1C: Artifact Review (RF-W1C.1) ───────────────────────────
    def show_artifact_review(self, review: ArtifactReview) -> None:
        """Apresenta o artefato no painel de output para revisão humana.

        RF-W1C.1: conteúdo do artefato (caminho + veredito) visível no
        #output-panel; o humano decide aprovar ou rejeitar com feedback
        (que persiste via ReviewArtifactCommand — RF-W1C.2).
        """
        status = "approved" if review.approved else "rejected"
        text = (
            f"📄 Artifact Review\nArtefato: {review.artifact}\n"
            f"Veredito: {status}"
        )
        if review.feedback:
            text += "\nFeedback:\n" + "\n".join(
                f"  - {item}" for item in review.feedback
            )
        self._output_text = text
        if "output-panel" in self._panels:
            self._panels["output-panel"]._text = text

    # ── PRP-WIZARD-1C: Scope Confirmation (RF-W1C.3) ────────────────────────
    def set_pending_scope(self, step_id: str, scope: str) -> None:
        """Registra escopo proposto pendente — bloqueia início do step."""
        self._pending_scopes[step_id] = scope

    def confirm_scope(self, step_id: str) -> None:
        """Confirmação humana libera o step para iniciar."""
        self._pending_scopes.pop(step_id, None)

    def can_start_step(self, step_id: str) -> bool:
        """Step pode iniciar? Falso enquanto houver escopo pendente (RF-W1C.3)."""
        return step_id not in self._pending_scopes

    # ── PRP-WIZARD-1C: Rerun automático (RF-W1C.4) ──────────────────────────
    async def rerun_step(self, step_id: str, runner=None):
        """Re-executa o step a partir da FailureRecoveryScreen, sem sair da TUI.

        RF-W1C.4: após rejeição de gate, "re-executar" reinicia o step no
        mesmo app. Desempilha a tela de recovery e reutiliza o runner
        injetado (ou selecionado) — mesmo fluxo de run_step_with_hitl.
        """
        if "FailureRecoveryScreen" in self._screen_stack:
            # remove a entrada específica (não o topo) — um DecisionModal pode
            # ter sido empilhado depois da rejeição (fix review WIZARD-1C)
            self._screen_stack.remove("FailureRecoveryScreen")
        self._recovery_screens.pop(step_id, None)
        async for _event in self.run_step_with_hitl(step_id, runner=runner):
            pass  # consuma os eventos — o rerun é síncrono do ponto de vista
            # do chamador (awaits até o step concluir ou pedir HITL novamente)

    def open_prompt_modal(self, prompt: PromptRequest) -> DecisionModal:
        """Abre um DecisionModal para um prompt pendente (RF-W1B.6).

        O modal usa o collector compartilhado: ao confirmar, submit_response()
        libera o request_input() do lado do agente/step.
        """
        modal = DecisionModal(prompt=prompt, collector=self.collector)
        self._screen_stack.append(f"DecisionModal:{prompt.prompt_id}")
        return modal

    async def run_step_with_hitl(self, step_id: str, task: str = "", runner=None):
        """Executa um step capturando output e roteando HITL.

        Usa o runner injetado, ou o runner selecionado (HarnessRunner quando há
        agente no PATH, senão FallbackRunner), repassando os eventos para a UI.
        Durante a execução, o collector coleta prompts que o app roteia para
        DecisionModal.
        """
        if runner is None:
            from llc_wizard.runner import select_runner

            runner = select_runner(step_id, task)
        async for event in runner.run_step():
            yield event


class _WizardPilot:
    """Pilot mínimo para testes headless — reproduz run_test() do Textual."""

    def __init__(self, app):
        self.app_object = app

    @property
    def app(self):
        return self.app_object

    async def __aenter__(self):
        self.app_object._panels = self.app_object._build()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class SimpleWidget:
    """Widget minimo com id, render() e um texto neutralizado para teste."""

    def __init__(self, node_id, text, has_flow=True):
        self.id = node_id
        self._text = text

    def render(self):
        return self._text


class GateChecklist:
    """Checklist de gate (SPEC 6.2) — itens obrigatorios bloqueiam Aprovar.

    Estado unchecked_required: can_approve() == False.
    Estado all_required_checked: can_approve() == True.
    """

    def __init__(self, gate_id: str, items: list[str],
                 required_all: bool = True, checked: set[int] | None = None):
        self.gate_id = gate_id
        self._checked: set[int] = set(checked or ())
        self.items = [GateItem(id=str(i), description=desc, required=required_all)
                      for i, desc in enumerate(items)]

    def toggle(self, index: int) -> None:
        if 0 <= index < len(self.items):
            if index in self._checked:
                self._checked.discard(index)
            else:
                self._checked.add(index)

    def can_approve(self) -> bool:
        if not self.items:
            return True
        required = [i for i in self.items if i.required]
        if not required:
            return True
        return all(i.id is not None and int(i.id) in self._checked for i in required)

    def render(self):
        lines = []
        for i, item in enumerate(self.items):
            mark = "[x]" if i in self._checked else "[ ]"
            lines.append(f"{mark} {item.description}")
        return "\n".join(lines)