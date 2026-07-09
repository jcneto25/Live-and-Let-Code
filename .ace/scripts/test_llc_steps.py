#!/usr/bin/env python3
"""Characterization test: pin the step -> gate -> checklist mapping.

Asserts the contract documented in llc_steps.py (each `gate` is a key into
gates.json with a non-empty checklist) and that no two steps collide on a
gate key. Deliberately does NOT assert gates[gate]["step"] == spec.number:
three gates have stale `step` display fields (DEFECT_BACKLOG D-01, LOW),
documented rather than fixed at this baseline.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import llc_steps

GATES_JSON = Path(__file__).resolve().parents[1] / "config" / "gates.json"


def _load_gates() -> dict:
    return json.loads(GATES_JSON.read_text(encoding="utf-8"))["gates"]


def test_every_step_gate_key_resolves_with_checklist():
    gates = _load_gates()
    failures = []
    for step_id, spec in llc_steps.REGISTRY.items():
        if spec.gate is None:
            continue
        if spec.gate not in gates:
            failures.append(f"step {step_id}: gate {spec.gate!r} missing from gates.json")
            continue
        if not gates[spec.gate].get("checklist"):
            failures.append(f"step {step_id}: gate {spec.gate!r} has empty checklist")
    assert not failures, "\n".join(failures)


def test_no_two_steps_share_a_gate_key():
    seen: dict[str, str] = {}
    for step_id, spec in llc_steps.REGISTRY.items():
        if spec.gate is None:
            continue
        if spec.gate in seen:
            raise AssertionError(
                f"gate {spec.gate!r} shared by steps {seen[spec.gate]} and {step_id}"
            )
        seen[spec.gate] = step_id
