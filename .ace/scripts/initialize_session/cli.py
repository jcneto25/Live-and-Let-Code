#!/usr/bin/env python3
"""initialize_session — CLI de inicialização de sessão ACE."""

import argparse
import json
import sys

from llc_steps import REGISTRY, normalize_step

from .paths import SESSIONS_DIR, logger
from .session import (
    cleanup_orphan_worktrees,
    create_session_file,
    create_worktree,
    extract_context_seed,
    get_next_session_id,
    get_previous_session,
    update_index,
)
from .graph import build_dependency_context, load_dependency_graph


def main():
    parser = argparse.ArgumentParser(description="Inicializa uma nova sessão ACE no LLC")
    parser.add_argument("--step", type=normalize_step, required=True,
                        help=f"Etapa LLC (id/alias/número). Válidos: {sorted(REGISTRY)}")
    parser.add_argument("--step-name", type=str, default=None,
                        help="Nome do step (opcional; inferido do mapa se omitido)")
    parser.add_argument("--task", type=str, required=True, help="Contexto da tarefa")
    parser.add_argument("--project", type=str, default="", help="Nome do projeto")
    parser.add_argument("--wave", type=int, default=1, help="Número da onda")
    parser.add_argument("--prp", type=str, default=None, help="ID do PRP (ex: PRP-001)")
    parser.add_argument("--no-worktree", action="store_true",
                        help="Desativa criacao automatica de git worktree (padrao: ativo p/ sessoes com --prp ou steps auto_worktree: 11, 11.1)")
    parser.add_argument("--tags", type=str, nargs="*", default=[], help="Tags da sessão")
    parser.add_argument("--json", action="store_true", help="Output em JSON (para tool calls)")
    args = parser.parse_args()

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_id = get_next_session_id()
    logger.info(f"🆔 Session ID: {session_id}")

    prev_session = get_previous_session()
    context_seed = None
    if prev_session:
        logger.info(f"📍 Sessão anterior: {prev_session.session_id}")
        prev_file = SESSIONS_DIR / prev_session.file
        context_seed = extract_context_seed(prev_file)
        if context_seed:
            logger.info(f"📦 Context seed carregado ({len(context_seed)} chars)")
        else:
            logger.warning("⚠️  Sessão anterior sem context_seed")
    else:
        logger.info("🆕 Primeira sessão do projeto")

    step_name = args.step_name or args.step.name

    dependency_context = ""
    graph = load_dependency_graph()
    if graph:
        dep_text = build_dependency_context(args.step.number, graph)
        if dep_text:
            dependency_context = dep_text
            logger.info(f"📊 Subgrafo de dependências carregado ({len(dep_text)} chars)")
            for line in dep_text.split("\n"):
                logger.info(f"   {line}")
        else:
            logger.info("ℹ️  Nenhuma dependência em cascata para este step.")

    session_file = create_session_file(
        session_id=session_id, llc_step=args.step.number, llc_step_id=args.step.id,
        step_name=step_name, task_context=args.task, project=args.project, wave=args.wave,
        prev_session=prev_session, context_seed=context_seed,
        dependency_context=dependency_context
    )

    update_index(session_id=session_id, llc_step=args.step.number,
                 llc_step_id=args.step.id, tags=args.tags, prp=args.prp)

    worktree_path = None
    auto_worktree = (args.prp is not None or args.step.auto_worktree) and not args.no_worktree
    if auto_worktree:
        cleanup_orphan_worktrees()
        worktree_path = create_worktree(session_id, args.prp, args.wave)
        if worktree_path:
            logger.info(f"🔀 Sessao isolada em worktree: {worktree_path}")
        else:
            logger.warning("⚠️  Worktree nao criado — continuando no workspace principal")

    result = {
        "session_id": session_id,
        "file": str(session_file),
        "prev_session": prev_session.session_id if prev_session else None,
        "context_seed": context_seed,
        "llc_step": args.step.number,
        "llc_step_id": args.step.id,
        "llc_step_name": step_name,
        "worktree": str(worktree_path) if worktree_path else None,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("✅ SESSÃO INICIALIZADA")
        print(f"{'='*60}")
        print(f"Session ID: {result['session_id']}")
        print(f"Arquivo: {result['file']}")
        print(f"Etapa LLC: {result['llc_step']} — {result['llc_step_name']}")
        if result['prev_session']:
            print(f"Sessão anterior: {result['prev_session']}")
        if result['context_seed']:
            print(f"\n📦 CONTEXT SEED:")
            print(f"{'-'*60}")
            print(result['context_seed'])
            print(f"{'-'*60}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
