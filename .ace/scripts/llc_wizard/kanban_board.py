"""llc_wizard.kanban_board — KanbanBoardWidget (PRP-WIZARD-1.1, KP1).

Camada visual do Kanban (ADR-0002 §2.5): renderiza o board produzido pelo
`KanbanBoardBuilder` com 6 colunas, WIP limits, SLA visual (card-stale),
scores de eval (PRP-EVALS-F1/F2 — exibidos apenas se disponíveis) e coluna
SKIPPED colapsada por padrão (D1). Widget puro — render() não tem side-effects.

Toggle `K` e integração com o app vivem em `llc_wizard.app`.
"""
from __future__ import annotations

from datetime import datetime

from llc_wizard.kanban import KanbanCard, KanbanColumn

# WIP limits por coluna (ADR-0002 §2.5) — REWORK=2 é o único limite rígido N1;
# RUNNING admite múltiplos cards N2 (PRPs em worktrees).
_DEFAULT_WIP_LIMITS: dict[str, int | None] = {
    "BACKLOG": None,
    "RUNNING": None,        # N2: múltiplos PRPs em worktrees são permitidos
    "AWAITING_HUMAN": None,  # SLA (stale) é o controle, não WIP
    "REWORK": 2,
    "DONE": None,
    "SKIPPED": None,
}

_COLUMN_ICON = {
    KanbanColumn.BACKLOG: "⏳",
    KanbanColumn.RUNNING: "🔄",
    KanbanColumn.AWAITING_HUMAN: "⚠️",
    KanbanColumn.REWORK: "❌",
    KanbanColumn.DONE: "✅",
    KanbanColumn.SKIPPED: "⏭️",
}

# Ordem fixa de exibição das colunas (ADR-0002 §2.5)
_COLUMN_ORDER = [
    KanbanColumn.BACKLOG,
    KanbanColumn.RUNNING,
    KanbanColumn.AWAITING_HUMAN,
    KanbanColumn.REWORK,
    KanbanColumn.DONE,
    KanbanColumn.SKIPPED,
]


class KanbanBoardWidget:
    """Board Kanban renderizável (PRP-WIZARD-1.1, FTDD W1.1.1-10)."""

    def __init__(
        self,
        board: dict[KanbanColumn, list[KanbanCard]],
        sla_minutes: int = 30,
        wip_limits: dict[str, int | None] | None = None,
        scores: dict[str, dict] | None = None,
        theme: str = "dark",
    ):
        self.board = board
        self.sla_minutes = sla_minutes
        self.wip_limits = {**_DEFAULT_WIP_LIMITS, **(wip_limits or {})}
        self.scores = scores or {}
        self.theme = theme if theme in ("dark", "light") else "dark"

    # ── Cabeçalho (WIP total / Block Time / Stale count) ───────────────────
    def header(self) -> str:
        """Header do board: WIP total, Block Time (min), stale count."""
        running = len(self.board.get(KanbanColumn.RUNNING, []))
        awaiting_cards = self.board.get(KanbanColumn.AWAITING_HUMAN, [])
        rework = len(self.board.get(KanbanColumn.REWORK, []))
        wip_total = running + len(awaiting_cards) + rework
        stale = sum(1 for c in awaiting_cards if c.is_stale(self.sla_minutes))
        # Block Time = minutos totais de espera humana (AWAITING_HUMAN)
        block_min = sum(
            max(0.0, (datetime.now() - c.entered_column_at).total_seconds())
            for c in awaiting_cards
        ) / 60
        return (f"📋 Kanban — WIP: {wip_total} · Block Time: "
                f"{block_min:.0f}m · Stale: {stale}")

    # ── Colunas ─────────────────────────────────────────────────────────────
    def _column_header(self, column: KanbanColumn) -> str:
        cards = self.board.get(column, [])
        count = len(cards)
        limit = self.wip_limits.get(column.value)
        if limit is None:
            return f"── {column.value} ({count}) ──"
        over = count > limit
        wip = f"{count}/{limit} WIP{' 🔴' if over else ''}"
        return f"── {column.value} ({wip}) ──"

    def _collapsed(self, column: KanbanColumn) -> bool:
        """SKIPPED colapsada por padrão (D1 ADR-0002 / RF-W1.1.7)."""
        return column is KanbanColumn.SKIPPED

    def _card_line(self, card: KanbanCard) -> str:
        """Linha do card: ícone + título (+ score de eval se disponível)."""
        icon = _COLUMN_ICON.get(card.column, "•")
        line = f"  {icon} {card.title}"
        stale = " card-stale" if card.is_stale(self.sla_minutes) else ""
        score = self.scores.get(card.step_id or card.id)
        if score:
            q = score.get("quality_score")
            tokens = score.get("tokens")
            parts = []
            if q is not None:
                parts.append(f"Q:{q}")
            if tokens is not None:
                parts.append(f"T:{tokens:g}")
            if parts:
                line += f" ({' '.join(parts)})"
        return line + stale

    # ── PRP-WIZARD-1.2: Drag & Drop (RF-W1.2.1/.2) ──────────────────────────
    def reorder(self, column: KanbanColumn, from_index: int,
                to_index: int) -> list[str]:
        """Reordena um card dentro de uma coluna (RF-W1.2.1).

        Única exceção ao movimento state-driven (ADR-0002 §2.5 D5): reordenação
        de prioridade dentro do BACKLOG. Muta a lista da coluna por design
        (drag & drop é a mutação sancionada do board; `render()` continua puro)
        e retorna a nova ordem de ids dos cards (persistida pelo app na
        sessão). No-op se os índices forem inválidos.
        """
        cards = self.board.get(column, [])
        if not (0 <= from_index < len(cards) and 0 <= to_index < len(cards)):
            return [c.id for c in cards]
        card = cards.pop(from_index)
        cards.insert(to_index, card)
        return [c.id for c in cards]

    def try_move(self, card_id: str, target: KanbanColumn) -> tuple[bool, str]:
        """Tenta mover um card para outra coluna (RF-W1.2.2).

        Movimentos state-driven para fora do BACKLOG são bloqueados por design
        (ADR-0002 §2.5): retorna (False, notificação) e o board permanece
        intacto. Movimento BACKLOG → BACKLOG (mesma coluna) é permitido como
        no-op.
        """
        for column in _COLUMN_ORDER:
            cards = self.board.get(column, [])
            if any(c.id == card_id for c in cards):
                if column is KanbanColumn.BACKLOG and target is not KanbanColumn.BACKLOG:
                    return (False,
                            f"movimento bloqueado: {card_id} permanece no BACKLOG "
                            "(drag só reordena prioridade dentro do BACKLOG)")
                if column is target:
                    return True, ""
                return (False,
                        f"movimento bloqueado: {column.value} → {target.value} "
                        "não é permitido (fluxo é state-driven)")
        return False, f"movimento bloqueado: card {card_id} não encontrado"

    def render(self) -> str:
        """Renderiza o board completo (RF-W1.1.1-10)."""
        lines = [self.header(), f"[tema: {self.theme}]", ""]
        for column in _COLUMN_ORDER:
            if self._collapsed(column):
                # colapsada: apenas o cabeçalho com marcador ▸ (conteúdo oculto)
                cards = self.board.get(column, [])
                lines.append(f"── SKIPPED ({len(cards)}) ▸")
                continue
            lines.append(self._column_header(column))
            cards = self.board.get(column, [])
            if not cards:
                lines.append("  (vazio)")
            for card in cards:
                lines.append(self._card_line(card))
            lines.append("")
        return "\n".join(lines).rstrip()
