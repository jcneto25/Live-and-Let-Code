"""llc_wizard.runner — execução de steps não-bloqueante (RF-W1A.9–11).

HarnessRunner embrulha llc_harness.step_run via asyncio.to_thread (não bloqueia
o event loop — RNF-W1A.7); FallbackRunner gera prompt copy-paste para clientes
de IA sem stdout capturável; select_runner escolhe com base no agente detectado.
"""
from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from typing import AsyncIterator, Union


@dataclass(frozen=True)
class OutputEvent:
    """Linha de saída produzida durante a execução do step."""

    text: str


@dataclass(frozen=True)
class CompletionEvent:
    """Step concluído com sucesso/fracasso."""

    step_id: str
    success: bool
    output: str = ""


RunnerEvent = Union[OutputEvent, CompletionEvent]


class HarnessRunner:
    """Executa um step via llc_harness.step_run em thread separada."""

    def __init__(self, step_id: str, task: str):
        self.step_id = step_id
        self.task = task

    def _blocking_call(self) -> str:
        from llc_harness import step_run

        return step_run(self.step_id, task=self.task)

    async def run_step(self) -> AsyncIterator[RunnerEvent]:
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, self._blocking_call)
        yield OutputEvent(text=str(output))
        yield CompletionEvent(step_id=self.step_id, success=True, output=str(output))


class FallbackRunner:
    """Gera prompt copy-paste para clientes de IA sem stdout capturável."""

    def __init__(self, step_id: str, task: str):
        self.step_id = step_id
        self.task = task

    async def run_step(self) -> AsyncIterator[RunnerEvent]:
        prompt = (
            f"Para executar o step {self.step_id} ({self.task}) fora do wizard, "
            "copie e cole o comando abaixo no terminal:\n"
            f"  llc run --step {self.step_id} --task \"{self.task}\""
        )
        yield OutputEvent(text=prompt)
        yield CompletionEvent(step_id=self.step_id, success=True, output=prompt)


_AGENTS = ("claude", "codex", "opencode", "cursor")


def select_runner(step_id: str, task: str = "") -> Union[HarnessRunner, FallbackRunner]:
    """Usa HarnessRunner se algum agente de IA estiver detectado no PATH,
    senão FallbackRunner (RF-W1A.11)."""
    for agent in _AGENTS:
        if shutil.which(agent):
            return HarnessRunner(step_id=step_id, task=task)
    return FallbackRunner(step_id=step_id, task=task)