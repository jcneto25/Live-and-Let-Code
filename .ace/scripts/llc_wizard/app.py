"""llc_wizard.app — WizardApp (Textual TUI) RF-W1A.12.

Monta o layout com tres paineis: #sidebar (steps), #context-panel (gate) e
#output-panel. Nesta fase (WP4) o app e somente-leitura de apresentacao:
le o estado via PipelineDataReader e deriva o progresso via PipelineStatus.
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

from llc_wizard.data import GateInfo, GateItem, PipelineDataReader, StepStatus
from llc_wizard.decisions import (
    ArtifactReview,
    PromptRequest,
    RealtimePromptCollector,
)
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

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.reader = PipelineDataReader(self.project_root)
        self.collector = RealtimePromptCollector()
        self._panels = {}
        self._gate_approved = False
        self._screen_stack: list[str] = []
        self._pending_scopes: dict[str, str] = {}  # step_id → escopo proposto
        self._recovery_screens: dict[str, FailureRecoveryScreen] = {}

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