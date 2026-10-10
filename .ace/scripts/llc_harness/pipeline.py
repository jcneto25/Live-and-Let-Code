#!/usr/bin/env python3
"""Pipeline orchestration: delta analysis phase, full pipeline run, step execution."""

import os
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
from .replay import agent_invoke, detect_agent_client
from .session import session_end, session_start
from .skill import skill_load

try:
    from llc_trace import input_hash, log_event, record_decision
except ImportError:  # pragma: no cover
    input_hash = None
    log_event = None
    record_decision = None

# ── F5/5.2: capabilities tool-agnostic (opcional) ───────────────────────────
try:
    from llc2.capabilities import (
        detect_modified_file_violations,
        generate_permission_profile,
        normalize_client_id,
        profile_path_for_client,
    )
except ImportError:  # pragma: no cover
    detect_modified_file_violations = None
    generate_permission_profile = None
    normalize_client_id = None
    profile_path_for_client = None

# ── F3/3.5: instrumentação de estado NodeMachine (append-only) ──────────────
# Default "0": habilitar apenas em validação. Não afeta writes existentes.
RECORD_ENV = "LLC2_RECORD"
RECORD_DEFAULT = "0"

# ── F5/5.2: aplica perfil de permissão por estado ────────────────────────────
# Default "0" (§9): opt-in — escrever settings do cliente é invasivo.
APPLY_PROFILE_ENV = "LLC2_APPLY_CAPABILITY_PROFILE"
APPLY_PROFILE_DEFAULT = "0"


def _apply_profile_enabled() -> bool:
    return _flag_enabled(APPLY_PROFILE_ENV, APPLY_PROFILE_DEFAULT)


def _apply_capability_profile(machine) -> str | None:
    """Gera+escreve o perfil do estado atual p/ o cliente detectado (F5/5.2).

    Retorna o caminho escrito, ou None se indisponível. Nunca levanta.
    """
    if (generate_permission_profile is None or normalize_client_id is None
            or profile_path_for_client is None or machine is None):
        return None
    try:
        client = normalize_client_id(detect_agent_client())
        state_id = machine.configuration()["configuration"]
        profile = generate_permission_profile(state_id, client)
        path = profile_path_for_client(client)
        profile.write(path)
        return str(path)
    except Exception:
        return None


def _git_modified_files() -> list[str] | None:
    """Arquivos modificados (tracked vs HEAD + untracked). Nunca levanta.

    Retorna None em falha de infra (git ausente/erro) — para o chamador
    distinguir "limpo" ([]) de "não verificado" (None).
    """
    files: list[str] = []
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return None
        files.extend(l.strip() for l in r.stdout.splitlines() if l.strip())
        u = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=30)
        if u.returncode == 0:
            files.extend(l.strip() for l in u.stdout.splitlines() if l.strip())
    except Exception:
        return None
    return files


def _flag_enabled(env_var: str, default: str) -> bool:
    """Idioma único de flag env (lê por chamada, nunca congela no import)."""
    return os.environ.get(env_var, default).strip().lower() \
        not in ("0", "", "false", "no")


def _record_enabled() -> bool:
    return _flag_enabled(RECORD_ENV, RECORD_DEFAULT)


def _record_node_state(*, machine, policy, question_set, sess, step,
                       phase, exit_code=None):
    """Decision Record do estado do NodeMachine (F3/3.2). Nunca levanta.

    `phase`: "start" (após machine.start) ou "end" (após AGENT_RETURNED).
    """
    if record_decision is None or input_hash is None or machine is None:
        return None
    try:
        configuration = machine.configuration()["configuration"]
        capabilities = sorted(str(c) for c in machine.capabilities())
        evidence = {
            "configuration": configuration,
            "capabilities": capabilities,
            "evidence_refs": [
                f"policy:{policy.id}@{policy.version}",
                f"question_set:{question_set.id}@{question_set.version}",
            ],
        }
        if exit_code is not None:
            evidence["agent_exit_code"] = exit_code
        return record_decision(
            "step_execution",
            outcome=f"node_{phase}",
            reason=str(configuration),
            state="STEP_EXECUTION",
            event="NODE_STATE",
            input_hash_value=input_hash({"step": str(step), "phase": phase}),
            state_hash=input_hash({"configuration": configuration}),
            evidence=evidence,
            automation="AUTO",
            session_id=sess.get("session_id"),
            step=str(step),
            config={
                "policy_version": policy.version,
                "policy_id": policy.id,
                "thresholds_hash": policy.thresholds_hash,
                "question_set_id": question_set.id,
                "question_set_version": question_set.version,
                "question_set_hash": question_set.hash,
            },
        )
    except Exception:
        return None


# ── Fase 4: NodeMachine integration (guarded by LLC2_STATECHART) ──────────
try:
    from llc2.contracts import (
        Event as NodeEvent,
        EventType as NodeEventType,
        NodeMachine,
        load_policy as load_llc2_policy,
        load_question_sets as load_llc2_question_sets,
    )
except ImportError:  # pragma: no cover
    NodeMachine = None
    NodeEvent = None
    NodeEventType = None
    load_llc2_policy = None
    load_llc2_question_sets = None


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
            if record_decision is not None:
                record_decision(
                    "smart_skip",
                    outcome="skipped",
                    reason=reason or "delta_plan",
                    state="STEP_SKIPPED",
                    event="SMART_SKIP",
                    step=spec.id,
                    evidence={"delta_change_type": delta_plan.get("change_type")},
                    automation="AUTO",
                )
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

    # ── Fase 4: NodeMachine integration ──────────────────────────────────
    machine = None
    policy = None
    question_set = None
    logged_start = False
    if NodeMachine is not None and load_llc2_policy is not None and load_llc2_question_sets is not None:
        # Check feature flag
        statechart_enabled = os.environ.get("LLC2_STATECHART", "1").lower() not in ("0", "", "false", "no")
        if statechart_enabled:
            try:
                policy = load_llc2_policy()
                question_sets = load_llc2_question_sets()
                question_set = question_sets.get("task-classification")

                if question_set:
                    machine = NodeMachine(node_id=str(step), policy=policy, question_set=question_set)
                    machine.start(str(step), question_set, policy)

                    # Log step.start via statechart
                    if log_event is not None:
                        log_event(
                            "step.start",
                            session_id=sess.get("session_id"),
                            step=str(step),
                            input_hash=sess.get("input_hash"),
                            fields={
                                "skill_file": skill_file,
                                "prompt_len": len(prompt),
                                "statechart_state": machine.configuration()["configuration"],
                                "statechart_capabilities": list(machine.capabilities()),
                            },
                        )
                        logged_start = True

                    # F3/3.2: record versionado do estado (LLC2_RECORD=1).
                    if _record_enabled():
                        _record_node_state(
                            machine=machine, policy=policy,
                            question_set=question_set, sess=sess,
                            step=step, phase="start",
                        )

                    # F5/5.2: perfil de permissão p/ o cliente detectado.
                    if _apply_profile_enabled():
                        try:
                            _apply_capability_profile(machine)
                        except Exception:
                            pass  # fallback gracioso: sem perfil, sem bloqueio
            except Exception:
                # graceful degradation - não bloqueia pipeline se statechart falhar
                machine = None

    # Fase 0: input_hash do step (prompt + metadados) para replay determinístico
    # F3/3.2 dedup: o bloco statechart acima já logou estes campos + extras.
    if log_event is not None and not logged_start:
        log_event(
            "step.start",
            session_id=sess.get("session_id"),
            step=str(step),
            input_hash=None,  # computado em session_start; aqui logamos o evento
            fields={"skill_file": skill_file, "prompt_len": len(prompt)},
        )

    # Snapshot pré-agente: sujeira pré-existente não é atribuída ao agente.
    try:
        _diff_before = set(_git_modified_files() or [])
    except Exception:
        _diff_before = set()

    _output, code, _context_seed = agent_invoke(prompt, task, client=None)
    if code != 0:
        print(f"⚠️  Agente retornou codigo {code}")

    # F5/5.3: detecção post-hoc — sempre roda, nunca bloqueia (warn-only).
    if detect_modified_file_violations is not None:
        try:
            _after_raw = _git_modified_files()
            if _after_raw is None:
                if Path(".git").exists():
                    print("⚠️  Post-hoc: git indisponível — "
                          "verificação pulada")
            else:
                _after = [f for f in _after_raw if f not in _diff_before]
                _violations = detect_modified_file_violations(
                    _after, machine=machine)
                if _violations:
                    _files = ", ".join(v.file_path for v in _violations)
                    print(f"⚠️  Post-hoc: {len(_violations)} violação(ões) "
                          f"de zona 🔴: {_files}")
        except Exception:
            pass

    # ── Fase 4: Process AGENT_RETURNED event ─────────────────────────────
    logged_end = False
    if machine is not None and NodeEvent is not None and NodeEventType is not None:
        try:
            event = NodeEvent(event_id=f"evt-{step}-agent-returned", type=NodeEventType.AGENT_RETURNED, node_id=str(step))
            state = machine.send(event)

            if log_event is not None:
                log_event(
                    "step.end",
                    session_id=sess.get("session_id"),
                    step=str(step),
                    fields={
                        "agent_exit_code": code,
                        "statechart_state": state.state_id,
                        "statechart_capabilities": list(machine.capabilities()),
                    },
                )
                logged_end = True

            # F3/3.2: record versionado do estado (LLC2_RECORD=1).
            if _record_enabled():
                _record_node_state(
                    machine=machine, policy=policy,
                    question_set=question_set, sess=sess,
                    step=step, phase="end", exit_code=code,
                )
        except Exception:
            pass  # graceful degradation

    # F3/3.2 dedup: o bloco statechart acima já logou estes campos + extras.
    if log_event is not None and not logged_end:
        log_event(
            "step.end",
            session_id=sess.get("session_id"),
            step=str(step),
            fields={"agent_exit_code": code},
        )

    return sess["session_id"]