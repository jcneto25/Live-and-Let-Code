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
        critical_ids: set[str] | None = None,
        next_ids: set[str] | None = None,
        waves: list | None = None,
        step_wave: dict[str, int] | None = None,
    ):
        self.board = board
        self.sla_minutes = sla_minutes
        self.wip_limits = {**_DEFAULT_WIP_LIMITS, **(wip_limits or {})}
        self.scores = scores or {}
        self.theme = theme if theme in ("dark", "light") else "dark"
        # P2b: steps no caminho crítico (ADR-0004 §2.7) ganham marcador 🔺
        self.critical_ids = set(critical_ids or ())
        # P2b-rest: steps prontos p/ execução (ready_nodes) — sugestão de
        # próximo step (RF-W1A.7) com marcador ➤
        self.next_ids = set(next_ids or ())
        # P3 (PRP-WIZARD-2.0): swimlanes por wave. `waves` vazio → board
        # plano (comportamento anterior). `step_wave` mapeia step_id → onda;
        # steps fora do mapa caem na swimlane "Sem onda". Estado de colapso é
        # por widget (não persiste entre toggles K — ver PRP-WIZARD-2.0 §1.3).
        self.waves = list(waves or ())
        self.step_wave = dict(step_wave or {})
        self._collapsed_waves: set[int | None] = set()

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
        """Linha do card: ícone + título (+ 🔺 crítico + score de eval)."""
        icon = _COLUMN_ICON.get(card.column, "•")
        line = f"  {icon} {card.title}"
        # P2b: step no caminho crítico do grafo (ADR-0004 §2.7)
        if (card.step_id or card.id) in self.critical_ids:
            line += " 🔺"
        # P2b-rest: step ready (elegível p/ execução agora) — sugestão ➤
        if (card.step_id or card.id) in self.next_ids:
            line += " ➤"
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

    # ── PRP-WIZARD-2.0: Swimlanes por wave (P3) ────────────────────────────
    def toggle_wave(self, wave_number: int | None) -> None:
        """Colapsa/expande a swimlane de uma wave (RF-W2.0.4/.5).

        `None` alterna a swimlane "Sem onda". Round-trip volta ao estado
        inicial (2× toggle desfaz).
        """
        if wave_number in self._collapsed_waves:
            self._collapsed_waves.discard(wave_number)
        else:
            self._collapsed_waves.add(wave_number)

    def _wave_of(self, card: KanbanCard) -> int | None:
        """Número da onda do card (None = sem onda)."""
        return self.step_wave.get(card.step_id or card.id)

    def _wave_label(self, wave_number: int | None, count: int) -> str:
        """Rótulo da swimlane: 'Onda N: Nome (count)' ou 'Sem onda (count)'."""
        if wave_number is None:
            return f"Sem onda ({count})"
        name = next((w.name for w in self.waves if w.number == wave_number), "")
        suffix = f": {name}" if name else ""
        return f"Onda {wave_number}{suffix} ({count})"

    def _render_swimlanes(self, cards: list[KanbanCard]) -> list[str]:
        """Sub-seções por onda dentro de uma coluna (P3)."""
        lines: list[str] = []
        groups: dict[int | None, list[KanbanCard]] = {}
        for card in cards:
            groups.setdefault(self._wave_of(card), []).append(card)
        # Ondas com número ordenadas por número; "Sem onda" (None) por último
        ordered = sorted((k for k in groups if k is not None))
        for wave_n in ordered + [None]:
            if wave_n not in groups:
                continue
            bucket = groups[wave_n]
            collapsed = wave_n in self._collapsed_waves
            marker = "▸" if collapsed else "▾"
            lines.append(f"  {marker} {self._wave_label(wave_n, len(bucket))}")
            if not collapsed:
                for card in bucket:
                    lines.append(self._card_line(card))
        return lines

    def render(self) -> str:
        """Renderiza o board completo (RF-W1.1.1-10 + P3 swimlanes)."""
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
            elif self.waves:
                # P3: swimlanes por wave quando há ondas definidas
                lines.extend(self._render_swimlanes(cards))
            else:
                for card in cards:
                    lines.append(self._card_line(card))
            lines.append("")
        return "\n".join(lines).rstrip()
