"""llc_wizard.widgets.decision_modal — DecisionModal (RF-W1B.6).

Modal HITL que renderiza um PromptRequest e aceita a resposta do usuário,
encaminhando-a ao RealtimePromptCollector via submit_response().
"""
from __future__ import annotations

from llc_wizard.decisions import PromptRequest, RealtimePromptCollector


class DecisionModal:
    """Modal de decisão HITL: prompt + opções + campo de resposta."""

    def __init__(self, prompt: PromptRequest, collector: RealtimePromptCollector):
        self.prompt = prompt
        self.collector = collector
        self._response = ""

    def render(self) -> str:
        """Renderiza o prompt (e opções, se definidas) para o usuário."""
        lines = [f"❓ {self.prompt.text}"]
        if self.prompt.options:
            lines.append("Opções:")
            for opt in self.prompt.options:
                lines.append(f"  • {opt}")
        return "\n".join(lines)

    def set_response(self, response: str) -> None:
        """Recebe a resposta digitada pelo usuário no campo do modal."""
        self._response = response

    def confirm(self) -> None:
        """Confirma e envia a resposta ao collector, liberando o prompt."""
        self.collector.submit_response(self.prompt.prompt_id, self._response)