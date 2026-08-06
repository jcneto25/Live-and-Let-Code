"""llc_wizard.decisions — UserDecisionWriter e RealtimePromptCollector.

PRP-WIZARD-1B (ADR-0002 §2.4 — Write-via-API). HITL estruturado durante e ao
final dos steps: decisões humanas são serializadas como tags XML append-only
no arquivo de sessão (.ace/sessions/{sid}.md). O frontmatter nunca é tocado.

UserDecisionWriter é mutador sancionado (GOV-003/R8): apenas APPEND de tags
HITL. Nenhuma reescrita de conteúdo pré-existente.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape


@dataclass(frozen=True)
class GateDecision:
    """Decisão de gate (approve/reject/conditional) com waiver opcional."""

    step: str
    decision: str
    waiver: bool = False
    waiver_note: str | None = None
    timestamp: str | None = None


@dataclass(frozen=True)
class QuestionAnswer:
    """Resposta a uma pergunta de clarificação do agente (HITL durante step)."""

    question_id: str
    question: str
    answer: str
    step_id: str | None = None
    timestamp: str | None = None


@dataclass(frozen=True)
class ArtifactReview:
    """Veredicto humano sobre um artefato gerado (HITL durante step)."""

    artifact: str
    verdict: str
    comments: str = ""
    timestamp: str | None = None


@dataclass(frozen=True)
class ScopeConfirmation:
    """Confirmação humana de escopo antes de executar um step."""

    step_id: str
    scope: str
    confirmed: bool = True
    timestamp: str | None = None


@dataclass(frozen=True)
class PromptRequest:
    """Prompt HITL endereçado ao humano durante a execução do step."""

    prompt_id: str
    text: str
    step_id: str | None = None
    kind: str = "question"
    options: list[str] = field(default_factory=list)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class UserDecisionWriter:
    """Escritor append-only de decisões HITL no arquivo de sessão.

    Sanção: GOV-003/R8 (AGENTS.md Critical Safeguard) — único mutador permitido
    além de initialize/finalize, com escopo restrito a tags HITL.
    """

    def __init__(self, session_file: Path):
        self.session_file = Path(session_file)

    def _append(self, xml_block: str) -> None:
        """Append do bloco XML ao arquivo de sessão (append-only)."""
        with self.session_file.open("a", encoding="utf-8") as fh:
            fh.write("\n" + xml_block + "\n")

    def submit_gate_decision(self, d: GateDecision) -> None:
        """Grava <gate_result step decision waiver> (+ <waiver_note> se waiver)."""
        ts = d.timestamp or _now()
        waiver_attr = ' waiver="true"' if d.waiver else ""
        block = (
            f'<gate_result step="{d.step}" decision="{d.decision}"'
            f'{waiver_attr} timestamp="{ts}">'
        )
        if d.waiver:
            note = _xml_escape(d.waiver_note or "")
            block += f"\n  <waiver_note>{note}</waiver_note>"
        block += "\n</gate_result>"
        self._append(block)

    def submit_question_answer(self, a: QuestionAnswer) -> None:
        """Grava <user_response type="question"> com <question>/<answer>."""
        ts = a.timestamp or _now()
        q = _xml_escape(a.question)
        ans = _xml_escape(a.answer)
        block = (
            f'<user_response type="question" question_id="{a.question_id}" '
            f'step_id="{a.step_id or ""}" timestamp="{ts}">\n'
            f"  <question>{q}</question>\n"
            f"  <answer>{ans}</answer>\n"
            "</user_response>"
        )
        self._append(block)

    def submit_artifact_review(self, r: ArtifactReview) -> None:
        """Grava <user_response type="artifact_review">."""
        ts = r.timestamp or _now()
        artifact = _xml_escape(r.artifact)
        verdict = _xml_escape(r.verdict)
        comments = _xml_escape(r.comments)
        block = (
            f'<user_response type="artifact_review" artifact="{artifact}" '
            f'verdict="{verdict}" timestamp="{ts}">\n'
            f"  <comments>{comments}</comments>\n"
            "</user_response>"
        )
        self._append(block)

    def submit_scope_confirmation(self, s: ScopeConfirmation) -> None:
        """Grava <user_response type="scope">."""
        ts = s.timestamp or _now()
        scope = _xml_escape(s.scope)
        confirmed = "true" if s.confirmed else "false"
        block = (
            f'<user_response type="scope" step_id="{s.step_id}" '
            f'confirmed="{confirmed}" timestamp="{ts}">\n'
            f"  <scope>{scope}</scope>\n"
            "</user_response>"
        )
        self._append(block)


class RealtimePromptCollector:
    """Coletor de prompts HITL em tempo real — bloqueia o agente até resposta.

    RF-W1B.3/4/5: request_input registra um PromptRequest pendente e aguarda
    (asyncio.Event) até que submit_response() libere o prompt correspondente.
    A ordem de resposta segue a ordem de abertura (FIFO) quando o cliente
    responde em sequência. Sem deadlock: cada prompt tem seu próprio Event.
    """

    def __init__(self):
        self._pending: dict[str, asyncio.Event] = {}
        self._requests: dict[str, PromptRequest] = {}
        self._responses: dict[str, str] = {}

    @property
    def pending_prompts(self) -> list[PromptRequest]:
        """Prompts aguardando resposta humana, na ordem de abertura."""
        return [self._requests[pid] for pid in self._pending]

    async def request_input(self, prompt: PromptRequest) -> str:
        """Registra o prompt e aguarda a resposta humana (bloqueante)."""
        event = asyncio.Event()
        self._pending[prompt.prompt_id] = event
        self._requests[prompt.prompt_id] = prompt
        await event.wait()
        self._pending.pop(prompt.prompt_id, None)
        self._requests.pop(prompt.prompt_id, None)
        return self._responses.pop(prompt.prompt_id, "")

    def submit_response(self, prompt_id: str, response: str) -> None:
        """Libera o prompt correspondente com a resposta do usuário."""
        self._responses[prompt_id] = response
        event = self._pending.get(prompt_id)
        if event is not None:
            event.set()
