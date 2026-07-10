#!/usr/bin/env python3
"""initialize_session — inicialização de sessão ACE (Step de abertura).

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - paths:     constantes, mapas de step (LLC_STEPS/STEP_ARTIFACTS), logging
  - graph:     grafo de dependências + contexto derivado (cascata de triggers)
  - session:   SessionInfo, criação de arquivo/index/worktree, contexto
  - cli:       entrypoint de linha de comando

Este __init__ re-exporta a API completa para manter o runner
`initialize_session.py` (subprocess, usado pelo harness) funcionando.
"""

from .paths import (
    ACE_DIR,
    GRAPH_FILE,
    INDEX_FILE,
    LLC_STEPS,
    SESSIONS_DIR,
    STEP_ARTIFACTS,
    TEMPLATE_FILE,
    VALID_STEPS,
    WORKTREES_DIR,
)
from .graph import (
    build_dependency_context,
    compute_checksum,
    load_dependency_graph,
    resolve_triggers,
)
from .session import (
    SessionInfo,
    cleanup_orphan_worktrees,
    create_session_file,
    create_worktree,
    extract_context_seed,
    get_next_session_id,
    get_previous_session,
    update_index,
)
from .cli import main

__all__ = [
    "ACE_DIR",
    "GRAPH_FILE",
    "INDEX_FILE",
    "LLC_STEPS",
    "SESSIONS_DIR",
    "STEP_ARTIFACTS",
    "TEMPLATE_FILE",
    "VALID_STEPS",
    "WORKTREES_DIR",
    "build_dependency_context",
    "compute_checksum",
    "load_dependency_graph",
    "resolve_triggers",
    "SessionInfo",
    "cleanup_orphan_worktrees",
    "create_session_file",
    "create_worktree",
    "extract_context_seed",
    "get_next_session_id",
    "get_previous_session",
    "update_index",
    "main",
]
