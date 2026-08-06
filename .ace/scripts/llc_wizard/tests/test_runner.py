"""Testes para llc_wizard.runner — RF-W1A.9/10/11 (WP3).

TDD: testes escritos primeiro (RED). Cobertura:
- RF-W1A.9: HarnessRunner.run_step() emite OutputEvent antes de CompletionEvent
- RF-W1A.10: FallbackRunner gera prompt copy-paste
- RF-W1A.11: select_runner() usa HarnessRunner se agente detectado
"""
import pytest

from llc_wizard.runner import (
    CompletionEvent,
    FallbackRunner,
    HarnessRunner,
    OutputEvent,
    select_runner,
)


def test_output_and_completion_events_are_dataclasses():
    out = OutputEvent(text="base do log")
    assert out.text == "base do log"
    comp = CompletionEvent(step_id="5", success=True)
    assert comp.success is True


def test_harness_runner_emits_output_then_completion():
    import asyncio
    from unittest.mock import patch

    async def consume():
        events = []
        runner = HarnessRunner(step_id="5", task="Arquitetura")
        with patch.object(runner, "_blocking_call", return_value="saida de teste"):
            async for ev in runner.run_step():
                events.append(ev)
        return events

    events = asyncio.run(consume())
    assert isinstance(events[0], OutputEvent)
    assert any(isinstance(e, CompletionEvent) for e in events)
    # OutputEvent precede CompletionEvent
    first_completion = next(i for i, e in enumerate(events) if isinstance(e, CompletionEvent))
    assert any(isinstance(e, OutputEvent) for e in events[:first_completion])


def test_fallback_runner_emits_copy_paste_prompt():
    import asyncio

    async def consume():
        events = []
        runner = FallbackRunner(step_id="5", task="Arquitetura")
        async for ev in runner.run_step():
            events.append(ev)
        return events

    events = asyncio.run(consume())
    combined = " ".join(e.text for e in events if isinstance(e, OutputEvent))
    assert "copie" in combined or "cole" in combined
    assert any(isinstance(e, CompletionEvent) for e in events)


def test_select_runner_uses_harness_when_agent_detected(monkeypatch):
    import shutil

    def fake_which(cmd):
        return "/usr/local/bin/claude" if cmd == "claude" else None

    monkeypatch.setattr(shutil, "which", fake_which)
    runner = select_runner(step_id="5")
    assert isinstance(runner, HarnessRunner)


def test_select_runner_uses_fallback_when_no_agent(monkeypatch):
    import shutil

    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    runner = select_runner(step_id="5")
    assert isinstance(runner, FallbackRunner)