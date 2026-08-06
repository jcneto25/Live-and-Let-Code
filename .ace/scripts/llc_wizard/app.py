"""llc_wizard.app — WizardApp (Textual TUI) RF-W1A.12.

Monta o layout com tres paineis: #sidebar (steps), #context-panel (gate) e
#output-panel. Nesta fase (WP4) o app e somente-leitura de apresentacao:
le o estado via PipelineDataReader e deriva o progresso via PipelineStatus.
Nunca escreve frontmatter em .ace/sessions/ (RF-W1A.15).
"""
from __future__ import annotations

from pathlib import Path

from llc_wizard.data import GateInfo, GateItem, PipelineDataReader, StepStatus

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
        self._panels = {}
        self._gate_approved = False
        self._screen_stack: list[str] = []

    def _build(self):
        status = self.reader.get_status()
        icons = "\n".join(STATUS_ICON[s.status] for s in status.steps)
        self._sidebar = SimpleWidget("sidebar", icons, has_flow=False)
        self._sidebar_text = " / ".join(s.id for s in status.steps)
        self._progress = SimpleWidget("progress-bar",
                                      f"{status.progress_percent:.0f}% ({status.progress_percent:.0f}/{len(status.steps)})")
        self._context = SimpleWidget("context-panel", "Contexto vazio")
        self._output = SimpleWidget("output-panel", "Aguardando execucao")
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
        """Registra rejeicao e empilha FailureRecoveryScreen (SPEC 6.1)."""
        self._screen_stack.append("FailureRecoveryScreen")


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