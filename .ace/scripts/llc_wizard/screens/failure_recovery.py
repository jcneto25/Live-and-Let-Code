"""llc_wizard.screens.failure_recovery — FailureRecoveryScreen (RF-W1C.4/5).

Exibida quando um gate é rejeitado: oferece 3 ações (re-executar / pular /
encerrar) com atalhos de teclado — fecha o ciclo de recovery iniciado como
stub no PRP-WIZARD-1A (SPEC 6.1).
"""
from __future__ import annotations

from enum import Enum


class FailureRecoveryAction(str, Enum):
    """Ações possíveis na tela de recovery (RF-W1C.5)."""

    RERUN = "rerun"    # re-executar o step sem sair da TUI
    SKIP = "skip"      # marcar o step como pulado (Smart Skip)
    QUIT = "quit"      # encerrar a TUI


# Atalhos de teclado (RF-W1C.5 — opções visíveis com atalhos)
_OPTIONS: list[tuple[str, str, FailureRecoveryAction]] = [
    ("r", "re-executar", FailureRecoveryAction.RERUN),
    ("s", "pular", FailureRecoveryAction.SKIP),
    ("q", "encerrar", FailureRecoveryAction.QUIT),
]


class FailureRecoveryScreen:
    """Tela de recovery pós-rejeição de gate (SPEC 6.1 / RF-W1C.4/5).

    Renderiza o step rejeitado + as 3 opções com atalhos de teclado.
    Pura (sem side-effects): a ação é decidida por `action_for(key)` e o
    chamador (WizardApp) executa — mantém a tela testável headless.
    """

    def __init__(self, step_id: str, reason: str = "Gate rejeitado"):
        self.step_id = step_id
        self.reason = reason

    def render(self) -> str:
        """Renderiza a tela com as 3 opções e seus atalhos."""
        lines = [
            f"⚠️  Step {self.step_id} falhou no gate — {self.reason}",
            "",
            "Escolha uma ação:",
        ]
        for key, label, _action in _OPTIONS:
            lines.append(f"  [{key}] {label}")
        return "\n".join(lines)

    def action_for(self, key: str) -> FailureRecoveryAction | None:
        """Ação correspondente ao atalho de teclado (None se desconhecido)."""
        for k, _label, action in _OPTIONS:
            if k == key:
                return action
        return None
