"""Testes para llc_wizard.kanban — RF-W1A.6/7/8 (WP2).

TDD: testes escritos primeiro (RED). Cobertura:
- RF-W1A.6: KanbanCard.is_stale respeita SLA configurável
- RF-W1A.7: KanbanBoardBuilder.build() mapeia steps para colunas
- RF-W1A.8: AWAITING_HUMAN ordenado por tempo de espera (mais antigo no topo)
"""
from datetime import datetime, timedelta

import pytest

from llc_wizard.kanban import (
    CardType,
    KanbanBoardBuilder,
    KanbanCard,
    KanbanColumn,
)
from llc_wizard.data import PipelineDataReader
from unittest.mock import patch


def test_kanban_columns_exist():
    valores = {c.value for c in KanbanColumn}
    assert valores == {"BACKLOG", "RUNNING", "AWAITING_HUMAN", "REWORK", "DONE", "SKIPPED"}


def test_card_types_exist():
    valores = {c.value for c in CardType}
    assert valores == {"step", "prp", "gate"}


def test_card_is_stale_true_when_beyond_sla():
    card = KanbanCard(
        id="c1",
        title="Gate 5",
        card_type=CardType.GATE,
        column=KanbanColumn.AWAITING_HUMAN,
        entered_column_at=datetime.now() - timedelta(minutes=31),
    )
    assert card.is_stale(sla_minutes=30) is True


def test_card_is_stale_false_within_sla():
    card = KanbanCard(
        id="c1",
        title="Gate 5",
        card_type=CardType.GATE,
        column=KanbanColumn.AWAITING_HUMAN,
        entered_column_at=datetime.now() - timedelta(minutes=29),
    )
    assert card.is_stale(sla_minutes=30) is False


def test_card_not_stale_if_not_awaiting_human():
    card = KanbanCard(
        id="c1",
        title="Step 5",
        card_type=CardType.STEP,
        column=KanbanColumn.RUNNING,
        entered_column_at=datetime.now() - timedelta(hours=5),
    )
    assert card.is_stale(sla_minutes=30) is False


def _fake_source(step_infos, status_since=None):
    """Fake PipelineDataSource com get_status() controlado."""

    class Fake:
        def __init__(self, infos, since):
            self._infos = infos
            self._since = since or {}

        def get_status(self):
            from llc_wizard.data import PipelineStatus

            return PipelineStatus(steps=self._infos)

        def get_status_since(self, step_id):
            import datetime as _dt

            if step_id in self._since:
                return self._since[step_id]
            return _dt.datetime.fromtimestamp(0)

        def get_pending_hitl(self):
            return []

    return Fake(step_infos, status_since)


def test_build_maps_steps_to_correct_columns():
    from llc_wizard.data import StepInfo, StepStatus

    infos = [
        StepInfo("1", "Visão", StepStatus.COMPLETED, in_pipeline=True),
        StepInfo("2", "Specs", StepStatus.IN_PROGRESS, in_pipeline=True),
        StepInfo("3", "PRDs", StepStatus.GATE_PENDING, in_pipeline=True),
        StepInfo("4", "Planejamento", StepStatus.FAILED, in_pipeline=True),
        StepInfo("5", "Arquitetura", StepStatus.PENDING, in_pipeline=True),
    ]
    board = KanbanBoardBuilder(_fake_source(infos)).build()
    assert [c.id for c in board[KanbanColumn.DONE]] == ["1"]
    assert [c.id for c in board[KanbanColumn.RUNNING]] == ["2"]
    assert [c.id for c in board[KanbanColumn.AWAITING_HUMAN]] == ["3"]
    assert [c.id for c in board[KanbanColumn.REWORK]] == ["4"]
    assert [c.id for c in board[KanbanColumn.BACKLOG]] == ["5"]


def test_build_orders_awaiting_human_oldest_first():
    """build() ordena AWAITING_HUMAN por entered_column_at (mais antigo topo)."""
    from llc_wizard.data import StepInfo, StepStatus

    infos = [
        StepInfo("3", "PRDs recente", StepStatus.GATE_PENDING, in_pipeline=True),
        StepInfo("2", "Specs antigo", StepStatus.GATE_PENDING, in_pipeline=True),
    ]
    since = {
        "2": datetime(2026, 8, 5, 9, 0, 0),  # mais antigo
        "3": datetime(2026, 8, 5, 10, 0, 0),  # mais recente
    }
    board = KanbanBoardBuilder(_fake_source(infos, since)).build()

    awaiting = board[KanbanColumn.AWAITING_HUMAN]
    assert [c.step_id for c in awaiting] == ["2", "3"]