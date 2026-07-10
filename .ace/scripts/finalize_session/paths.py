#!/usr/bin/env python3
"""finalize_session — constantes de caminho e docs de planejamento."""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"
MEMORY_DIR = ACE_DIR / "memory"
LEARNING_POINTS_FILE = MEMORY_DIR / "learning_points.md"
SKILL_FEEDBACK_FILE = MEMORY_DIR / "skill_feedback.md"
TASKS_FILE = Path("docs/planning/TASKS.md")
WORKTREES_DIR = ACE_DIR / "worktrees"

# Docs de planejamento cujas tabelas de Status refletem task_completed.
# Nota: o status de onda em chave-valor (EXECUTION_WAVES §2.{N}.1 "| **Status** | ...")
# tem formato distinto e permanece atualização manual/da skill.
PLANNING_DOCS = [
    (TASKS_FILE, "TASKS.md"),
    (Path("docs/planning/EXECUTION_WAVES.md"), "EXECUTION_WAVES.md"),
    (Path("docs/planning/PLAN.md"), "PLAN.md"),
]
