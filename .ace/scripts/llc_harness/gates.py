#!/usr/bin/env python3
"""Gate logic: checklist resolution and the human A/R checkpoint."""

from llc_steps import normalize_step

from .common import load_gates_config


def get_gate_checklist(step):
    """Resolve o checklist de um gate a partir do step (id/alias/número)."""
    spec = normalize_step(step)
    if spec.gate is None:
        return None, []
    config = load_gates_config()
    gate = config.get("gates", {}).get(spec.gate, {})
    return spec.gate, gate.get("checklist", [])


def gate_check(step, _output=None, auto_approve=False):
    """Exibe checklist do gate e aguarda decisao humana.
    Se auto_approve=True (CI/non-interactive), aprova automaticamente.
    Caso contrario, aguarda indefinidamente — timeout NAO auto-aprova.
    Em modo interativo, so aprova com token explicito (a/approve); input
    ambiguo (vazio, typo, qualquer coisa != a/approve/r/reject) re-pergunta,
    nunca aprova silenciosamente (fechamento do fail-open E-13)."""
    gate_num, items = get_gate_checklist(step)
    if gate_num is None:
        print(f"ℹ️  Nenhum gate definido para step {step}. Avancando automaticamente.")
        return "approved"

    print(f"\n👤 Gate {gate_num}:")
    for item in items:
        print(f"  - {item}")

    if auto_approve:
        print("\n⚡ Modo auto-aprove (CI). Avancando automaticamente.")
        return "approved"

    while True:
        print()
        print("[A]provar  [R]ejeitar")
        print("(sem timeout — aguardando decisao humana explicita)")
        choice = input().strip().lower()

        if choice in ("a", "approve"):
            return "approved"
        if choice in ("r", "reject"):
            return "rejected"
        print("⚠️  Decisao ambigua — digite 'a' (aprovar) ou 'r' (rejeitar).")
