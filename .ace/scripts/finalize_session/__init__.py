#!/usr/bin/env python3
"""finalize_session — finalização de sessão ACE (Step de encerramento).

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - paths:     constantes de caminho + PLANNING_DOCS
  - extract:   extração de tags do arquivo de sessão
  - context:   geração/gravação de context_seed + status do arquivo
  - promote:   promoção de learning_points e skill_feedback
  - planning:  reflexão de task_completed nos docs de planejamento
  - index:     atualização do index.json
  - worktree:  merge/cleanup de worktree + git commit
  - cli:       entrypoint de linha de comando

Este __init__ re-exporta a API completa para manter o runner
`finalize_session.py` (subprocess, usado pelo harness) funcionando.
"""

from .paths import (
    ACE_DIR,
    INDEX_FILE,
    LEARNING_POINTS_FILE,
    MEMORY_DIR,
    PLANNING_DOCS,
    SESSIONS_DIR,
    SKILL_FEEDBACK_FILE,
    TASKS_FILE,
    WORKTREES_DIR,
)
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
from .planning import (
    map_status_emoji,
    update_planning_doc,
    update_planning_docs,
    update_status_cell,
)
from .index import update_index
from .worktree import (
    get_worktree_for_session,
    git_commit,
    merge_and_cleanup_worktree,
)
from .cli import main

__all__ = [
    "ACE_DIR",
    "INDEX_FILE",
    "LEARNING_POINTS_FILE",
    "MEMORY_DIR",
    "PLANNING_DOCS",
    "SESSIONS_DIR",
    "SKILL_FEEDBACK_FILE",
    "TASKS_FILE",
    "WORKTREES_DIR",
    "extract_actions",
    "extract_all_tags",
    "extract_blockers",
    "extract_files_touched",
    "extract_learning_points",
    "extract_skill_feedback",
    "extract_task_completions",
    "build_context_seed",
    "update_session_status",
    "write_context_seed",
    "promote_learning_points",
    "save_skill_feedback",
    "map_status_emoji",
    "update_planning_doc",
    "update_planning_docs",
    "update_status_cell",
    "update_index",
    "get_worktree_for_session",
    "git_commit",
    "merge_and_cleanup_worktree",
    "main",
]
