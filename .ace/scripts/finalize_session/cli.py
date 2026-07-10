#!/usr/bin/env python3
"""finalize_session — CLI de finalização de sessão ACE."""

import argparse
import json
import sys

from .paths import INDEX_FILE, SESSIONS_DIR, logger
from .extract import (
    extract_actions,
    extract_all_tags,
    extract_blockers,
    extract_files_touched,
    extract_learning_points,
    extract_skill_feedback,
    extract_task_completions,
)
from .context import (
    build_context_seed,
    update_session_status,
    write_context_seed,
)
from .promote import promote_learning_points, save_skill_feedback
from .planning import update_planning_docs
from .index import update_index
from .worktree import get_worktree_for_session, git_commit, merge_and_cleanup_worktree


def main():
    parser = argparse.ArgumentParser(description="Finaliza uma sessão ACE no LLC")
    parser.add_argument("--session", type=str, help="Session ID (padrão: última sessão in_progress)")
    parser.add_argument("--context-seed", type=str, default=None,
                        help="Context seed fornecido pelo agente (schema: state/pending/blockers/next_action)")
    parser.add_argument("--commit", action="store_true", help="Faz git commit automático")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar alterações em arquivos")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--block-merge", action="store_true",
                        help="Força gate_decision='rejected' (override de qualquer <gate_result>). "
                             "Usado pelo harness quando prp_verify encontra CRITICAL — impede o merge.")
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
    files_touched = extract_files_touched(content)
    logger.info(f"📋 {len(completed_tasks)} task_completed, {len(skill_feedback)} skill_feedback, "
                f"{len(files_touched)} arquivo(s) tocado(s)")

    context_seed = build_context_seed(actions, learnings, blockers, gate_present, args.context_seed)
    logger.info(f"📦 Context seed gerado ({len(context_seed)} chars)")

    write_context_seed(session_file, context_seed, dry_run=args.dry_run)
    update_session_status(session_file, "completed", dry_run=args.dry_run)
    promote_learning_points(session_file, dry_run=args.dry_run)
    feedback_saved = save_skill_feedback(skill_feedback, session_id, dry_run=args.dry_run)
    tasks_updated = update_planning_docs(completed_tasks, dry_run=args.dry_run)
    update_index(session_id, status="completed", files_touched=files_touched, dry_run=args.dry_run)

    gate_decision = None
    for g in gates:
        d = g["attrs"].get("decision")
        if d:
            gate_decision = d

    if args.block_merge:
        logger.info("⛔ --block-merge ativo: merge bloqueado (prp_verify CRITICAL)")
        gate_decision = "rejected"

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
