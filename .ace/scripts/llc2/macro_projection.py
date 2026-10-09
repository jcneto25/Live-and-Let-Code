"""Derived macro view for LLC 2.0 NodeMachine configurations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

PHASE_BY_PREFIX: tuple[tuple[str, str], ...] = (
    ("0", "discovery"),
    ("1", "discovery"),
    ("2", "discovery"),
    ("3", "planning"),
    ("4", "planning"),
    ("5", "planning"),
    ("6", "planning"),
    ("7", "planning"),
    ("8", "implementation"),
    ("9", "implementation"),
    ("10", "implementation"),
    ("11", "implementation"),
)

_SUBSTATE_OF_NODE: dict[str, str] = {
    "0": "discovery.ingestion",
    "0.5": "discovery.vision",
    "1": "discovery.specs",
    "2": "discovery.prd_generation",
    "3": "planning.prp_generation",
    "4": "planning.planning_waves",
    "5": "planning.architecture",
    "6": "planning.tasks",
}

TERMINAL_STATES = frozenset({"done", "skipped"})
FAILED_STATES = frozenset({"failed"})


def phase_of(node_id: str) -> str:
    """Return a node's macro phase, or `unmapped` when it has no mapping."""
    for prefix, phase in PHASE_BY_PREFIX:
        if node_id == prefix or node_id.startswith(prefix + "."):
            return phase
    return "unmapped"


def substate_of(node_id: str, state_id: str) -> str:
    if state_id.startswith("governance"):
        return "governance"
    if state_id in TERMINAL_STATES | FAILED_STATES:
        return state_id
    return _SUBSTATE_OF_NODE.get(node_id, f"{phase_of(node_id)}.{node_id}")


@dataclass(frozen=True)
class MacroView:
    phase: str
    substate: str
    per_phase: Mapping[str, Mapping[str, int]]
    blocked_by_human: tuple[str, ...]
    failed: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "phase": self.phase,
            "substate": self.substate,
            "per_phase": dict(self.per_phase),
            "blocked_by_human": list(self.blocked_by_human),
            "failed": list(self.failed),
        }


def macro_view(configs: Mapping[str, str]) -> MacroView:
    """Project micro node states into a pure, derived macro view."""
    if not configs:
        return MacroView("empty", "", {}, (), ())

    per_phase: dict[str, dict[str, int]] = {}
    human: list[str] = []
    failed: list[str] = []

    for node_id, state_id in sorted(configs.items()):
        phase = phase_of(node_id)
        bucket = per_phase.setdefault(
            phase,
            {"total": 0, "done": 0, "skipped": 0, "failed": 0,
             "active": 0, "awaiting_human": 0},
        )
        bucket["total"] += 1
        if state_id.startswith("governance.awaiting_human"):
            bucket["awaiting_human"] += 1
            human.append(node_id)
        elif state_id in FAILED_STATES:
            bucket["failed"] += 1
            failed.append(node_id)
        elif state_id in TERMINAL_STATES:
            bucket[state_id] += 1
        else:
            bucket["active"] += 1

    if human:
        first = sorted(human)[0]
        return MacroView(
            "governance", substate_of(first, configs[first]), per_phase,
            tuple(sorted(human)), tuple(sorted(failed)),
        )

    active = [
        node_id for node_id, state_id in sorted(configs.items())
        if state_id not in TERMINAL_STATES and state_id not in FAILED_STATES
    ]
    if active:
        head = active[0]
        return MacroView(
            phase_of(head), substate_of(head, configs[head]), per_phase, (),
            tuple(sorted(failed)),
        )

    return MacroView("terminal", "terminal", per_phase, (), tuple(sorted(failed)))


UNPRODUCED_MACRO_STATES = (
    "discovery.use_cases",
    "self_heal",
    "deployed",
)
FORBIDDEN_IN_MACRO_CHART = ("deploy",)


def divergences() -> tuple[str, ...]:
    """List macro states/actions not represented by the runtime model."""
    return tuple(
        [f"estado sem origem no registry: {state}" for state in UNPRODUCED_MACRO_STATES]
        + [f"ação proibida pela matriz: {action}" for action in FORBIDDEN_IN_MACRO_CHART]
    )