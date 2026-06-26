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
import subprocess
import sys
import shutil
from pathlib import Path

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
            _gates_config = json.loads(GATES_FILE.read_text(encoding='utf-8'))
        else:
            _gates_config = {"gates": {}, "step_to_gate": {}}
    return _gates_config


def get_gate_checklist(step):
    config = _load_gates_config()
    gate_num = config.get("step_to_gate", {}).get(str(step))
    if gate_num is None:
        return None, []
    gate = config.get("gates", {}).get(str(gate_num), {})
    return gate_num, gate.get("checklist", [])


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
        find_best_script, deterministic_replay,
        log_replay_event, is_red_zone, check_target_files_stale,
        get_architecture_version, preflight_all_steps, extract_files_from_script,
    )
    CLASSIFY_REPLAY_AVAILABLE = True
except ImportError:
    CLASSIFY_REPLAY_AVAILABLE = False

# ── Agent CLI detection ──

AGENT_CLIENTS = ["claude", "opencode", "codex", "cursor"]

def detect_agent_client():
    """Detecta o primeiro cliente de IA CLI disponivel no PATH."""
    for client in AGENT_CLIENTS:
        if shutil.which(client):
            return client
    return None

# ── Session management ──

def session_start(step, prp=None, task=None, wave=1, no_worktree=False):
    """Inicializa sessao ACE. Retorna dict com session_id, context_seed, worktree_path."""
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "initialize_session.py"),
        "--step", str(step),
        "--task", task or f"Step {step}",
        "--wave", str(wave),
        "--json"
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
    """Le o llc_step de uma sessao no index.json (ou None)."""
    index_file = ACE_DIR / "index.json"
    if not index_file.exists():
        return None
    try:
        idx = json.loads(index_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for s in idx.get("sessions", []):
        if s.get("session_id") == session_id:
            return s.get("llc_step")
    return None


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
        in_progress = [s for s in idx.get("sessions", [])
                       if s.get("status") == "in_progress"]
        if in_progress:
            s = in_progress[-1]
            return s.get("session_id"), s.get("llc_step")

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
    tag = (f'<gate_result{step_attr} decision="{decision}" reviewer="harness">'
           f'human gate</gate_result>')
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

    # Registra o <gate_result> no arquivo da sessao — lido por finalize_session.py
    if real_id and gate_decision:
        _record_gate_result(real_id, eff_step, gate_decision)

    # Finaliza via finalize_session.py com as flags REAIS (--session, --context-seed)
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "finalize_session.py"),
        "--context-seed", context_seed_output,
        "--json",
    ]
    if real_id:
        cmd.extend(["--session", real_id])

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

    content = AGENTS_FILE.read_text(encoding='utf-8')
    # Extrai apenas a secao Documentation Index (compacta, ~400 tokens)
    import re
    match = re.search(
        r'### Documentation Index \(Compressed\)(.*?)(?=\n## |\n---\n## |\Z)',
        content, re.DOTALL
    )
    if match:
        index_section = match.group(0)
        return (
            "---\n# CONVENTIONS (Document Index only — progressive disclosure)\n---\n\n"
            + index_section
            + "\n\n---\n# TASK\n---\n\n"
        )
    # Fallback: carrega so as primeiras 50 linhas (cabecalho + zonas)
    lines = content.split('\n')[:50]
    return "---\n# CONVENTIONS (header only)\n---\n\n" + '\n'.join(lines) + "\n\n---\n# TASK\n---\n\n"


def skill_load(step, context_seed=None, task=None):
    """Carrega skill + convencoes minimal + context_seed. Retorna prompt montado."""
    skill_file = SKILLS_DIR / f"llc-step-{step}.md"
    if not skill_file.exists():
        import glob
        matches = list(SKILLS_DIR.glob(f"llc-step-{str(step).replace('.', '-')}*.md"))
        if matches:
            skill_file = matches[0]
        else:
            print(f"❌ Skill nao encontrada: {skill_file}")
            sys.exit(1)

    conventions = load_agents_conventions()
    skill = skill_file.read_text(encoding='utf-8')

    prompt = conventions + skill

    if context_seed:
        prompt += f"\n\n---\n# CONTEXT (sessao anterior)\n---\n\n{context_seed}"

    if task:
        prompt += f"\n\n---\n# TASK\n---\n\n{task}"

    prompt += "\n\n---\n# FINALIZACAO\n---\n\n"
    prompt += "Ao concluir este step, gere um context_seed no formato ACE de 4 campos:\n"
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
            log_replay_event("classify", None,
                             type=classification["type"],
                             confidence=classification["confidence"])
            print(f"🏷️  Classificado: {classification['type']} "
                  f"(confianca: {classification['confidence']:.0%})")

    if classification:
        # 2. Buscar script no cache
        script = find_best_script(classification["type"], task_description)

        if script:
            log_replay_event("replay_hit", script["id"],
                             type=classification["type"],
                             usage_count=script.get("usage_count", 0),
                             match_score="computed")

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
                if gate_check(11, script) != "approved":
                    log_replay_event("llm_fallback", None, reason="zone_red_rejected")
                    return _llm_invoke(prompt, client)

            # 2d. Pre-flight (C)
            if not preflight_all_steps(script, {}):
                log_replay_event("llm_fallback", None, reason="preflight_fail")
                return _llm_invoke(prompt, client)

            # 3. REPLAY (R5: rollback integrado)
            print(f"⚡ Replay: {classification['type']} "
                  f"(script {script['id']}, {script.get('usage_count', 0)} usos)")
            return deterministic_replay(
                script, {}, gate_check, _llm_invoke, prompt, client
            )
        else:
            log_replay_event("replay_miss", None,
                             type=classification["type"], reason="no_cache")

    # 4. Fallback: execucao normal via LLM
    log_replay_event("llm_fallback", None,
                     reason="no_classify" if not classification else "cache_miss")
    return _llm_invoke(prompt, client)


def _llm_invoke(prompt, client=None):
    """Execucao LLM com streaming real e extracao de context_seed (G2, R3)."""
    if client is None:
        client = detect_agent_client()

    if client:
        print(f"🤖 Invocando {client}...")
        import re
        import time

        process = subprocess.Popen(
            [client, "--prompt", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=Path.cwd()
        )

        output_lines = []
        start_time = time.time()
        timeout = 600  # 10 min

        try:
            for line in process.stdout:
                print(line, end="")  # Streaming em tempo real
                output_lines.append(line)

                if time.time() - start_time > timeout:
                    process.kill()
                    print(f"\n⏰ Timeout ({timeout}s).")
                    return "\n".join(output_lines), 124, None

            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"\n⏰ Timeout.")
            return "\n".join(output_lines), 124, None

        output = "\n".join(output_lines)

        # Extrai context_seed do output do agente (G2)
        seed_match = re.search(
            r'state:\s*(.*?)\n\s*pending:\s*(.*?)\n\s*blockers:\s*(.*?)\n\s*next_action:\s*(.*?)(?:\n|$)',
            output, re.DOTALL | re.IGNORECASE
        )
        if seed_match:
            context_seed = (
                f"state: {seed_match.group(1).strip()}\n"
                f"pending: {seed_match.group(2).strip()}\n"
                f"blockers: {seed_match.group(3).strip()}\n"
                f"next_action: {seed_match.group(4).strip()}"
            )
            print(f"✅ Context seed extraido ({len(context_seed)} chars)")
            return output, process.returncode, context_seed

        return output, process.returncode, None
    else:
        print("📋 Nenhum cliente CLI detectado. Modo manual:")
        print("=" * 60)
        print(prompt[:2000])
        if len(prompt) > 2000:
            print(f"... (truncado — {len(prompt)} chars totais)")
        print("=" * 60)
        print("\nCole o prompt acima no seu cliente de IA.")
        return "", 0, None

# ── Pipeline orchestration ──

def pipeline_run(from_step=0, to_step=11, task=None):
    """Executa pipeline completo do step inicial ao final."""
    steps = [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 11]
    started = False

    for step in steps:
        if step < from_step:
            continue
        if step > to_step:
            break
        if not started:
            print(f"\n{'='*60}")
            print(f"🚀 Iniciando pipeline LLC (Step {from_step} → {to_step})")
            print(f"{'='*60}")
            started = True

        sid = step_run(step, task=task)
        decision = gate_check(step, None)
        session_end(sid, decision, None, step=step)

        if decision == "rejected":
            print(f"\n⛔ Gate {get_gate_checklist(step)[0]} REPROVADO. Pipeline pausado.")
            print("Corrija os problemas e reexecute a partir deste step:")
            print(f"  llc run --step {step}")
            return False

    print(f"\n{'='*60}")
    print("✅ Pipeline concluido com sucesso!")
    print(f"{'='*60}")
    return True

def step_run(step, prp=None, task=None, no_worktree=False):
    """Executa um step e retorna session_id."""
    sess = session_start(step, prp=prp, task=task, no_worktree=no_worktree)
    skill_file, prompt = skill_load(step, sess["context_seed"], task)
    print(f"📄 Skill: {skill_file}")
    print(f"📦 Context seed: {len(sess.get('context_seed', '') or '')} chars")

    _output, code, _context_seed = agent_invoke(prompt, task, client=None)
    if code != 0:
        print(f"⚠️  Agente retornou codigo {code}")
    return sess["session_id"]
