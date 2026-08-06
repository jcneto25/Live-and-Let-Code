#!/usr/bin/env python3
"""Session lifecycle: start, index resolution, PRP-verify merge block, end."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from llc_steps import UnknownStepError, canonical_id

from .common import ACE_DIR, SCRIPTS_DIR

SESSIONS_DIR = ACE_DIR / "sessions"


def session_start(step, prp=None, task=None, wave=1, no_worktree=False):
    """Inicializa sessao ACE. Retorna dict com session_id, context_seed, worktree_path."""
    # GOV-002 Decisão item 2 / GOV-003 R7: falha explícita em vez de manufaturar
    # task placeholder ("Step N") — padrão das sessões órfãs. O initialize_session
    # repete a mesma guarda (defense in depth).
    from initialize_session.session import is_placeholder_task
    if is_placeholder_task(task):
        print(f"❌ Sessão recusada (GOV-002): step {step} sem --task real.")
        print('   Informe a tarefa: llc run --step N --task "Descrever a tarefa real".')
        print("   Tasks placeholder (ex.: 'Step N') são proibidas.")
        sys.exit(2)

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "initialize_session.py"),
        "--step",
        str(step),
        "--task",
        task,
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
    wt = ACE_DIR / "worktrees" / session_id
    if wt.exists():
        try:
            r = subprocess.run(
                ["git", "-C", str(wt), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            m = re.search(r"prp-(PRP-\d+)", r.stdout)
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
    index_file = ACE_DIR / "index.json"

    if session_id and (SESSIONS_DIR / f"{session_id}.md").exists():
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
    session_file = SESSIONS_DIR / f"{session_id}.md"
    if not session_file.exists():
        return
    content = session_file.read_text(encoding="utf-8")

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
