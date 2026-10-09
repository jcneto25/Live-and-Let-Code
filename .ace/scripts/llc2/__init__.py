"""LLC 2.0 — Deterministic Agentic Runtime (production package).

Fase 1: Jev Choice no Early Commitment.
Fase 2: Jev Score/Noul no DocJudge.
Fase 4: NodeMachine Statechart no Pipeline.
Fase 5: Capability Control.
"""
from __future__ import annotations

from .contracts import (
    Action,
    Automation,
    Check,
    Classification,
    Decision,
    DecisionState,
    EventType,
    HardEvalResult,
    JevChoice,
    JevNoul,
    JevResult,
    JevScore,
    NodeMachine,  # ← ADD THIS
    PolicySpec,
    RiskClass,
    canonical_hash,
    decide,
    load_policy,
    load_question_sets,
    automation_for,
)
from .jev_adapter import (
    FakeJevTransport,
    JevAdapter,
    JevRequest,
    JevRawResponse,
    SemanticUnavailable,
    record_payload,
)
from .classifier import classify_task_v2
from .doc_judge import doc_judge_v2
from .delta import delta_semantic_impact
from .capabilities import (
    CAPABILITY_TO_CLIENT_TOOLS,
    FORBIDDEN_TO_CLIENT_TOOLS,
    ClientPermissionProfile,
    generate_permission_profile,
    CapabilityManager,
    AuditingToolBroker,
    PostHocViolation,
    detect_capability_violations,
    install_capability_hooks,
    write_permission_profile_for_state,
)
from .contracts import capabilities_for_state

__all__ = [
    # enums
    "Automation",
    "Action",
    "RiskClass",
    "EventType",
    # jev primitives
    "JevChoice",
    "JevScore",
    "JevNoul",
    "JevResult",
    # eval / decision
    "Check",
    "HardEvalResult",
    "Classification",
    "Decision",
    "DecisionState",
    "PolicySpec",
    "canonical_hash",
    "decide",
    "load_policy",
    "load_question_sets",
    "automation_for",
    # adapter
    "FakeJevTransport",
    "JevAdapter",
    "JevRequest",
    "JevRawResponse",
    "SemanticUnavailable",
    "record_payload",
    # classifier
    "classify_task_v2",
    # doc_judge
    "doc_judge_v2",
    # delta
    "delta_semantic_impact",
    # nodemachine (Fase 4)
    "NodeMachine",
    # capabilities (Fase 5)
    "CAPABILITY_TO_CLIENT_TOOLS",
    "FORBIDDEN_TO_CLIENT_TOOLS",
    "ClientPermissionProfile",
    "generate_permission_profile",
    "CapabilityManager",
    "AuditingToolBroker",
    "PostHocViolation",
    "detect_capability_violations",
    "install_capability_hooks",
    "write_permission_profile_for_state",
    "capabilities_for_state",
]
