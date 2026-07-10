#!/usr/bin/env python3
"""Pipeline orchestration: delta analysis phase, full pipeline run, step execution."""

import subprocess
import sys
from pathlib import Path

from llc_delta import (
    delta_report_exists,
    generate_skip_note,
    get_skip_reason,
    is_step_skipped,
    parse_delta_report,
)
from llc_steps import canonical_id, pipeline_steps

from .gates import gate_check, get_gate_checklist
from .replay import agent_invoke
from .session import session_end, session_start
from .skill import skill_load


def _run_delta_analysis(auto_approve=False, iteration=None):
    """Executa a fase de analise delta (Δ.0 + Δ.1) antes do pipeline principal.

    1. Executa Step Δ.0 (Delta Impact Analysis) — gera DELTA_REPORT.md
    2. Gate Δ.0 — validacao humana
    3. Executa Step Δ.1 (Delta Grill Me) — resolve ambiguidades
    4. Gate Δ.1 — validacao humana
    """
    print(f"\n{'='*60}")
    print("📊 FASE Δ — ANALISE DE IMPACTO (Modo Delta)")
    print(f"{'='*60}")
    if iteration:
        print(f"Iteracao: {iteration}")

    # Step Δ.0
    sid = session_start("0.2", task="Delta Impact Analysis")
    decision = gate_check("0.2", None, auto_approve=auto_approve)
    session_end(sid, decision, None, step="0.2")
    if decision == "rejected":
        print("\n⛔ Gate Δ.0 REPROVADO. Pipeline pausado.")
        return False

    # Step Δ.1
    sid = session_start("0.3", task="Delta Grill Me")
    decision = gate_check("0.3", None, auto_approve=auto_approve)
    session_end(sid, decision, None, step="0.3")
    if decision == "rejected":
        print("\n⛔ Gate Δ.1 REPROVADO. Pipeline pausado.")
        return False

    print("\n✅ Fase Δ concluida. Iniciando pipeline de execucao...")
    return True


def pipeline_run(from_step="0.5", to_step="11.1", task=None,
                 delta=False, iteration=None, auto_approve=False):
    """Executa pipeline completo do step inicial ao final (ids canonicos).

    A sequencia e a subselecao vem de llc_steps.pipeline_steps() (ordenada por
    numero), entao inclui 10.6/10.7/11.1 nas posicoes corretas.

    Inclui verificacao de consistencia automatica apos cada step.

    Modo delta (--delta):
      - Executa fase Δ (Δ.0 + Δ.1) antes do pipeline principal
      - Le DELTA_REPORT.md para determinar steps a pular
      - Gera skip notes para steps nao executados
      - Auto-aprova gates de steps skipados
    """
    # ── Modo Delta ──
    if delta:
        # 1. Executa fase de analise delta (se DELTA_REPORT.md nao existe ainda)
        if not delta_report_exists():
            success = _run_delta_analysis(
                auto_approve=auto_approve, iteration=iteration
            )
            if not success:
                return False

        # 2. Le o plano delta
        delta_plan = parse_delta_report()
        if delta_plan is None:
            print("⚠️  DELTA_REPORT.md nao encontrado ou invalido.")
            print("   Continuando sem modo delta (pipeline padrao).")
            delta = False
        else:
            print(f"\n📋 Plano Delta: {delta_plan['change_type'].upper()}")
            print(f"   Steps a executar: {len(delta_plan['execute_steps'])}")
            print(f"   Steps a pular: {len(delta_plan['skip_steps'])}")

            # Atualiza from_step/to_step com base no plano delta
            if delta_plan["execute_steps"]:
                # Usa os steps do plano delta em vez do range padrao
                pass  # Delta steps sao tratados no loop abaixo

    # ── Pipeline Padrao ──
    specs = pipeline_steps(from_id=from_step, to_id=to_step)
    started = False

    for spec in specs:
        # ── Smart Skip (modo delta) ──
        if delta and delta_plan and is_step_skipped(spec.id, delta_plan):
            reason = get_skip_reason(spec.id, spec.name, delta_plan)
            note_file = generate_skip_note(
                spec.id, spec.name, reason or "Step nao afetado",
                iteration=delta_plan.get("iteration"),
            )
            print(f"\n⏭️  Step {spec.id} ({spec.name}) — PULADO (Smart Skip)")
            print(f"   Motivo: {reason or 'Step nao afetado'}")
            print(f"   Skip note: {note_file}")
            continue
        if not started:
            print(f"\n{'=' * 60}")
            print(
                f"🚀 Iniciando pipeline LLC (Step {canonical_id(from_step)} → {canonical_id(to_step)})"
            )
            print(f"{'=' * 60}")
            started = True

        sid = step_run(spec.id, task=task)
        decision = gate_check(spec.id, None)
        session_end(sid, decision, None, step=spec.id)

        if decision == "rejected":
            print(
                f"\n⛔ Gate {get_gate_checklist(spec.id)[0]} REPROVADO. Pipeline pausado."
            )
            print("Corrija os problemas e reexecute a partir deste step:")
            print(f"  llc run --step {spec.id}")
            return False

        # Verificacao de consistencia apos cada step (exceto steps muito iniciais)
        if spec.id not in ["0", "0.1", "0.5", "1"]:
            print(f"\n📋 Verificando consistencia apos step {spec.id}...")
            try:
                result = subprocess.run(
                    ["python3", ".ace/scripts/consistency-check.py"],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd(),
                )
                if result.stdout:
                    for line in result.stdout.split("\n"):
                        if line.strip() and not line.startswith("="):
                            print(f"   {line.strip()}")
                if result.stderr and "ERRO" in result.stderr:
                    print(f"   ⚠️  Aviso: {result.stderr.strip()}")
            except Exception as e:
                print(f"   ℹ️  consistency-check não executado: {e}")

    print(f"\n{'=' * 60}")
    print("✅ Pipeline concluido com sucesso!")
    print(f"{'=' * 60}")
    return True


def step_run(step, prp=None, task=None, wave=1, no_worktree=False):
    """Executa um step e retorna session_id."""
    sess = session_start(step, prp=prp, task=task, wave=wave, no_worktree=no_worktree)
    skill_file, prompt = skill_load(step, sess["context_seed"], task)
    print(f"📄 Skill: {skill_file}")
    print(f"📦 Context seed: {len(sess.get('context_seed', '') or '')} chars")

    _output, code, _context_seed = agent_invoke(prompt, task, client=None)
    if code != 0:
        print(f"⚠️  Agente retornou codigo {code}")
    return sess["session_id"]
