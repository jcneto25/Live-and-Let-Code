"""Fase 2 (R-4) — política impact_of-first no fluxo de Delta.

Jev/avaliação semântica só no residual afetado por `GraphEngine.impact_of()`:
fora do conjunto afetado → skip determinístico, sem semântica.
"""
from __future__ import annotations

import pytest

from llc_delta.skip import (
    ALWAYS_RUN,
    residual_impact,
    should_use_semantic_impact,
)
from llc_delta.report import (
    affected_nodes_for_delta,
    should_assess_step_impact,
)
from llc_graph.engine import GraphEngine
from llc_graph.model import EdgeKind, Graph, GraphEdge, GraphNode, NodeKind


def _chain() -> Graph:
    """step-1 → step-2 → step-3 (mesmo formato do builder/test_engine)."""
    g = Graph()
    for nid in ("step-1", "step-2", "step-3"):
        g.add_node(GraphNode(id=nid, kind=NodeKind.STEP, requires_human=False,
                             auto_parallelizable=True))
    for src, tgt in (("step-1", "step-2"), ("step-2", "step-3")):
        g.add_edge(GraphEdge(source=src, target=tgt, kind=EdgeKind.DEPENDS_ON))
    return g


@pytest.fixture
def engine():
    return GraphEngine(_chain())


# ── Helpers puros (skip.py) ─────────────────────────────────────────────────

def test_member_of_affected_set_needs_semantic():
    assert should_use_semantic_impact("2", {"step-1", "step-2"}) is True


def test_outside_affected_set_skips_semantic():
    assert should_use_semantic_impact("3", {"step-1"}) is False


def test_empty_affected_set_needs_no_semantic():
    assert should_use_semantic_impact("1", set()) is False
    assert should_use_semantic_impact("1", None) is False


def test_step_alias_resolves_to_canonical():
    assert should_use_semantic_impact("verify", {"step-11.2"}) is True


def test_non_step_nodes_never_match_a_step():
    assert should_use_semantic_impact("5", {"gate-5", "PRP-001"}) is False


def test_always_run_steps_always_assessed():
    """ALWAYS_RUN fora do residual ainda avalia (fail-closed, tarefa 2.6)."""
    for step_id in sorted(ALWAYS_RUN):
        assert should_use_semantic_impact(step_id, {"step-1"}) is True


def test_always_run_guard_beats_empty_set():
    """Exceção documentada à regra 2.6: guarda vence conjunto vazio."""
    assert should_use_semantic_impact("11", set()) is True
    assert should_use_semantic_impact("10.8", None) is True


def test_residual_direct():
    assert residual_impact("2", {"step-2", "step-3"}, {"step-2"}) == "direct"


def test_residual_propagated():
    assert residual_impact("3", {"step-2", "step-3"}, {"step-2"}) == "propagated"


def test_residual_none():
    assert residual_impact("1", {"step-2"}, set()) == "none"


def test_residual_direct_wins_over_affected():
    assert residual_impact("2", set(), {"step-2"}) == "direct"


# ── Wiring com o grafo (report.py) ───────────────────────────────────────────

def test_affected_nodes_unions_impact_of(engine):
    assert affected_nodes_for_delta({"step-1"}, engine=engine) == {
        "step-2", "step-3"}


def test_affected_nodes_empty_roots_is_empty(engine):
    assert affected_nodes_for_delta(set(), engine=engine) == frozenset()


def test_affected_nodes_unknown_root_raises(engine):
    with pytest.raises(KeyError):
        affected_nodes_for_delta({"GHOST"}, engine=engine)


def test_gate_true_for_downstream_step(engine):
    assert should_assess_step_impact("3", {"step-1"}, engine=engine) is True


def test_gate_false_for_changed_root_itself(engine):
    """A raiz é a mudança conhecida (vai p/ execute_steps); sem Jev p/ decidir."""
    assert should_assess_step_impact("1", {"step-1"}, engine=engine) is False


def test_gate_false_outside_residual(engine):
    assert should_assess_step_impact("1", {"step-2"}, engine=engine) is False


def test_gate_inherits_always_run_guard(engine):
    assert should_assess_step_impact("11.2", {"step-1"}, engine=engine) is True


def test_gate_true_on_unknown_root_conservative(engine):
    assert should_assess_step_impact("9", {"GHOST"}, engine=engine) is True


def test_gate_true_when_engine_unavailable(monkeypatch):
    import llc_delta.report as rep

    monkeypatch.setattr(rep, "_default_engine", lambda: None)
    assert should_assess_step_impact("3", {"step-1"}) is True


def test_gate_flag_off_is_legacy_always_true(monkeypatch, engine):
    monkeypatch.setenv("LLC2_DELTA_IMPACT_FIRST", "0")
    assert should_assess_step_impact("1", {"step-2"}, engine=engine) is True
    assert should_assess_step_impact("1", set(), engine=engine) is True


def test_gate_default_flag_is_active(monkeypatch, engine):
    """Default 1 (§9): sem env, o portão restringe (fora do residual → False)."""
    monkeypatch.delenv("LLC2_DELTA_IMPACT_FIRST", raising=False)
    assert should_assess_step_impact("1", {"step-2"}, engine=engine) is False
