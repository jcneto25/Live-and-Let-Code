#!/usr/bin/env python3
"""Smart Skip (E-12) e geracao de skip notes do fluxo delta."""

import sys
from pathlib import Path

from .paths import SKIP_NOTES_DIR

# Steps que SEMPRE executam — o DELTA_REPORT.md nunca pode pulá-los (E-12).
# Set do guia: 10, 10.6, 10.7, 10.8, 11, 11.1, 11.2 (ids canônicos llc_steps).
ALWAYS_RUN: frozenset[str] = frozenset(
    {"10", "10.6", "10.7", "10.8", "11", "11.1", "11.2"}
)


def _canonical_step_id(step_id: str) -> str:
    """Resolve step_id (id/alias/slug) para o id canônico llc_steps.
    Em caso de falha de import/resolve, retorna o valor cru (comparação
    defensiva, ainda assim protegida por ALWAYS_RUN quando resolúvel)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import llc_steps

        return llc_steps.canonical_id(step_id)
    except Exception:
        return step_id


def is_step_skipped(step_id: str, delta_plan: dict | None) -> bool:
    """Verifica se um step deve ser pulado no modo delta.
    Steps em ALWAYS_RUN nunca são pulados, independente do DELTA_REPORT.md
    (E-12): protege os gates obrigatórios (coverage 10.8, PRP-acceptance 11.2,
    security 10.6, etc.) de skip silencioso ou adversarial."""
    if delta_plan is None:
        return False
    canon = _canonical_step_id(step_id)
    if canon in ALWAYS_RUN:
        return False
    for skip in delta_plan.get("skip_steps", []):
        if _canonical_step_id(skip["step_id"]) == canon:
            return True
    return False


def _affected_step_ids(
    affected_nodes: set[str] | frozenset[str] | None,
) -> set[str]:
    """Normaliza ids de nó do grafo ("step-X") para ids canônicos de step.

    Nós que não são steps (gates, artefatos N2) nunca casam com um step —
    o portão semântico é por step executável.
    """
    steps: set[str] = set()
    for node in affected_nodes or ():
        if isinstance(node, str) and node.startswith("step-") and len(node) > 5:
            steps.add(_canonical_step_id(node[5:]))
    return steps


def should_use_semantic_impact(
    step_id: str,
    affected_nodes: set[str] | frozenset[str] | None,
) -> bool:
    """Política impact_of-first (Fase 2 / R-4): o step merece avaliação semântica?

    True somente se o step (canônico) está no conjunto afetado não-vazio.
    Pura — não toca no grafo; o chamador obtém `affected_nodes` via
    `llc_delta.report.affected_nodes_for_delta()`.

    Guarda fail-closed (tarefa 2.6): steps em ALWAYS_RUN sempre retornam
    True — mesmo fora do residual ou com conjunto vazio (exceção
    documentada à regra do vazio: avaliar é barato, pular é proibido).
    """
    canon = _canonical_step_id(step_id)
    if canon in ALWAYS_RUN:
        return True
    if not affected_nodes:
        return False
    return canon in _affected_step_ids(affected_nodes)


def residual_impact(
    step_id: str,
    affected_nodes: set[str] | frozenset[str] | None,
    direct_impact: set[str] | frozenset[str] = frozenset(),
) -> str:
    """Granularidade do impacto de um step: "direct" | "propagated" | "none".

    `direct_impact` (raízes da mudança, no namespace de nós do grafo) vence
    sobre o conjunto propagado — a raiz é trivialmente impactada.
    """
    canon = _canonical_step_id(step_id)
    if canon in _affected_step_ids(direct_impact):
        return "direct"
    if not affected_nodes:
        return "none"
    if canon in _affected_step_ids(affected_nodes):
        return "propagated"
    return "none"


def get_skip_reason(step_id: str, step_name: str, delta_plan: dict | None) -> str | None:
    """Retorna a justificativa de skip para um step, ou None se nao for skip."""
    if delta_plan is None:
        return None
    for skip in delta_plan.get("skip_steps", []):
        if skip["step_id"] == step_id:
            return skip.get("reason", "Nao informado")
    return None


def generate_skip_note(step_id: str, step_name: str, reason: str,
                       iteration: str | None = None) -> Path:
    """Gera um skip note para o step e retorna o caminho do arquivo."""
    SKIP_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_file = SKIP_NOTES_DIR / f"step-{step_id}.md"

    content = [
        f"# Skip Note: Step {step_id} — {step_name}",
        "",
        f"**Decisao:** Step pulado conforme DELTA_REPORT.md",
        f"**Justificativa:** {reason}",
        "",
    ]
    if iteration:
        content.append(f"**Iteracao:** {iteration}")
    content.append("")
    content.append(
        "**Gate:** ✅ Auto-aprovado via Smart Skip "
        "(reaproveitando artefatos da versao anterior)"
    )
    content.append("")

    note_file.write_text("\n".join(content), encoding="utf-8")
    return note_file
