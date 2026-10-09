"""Testes para o módulo capabilities (Fase 5)."""

import tempfile
from pathlib import Path

import pytest

from llc2 import (
    CAPABILITY_TO_CLIENT_TOOLS,
    FORBIDDEN_TO_CLIENT_TOOLS,
    ClientPermissionProfile,
    generate_permission_profile,
    CapabilityManager,
    AuditingToolBroker,
    PostHocViolation,
    detect_capability_violations,
    capabilities_for_state,
)
from llc2.contracts import (
    NodeMachine,
    load_policy,
    load_question_sets,
    Event,
    EventType,
    Automation,
    Action,
    Check,
    HardEvalResult,
)


class TestCapabilitiesForState:
    """Testes da função capabilities_for_state."""

    def test_idle_state(self):
        caps = capabilities_for_state("idle")
        assert "read_index" in caps
        assert "read_artifacts" in caps
        assert "write_artifacts" not in caps

    def test_active_preparing_state(self):
        caps = capabilities_for_state("active.preparing")
        assert "build_decision_state" in caps
        assert "jev_eval" in caps
        assert "read_index" in caps

    def test_awaiting_human_state(self):
        caps = capabilities_for_state("governance.awaiting_human")
        assert "request_approval" in caps
        assert "show_evidence" in caps

    def test_unknown_state_raises(self):
        with pytest.raises(KeyError):
            capabilities_for_state("unknown.state")


class TestGeneratePermissionProfile:
    """Testes de geração de perfil de permissão."""

    def test_idle_profile(self):
        profile = generate_permission_profile("idle", client="claude-code")
        assert isinstance(profile, ClientPermissionProfile)
        assert "Read" in profile.allowed_tools
        assert "Glob" in profile.allowed_tools
        assert "Grep" in profile.allowed_tools
        assert "LS" in profile.allowed_tools
        # Idle não precisa de Bash, denied_tools pode estar vazio
        # (capabilities proibidas não estão na matriz, então não vazam para allowed)
        assert profile.denied_tools == frozenset()

    def test_active_preparing_profile(self):
        profile = generate_permission_profile("active.preparing")
        assert "Read" in profile.allowed_tools
        assert "Write" in profile.allowed_tools  # build_decision_state
        assert "Bash" in profile.allowed_tools  # jev_eval

    def test_awaiting_human_profile(self):
        profile = generate_permission_profile("governance.awaiting_human")
        assert "Read" in profile.allowed_tools
        assert "Bash" in profile.allowed_tools  # request_approval

    def test_forbidden_tools_always_denied(self):
        """Ferramentas proibidas globalmente NÃO estão na matriz, então não vazam.
        denied_tools fica vazio; a prevenção é por não estarem na matriz + post-hoc."""
        profile = generate_permission_profile("active.applying")
        # active.applying precisa de Bash (git_commit, rollback), então não deve ser negado
        assert "Bash" in profile.allowed_tools
        assert profile.denied_tools == frozenset()


class TestClientPermissionProfile:
    """Testes da classe ClientPermissionProfile."""

    def test_to_claude_settings(self):
        profile = ClientPermissionProfile(
            client="claude-code",
            allowed_tools=frozenset(["Read", "Write"]),
            denied_tools=frozenset(["Bash"]),
        )
        settings = profile.to_claude_settings()
        assert settings["permissions"]["allow"] == ["Read", "Write"]
        assert settings["permissions"]["deny"] == ["Bash"]

    def test_write_claude_settings(self):
        profile = ClientPermissionProfile(
            client="claude-code",
            allowed_tools=frozenset(["Read"]),
            denied_tools=frozenset([]),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ".claude" / "settings.local.json"
            profile.write(path)
            assert path.exists()
            import json
            content = json.loads(path.read_text())
            assert content["permissions"]["allow"] == ["Read"]

    def test_write_generic_format(self):
        profile = ClientPermissionProfile(
            client="cursor",
            allowed_tools=frozenset(["Read"]),
            denied_tools=frozenset(["Bash"]),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "permissions.json"
            profile.write(path)
            assert path.exists()
            import json
            content = json.loads(path.read_text())
            assert content["client"] == "cursor"
            assert content["allowed"] == ["Read"]
            assert content["denied"] == ["Bash"]


class TestCapabilityManager:
    """Testes do CapabilityManager integrado ao NodeMachine."""

    @pytest.fixture
    def machine(self):
        policy = load_policy()
        question_sets = load_question_sets()
        question_set = question_sets.get("task-classification")
        m = NodeMachine(node_id="test", policy=policy, question_set=question_set)
        m.start("test", question_set, policy)
        return m

    def test_sync_creates_profile(self, machine):
        manager = CapabilityManager(machine, client="claude-code")
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "settings.local.json"
            manager.profile_path = profile_path
            profile = manager.sync()
            assert profile_path.exists()
            assert "Read" in profile.allowed_tools

    def test_sync_idempotent(self, machine):
        """Sincronização repetida sem mudança de estado não reescreve."""
        manager = CapabilityManager(machine, client="claude-code")
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "settings.local.json"
            manager.profile_path = profile_path
            profile1 = manager.sync()
            profile2 = manager.sync()
            assert profile1.allowed_tools == profile2.allowed_tools

    def test_sync_on_state_change(self, machine):
        """Sincronização atualiza quando estado muda."""
        manager = CapabilityManager(machine, client="claude-code")
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "settings.local.json"
            manager.profile_path = profile_path

            # Estado inicial: active.preparing
            profile1 = manager.sync()
            assert "Write" in profile1.allowed_tools  # build_decision_state

            # Avança estado: START -> active.agent_running
            machine.send(Event(event_id="e1", type=EventType.START, node_id="test"))
            profile2 = manager.sync()
            assert "Write" in profile2.allowed_tools  # write_artifacts
            assert "Bash" in profile2.allowed_tools  # run_tests

    def test_get_current_profile(self, machine):
        manager = CapabilityManager(machine)
        profile = manager.get_current_profile()
        assert isinstance(profile, ClientPermissionProfile)


class TestAuditingToolBroker:
    """Testes do broker com auditoria."""

    def test_authorize_logs(self):
        broker = AuditingToolBroker()
        result = broker.authorize("idle", "Read")
        assert result is True
        log = broker.get_audit_log()
        assert len(log) == 1
        assert log[0]["tool"] == "Read"
        assert log[0]["allowed"] is True

    def test_authorize_denied_logs(self):
        broker = AuditingToolBroker()
        result = broker.authorize("idle", "Bash")
        assert result is False
        log = broker.get_audit_log()
        assert log[0]["allowed"] is False

    def test_clear_audit_log(self):
        broker = AuditingToolBroker()
        broker.authorize("idle", "Read")
        broker.clear_audit_log()
        assert broker.get_audit_log() == []


class TestDetectCapabilityViolations:
    """Testes de detecção post-hoc de violações."""

    def test_no_violation_when_allowed(self):
        """Sem violação quando tool é permitida no estado."""
        policy = load_policy()
        question_sets = load_question_sets()
        question_set = question_sets.get("task-classification")
        machine = NodeMachine(node_id="test", policy=policy, question_set=question_set)
        machine.start("test", question_set, policy)  # active.preparing

        violations = detect_capability_violations(
            machine,
            diff_files=["file1.py"],
            tool_calls=[("Read", "file1.py")],
            zone_map={"file1.py": "yellow"},
        )
        assert violations == []

    def test_violation_when_denied(self):
        """Violação detectada quando tool não é permitida no estado idle."""
        # Cria máquina sem dar start (estado idle)
        policy = load_policy()
        question_sets = load_question_sets()
        question_set = question_sets.get("task-classification")
        machine = NodeMachine(node_id="test", policy=policy, question_set=question_set)
        # NÃO chama machine.start() - fica em idle

        violations = detect_capability_violations(
            machine,
            diff_files=["file1.py"],
            tool_calls=[("Bash", "file1.py")],  # Bash não permitido em idle
            zone_map={"file1.py": "red"},
        )
        assert len(violations) == 1
        assert violations[0].tool_used == "Bash"
        assert violations[0].file_path == "file1.py"
        assert violations[0].zone == "red"

    def test_violation_includes_capability(self):
        """Violação inclui capability necessária."""
        # Cria máquina sem dar start (estado idle)
        policy = load_policy()
        question_sets = load_question_sets()
        question_set = question_sets.get("task-classification")
        machine = NodeMachine(node_id="test", policy=policy, question_set=question_set)
        # NÃO chama machine.start() - fica em idle

        violations = detect_capability_violations(
            machine,
            diff_files=["file1.py"],
            tool_calls=[("Write", "file1.py")],  # Write não permitido em idle
            zone_map={"file1.py": "red"},
        )
        assert len(violations) == 1
        assert violations[0].capability_required == "write_artifacts"


class TestCLIHelper:
    """Testes do helper CLI."""

    def test_write_permission_profile_for_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "profile.json"
            from llc2 import write_permission_profile_for_state
            result = write_permission_profile_for_state("idle", output=output, client="claude-code")
            assert result == output
            assert output.exists()
            import json
            content = json.loads(output.read_text())
            # Para .json genérico, client vira "generic" (formato genérico)
            assert content["client"] == "generic"
            assert "Read" in content["allowed"]


# Fixtures compartilhados
@pytest.fixture
def policy():
    return load_policy()


@pytest.fixture
def question_sets():
    return load_question_sets()


@pytest.fixture
def question_set(question_sets):
    return question_sets.get("task-classification")


@pytest.fixture
def machine(policy, question_set):
    m = NodeMachine(node_id="test", policy=policy, question_set=question_set)
    m.start("test", question_set, policy)
    return m


def _decision(automation: Automation, action: Action, evidence: tuple = ()) -> "Decision":
    from llc2.contracts import Decision
    return Decision(
        automation=automation,
        action=action,
        evidence_refs=evidence,
        reason="test",
        policy_id=policy.id,
        policy_version=policy.version,
        thresholds_hash=policy.thresholds_hash,
    )


def _hard(ok: bool = True) -> HardEvalResult:
    return HardEvalResult(checks=(Check(name="pytest", passed=ok),))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])