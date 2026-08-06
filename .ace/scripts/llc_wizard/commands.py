"""llc_wizard.commands — Command pattern para as 6 categorias HITL.

PRP-WIZARD-1B (ADR-0002 §2.4): cada decisão humana tipada, validada e
auditável. HITLCommand é a base; cada comando concreto implementa validate()
e execute(writer).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from llc_wizard.decisions import (
    ArtifactReview,
    GateDecision,
    QuestionAnswer,
    ScopeConfirmation,
    UserDecisionWriter,
)

MIN_WAIVER_NOTE_LENGTH = 10


class HITLCommand(ABC):
    """Comando HITL: valida a intenção antes de persistir via UserDecisionWriter."""

    @abstractmethod
    def validate(self) -> bool:
        """Retorna False se o comando não pode ser executado."""

    @abstractmethod
    async def execute(self, writer: UserDecisionWriter) -> None:
        """Persiste a decisão via writer (só se validate() == True)."""


@dataclass(frozen=True)
class ApproveGateCommand(HITLCommand):
    """Gate Approval — grava <gate_result decision="approved">."""

    gate_decision: GateDecision

    def validate(self) -> bool:
        return (
            self.gate_decision.decision == "approved"
            and bool(self.gate_decision.step)
        )

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_gate_decision, self.gate_decision)


@dataclass(frozen=True)
class RejectGateCommand(HITLCommand):
    """Gate Rejection — grava <gate_result decision="rejected">."""

    gate_decision: GateDecision

    def validate(self) -> bool:
        return (
            self.gate_decision.decision == "rejected"
            and bool(self.gate_decision.step)
        )

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_gate_decision, self.gate_decision)


@dataclass(frozen=True)
class WaiveGateCommand(HITLCommand):
    """Waiver — gate aprovado com ressalva; exige nota mínima de 10 chars."""

    gate_decision: GateDecision

    def validate(self) -> bool:
        if not (self.gate_decision.waiver and self.gate_decision.step):
            return False
        note = self.gate_decision.waiver_note or ""
        return len(note.strip()) >= MIN_WAIVER_NOTE_LENGTH

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_gate_decision, self.gate_decision)


@dataclass(frozen=True)
class AnswerQuestionCommand(HITLCommand):
    """Question Answer — grava <user_response type="question">."""

    answer: QuestionAnswer

    def validate(self) -> bool:
        return bool(self.answer.answer.strip())

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_question_answer, self.answer)


@dataclass(frozen=True)
class ReviewArtifactCommand(HITLCommand):
    """Artifact Review — grava <user_response type="artifact_review"> (RF-W1C.2).

    Rejeição (approved=False) exige pelo menos um item de `feedback` —
    revisão sem justificativa não é auditável (ADR-0002 §2.4).
    """

    review: ArtifactReview

    def validate(self) -> bool:
        if not (self.review.artifact.strip() and self.review.verdict.strip()):
            return False
        if not self.review.approved:
            # rejeição exige >= 1 item de feedback NÃO-vazio (auditabilidade)
            return any(str(item).strip() for item in self.review.feedback)
        return True

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_artifact_review, self.review)


@dataclass(frozen=True)
class ConfirmScopeCommand(HITLCommand):
    """Scope Confirmation — grava <user_response type="scope">."""

    confirmation: ScopeConfirmation

    def validate(self) -> bool:
        return bool(self.confirmation.step_id and self.confirmation.scope.strip())

    async def execute(self, writer: UserDecisionWriter) -> None:
        if self.validate():
            await _maybe_async(writer.submit_scope_confirmation, self.confirmation)


async def _maybe_async(fn, arg) -> None:
    """Invoca fn(arg) suportando fn síncrono ou assíncrono (writer double-mode)."""
    result = fn(arg)
    if hasattr(result, "__await__"):
        await result
