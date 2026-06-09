#!/usr/bin/env python3
"""
Finaliza uma sessão ACE no Live-and-Let-Code.

Fluxo:
1. Lê o arquivo de sessão atual
2. Gera context_seed estruturado (schema de 4 campos)
3. Substitui placeholder de context_seed no arquivo
4. Promove learning_points de alta prioridade
5. Atualiza index.json (status: completed)
6. Opcionalmente faz commit git

Uso:
    python .ace/scripts/finalize_session.py
    python .ace/scripts/finalize_session.py --session 2026-06-09-001
    python .ace/scripts/finalize_session.py --context-seed "state: auth refatorado\npending: refresh token\n..."
    python .ace/scripts/finalize_session.py --commit
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"
MEMORY_DIR = ACE_DIR / "memory"
LEARNING_POINTS_FILE = MEMORY_DIR / "learning_points.md"
TASKS_FILE = Path("docs/planning/TASKS.md")


def extract_all_tags(content: str, tag: str) -> list[dict]:
    pattern = f'<{tag}([^>]*)>(.*?)</{tag}>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({"attrs": attrs, "content": body.strip()})
    return results


def extract_actions(content: str) -> list[dict]:
    return extract_all_tags(content, "action")


def extract_learning_points(content: str) -> list[dict]:
    return extract_all_tags(content, "learning_point")


def extract_blockers(content: str) -> list[dict]:
    return extract_all_tags(content, "blocker")


def build_context_seed(
    actions: list[dict],
    learnings: list[dict],
    blockers: list[dict],
    gate_present: bool,
    agent_seed: Optional[str] = None,
) -> str:
    """Constrói o context_seed no schema de 4 campos OBRIGATÓRIOS."""
    if agent_seed:
        return agent_seed

    # Campo: state
    state_parts = []
    if actions:
        last_actions = actions[-5:]
        for a in last_actions:
            a_type = a["attrs"].get("type", "?")
            desc_match = re.search(r'<description>(.*?)</description>', a["content"])
            file_match = re.search(r'<file_delta>(.*?)</file_delta>', a["content"])
            file_delta = file_match.group(1).strip() if file_match else ""
            description = desc_match.group(1).strip() if desc_match else ""
            if description:
                state_parts.append(f"[{a_type}] {description}")
    state = "; ".join(state_parts) if state_parts else "sessão concluída"

    # Campo: pending
    pending_parts = []
    unresolved = [b for b in blockers if b["attrs"].get("resolved", "false").lower() == "false"]
    for b in unresolved[:3]:
        pending_parts.append(b["content"].strip())
    if not pending_parts:
        pending_parts.append("nenhuma pendência identificada")
    pending = "; ".join(pending_parts)

    # Campo: blockers
    if unresolved:
        blocker_texts = [b["content"].strip() for b in unresolved[:3]]
        blockers_str = "; ".join(blocker_texts)
    else:
        blockers_str = "nenhum ativo"

    # Campo: next_action
    if unresolved:
        next_action = f"resolver blocker: {unresolved[0]['content'].strip()}"
    elif not gate_present:
        next_action = "validar etapa atual (gate pendente)"
    else:
        next_action = "prosseguir para a próxima etapa"

    return f"state: {state}\npending: {pending}\nblockers: {blockers_str}\nnext_action: {next_action}"


def write_context_seed(session_file: Path, context_seed: str):
    """
    Substitui APENAS o placeholder de context_seed na seção ## Encerramento.
    Não modifica o <context_seed> da seção ## Contexto (que é da sessão anterior).
    """
    content = session_file.read_text(encoding='utf-8')

    placeholder = "state: [preencher no encerramento]\npending: [preencher no encerramento]\nblockers: [preencher no encerramento]\nnext_action: [preencher no encerramento]"

    if placeholder in content:
        content = content.replace(placeholder, context_seed)
        session_file.write_text(content, encoding='utf-8')
        logger.info("✅ context_seed gravado na seção Encerramento")
    else:
        logger.warning("⚠️  Placeholder de context_seed não encontrado — appendando ao final")
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Contexto para Próxima Sessão\n\n<context_seed>\n{context_seed}\n</context_seed>\n")


def promote_learning_points(session_file: Path):
    content = session_file.read_text(encoding='utf-8')
    learnings = extract_learning_points(content)
    high_priority = [l for l in learnings if l["attrs"].get("priority") == "high"]

    if not high_priority:
        logger.info("ℹ️  Nenhum learning_point de alta prioridade para promover")
        return

    MEMORY_DIR.mkdir(exist_ok=True)
    existing = LEARNING_POINTS_FILE.read_text(encoding='utf-8') if LEARNING_POINTS_FILE.exists() else "# Learning Points Consolidados\n\n"

    promoted = 0
    for learning in high_priority:
        text = learning["content"]
        if text not in existing:
            existing += f"\n## {session_file.stem}\n\n{text}\n"
            promoted += 1

    if promoted:
        LEARNING_POINTS_FILE.write_text(existing, encoding='utf-8')
        logger.info(f"✅ {promoted} learning_point(s) promovido(s)")
    else:
        logger.info("ℹ️  Todos os learning_points já foram promovidos")


def update_index(session_id: str, status: str = "completed"):
    if not INDEX_FILE.exists():
        logger.error("❌ index.json não encontrado")
        return
    try:
        index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"❌ index.json inválido: {e}")
        return

    updated = False
    for session in index["sessions"]:
        if session["session_id"] == session_id:
            session["status"] = status
            session["completed_at"] = datetime.now().isoformat()
            updated = True
            break

    if not updated:
        logger.warning(f"⚠️  Sessão {session_id} não encontrada no index")
        return

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info(f"✅ index.json atualizado (status: {status})")


def extract_task_completions(content: str) -> list[dict]:
    """Extrai tarefas concluídas das tags <task_completed>."""
    pattern = r'<task_completed([^>]*)>(.*?)</task_completed>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({
            "task_id": attrs.get("id", ""),
            "prp": attrs.get("prp", ""),
            "status": attrs.get("status", "done"),
            "description": body.strip()
        })
    return results


def update_tasks_md(completed_tasks: list[dict], dry_run: bool = False) -> int:
    """Atualiza TASKS.md marcando checkboxes concluídas."""
    if not completed_tasks:
        return 0

    if not TASKS_FILE.exists():
        logger.warning("⚠️  TASKS.md não encontrado — task_completed ignorados")
        return 0

    content = TASKS_FILE.read_text(encoding='utf-8')
    updated_count = 0

    for task in completed_tasks:
        task_id = task["task_id"]
        if not task_id:
            continue

        pattern = re.compile(
            rf'^(\s*- \[)([ x/])(\] .*?\b{re.escape(task_id)}\b.*)$',
            re.MULTILINE
        )

        def replace_cb(match):
            nonlocal updated_count
            if match.group(2) != 'x':
                updated_count += 1
                return f'{match.group(1)}x{match.group(3)}'
            return match.group(0)

        new_content = pattern.sub(replace_cb, content)
        if new_content != content:
            content = new_content

    if updated_count > 0 and not dry_run:
        TASKS_FILE.write_text(content, encoding='utf-8')
        logger.info(f"✅ TASKS.md atualizado — {updated_count} tarefa(s) marcada(s) como [x]")
    elif updated_count > 0:
        logger.info(f"🔍 [DRY RUN] {updated_count} tarefa(s) seriam marcadas no TASKS.md")
    else:
        logger.info("ℹ️  Nenhuma task_completed nova encontrada ou já marcada")

    return updated_count


def git_commit(session_id: str):
    try:
        subprocess.run(["git", "add", ".ace/"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"ace: session {session_id} completed"], check=True, capture_output=True)
        logger.info("✅ Git commit realizado")
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️  Git commit falhou: {e.stderr.decode()}")


def main():
    parser = argparse.ArgumentParser(description="Finaliza uma sessão ACE no LLC")
    parser.add_argument("--session", type=str, help="Session ID (padrão: última sessão in_progress)")
    parser.add_argument("--context-seed", type=str, default=None,
                        help="Context seed fornecido pelo agente (schema: state/pending/blockers/next_action)")
    parser.add_argument("--commit", action="store_true", help="Faz git commit automático")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    args = parser.parse_args()

    if args.session:
        session_file = SESSIONS_DIR / f"{args.session}.md"
        session_id = args.session
    else:
        if not INDEX_FILE.exists():
            logger.error("❌ index.json não encontrado")
            return 1
        try:
            index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            logger.error("❌ index.json inválido")
            return 1
        in_progress = [s for s in index["sessions"] if s["status"] == "in_progress"]
        if not in_progress:
            logger.error("❌ Nenhuma sessão in_progress encontrada")
            return 1
        last_session = in_progress[-1]
        session_id = last_session["session_id"]
        session_file = SESSIONS_DIR / last_session["file"]

    if not session_file.exists():
        logger.error(f"❌ Arquivo de sessão não encontrado: {session_file}")
        return 1

    logger.info(f"🔄 Finalizando sessão: {session_id}")

    content = session_file.read_text(encoding='utf-8')
    actions = extract_actions(content)
    learnings = extract_learning_points(content)
    blockers = extract_blockers(content)
    gates = extract_all_tags(content, "gate_result")
    gate_present = len(gates) > 0

    logger.info(f"📊 {len(actions)} ações, {len(learnings)} learning_points, "
                f"{len(blockers)} blockers, gate={'✓' if gate_present else '✗'}")

    completed_tasks = extract_task_completions(content)
    logger.info(f"📋 {len(completed_tasks)} task_completed encontradas")

    context_seed = build_context_seed(actions, learnings, blockers, gate_present, args.context_seed)
    logger.info(f"📦 Context seed gerado ({len(context_seed)} chars)")

    write_context_seed(session_file, context_seed)
    promote_learning_points(session_file)
    tasks_updated = update_tasks_md(completed_tasks)
    update_index(session_id, status="completed")

    if args.commit:
        git_commit(session_id)

    result = {
        "session_id": session_id, "file": str(session_file),
        "context_seed": context_seed, "actions_count": len(actions),
        "learnings_count": len(learnings), "blockers_count": len(blockers),
        "gate_present": gate_present, "tasks_updated": tasks_updated
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("✅ SESSÃO FINALIZADA")
        print(f"{'='*60}")
        print(f"Session ID: {result['session_id']}")
        print(f"\n📦 CONTEXT SEED:")
        print(f"{'-'*60}")
        print(context_seed)
        print(f"{'-'*60}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
