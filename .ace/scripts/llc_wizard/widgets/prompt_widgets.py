"""llc_wizard.widgets.prompt_widgets — widgets de exibição de prompts HITL.

PendingPromptsWidget renderiza a fila de prompts aguardando decisão humana a
partir do RealtimePromptCollector, mantendo visível o estado "AWAITING_HUMAN".
"""
from __future__ import annotations

from llc_wizard.decisions import RealtimePromptCollector


class PendingPromptsWidget:
    """Widget de lista de prompts pendentes (HITL aguardando humano)."""

    def __init__(self, collector: RealtimePromptCollector):
        self.collector = collector

    def render(self) -> str:
        """Renderiza os prompts pendentes, um por linha."""
        prompts = self.collector.pending_prompts
        if not prompts:
            return "Sem prompts pendentes."
        lines = [f"[{p.kind}] {p.text}" for p in prompts]
        return "\n".join(lines)
