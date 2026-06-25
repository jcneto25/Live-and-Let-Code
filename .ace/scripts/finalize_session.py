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
SKILL_FEEDBACK_FILE = MEMORY_DIR / "skill_feedback.md"
TASKS_FILE = Path("docs/planning/TASKS.md")
WORKTREES_DIR = ACE_DIR / "worktrees"


def get_worktree_for_session(session_id: str) -> Path | None:
    """Return the worktree path for a session if it exists."""
    worktree_path = WORKTREES_DIR / session_id
    return worktree_path if worktree_path.exists() else None


def merge_and_cleanup_worktree(session_id: str, decision: str, dry_run: bool = False) -> bool:
    """
    Se decision == 'approved': merge branch e remove worktree.
    Se decision == 'rejected': apenas remove worktree sem merge.
    """
    worktree_path = get_worktree_for_session(session_id)
    if not worktree_path:
        return False

    branch_name = None
    try:
        result = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch_name = result.stdout.strip()
    except subprocess.CalledProcessError:
        logger.warning(f"⚠️  Não foi possível determinar o branch do worktree {worktree_path}")
        return False

    if decision == "approved":
        logger.info(f"🔀 Mergeando branch {branch_name} → master")
        if not dry_run:
            try:
                subprocess.run(
                    ["git", "merge", "--no-ff", branch_name, "-m",
                     f"ace: merge {branch_name} — session {session_id}"],
                    capture_output=True, text=True, check=True
                )
                logger.info(f"✅ Branch {branch_name} mergeado em master")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Falha no merge: {e.stderr}")
                return False
    else:
        logger.info(f"⏭️  Branch {branch_name} não mergeado (gate: {decision})")

    logger.info(f"🧹 Removendo worktree: {worktree_path}")
    if not dry_run:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            capture_output=True, text=True
        )
        if branch_name:
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                capture_output=True, text=True
            )

    return True


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


def write_context_seed(session_file: Path, context_seed: str, dry_run: bool = False):
    """
    Substitui APENAS o placeholder de context_seed na seção ## Encerramento.
    Não modifica o <context_seed> da seção ## Contexto (que é da sessão anterior).
    """
    content = session_file.read_text(encoding='utf-8')

    placeholder = "state: [preencher no encerramento]\npending: [preencher no encerramento]\nblockers: [preencher no encerramento]\nnext_action: [preencher no encerramento]"

    if placeholder in content:
        if not dry_run:
            content = content.replace(placeholder, context_seed)
            session_file.write_text(content, encoding='utf-8')
        logger.info("✅ context_seed gravado na seção Encerramento")
    else:
        logger.warning("⚠️  Placeholder de context_seed não encontrado — appendando ao final")
        if not dry_run:
            with open(session_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## Contexto para Próxima Sessão\n\n<context_seed>\n{context_seed}\n</context_seed>\n")


def promote_learning_points(session_file: Path, dry_run: bool = False):
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
        if not dry_run:
            LEARNING_POINTS_FILE.write_text(existing, encoding='utf-8')
        logger.info(f"✅ {promoted} learning_point(s) promovido(s)")
    else:
        logger.info("ℹ️  Todos os learning_points já foram promovidos")


def update_index(session_id: str, status: str = "completed", dry_run: bool = False):
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

    if not dry_run:
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


def extract_skill_feedback(content: str) -> list[dict]:
    """Extrai sugestões de melhoria de skills via <skill_feedback>."""
    pattern = r'<skill_feedback([^>]*)>(.*?)</skill_feedback>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({
            "skill": attrs.get("skill", "unknown"),
            "priority": attrs.get("priority", "medium"),
            "content": body.strip()
        })
    return results


def save_skill_feedback(feedback_items: list[dict], session_id: str, dry_run: bool = False) -> int:
    """Appenda sugestões de melhoria de skills ao arquivo de feedback."""
    if not feedback_items:
        return 0

    MEMORY_DIR.mkdir(exist_ok=True)

    if SKILL_FEEDBACK_FILE.exists():
        existing = SKILL_FEEDBACK_FILE.read_text(encoding='utf-8')
    else:
        existing = ""

    new_count = 0
    for item in feedback_items:
        if item["content"] not in existing:
            if not dry_run:
                with open(SKILL_FEEDBACK_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n## [{item['priority'].upper()}] {item['skill']} — {session_id}\n\n"
                            f"{item['content']}\n"
                            f"<!-- status: pending -->\n")
            new_count += 1

    if new_count > 0 and not dry_run:
        logger.info(f"✅ {new_count} skill_feedback appenado(s) a {SKILL_FEEDBACK_FILE}")
    elif new_count > 0:
        logger.info(f"🔍 [DRY RUN] {new_count} skill_feedback seriam appenados")
    return new_count


# Mapeia <task_completed status="..."> -> emoji da coluna Status (TASKS.md §2.1).
STATUS_EMOJI = {
    "done": "✅",
    "partial": "🔄",
}


def map_status_emoji(status: str) -> str:
    """Converte status de <task_completed> no emoji da coluna Status do TASKS.md."""
    return STATUS_EMOJI.get(status, "✅")


def update_status_cell(content: str, id_to_emoji: dict) -> tuple[str, int]:
    """
    Atualiza tabelas markdown: para cada linha de dados sob um header que contenha uma
    coluna "Status", se alguma célula da linha casar um task_id (word-boundary), substitui
    o conteúdo da célula Status pelo emoji mapeado. Tabelas sem coluna "Status" não são
    tocadas. Retorna (novo_conteúdo, n_células_atualizadas).
    """
    if not id_to_emoji:
        return content, 0

    id_patterns = {tid: re.compile(rf"\b{re.escape(tid)}\b") for tid in id_to_emoji}
    lines = content.split("\n")
    status_col = None  # índice (em line.split('|')) da coluna Status na tabela atual
    updated = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            status_col = None  # saiu da tabela
            continue

        parts = line.split("|")
        cells = [p.strip() for p in parts]

        if status_col is None:
            # procura um header cuja célula seja exatamente "Status"
            col = next((idx for idx, c in enumerate(cells) if c.lower() == "status"), None)
            if col is not None:
                status_col = col
            continue  # header/separador: nunca atualiza

        # linha de dados dentro de uma tabela com coluna Status
        if status_col >= len(parts):
            continue
        matched_emoji = None
        for tid, pat in id_patterns.items():
            if any(pat.search(c) for c in cells):
                matched_emoji = id_to_emoji[tid]
                break
        if matched_emoji is not None and parts[status_col].strip() != matched_emoji:
            parts[status_col] = f" {matched_emoji} "
            lines[i] = "|".join(parts)
            updated += 1

    return "\n".join(lines), updated


def update_planning_doc(file_path: Path, completed_tasks: list[dict],
                        dry_run: bool, label: str) -> int:
    """Reflete task_completed num doc de planejamento: checkboxes `- [ ]` + coluna Status."""
    if not completed_tasks or not file_path.exists():
        return 0

    content = file_path.read_text(encoding="utf-8")
    updated = 0

    # 1) checkboxes no formato "- [x] ... <task_id> ..." (legenda TASKS.md §2.2)
    for task in completed_tasks:
        tid = task["task_id"]
        if not tid:
            continue
        pattern = re.compile(
            rf'^(\s*- \[)([^\]])(\] .*?\b{re.escape(tid)}\b.*)$',
            re.MULTILINE
        )

        def replace_cb(match):
            nonlocal updated
            if match.group(2) != 'x':
                updated += 1
                return f'{match.group(1)}x{match.group(3)}'
            return match.group(0)

        content = pattern.sub(replace_cb, content)

    # 2) tabelas com coluna "Status" (formato real do TASKS/WAVES/PLAN)
    id_to_emoji = {
        t["task_id"]: map_status_emoji(t["status"])
        for t in completed_tasks if t["task_id"]
    }
    content, table_updated = update_status_cell(content, id_to_emoji)
    updated += table_updated

    if updated > 0:
        if not dry_run:
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"✅ {label} atualizado — {updated} status refletem task_completed")
        else:
            logger.info(f"🔍 [DRY RUN] {updated} status seriam atualizados em {label}")
    return updated


# Docs de planejamento cujas tabelas de Status refletem task_completed.
# Nota: o status de onda em chave-valor (EXECUTION_WAVES §2.{N}.1 "| **Status** | ...")
# tem formato distinto e permanece atualização manual/da skill.
PLANNING_DOCS = [
    (TASKS_FILE, "TASKS.md"),
    (Path("docs/planning/EXECUTION_WAVES.md"), "EXECUTION_WAVES.md"),
    (Path("docs/planning/PLAN.md"), "PLAN.md"),
]


def update_planning_docs(completed_tasks: list[dict], dry_run: bool = False) -> int:
    """Reflete task_completed nas tabelas de Status de TASKS.md, EXECUTION_WAVES.md e PLAN.md."""
    total = 0
    for path, label in PLANNING_DOCS:
        total += update_planning_doc(path, completed_tasks, dry_run, label)
    if total == 0 and completed_tasks:
        logger.info("ℹ️  Nenhum task_completed pôde ser refletido nos docs de planejamento "
                    "(IDs sem linha correspondente ou já marcados)")
    return total


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
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar alterações em arquivos")
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
    skill_feedback = extract_skill_feedback(content)
    logger.info(f"📋 {len(completed_tasks)} task_completed, {len(skill_feedback)} skill_feedback")

    context_seed = build_context_seed(actions, learnings, blockers, gate_present, args.context_seed)
    logger.info(f"📦 Context seed gerado ({len(context_seed)} chars)")

    write_context_seed(session_file, context_seed, dry_run=args.dry_run)
    promote_learning_points(session_file, dry_run=args.dry_run)
    feedback_saved = save_skill_feedback(skill_feedback, session_id, dry_run=args.dry_run)
    tasks_updated = update_planning_docs(completed_tasks, dry_run=args.dry_run)
    update_index(session_id, status="completed", dry_run=args.dry_run)

    gate_decision = None
    for m in re.finditer(r'<gate_result[^>]*decision="([^"]*)"', content):
        gate_decision = m.group(1)

    worktree_cleaned = False
    if gate_decision:
        worktree_cleaned = merge_and_cleanup_worktree(session_id, gate_decision, dry_run=args.dry_run)
    else:
        wt = get_worktree_for_session(session_id)
        if wt:
            logger.info(f"ℹ️  Worktree existe mas sem gate_decision — mantido para revisão manual: {wt}")

    if args.commit and not args.dry_run:
        git_commit(session_id)

    result = {
        "session_id": session_id, "file": str(session_file),
        "context_seed": context_seed, "actions_count": len(actions),
        "learnings_count": len(learnings), "blockers_count": len(blockers),
        "gate_present": gate_present, "tasks_updated": tasks_updated,
        "feedback_saved": feedback_saved,
        "worktree_cleaned": worktree_cleaned,
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
