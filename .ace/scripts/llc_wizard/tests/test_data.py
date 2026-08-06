"""Testes para llc_wizard.data — RF-W1A.1 e RF-W1A.2 (WP1).

TDD: testes escritos primeiro (RED). Cobertura dos requisitos:
- RF-W1A.1: StepStatus enum com exatamente 7 estados
- RF-W1A.2: StepInfo é frozen dataclass (imutável)
"""
import pytest

from llc_wizard.data import (
    GateInfo,
    GateItem,
    PipelineDataReader,
    PipelineStatus,
    StepInfo,
    StepStatus,
)


def test_step_status_has_exactly_seven_states():
    estados = {s.value for s in StepStatus}
    assert estados == {
        "pending",
        "in_progress",
        "gate_pending",
        "completed",
        "failed",
        "skipped",
        "excluded",
    }


def test_step_info_is_frozen():
    info = StepInfo(
        id="5", name="Arquitetura", status=StepStatus.PENDING, in_pipeline=True
    )
    with pytest.raises(Exception):
        info.id = "outro"


def test_gate_item_required_defaults_true():
    item = GateItem(id="1", description="Visão completa?")
    assert item.required is True
    assert item.checked is False


def test_gate_info_all_required_met_false_when_unchecked():
    gate = GateInfo(
        id="1",
        items=[GateItem(id="1", description="a"), GateItem(id="2", description="b")],
    )
    assert len(gate.items) == 2
    assert all(i.required for i in gate.items)
    assert gate.all_required_met is False


def test_progress_percent_counts_only_in_pipeline_steps():
    steps = [
        StepInfo("1", "A", StepStatus.COMPLETED, in_pipeline=True),
        StepInfo("2", "B", StepStatus.COMPLETED, in_pipeline=True),
        StepInfo("3", "C", StepStatus.PENDING, in_pipeline=True),
        StepInfo("4", "D", StepStatus.EXCLUDED, in_pipeline=False),
    ]
    status = PipelineStatus(steps=steps)
    assert status.progress_percent == pytest.approx(66.7, abs=0.1)


def test_reader_tolerates_missing_index(project_root):
    (project_root / ".ace" / "index.json").unlink()
    reader = PipelineDataReader(project_root)
    status = reader.get_status()
    assert isinstance(status, PipelineStatus)
    assert all(s.status == StepStatus.PENDING for s in status.steps if s.in_pipeline)
    assert all(s.status == StepStatus.EXCLUDED for s in status.steps if not s.in_pipeline)


def test_reader_parses_gate_from_gates_json(project_root, make_gates):
    make_gates(
        project_root,
        {
            "gates": {
                "1": {
                    "label": "Visao Estrategica + Modulos",
                    "checklist": ["Visão cobre todo o escopo?", "Módulos OK?"],
                }
            }
        },
    )
    reader = PipelineDataReader(project_root)
    gate = reader.get_gate_for_step("1")
    assert gate is not None
    assert len(gate.items) == 2
    assert all(i.required for i in gate.items)
    assert gate.all_required_met is False


def test_reader_returns_none_for_unknown_gate(project_root):
    reader = PipelineDataReader(project_root)
    assert reader.get_gate_for_step("999") is None


def test_status_since_returns_last_timestamp(project_root, make_index):
    make_index(
        project_root,
        [
            {"llc_step_id": "5", "status": "in_progress", "timestamp": "2026-08-05T10:00:00"},
            {"llc_step_id": "5", "status": "completed", "timestamp": "2026-08-05T11:00:00"},
        ],
    )
    reader = PipelineDataReader(project_root)
    assert reader.get_status_since("5") == __import__("datetime").datetime.fromisoformat(
        "2026-08-05T11:00:00"
    )


def test_status_since_returns_epoch_when_no_session(project_root):
    reader = PipelineDataReader(project_root)
    assert reader.get_status_since("5") == __import__("datetime").datetime.fromtimestamp(0)


def test_get_pending_hitl_returns_list(project_root):
    reader = PipelineDataReader(project_root)
    assert reader.get_pending_hitl() == []


def test_confirmed_session_derives_completed(project_root, make_index):
    make_index(
        project_root,
        [{"llc_step_id": "5", "status": "completed", "timestamp": "2026-08-05T10:00:00"}],
    )
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["5"].status == StepStatus.COMPLETED


def test_gate_pending_when_step_has_gate_and_in_progress(project_root, make_index, make_gates):
    make_gates(project_root, {"gates": {"6": {"checklist": ["OK?"]}}})
    make_index(
        project_root,
        [{"llc_step_id": "5", "status": "in_progress", "timestamp": "2026-08-05T10:00:00"}],
    )
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["5"].status == StepStatus.GATE_PENDING


def _session_file(project_root, session_id, gate_decision):
    """Cria o arquivo .md de uma sessao com <gate_result> real (nao-placeholder)."""
    path = project_root / ".ace" / "sessions" / f"{session_id}.md"
    path.write_text(
        f"---\nstatus: completed\n---\n\n"
        f'<gate_result step="5" decision="{gate_decision}" reviewer="harness">'
        f"human gate</gate_result>\n",
        encoding="utf-8",
    )
    return path


def test_derives_failed_when_gate_rejected(project_root, make_index):
    """Regra 1 §7.6: sessao completed + <gate_result decision=rejected> -> failed."""
    _session_file(project_root, "2026-08-05-090", "rejected")
    make_index(
        project_root,
        [{
            "session_id": "2026-08-05-090",
            "llc_step_id": "5",
            "status": "completed",
            "timestamp": "2026-08-05T10:00:00",
        }],
    )
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["5"].status == StepStatus.FAILED


def test_derives_completed_when_gate_approved(project_root, make_index):
    """Regra 2 §7.6: sessao completed + gate approved -> completed."""
    _session_file(project_root, "2026-08-05-091", "approved")
    make_index(
        project_root,
        [{
            "session_id": "2026-08-05-091",
            "llc_step_id": "5",
            "status": "completed",
            "timestamp": "2026-08-05T10:00:00",
        }],
    )
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["5"].status == StepStatus.COMPLETED


def test_derives_in_progress_when_no_gate(project_root, make_index):
    """Regra 4 §7.6: step sem gate em gates.json + sessao in_progress -> in_progress."""
    make_index(
        project_root,
        [{"llc_step_id": "11", "status": "in_progress", "timestamp": "2026-08-05T10:00:00"}],
    )
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["11"].status == StepStatus.IN_PROGRESS


def test_derives_skipped_when_skip_note_exists(project_root, make_index):
    """Regra 5 §7.6: skip note em docs/delta/skip-notes/step-{id}.md -> skipped."""
    skip = project_root / "docs" / "delta" / "skip-notes"
    skip.mkdir(parents=True)
    (skip / "step-5.md").write_text("Step nao afetado nesta onda.\n", encoding="utf-8")
    make_index(project_root, [])
    reader = PipelineDataReader(project_root)
    steps = {s.id: s for s in reader.get_steps()}
    assert steps["5"].status == StepStatus.SKIPPED