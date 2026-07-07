#!/usr/bin/env python3
"""
LLC Thin Harness — modulo de orquestracao do pipeline Live and Let Code.

Responsabilidades:
- session_start(): inicializa sessao ACE + worktree opcional
- skill_load(): carrega skill Markdown + AGENTS.md + context_seed
- agent_invoke(): detecta cliente CLI ou exibe prompt manual
- gate_check(): exibe checklist do gate, aguarda decisao humana
- session_end(): finaliza sessao, merge/discard worktree, learning points

Nao substitui os scripts ACE — os invoca via subprocess.
"""

import json
import os
import shutil
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
from llc_steps import (
    REGISTRY,
    UnknownStepError,
    canonical_id,
    normalize_step,
    pipeline_steps,
)

ACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ACE_DIR / "scripts"
CONFIG_DIR = ACE_DIR / "config"
SKILLS_DIR = Path("docs/skills")
AGENTS_FILE = Path("AGENTS.md")

# ── Load gate configuration (R1: externalized from code) ──

GATES_FILE = CONFIG_DIR / "gates.json"
_gates_config = None


def _load_gates_config():
    global _gates_config
    if _gates_config is None:
        if GATES_FILE.exists():
            _gates_config = json.loads(GATES_FILE.read_text(encoding="utf-8"))
        else:
            _gates_config = {"gates": {}, "step_to_gate": {}}
    return _gates_config


def get_gate_checklist(step):
    spec = normalize_step(step)
    if spec.gate is None:
        return None, []
    config = _load_gates_config()
    gate = config.get("gates", {}).get(spec.gate, {})
    return spec.gate, gate.get("checklist", [])


def gate_check(step, _output=None, auto_approve=False):
    """Exibe checklist do gate e aguarda decisao humana.
    Se auto_approve=True (CI/non-interactive), aprova automaticamente.
    Caso contrario, aguarda indefinidamente — timeout NAO auto-aprova."""
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

    print()
    print("[A]provar  [R]ejeitar")
    print("(sem timeout — aguardando decisao humana)")
    choice = input().strip().lower()

    if choice in ("a", "approve"):
        return "approved"
    elif choice in ("r", "reject"):
        return "rejected"
    return "approved"


from pathlib import Path

# ── Early Commitment + Replay imports ──
try:
    from llc_classify import classify_task
    from llc_replay import (
        check_target_files_stale,
        deterministic_replay,
        extract_files_from_script,
        find_best_script,
        get_architecture_version,
        is_red_zone,
        log_replay_event,
        preflight_all_steps,
    )

    CLASSIFY_REPLAY_AVAILABLE = True
except ImportError:
    CLASSIFY_REPLAY_AVAILABLE = False

# ── Agent CLI detection ──


def detect_agent_client():
    """Detecta o cliente de IA CLI via ambiente ou PATH.

    Ordem de precedência:
    1. Variável LLC_AGENT_CLI (ex: LLC_AGENT_CLI=claude)
    2. Primeiro CLI conhecido encontrado no PATH (fallback)

    Nenhum hardcode de flags — todo cliente recebe o prompt via STDIN.
    """
    env_client = os.environ.get("LLC_AGENT_CLI", "").strip()
    if env_client:
        return env_client

    # Fallback: procura CLIs conhecidos no PATH (sem flags — via stdin resolve)
    KNOWN_CLIS = ["claude", "opencode", "codex", "cursor", "windsurf", "copilot"]
    for client in KNOWN_CLIS:
        if shutil.which(client):
            return client
    return None


# ── Session management ──


def session_start(step, prp=None, task=None, wave=1, no_worktree=False):
    """Inicializa sessao ACE. Retorna dict com session_id, context_seed, worktree_path."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "initialize_session.py"),
        "--step",
        str(step),
        "--task",
        task or f"Step {step}",
        "--wave",
        str(wave),
        "--json",
    ]
    if prp:
        cmd.extend(["--prp", prp])
    if no_worktree:
        cmd.append("--no-worktree")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    if result.returncode != 0:
        print(f"❌ Erro ao inicializar sessao:\n{result.stderr}")
        sys.exit(1)

    data = json.loads(result.stdout)
    print(f"✅ Sessao iniciada: {data.get('session_id')}")
    if data.get("worktree"):
        print(f"🔀 Worktree: {data.get('worktree')}")

    return {
        "session_id": data.get("session_id"),
        "context_seed": data.get("context_seed"),
        "worktree_path": data.get("worktree"),
    }


def _step_from_index(session_id):
    """Le o step (id canonico) de uma sessao no index.json (ou None).

    Prefere `llc_step_id`; fallback p/ `llc_step` (legado). Normaliza quando
    possivel; senao devolve o valor cru como string (usado so como display).
    """
    index_file = ACE_DIR / "index.json"
    if not index_file.exists():
        return None
    try:
        idx = json.loads(index_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for s in idx.get("sessions", []):
        if s.get("session_id") == session_id:
            raw = s.get("llc_step_id") or s.get("llc_step")
            if raw is None:
                return None
            try:
                return canonical_id(raw)
            except UnknownStepError:
                return str(raw)
    return None


def _prp_from_index(session_id):
    """Le o PRP de uma sessao no index.json (ou None).

    Prefere o campo `prp` persistido pelo init (pos-v1.6); fallback para o nome
    do branch do worktree (`prp-{id}/wave-{n}`) em sessoes legadas."""
    index_file = ACE_DIR / "index.json"
    if index_file.exists():
        try:
            idx = json.loads(index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            idx = {"sessions": []}
        for s in idx.get("sessions", []):
            if s.get("session_id") == session_id:
                prp = s.get("prp")
                if prp:
                    return prp

    # Fallback: branch do worktree
    import re as _re

    wt = ACE_DIR / "worktrees" / session_id
    if wt.exists():
        try:
            r = subprocess.run(
                ["git", "-C", str(wt), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            m = _re.search(r"prp-(PRP-\d+)", r.stdout)
            if m:
                return m.group(1)
        except (subprocess.CalledProcessError, OSError):
            pass
    return None


def _run_prp_verify(prp_id):
    """Roda prp_verify.py --strict para o PRP. Retorna True se houver CRITICAL (exit 2)."""
    script = SCRIPTS_DIR / "prp_verify.py"
    if not script.exists():
        return False
    result = subprocess.run(
        [sys.executable, str(script), "--prp", prp_id, "--strict", "--json"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    if result.returncode == 2:
        try:
            data = json.loads(result.stdout)
            print(
                f"⛔ prp_verify CRITICAL em {prp_id}: "
                f"{data.get('critical', 0)} pendência(s) bloqueante(s)"
            )
        except (json.JSONDecodeError, TypeError):
            print(f"⛔ prp_verify CRITICAL em {prp_id}")
        return True
    return False


def _maybe_block_on_prp_verify(session_id, eff_step):
    """Gate deterministico de aceite de PRP (Step 11.2). Retorna True se o merge
    deve ser bloqueado.

    Roda prp_verify.py --strict apenas para sessoes de execucao (step 11) com um
    PRP associado. Bypass explicito via LLC_PRP_NO_VERIFY=1 (logado). Espelha o
    enforcement de §8.7 (defense in depth): a skill llc-prp-verify e advisory;
    este e o check deterministico que impede o merge."""
    if os.environ.get("LLC_PRP_NO_VERIFY") == "1":
        print("⚠️  prp_verify BYPASSADO via LLC_PRP_NO_VERIFY=1 (override explicito)")
        return False
    if not session_id or eff_step is None:
        return False
    try:
        is_exec = canonical_id(eff_step) == "11"
    except UnknownStepError:
        return False
    if not is_exec:
        return False
    prp_id = _prp_from_index(session_id)
    if not prp_id:
        return False
    return _run_prp_verify(prp_id)


def _resolve_session(session_id):
    """Resolve o session_id valido + step: id informado existente, ou ultima in_progress.
    Retorna (session_id, llc_step) ou (None, None). Cobre o modo manual ('manual'/None)."""
    sessions_dir = ACE_DIR / "sessions"
    index_file = ACE_DIR / "index.json"

    if session_id and (sessions_dir / f"{session_id}.md").exists():
        return session_id, _step_from_index(session_id)

    if index_file.exists():
        try:
            idx = json.loads(index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            idx = {"sessions": []}
        in_progress = [
            s for s in idx.get("sessions", []) if s.get("status") == "in_progress"
        ]
        if in_progress:
            s = in_progress[-1]
            raw = s.get("llc_step_id") or s.get("llc_step")
            try:
                step_id = canonical_id(raw) if raw is not None else None
            except UnknownStepError:
                step_id = str(raw) if raw is not None else None
            return s.get("session_id"), step_id

    return None, None


def _record_gate_result(session_id, step, decision):
    """Registra <gate_result> na secao ## Gates do arquivo da sessao (idempotente).
    finalize_session.py le essa tag para decidir merge/discard do worktree."""
    session_file = ACE_DIR / "sessions" / f"{session_id}.md"
    if not session_file.exists():
        return
    content = session_file.read_text(encoding="utf-8")
    import re

    # Idempotencia: so retornar se houver uma tag REAL — ignora o placeholder
    # comentado do template (<!-- <gate_result ... -->), que tambem casa "<gate_result".
    if "<gate_result" in re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL):
        return
    step_attr = f' step="{step}"' if step is not None else ""
    tag = (
        f'<gate_result{step_attr} decision="{decision}" reviewer="harness">'
        f"human gate</gate_result>"
    )
    placeholder = '<!-- <gate_result step="N" decision="approved" reviewer="...">...</gate_result> -->'
    if placeholder in content:
        content = content.replace(placeholder, tag)
    elif "## Gates" in content:
        content = content.replace("## Gates", f"## Gates\n\n{tag}", 1)
    else:
        content += f"\n\n## Gates\n\n{tag}\n"
    session_file.write_text(content, encoding="utf-8")


def session_end(session_id, gate_decision, context_seed_output, step=None):
    """Finaliza sessao ACE: registra <gate_result>, finaliza via finalize_session.py
    (que faz merge/discard do worktree + context_seed + atualiza o index)."""
    if not context_seed_output:
        context_seed_output = "state: step concluido\npending: nenhum\nblockers: nenhum\nnext_action: proximo step"

    # Resolve a sessao real (id valido ou ultima in_progress) + step
    real_id, resolved_step = _resolve_session(session_id)
    eff_step = step if step is not None else resolved_step

    # Gate deterministico de aceite de PRP (Step 11.2) — bloqueia o merge em CRITICAL.
    if _maybe_block_on_prp_verify(real_id, eff_step):
        block_merge = True
        if gate_decision != "rejected":
            gate_decision = "rejected"
    else:
        block_merge = False

    # Registra o <gate_result> no arquivo da sessao — lido por finalize_session.py
    if real_id and gate_decision:
        _record_gate_result(real_id, eff_step, gate_decision)

    # Finaliza via finalize_session.py com as flags REAIS (--session, --context-seed)
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "finalize_session.py"),
        "--context-seed",
        context_seed_output,
        "--json",
    ]
    if real_id:
        cmd.extend(["--session", real_id])
    if block_merge:
        cmd.append("--block-merge")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    if result.returncode != 0:
        print(f"⚠️  Aviso ao finalizar sessao:\n{result.stderr}")

    data = json.loads(result.stdout) if result.stdout else {}
    print(f"✅ Sessao finalizada. Gate: {gate_decision}")

    return data


# ── Skill loading (R4: progressive disclosure) ──


def load_agents_conventions():
    """Carrega apenas o Document Index do AGENTS.md, nao o arquivo inteiro (R4).
    O agente usa o indice comprimido para decidir quais arquivos carregar sob demanda."""
    if not AGENTS_FILE.exists():
        return ""

    content = AGENTS_FILE.read_text(encoding="utf-8")
    # Extrai apenas a secao Documentation Index (compacta, ~400 tokens)
    import re

    match = re.search(
        r"### Documentation Index \(Compressed\)(.*?)(?=\n## |\n---\n## |\Z)",
        content,
        re.DOTALL,
    )
    if match:
        index_section = match.group(0)
        return (
            "---\n# CONVENTIONS (Document Index only — progressive disclosure)\n---\n\n"
            + index_section
            + "\n\n---\n# TASK\n---\n\n"
        )
    # Fallback: carrega so as primeiras 50 linhas (cabecalho + zonas)
    lines = content.split("\n")[:50]
    return (
        "---\n# CONVENTIONS (header only)\n---\n\n"
        + "\n".join(lines)
        + "\n\n---\n# TASK\n---\n\n"
    )


def skill_load(step, context_seed=None, task=None):
    """Carrega skill + convencoes minimal + context_seed. Retorna prompt montado.

    Resolucao deterministica via llc_steps.REGISTRY (sem glob/ambiguidade):
    cada StepSpec aponta para um skill_file exato. Step sem skill_file -> erro.
    """
    spec = normalize_step(step)
    if not spec.skill_file:
        print(f"❌ Step {spec.id} ({spec.name}) nao tem skill associada.")
        sys.exit(1)
    skill_file = SKILLS_DIR / f"{spec.skill_file}.md"
    if not skill_file.exists():
        print(f"❌ Skill nao encontrada: {skill_file} (step {spec.id})")
        sys.exit(1)

    conventions = load_agents_conventions()
    skill = skill_file.read_text(encoding="utf-8")

    prompt = conventions + skill

    if context_seed:
        prompt += f"\n\n---\n# CONTEXT (sessao anterior)\n---\n\n{context_seed}"

    if task:
        prompt += f"\n\n---\n# TASK\n---\n\n{task}"

    prompt += "\n\n---\n# FINALIZACAO\n---\n\n"
    prompt += (
        "Ao concluir este step, gere um context_seed no formato ACE de 4 campos:\n"
    )
    prompt += "state: [acoes concluidas, arquivos alterados]\n"
    prompt += "pending: [tarefas incompletas]\n"
    prompt += "blockers: [impedimentos ativos]\n"
    prompt += "next_action: [proximo passo recomendado]\n"

    return str(skill_file), prompt


# ── Agent invocation ──


def agent_invoke(prompt, task_description=None, client=None):
    """Invoca cliente CLI com Early Commitment + Replay."""
    if not CLASSIFY_REPLAY_AVAILABLE:
        return _llm_invoke(prompt, client)

    # 1. Early Commitment: classificar tarefa
    classification = None
    if task_description:
        classification = classify_task(task_description, client)
        if classification:
            log_replay_event(
                "classify",
                None,
                type=classification["type"],
                confidence=classification["confidence"],
            )
            print(
                f"🏷️  Classificado: {classification['type']} "
                f"(confianca: {classification['confidence']:.0%})"
            )

    if classification:
        # 2. Buscar script no cache
        script = find_best_script(classification["type"], task_description)

        if script:
            log_replay_event(
                "replay_hit",
                script["id"],
                type=classification["type"],
                usage_count=script.get("usage_count", 0),
                match_score="computed",
            )

            # 2a. Stale cache check (R3)
            if check_target_files_stale(script.get("target_files", [])):
                log_replay_event("llm_fallback", None, reason="stale_cache")
                print("⚠️  Script obsoleto (arquivos mudaram). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2b. Architecture version check (R3)
            current_arch = get_architecture_version()
            if script.get("architecture_version", "") != current_arch:
                log_replay_event("llm_fallback", None, reason="arch_changed")
                print("⚠️  Script obsoleto (arquitetura mudou). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2c. Zone check (R2)
            target_files = extract_files_from_script(script)
            if any(is_red_zone(Path(f)) for f in target_files):
                print("🔴 Zona VERMELHA detectada. Gate humano necessario.")
                if gate_check(canonical_id(11), script) != "approved":
                    log_replay_event("llm_fallback", None, reason="zone_red_rejected")
                    return _llm_invoke(prompt, client)

            # 2d. Pre-flight (C)
            if not preflight_all_steps(script, {}):
                log_replay_event("llm_fallback", None, reason="preflight_fail")
                return _llm_invoke(prompt, client)

            # 3. REPLAY (R5: rollback integrado)
            print(
                f"⚡ Replay: {classification['type']} "
                f"(script {script['id']}, {script.get('usage_count', 0)} usos)"
            )
            return deterministic_replay(
                script, {}, gate_check, _llm_invoke, prompt, client
            )
        else:
            log_replay_event(
                "replay_miss", None, type=classification["type"], reason="no_cache"
            )

    # 4. Fallback: execucao normal via LLM
    log_replay_event(
        "llm_fallback",
        None,
        reason="no_classify" if not classification else "cache_miss",
    )
    return _llm_invoke(prompt, client)


def _llm_invoke(prompt, client=None):
    """Execucao LLM via pipe STDIN — funciona com qualquer terminal agentico.

    Nao usa flags como --prompt porque cada CLI tem sua propria convencao.
    O prompt e enviado via STDIN (communicate), que todos os CLIs aceitam.

    Se LLC_AGENT_CLI estiver definida, usa esse binario.
    Se nao, detecta o primeiro CLI disponivel no PATH.
    Se nenhum CLI for encontrado, exibe o prompt em modo manual.

    Retorna (output, exit_code, context_seed).
    """
    if client is None:
        client = detect_agent_client()

    if client:
        import re
        import time

        print(f"🤖 Invocando {client} (prompt via STDIN, {len(prompt)} chars)...")

        process = subprocess.Popen(
            [client],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path.cwd(),
        )

        output = ""
        code = 1
        try:
            output, _ = process.communicate(input=prompt, timeout=600)
            code = process.returncode
            # Print output after execution (modo batch — sem streaming real)
            if output.strip():
                print(output)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            print(f"\n⏰ Timeout (600s).")
            return output or "", 124, None
        except BrokenPipeError:
            print(f"\n⚠️  Pipe quebrado — {client} pode nao aceitar STDIN.")
            return output or "", 1, None

        if code != 0 and not output.strip():
            print(f"\n⚠️  {client} retornou exit code {code} sem output.")
            print(f"   Configure LLC_AGENT_CLI ou execute em modo manual.\n")
            return output, code, None

        # Extrai context_seed do output do agente (G2)
        seed_match = re.search(
            r"state:\s*(.*?)\n\s*pending:\s*(.*?)\n\s*blockers:\s*(.*?)\n\s*next_action:\s*(.*?)(?:\n|$)",
            output,
            re.DOTALL | re.IGNORECASE,
        )
        if seed_match:
            context_seed = (
                f"state: {seed_match.group(1).strip()}\n"
                f"pending: {seed_match.group(2).strip()}\n"
                f"blockers: {seed_match.group(3).strip()}\n"
                f"next_action: {seed_match.group(4).strip()}"
            )
            print(f"✅ Context seed extraido ({len(context_seed)} chars)")
            return output, code, context_seed

        return output, code, None

    # Fallback: modo manual
    print("📋 Nenhum cliente CLI configurado. Modo manual:")
    print("=" * 60)
    print(prompt[:3000])
    if len(prompt) > 3000:
        print(f"... (truncado — {len(prompt)} chars totais)")
    print("=" * 60)
    print("\nCole o prompt acima no seu terminal agentico e, ao finalizar,")
    print("certifique-se de que o output contenha um context_seed com:")
    print("  state: ...")
    print("  pending: ...")
    print("  blockers: ...")
    print("  next_action: ...")
    print(f"\n💡 Dica: defina LLC_AGENT_CLI=claude (ou opencode, codex, windsurf)")
    print("   para envio automatico via STDIN.")
    return "", 0, None


# ── Pipeline orchestration ──


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
    sid = step_run("0.2", task="Delta Impact Analysis")
    decision = gate_check("0.2", None, auto_approve=auto_approve)
    session_end(sid, decision, None, step="0.2")
    if decision == "rejected":
        print("\n⛔ Gate Δ.0 REPROVADO. Pipeline pausado.")
        return False

    # Step Δ.1
    sid = step_run("0.3", task="Delta Grill Me")
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
                import subprocess

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
