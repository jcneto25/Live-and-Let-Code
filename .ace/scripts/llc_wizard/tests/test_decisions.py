"""Testes para llc_wizard.decisions — RF-W1B.1, .3, .4, .5 (PRP-WIZARD-1B).

UserDecisionWriter (append-only) + RealtimePromptCollector (asyncio.Event).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


@pytest.fixture
def make_sessions_file(tmp_path: Path):
    def _make(content: str = "linha-inicial\n") -> Path:
        f = tmp_path / ".ace" / "sessions" / "2026-08-06-004.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return f

    return _make


# ─────────────────────────── UserDecisionWriter ───────────────────────────


def test_writer_appends_question_response(make_sessions_file):
    """RF-W1B.1: UserDecisionWriter persiste <user_response type="question">."""
    from llc_wizard.decisions import QuestionAnswer, UserDecisionWriter

    sf = make_sessions_file()
    writer = UserDecisionWriter(sf)
    writer.submit_question_answer(
        QuestionAnswer(
            question_id="q-1",
            question="Qual escopo?",
            answer="Apenas steps 1-5",
            step_id="5",
        )
    )

    content = sf.read_text(encoding="utf-8")
    assert '<user_response type="question" question_id="q-1"' in content
    assert "<question>Qual escopo?</question>" in content
    assert "<answer>Apenas steps 1-5</answer>" in content
    assert content.startswith("linha-inicial\n")


def test_writer_append_only_never_truncates(make_sessions_file):
    """DoD: UserDecisionWriter usa apenas append — conteudo pre-existente intacto."""
    from llc_wizard.decisions import QuestionAnswer, UserDecisionWriter

    sf = make_sessions_file("---\nfront\n---\n\n## Deltas\n")
    writer = UserDecisionWriter(sf)
    writer.submit_question_answer(
        QuestionAnswer(question_id="a", question="q", answer="r")
    )
    writer.submit_question_answer(
        QuestionAnswer(question_id="b", question="q", answer="r")
    )
    content = sf.read_text(encoding="utf-8")
    assert content.count('<user_response type="question"') == 2
    assert content.startswith("---\nfront\n---\n\n## Deltas\n")


def test_writer_gate_decision_with_waiver_note(make_sessions_file):
    """RF-W1B.2: gate_result com waiver grava <waiver_note> (min 10 chars)."""
    from llc_wizard.decisions import GateDecision, UserDecisionWriter

    sf = make_sessions_file()
    writer = UserDecisionWriter(sf)
    writer.submit_gate_decision(
        GateDecision(
            step="5", decision="approved", waiver=True, waiver_note="Nota longa doi"
        )
    )
    content = sf.read_text(encoding="utf-8")
    assert 'waiver="true"' in content
    assert "<waiver_note>Nota longa doi</waiver_note>" in content


# ────────────────────────── RealtimePromptCollector ──────────────────────────


def test_collector_blocks_until_response():
    """RF-W1B.3: request_input bloqueia (asyncio.Event) ate submit_response."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector

    c = RealtimePromptCollector()

    async def run():
        task = asyncio.create_task(
            c.request_input(PromptRequest(prompt_id="p-1", step_id="5", text="Pergunta"))
        )
        await asyncio.sleep(0.05)
        assert not task.done()  # ainda bloqueado
        c.submit_response("p-1", "minha resposta")
        result = await task
        assert result == "minha resposta"

    asyncio.run(run())


def test_collector_submit_releases_only_matching_prompt():
    """RF-W1B.5: submit_response libera apenas o prompt correspondente."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector

    c = RealtimePromptCollector()

    async def run():
        t1 = asyncio.create_task(c.request_input(
            PromptRequest(prompt_id="p-1", text="a")))
        t2 = asyncio.create_task(c.request_input(
            PromptRequest(prompt_id="p-2", text="b")))
        await asyncio.sleep(0.02)
        c.submit_response("p-2", "resp2")  # libera apenas p-2
        r2 = await t2
        assert r2 == "resp2"
        assert not t1.done()  # p-1 continua em espera
        c.submit_response("p-1", "resp1")
        await t1

    asyncio.run(run())


def test_prompts_fifo_order():
    """RF-W1B.4: múltiplos prompts preservam ordem FIFO de abertura."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector

    c = RealtimePromptCollector()

    async def run():
        tasks = [
            asyncio.create_task(c.request_input(
                PromptRequest(prompt_id=f"p-{i}", text=str(i))))
            for i in range(3)
        ]
        await asyncio.sleep(0.05)
        for i in range(3):
            c.submit_response(f"p-{i}", f"r{i}")
        results = [await t for t in tasks]
        assert results == ["r0", "r1", "r2"]

    asyncio.run(run())


def test_pending_prompts_exposed_for_ui():
    """RF: pending_prompts expõe prompts aguardando humana (para a UI)."""
    from llc_wizard.decisions import PromptRequest, RealtimePromptCollector

    c = RealtimePromptCollector()

    async def run():
        asyncio.create_task(c.request_input(
            PromptRequest(prompt_id="p9", text="x", step_id="5")))
        asyncio.create_task(c.request_input(
            PromptRequest(prompt_id="p8", text="y", step_id="3")))
        await asyncio.sleep(0.02)
        assert len(c.pending_prompts) == 2
        ids = [p.prompt_id for p in c.pending_prompts]
        assert set(ids) == {"p9", "p8"}

    asyncio.run(run())
