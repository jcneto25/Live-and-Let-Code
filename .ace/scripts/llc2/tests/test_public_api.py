"""Tests for the consolidated LLC 2.0 production package API."""

from pathlib import Path


def test_policy_module_reexports_contract_api():
    from llc2 import contracts
    from llc2.policy import automation_for, decide, load_policy

    assert decide is contracts.decide
    assert load_policy is contracts.load_policy
    assert automation_for is contracts.automation_for
    assert load_policy().thresholds_hash.startswith("sha256:")


def test_semantic_module_reexports_adapter_api():
    from llc2 import jev_adapter
    from llc2.semantic import FakeJevTransport, JevAdapter, SemanticUnavailable

    assert JevAdapter is jev_adapter.JevAdapter
    assert FakeJevTransport is jev_adapter.FakeJevTransport
    assert SemanticUnavailable is jev_adapter.SemanticUnavailable


def test_macro_projection_is_exported_by_package():
    from llc2 import divergences, macro_view, phase_of

    assert phase_of("1") == "discovery"
    assert macro_view({"1": "active.preparing"}).phase == "discovery"
    assert divergences()


def test_runtime_policy_and_question_sets_use_config_directory():
    from llc2.contracts import DEFAULT_POLICY_PATH, DEFAULT_QUESTION_SETS_PATH

    assert DEFAULT_POLICY_PATH.parent.name == "config"
    assert DEFAULT_QUESTION_SETS_PATH.parent.name == "config"
    assert Path(DEFAULT_POLICY_PATH).is_file()
    assert Path(DEFAULT_QUESTION_SETS_PATH).is_file()