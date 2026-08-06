"""Testes para llc_graph.state — RF-G1A.5/6 do PRP-GRAPH-1A.

AceStateReader deriva NodeState dos nós a partir das sessões ACE
(.ace/index.json). Estado é sempre derivado — nunca fonte primária (D1/P3).
"""
import json
from pathlib import Path

from llc_graph.model import NodeState
from llc_graph.state import AceStateReader


def _write_index(tmp_path: Path, sessions: list[dict]):
    p = tmp_path / ".ace" / "index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"sessions": sessions}), encoding="utf-8")


def test_node_state_done_from_completed_session(tmp_path):
    """RF-G1A.5: sessão completed → NodeState.DONE."""
    _write_index(tmp_path, [
        {"session_id": "s-1", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-5") == NodeState.DONE


def test_node_state_missing_index_returns_pending(tmp_path):
    """RF-G1A.6: index.json ausente → PENDING, sem exceção."""
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-5") == NodeState.PENDING


def test_node_state_in_progress_is_running(tmp_path):
    _write_index(tmp_path, [
        {"session_id": "s-2", "llc_step_id": "10.8", "status": "in_progress",
         "timestamp": "2026-08-06T09:00:00"},
    ])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-10.8") == NodeState.RUNNING


def test_node_state_no_session_is_pending(tmp_path):
    _write_index(tmp_path, [])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-5") == NodeState.PENDING


def test_node_state_unknown_node_is_pending(tmp_path):
    _write_index(tmp_path, [
        {"session_id": "s-1", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-999") == NodeState.PENDING


def test_node_state_failed_session(tmp_path):
    _write_index(tmp_path, [
        {"session_id": "s-3", "llc_step_id": "5", "status": "failed",
         "timestamp": "2026-08-06T08:00:00"},
    ])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-5") == NodeState.FAILED


def test_node_state_latest_session_wins(tmp_path):
    _write_index(tmp_path, [
        {"session_id": "s-old", "llc_step_id": "5", "status": "failed",
         "timestamp": "2026-08-06T08:00:00"},
        {"session_id": "s-new", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    reader = AceStateReader(project_root=tmp_path)
    assert reader.node_state("step-5") == NodeState.DONE
