#!/usr/bin/env python3
"""Gate logic: checklist resolution and the human A/R checkpoint."""

from llc_steps import normalize_step, UnknownStepError

from .common import load_gates_config

try:
    from llc_trace import record_decision
except ImportError:  # pragma: no cover
    record_decision = None


def get_gate_checklist(step):
    """Resolve o checklist de um gate a partir do step (id/alias/número)
    ou diretamente de uma gate-key de gates.json (ex: "11-SEC", "12-NULL").

    Aceita:
      - Step id/alias/número (ex: "5", "security", "10.8") -> usa spec.gate.
      - Gate-key de gates.json (ex: "11-SEC", "12-NULL", "11-OWASP") -> lookup
        direto em gates.json (cobre o caminho `llc gate run --gate <alias>`,
        onde GATE_ALIASES mapeia para gate-keys, não para step ids).
    Retorna (gate_key, checklist) ou (None, []) se não houver gate.
    """
    # Caminho 1: tentar resolver como step (id/alias/número).
    try:
        spec = normalize_step(step)
        gate_key = spec.gate
    except UnknownStepError:
        # Caminho 2: `step` é uma gate-key de gates.json (ex: "11-SEC").
        gate_key = step
    if gate_key is None:
        return None, []
    config = load_gates_config()
    gate = config.get("gates", {}).get(gate_key, {})
    return gate_key, gate.get("checklist", [])


def _trace_gate(step, gate_num, items, decision, auto_approve):
    """Decision Record do gate — instrumentacao Fase 0 (INV-T1/T2/T3/T4)."""
    if record_decision is None:
        return
    reason = "auto_approve" if auto_approve else "human"
    if gate_num is None:
        reason = "no_gate"
    record_decision(
        "gate",
        outcome=decision,
        reason=reason,
        state="GATE_CHECK",
        event="GATE_DECIDED",
        step=str(step) if step is not None else None,
        evidence={"gate_key": gate_num, "checklist_items": len(items)},
        automation="AUTO" if auto_approve else "HUMAN_REQUIRED",
    )


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
        decision = "approved"
        _trace_gate(step, gate_num, items, decision, auto_approve)
        return decision

    print(f"\n👤 Gate {gate_num}:")
    for item in items:
        print(f"  - {item}")

    if auto_approve:
        print("\n⚡ Modo auto-aprove (CI). Avancando automaticamente.")
        decision = "approved"
        _trace_gate(step, gate_num, items, decision, auto_approve)
        return decision

    while True:
        print()
        print("[A]provar  [R]ejeitar")
        print("(sem timeout — aguardando decisao humana explicita)")
        choice = input().strip().lower()

        if choice in ("a", "approve"):
            decision = "approved"
            _trace_gate(step, gate_num, items, decision, auto_approve)
            return decision
        if choice in ("r", "reject"):
            decision = "rejected"
            _trace_gate(step, gate_num, items, decision, auto_approve)
            return decision
        print("⚠️  Decisao ambigua — digite 'a' (aprovar) ou 'r' (rejeitar).")
