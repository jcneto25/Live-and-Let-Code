"""llc_wizard.kanban — modelo de dados Kanban (sem UI).

RF-W1A.6/7/8 — KanbanCard com SLA (is_stale) e KanbanBoardBuilder que projeta
steps do PipelineDataSource para colunas. Sem UI — a camada visual é o
PRP-WIZARD-1.1 (KP1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class KanbanColumn(str, Enum):
    """Colunas do Kanban (ADR-0002 §2.5)."""

    BACKLOG = "BACKLOG"
    RUNNING = "RUNNING"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    REWORK = "REWORK"
    DONE = "DONE"
    SKIPPED = "SKIPPED"


class CardType(str, Enum):
    """Tipos de card: step do pipeline (N1), PRP em worktree (N2) ou gate."""

    STEP = "step"
    PRP = "prp"
    GATE = "gate"


@dataclass(frozen=True)
class KanbanCard:
    """Card do Kanban — imutável (§7.3)."""

    id: str
    title: str
    card_type: CardType
    column: KanbanColumn
    entered_column_at: datetime
    step_id: str | None = None
    session_id: str | None = None
    agent: str | None = None
    meta: dict = field(default_factory=dict)

    def is_stale(self, sla_minutes: int) -> bool:
        """True se o card está em AWAITING_HUMAN além do SLA (RF-W1A.6)."""
        if self.column is not KanbanColumn.AWAITING_HUMAN:
            return False
        elapsed = (datetime.now() - self.entered_column_at).total_seconds() / 60
        return elapsed > sla_minutes


_STATUS_TO_COLUMN = {
    "pending": KanbanColumn.BACKLOG,
    "in_progress": KanbanColumn.RUNNING,
    "gate_pending": KanbanColumn.AWAITING_HUMAN,
    "failed": KanbanColumn.REWORK,
    "completed": KanbanColumn.DONE,
    "skipped": KanbanColumn.SKIPPED,
    "excluded": None,
}


class KanbanBoardBuilder:
    """Projeta steps do PipelineDataSource para cards Kanban (RF-W1A.7/8).

    Recebe a interface PipelineDataSource (RNF-W1A.8 / ADR-0004 §2.3), não a
    implementação concreta — preserva a estratégia adapter do GOV-003/R3.
    """

    def __init__(self, source, sla_minutes: int = 30):
        self.source = source
        self.sla_minutes = sla_minutes

    def build(self) -> dict[KanbanColumn, list[KanbanCard]]:
        """Mapeia cada step para a coluna correspondente ao seu status.

        Steps excluded são omitidos. AWAITING_HUMAN é ordenado por
        entered_column_at crescente (mais antigo no topo — RF-W1A.8).
        """
        board = {col: [] for col in KanbanColumn}
        status = self.source.get_status()
        for step in status.steps:
            column = _STATUS_TO_COLUMN.get(step.status.value)
            if column is None:
                continue
            entered = self.source.get_status_since(step.id)
            card = KanbanCard(
                id=step.id,
                title=step.name,
                card_type=CardType.STEP,
                column=column,
                entered_column_at=entered,
                step_id=step.id,
            )
            board[column].append(card)
        board[KanbanColumn.AWAITING_HUMAN].sort(
            key=lambda c: c.entered_column_at
        )
        return board