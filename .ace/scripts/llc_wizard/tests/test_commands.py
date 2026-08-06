"""Testes para llc_wizard.commands — RF-W1B.2 (PRP-WIZARD-1B).

HITLCommand ABC + 6 comandos concretos com validate() e execute(writer).
"""
from __future__ import annotations

from pathlib import Path

import pytest


class FakeWriter:
    """Espia as chamadas do UserDecisionWriter (não toca disco)."""

    def __init__(self):
        self.calls = []

    async def submit_gate_decision(self, d):
        self.calls.append(("gate", d))

    async def submit_question_answer(self, a):
        self.calls.append(("question", a))

    async def submit_artifact_review(self, r):
        self.calls.append(("artifact", r))

    async def submit_scope_confirmation(self, s):
        self.calls.append(("scope", s))


def test_waive_gate_rejects_short_note():
    """RF-W1B.2: WaiveGateCommand.validate() False para nota < 10 chars."""
    from llc_wizard.commands import WaiveGateCommand
    from llc_wizard.decisions import GateDecision

    cmd = WaiveGateCommand(GateDecision(
        step="5", decision="approved", waiver=True, waiver_note="curta"))
    assert cmd.validate() is False


def test_waive_gate_accepts_note_min_10_chars():
    """RF-W1B.2: nota com >= 10 chars passa na validacao."""
    from llc_wizard.commands import WaiveGateCommand
    from llc_wizard.decisions import GateDecision

    cmd = WaiveGateCommand(GateDecision(
        step="5", decision="approved", waiver=True,
        waiver_note="Performance aceitavel porque o cache resolve"))
    assert cmd.validate() is True


def test_answer_question_requires_nonempty_answer():
    """RF-W1B.1: AnswerQuestionCommand rejeita resposta vazia."""
    from llc_wizard.commands import AnswerQuestionCommand
    from llc_wizard.decisions import QuestionAnswer

    empty = AnswerQuestionCommand(QuestionAnswer(
        question_id="q", question="Pergunta", answer=""))
    assert empty.validate() is False

    filled = AnswerQuestionCommand(QuestionAnswer(
        question_id="q", question="Pergunta", answer="resposta"))
    assert filled.validate() is True


def test_approve_gate_executes_writer():
    """RF: ApproveGateCommand.execute chama submit_gate_decision."""
    import asyncio

    from llc_wizard.commands import ApproveGateCommand
    from llc_wizard.decisions import GateDecision

    cmd = ApproveGateCommand(GateDecision(step="5", decision="approved"))
    writer = FakeWriter()
    assert cmd.validate() is True
    asyncio.run(cmd.execute(writer))
    assert len(writer.calls) == 1
    kind, d = writer.calls[0]
    assert kind == "gate" and d.step == "5" and d.decision == "approved"


def test_reject_gate_executes_writer():
    """RF: RejectGateCommand grava decision=rejected."""
    import asyncio

    from llc_wizard.commands import RejectGateCommand
    from llc_wizard.decisions import GateDecision

    cmd = RejectGateCommand(GateDecision(step="5", decision="rejected"))
    writer = FakeWriter()
    assert cmd.validate() is True
    asyncio.run(cmd.execute(writer))
    assert writer.calls[0][1].decision == "rejected"


def test_review_artifact_executes_writer():
    """RF: ReviewArtifactCommand chama submit_artifact_review."""
    import asyncio

    from llc_wizard.commands import ReviewArtifactCommand
    from llc_wizard.decisions import ArtifactReview

    cmd = ReviewArtifactCommand(ArtifactReview(
        artifact="docs/prps/PRP-WIZARD-1B.md", verdict="approved",
        comments="Coerente"))
    writer = FakeWriter()
    assert cmd.validate() is True
    asyncio.run(cmd.execute(writer))
    assert writer.calls[0][0] == "artifact"


def test_confirm_scope_executes_writer():
    """RF: ConfirmScopeCommand chama submit_scope_confirmation."""
    import asyncio

    from llc_wizard.commands import ConfirmScopeCommand
    from llc_wizard.decisions import ScopeConfirmation

    cmd = ConfirmScopeCommand(ScopeConfirmation(
        step_id="5", scope="Steps 1-5 do pipeline"))
    writer = FakeWriter()
    assert cmd.validate() is True
    asyncio.run(cmd.execute(writer))
    assert writer.calls[0][0] == "scope"
