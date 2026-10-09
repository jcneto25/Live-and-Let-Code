"""Testes do NodeMachine LLC 2.0 (Fase 4).

Valida o statechart determinístico: transições, guards, snapshot/restore.
"""
from __future__ import annotations

import pytest

from llc2.contracts import (
    Action,
    Automation,
    Check,
    DagView,
    Decision,
    DecisionState,
    Event,
    EventType,
    HardEvalResult,
    NodeMachine,
    PolicySpec,
    QuestionSet,
    RiskClass,
    load_policy,
    load_question_sets,
)


class FakeDagView:
    """DagView fake para testes."""

    def __init__(self, satisfied: bool = True):
        self._satisfied = satisfied

    def deps_satisfied(self, node_id: str) -> bool:
        return self._satisfied

    def requires_human(self, node_id: str) -> RiskClass:
        return RiskClass.R1

    def risk_class(self, node_id: str) -> RiskClass:
        return RiskClass.R1

    def impact_of(self, node_id: str) -> frozenset[str]:
        return frozenset()

    def frontier(self) -> tuple[str, ...]:
        return ()


@pytest.fixture
def policy() -> PolicySpec:
    return load_policy()


@pytest.fixture
def question_sets() -> dict[str, QuestionSet]:
    return load_question_sets()


@pytest.fixture
def question_set(question_sets) -> QuestionSet:
    return question_sets["task-classification"]


@pytest.fixture
def machine(policy, question_set) -> NodeMachine:
    return NodeMachine(node_id="test-node", policy=policy, question_set=question_set)


class TestNodeMachineBasics:
    """Testes básicos do NodeMachine."""

    def test_initial_state_is_idle_before_start(self, machine):
        """Antes de start, configuração mostra idle."""
        config = machine.configuration()
        assert config["state"] == "idle"
        assert config["configuration"] == "idle"

    def test_start_returns_decision_state(self, machine, question_set, policy):
        """start() retorna DecisionState no estado initial."""
        state = machine.start("test-node", question_set, policy)
        assert isinstance(state, DecisionState)
        assert state.node_id == "test-node"
        assert state.state_id == "active.preparing"
        assert state.decision_kind == "early_commitment"

    def test_after_start_state_is_active_preparing(self, machine, question_set, policy):
        """Após start, estado vai para active.preparing."""
        machine.start("test-node", question_set, policy)
        config = machine.configuration()
        assert config["state"] == "active.preparing"
        assert config["configuration"] == "active.preparing"


class TestNodeMachineTransitions:
    """Testes das transições do statechart."""

    def _evt(self, type_: EventType, node_id: str = "test-node", eid: str = "e1") -> Event:
        return Event(event_id=eid, type=type_, node_id=node_id)

    def _decision(self, automation: Automation, action: Action, evidence: tuple = ()) -> Decision:
        policy = load_policy()
        return Decision(
            automation=automation,
            action=action,
            evidence_refs=evidence,
            reason="test",
            policy_id=policy.id,
            policy_version=policy.version,
            thresholds_hash=policy.thresholds_hash,
        )

    def _hard(self, ok: bool = True) -> HardEvalResult:
        return HardEvalResult(checks=(Check(name="pytest", passed=ok),))

    def test_start_event_from_idle(self, machine):
        """Event START de idle -> active.preparing (se deps_satisfied)."""
        machine._dag = FakeDagView(satisfied=True)
        event = self._evt(EventType.START, node_id="test-node")
        state = machine.send(event)
        assert state.state_id == "active.preparing"

    def test_skip_event_from_idle(self, machine):
        """Event SKIP de idle -> skipped."""
        event = self._evt(EventType.SKIP, node_id="test-node")
        state = machine.send(event)
        assert state.state_id == "skipped"

    def test_agent_returned_transition(self, machine):
        """AGENT_RETURNED: active.preparing -> active.agent_running."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))

        event = self._evt(EventType.AGENT_RETURNED)
        state = machine.send(event)
        assert state.state_id == "active.agent_running"

    def test_hard_eval_done_transition(self, machine):
        """HARD_EVAL_DONE: active.agent_running -> active.verifying."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))

        event = self._evt(EventType.HARD_EVAL_DONE)
        state = machine.send(event)
        assert state.state_id == "active.verifying"

    def test_semantic_not_needed_when_no_question_set(self, machine):
        """SEMANTIC_NOT_NEEDED quando hard passou e não há question set."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))

        machine._hard = self._hard(True)
        machine._has_question_set = False

        event = self._evt(EventType.SEMANTIC_NOT_NEEDED)
        state = machine.send(event)
        assert state.state_id == "active.verifying.semantic.not_needed"
        assert machine._regions.get("semantic") == "not_needed"

    def test_verification_complete_join(self, machine):
        """VERIFICATION_COMPLETE join: hard passed + semantic ready/not_needed -> active.deciding."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}

        event = self._evt(EventType.VERIFICATION_COMPLETE)
        state = machine.send(event)
        assert state.state_id == "active.deciding"

    def test_verification_complete_hard_failed_goes_awaiting_human(self, machine):
        """VERIFICATION_COMPLETE com hard failed -> governance.awaiting_human."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(False)
        machine._regions = {"hard": "failed", "semantic": "ready"}

        event = self._evt(EventType.VERIFICATION_COMPLETE)
        state = machine.send(event)
        assert state.state_id == "governance.awaiting_human"

    def test_decided_auto_routing(self, machine):
        """DECIDED com AUTO -> governance.auto_approved."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))

        machine._decision = self._decision(Automation.AUTO, Action.CONTINUE)
        event = self._evt(EventType.DECIDED)
        state = machine.send(event)
        assert state.state_id == "governance.auto_approved"

    def test_decided_review_routing(self, machine):
        """DECIDED com REVIEW_REQUIRED -> governance.awaiting_human."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))

        machine._decision = self._decision(Automation.REVIEW_REQUIRED, Action.IMPLEMENT_WITH_REVIEW)
        event = self._evt(EventType.DECIDED)
        state = machine.send(event)
        assert state.state_id == "governance.awaiting_human"

    def test_decided_human_routing(self, machine):
        """DECIDED com HUMAN_REQUIRED -> governance.awaiting_human."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))

        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        event = self._evt(EventType.DECIDED)
        state = machine.send(event)
        assert state.state_id == "governance.awaiting_human"

    def test_human_approved_from_awaiting(self, machine):
        """HUMAN_APPROVED de awaiting -> governance.auto_approved."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        machine.send(self._evt(EventType.DECIDED))

        event = self._evt(EventType.HUMAN_APPROVED)
        state = machine.send(event)
        assert state.state_id == "governance.auto_approved"

    def test_human_rejected_with_retries_goes_rework(self, machine):
        """HUMAN_REJECTED com retries left -> governance.rework."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        machine.send(self._evt(EventType.DECIDED))
        machine._retries = 0
        machine._max_retries = 3

        event = self._evt(EventType.HUMAN_REJECTED)
        state = machine.send(event)
        assert state.state_id == "governance.rework"
        assert machine._retries == 1

    def test_retry_from_rework_goes_preparing(self, machine):
        """RETRY de rework -> active.preparing (com rollback)."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        machine.send(self._evt(EventType.DECIDED))
        machine._retries = 0
        machine._max_retries = 3
        machine.send(self._evt(EventType.HUMAN_REJECTED))

        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine._hard = self._hard(True)
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)

        event = self._evt(EventType.RETRY)
        state = machine.send(event)
        assert state.state_id == "active.preparing"
        assert machine._regions == {}
        assert machine._hard_eval is None
        assert machine._decision_obj is None

    def test_applied_with_hard_passed_goes_done(self, machine):
        """APPLIED com hard passed -> done (via active.applying)."""
        machine.start("test-node", machine.question_set, machine.policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.AUTO, Action.CONTINUE, evidence=("evidence1",))
        machine.send(self._evt(EventType.DECIDED))
        # First APPLIED: governance.auto_approved -> active.applying (gate_has_evidence)
        machine.send(self._evt(EventType.APPLIED))
        # Second APPLIED: active.applying -> done (hard_eval_passed)
        machine._hard = self._hard(True)
        machine.send(self._evt(EventType.APPLIED))
        state = machine.send(self._evt(EventType.APPLIED))
        assert state.state_id == "done"


class TestNodeMachineSnapshotRestore:
    """Testes de snapshot e restore."""

    def _evt(self, type_: EventType, node_id: str = "test-node", eid: str = "e1") -> Event:
        return Event(event_id=eid, type=type_, node_id=node_id)

    def _decision(self, automation: Automation, action: Action, evidence: tuple = ()) -> Decision:
        policy = load_policy()
        return Decision(
            automation=automation,
            action=action,
            evidence_refs=evidence,
            reason="test",
            policy_id=policy.id,
            policy_version=policy.version,
            thresholds_hash=policy.thresholds_hash,
        )

    def test_snapshot_contains_state(self, machine, question_set, policy):
        """Snapshot contém estado e metadados."""
        machine.start("test-node", question_set, policy)
        snap = machine.snapshot()

        assert "state" in snap
        assert snap["state"] == "active.preparing"
        assert "node_id" in snap
        assert "retries" in snap
        assert "regions" in snap

    def test_restore_returns_to_state(self, machine, question_set, policy):
        """Restore repõe o estado do snapshot."""
        machine.start("test-node", question_set, policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))

        snap = machine.snapshot()

        machine2 = NodeMachine(node_id="test-node", policy=policy, question_set=question_set)
        machine2.restore(snap)

        assert machine2.configuration()["state"] == "active.agent_running"

    def test_restore_preserves_retries(self, machine, question_set, policy):
        """Restore preserva contagem de retries."""
        machine.start("test-node", question_set, policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        machine.send(self._evt(EventType.DECIDED))
        machine._retries = 1
        machine._max_retries = 3
        machine.send(self._evt(EventType.HUMAN_REJECTED))

        snap = machine.snapshot()

        machine2 = NodeMachine(node_id="test-node", policy=policy, question_set=question_set)
        machine2.restore(snap)

        # HUMAN_REJECTED triggers increment_retries, so retries becomes 2
        assert machine2.configuration()["retries"] == 2


class TestNodeMachineErrorHandling:
    """Testes de tratamento de erros."""

    def _evt(self, type_: EventType, node_id: str = "test-node", eid: str = "e1") -> Event:
        return Event(event_id=eid, type=type_, node_id=node_id)

    def test_send_unknown_event_no_crash(self, machine, question_set, policy):
        """Evento desconhecido não crasha."""
        machine.start("test-node", question_set, policy)
        event = self._evt(EventType.HUMAN_APPROVED, node_id="test-node")
        state = machine.send(event)
        assert state is not None
        assert state.state_id == "active.preparing"

    def test_send_wrong_node_id_ignored(self, machine, question_set, policy):
        """Evento com node_id diferente é ignorado."""
        machine.start("test-node", question_set, policy)
        event = self._evt(EventType.START, node_id="other-node")
        state = machine.send(event)
        assert state.state_id == "active.preparing"


class TestNodeMachinePersistence:
    """Testes de campos de persistência."""

    def _evt(self, type_: EventType, node_id: str = "test-node", eid: str = "e1") -> Event:
        return Event(event_id=eid, type=type_, node_id=node_id)

    def test_configuration_includes_all_fields(self, machine, question_set, policy):
        """Configuration inclui todos campos necessários para persistência."""
        machine.start("test-node", question_set, policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        config = machine.configuration()

        required = {"node_id", "machine", "version", "configuration",
                    "retries", "gate_id", "policy_version", "last_event", "updated_at"}
        assert required.issubset(config.keys())
        assert config["node_id"] == "test-node"
        assert config["machine"] == "NodeMachine"
        assert config["policy_version"] == machine.policy.version


class TestNodeMachineCapabilities:
    """Testes de capabilities por estado."""

    def _evt(self, type_: EventType, node_id: str = "test-node", eid: str = "e1") -> Event:
        return Event(event_id=eid, type=type_, node_id=node_id)

    def _decision(self, automation: Automation, action: Action, evidence: tuple = ()) -> Decision:
        policy = load_policy()
        return Decision(
            automation=automation,
            action=action,
            evidence_refs=evidence,
            reason="test",
            policy_id=policy.id,
            policy_version=policy.version,
            thresholds_hash=policy.thresholds_hash,
        )

    def _hard(self, ok: bool = True) -> HardEvalResult:
        return HardEvalResult(checks=(Check(name="pytest", passed=ok),))

    def test_capabilities_idle(self, machine):
        """Capabilities em idle."""
        caps = machine.capabilities()
        assert "read_index" in caps
        assert "read_artifacts" in caps

    def test_capabilities_active_preparing(self, machine, question_set, policy):
        """Capabilities em active.preparing."""
        machine.start("test-node", question_set, policy)
        caps = machine.capabilities()
        assert "build_decision_state" in caps
        assert "jev_eval" in caps

    def test_capabilities_awaiting_human(self, machine, question_set, policy):
        """Capabilities em governance.awaiting_human."""
        machine.start("test-node", question_set, policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.HUMAN_REQUIRED, Action.ESCALATE)
        machine.send(self._evt(EventType.DECIDED))

        caps = machine.capabilities()
        assert "request_approval" in caps
        assert "show_evidence" in caps

    def test_capabilities_done(self, machine, question_set, policy):
        """Capabilities em done."""
        machine.start("test-node", question_set, policy)
        machine._dag = FakeDagView(satisfied=True)
        machine.send(self._evt(EventType.START))
        machine.send(self._evt(EventType.AGENT_RETURNED))
        machine.send(self._evt(EventType.HARD_EVAL_DONE))
        machine._hard = self._hard(True)
        machine._regions = {"hard": "passed", "semantic": "not_needed"}
        machine.send(self._evt(EventType.VERIFICATION_COMPLETE))
        machine._decision = self._decision(Automation.AUTO, Action.CONTINUE, evidence=("evidence1",))
        machine.send(self._evt(EventType.DECIDED))
        # First APPLIED: governance.auto_approved -> active.applying (gate_has_evidence)
        machine.send(self._evt(EventType.APPLIED))
        # Second APPLIED: active.applying -> done (hard_eval_passed)
        machine._hard = self._hard(True)
        machine.send(self._evt(EventType.APPLIED))

        caps = machine.capabilities()
        assert "read_index" in caps
        assert "read_artifacts" in caps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])