#!/usr/bin/env python3
"""Characterization tests — must-not-break contract do BEHAVIOR_BASELINE.

Pins the enforcement behaviors the clean-code refactor (sub-projeto 2) must
preserve. Reproduces the Proof commands do AUDIT_REPORT / BEHAVIOR_BASELINE.

Coberto aqui (exercisable on this baseline):
  - D-01: gates.json step<->gate resolution has 0 mismatches.
  - E-12: llc_delta.is_step_skipped protects ALWAYS_RUN steps.
  - E-13: llc_harness.gate_check requires explicit a/approve (re-prompts).
  - A-01/A-02: _pre_wave_check / _post_wave_check return bool (not None).

Itens not-exercisable-on-this-baseline (no PRPs) are covered by inspection in
the audit, not here: #4, #9.
"""

import builtins
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import llc_steps
import llc_delta
import llc_harness
import llc_wave


# ── D-01: gates.json step<->gate resolution ──


def test_d01_gate_step_fields_match_registry():
    gates = json.load(open(Path(__file__).parent.parent / "config" / "gates.json"))["gates"]
    mismatches = []
    for sid, spec in sorted(llc_steps.REGISTRY.items(), key=lambda kv: kv[1].number):
        if spec.gate is None:
            continue
        gj_step = gates.get(spec.gate, {}).get("step")
        match = spec.gate in gates and abs(gj_step - spec.number) < llc_steps.EPS
        if not match:
            mismatches.append((sid, spec.gate, gj_step, spec.number))
    assert mismatches == [], f"D-01 mismatches: {mismatches}"


# ── E-12: smart-skip ALWAYS_RUN guard ──


def test_e12_always_run_steps_never_skipped():
    plan = {"skip_steps": [{"step_id": s, "reason": "x"} for s in
                           ["10", "10.6", "10.7", "10.8", "11", "11.1", "11.2"]]}
    for s in ["10", "10.6", "10.7", "10.8", "11", "11.1", "11.2",
              "security", "test-coverage", "owasp", "11.2"]:
        assert llc_delta.is_step_skipped(s, plan) is False


def test_e12_always_run_via_aliases_never_skipped():
    plan = {"skip_steps": [{"step_id": "11.2", "reason": "x"}]}
    # alias "verify" -> 11.2 must also be protected
    assert llc_delta.is_step_skipped("verify", plan) is False


def test_e12_normal_steps_still_skippable():
    plan = {"skip_steps": [{"step_id": "10.5", "reason": "x"}]}
    assert llc_delta.is_step_skipped("10.5", plan) is True
    assert llc_delta.is_step_skipped("10.5", None) is False


def test_e12_always_run_set_is_complete():
    assert llc_delta.ALWAYS_RUN == frozenset(
        {"10", "10.6", "10.7", "10.8", "11", "11.1", "11.2"}
    )


# ── E-13: gate_check requires explicit approve (no silent fail-open) ──


class _InputStub:
    def __init__(self, values):
        self._it = iter(values)
        self.calls = 0

    def __call__(self, *a):
        self.calls += 1
        if self.calls > 20:
            raise RuntimeError("gate_check did not terminate (loop guard)")
        return next(self._it)


def test_e13_approve_on_explicit_a():
    builtins.input = _InputStub(["a"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "approved"


def test_e13_reject_on_r():
    builtins.input = _InputStub(["r"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "rejected"


def test_e13_ambiguous_input_reprompts_then_approves():
    builtins.input = _InputStub(["", "xyz", "approve"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "approved"
    assert builtins.input.calls >= 3  # re-prompted before approving


def test_e13_typo_rejects_only_after_explicit_r():
    builtins.input = _InputStub(["rejct", "r"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "rejected"
    assert builtins.input.calls >= 2


def test_e13_auto_approve_bypasses_interactive():
    builtins.input = _InputStub([])  # would hang/loop if reached
    assert llc_harness.gate_check("10.8", auto_approve=True) == "approved"


# ── A-01 / A-02: wave checks return bool, not None ──


def test_a01_pre_wave_check_returns_bool(monkeypatch, tmp_path):
    monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
    assert llc_wave._pre_wave_check(dry_run=False, wave_num=1) is True


def test_a02_post_wave_check_returns_bool(monkeypatch, tmp_path):
    monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
    monkeypatch.delenv("LLC_PRP_NO_VERIFY", raising=False)
    result = llc_wave._post_wave_check(dry_run=False, wave_num=1, prp_ids=None)
    assert result is True  # pre-fix this was None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
