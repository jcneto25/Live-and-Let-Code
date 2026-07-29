#!/usr/bin/env python3
"""initialize_session — criação de sessão, index e worktree."""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Optional

import session_sequence
from llc_steps import normalize_step, REGISTRY

from .paths import (
    INDEX_FILE,
    SESSIONS_DIR,
    TEMPLATE_FILE,
    WORKTREES_DIR,
    logger,
)
from .graph import build_dependency_context, load_dependency_graph


@dataclass
class SessionInfo:
    session_id: str
    file: str
    status: str
    llc_step: float
    llc_step_id: str = ""
    tags: list = field(default_factory=list)
    timestamp: str = ""


def extract_context_seed(session_file: Path) -> Optional[str]:
    if not session_file.exists():
        return None
    content = session_file.read_text(encoding='utf-8')
    match = re.search(r'<context_seed>(.*?)</context_seed>', content, re.DOTALL)
    return match.group(1).strip() if match else None


def get_next_session_id() -> str:
    """Próximo ID de sessão livre (max+1) — delega ao módulo compartilhado
    session_sequence (sem duplicar a lógica usada por validate-session-write)."""
    return session_sequence.get_next_session_id()


def get_previous_session() -> Optional[SessionInfo]:
    if not INDEX_FILE.exists():
        return None
    try:
        index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"index.json inválido: {e}")
        return None
    sessions = index.get("sessions", [])
    known_fields = {f.name for f in fields(SessionInfo)}
    for session_data in reversed(sessions):
        if session_data.get("status") in ("completed", "in_progress"):
            # Tolera campos extras do index.json (completed_at, prp, futuros)
            # gravados por finalize_session/update_index — só os campos do
            # dataclass são desempacotados.
            return SessionInfo(**{k: v for k, v in session_data.items()
                                  if k in known_fields})
    return None


def build_context_block(prev_session: Optional[SessionInfo], context_seed: Optional[str],
                        dependency_context: str = "") -> str:
    """Constrói o bloco de contexto usando lógica nativa Python (sem {{#if}} frágil)."""
    blocks = []
    if context_seed and prev_session:
        blocks.append(
            f"**Sessão anterior:** {prev_session.session_id}\n\n"
            f"<context_seed>\n{context_seed}\n</context_seed>"
        )
    else:
        blocks.append("Primeira sessão do projeto.")

    if dependency_context:
        blocks.append(
            f"\n\n**Dependências consultadas:**\n"
            f"<dependencies>\n{dependency_context}\n</dependencies>"
        )

    return "\n".join(blocks)


def render_template(session_id: str, llc_step: float, llc_step_id: str,
                    step_name: str, task_context: str, project: str, wave: int,
                    prev_session: Optional[SessionInfo],
                    context_seed: Optional[str], status: str = "in_progress",
                    dependency_context: str = "") -> str:
    if not TEMPLATE_FILE.exists():
        logger.error(f"Template não encontrado: {TEMPLATE_FILE}")
        sys.exit(1)

    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    prev_session_id = prev_session.session_id if prev_session else "null"
    context_block = build_context_block(prev_session, context_seed, dependency_context)

    return (template
            .replace("{{session_id}}", session_id)
            .replace("{{llc_step}}", str(llc_step))
            .replace("{{llc_step_id}}", llc_step_id)
            .replace("{{status}}", status)
            .replace("{{llc_step_name}}", step_name)
            .replace("{{project}}", project)
            .replace("{{wave}}", str(wave))
            .replace("{{task_context}}", task_context)
            .replace("{{prev_session_id}}", prev_session_id)
            .replace("{{context_block}}", context_block)
            .replace("{{duration}}", "0"))


def create_session_file(session_id: str, llc_step: float, llc_step_id: str,
                        step_name: str, task_context: str, project: str, wave: int,
                        prev_session: Optional[SessionInfo],
                        context_seed: Optional[str], status: str = "in_progress",
                        dependency_context: str = "") -> Path:
    content = render_template(session_id, llc_step, llc_step_id, step_name,
                              task_context, project, wave,
                              prev_session, context_seed, status,
                              dependency_context=dependency_context)
    session_file = SESSIONS_DIR / f"{session_id}.md"
    if session_file.exists():
        raise RuntimeError(
            f"OVERWRITE RECUSADO: {session_file} já existe. Histórico ACE é "
            f"imutável — reexecute initialize_session.py (computa o próximo ID "
            f"livre) ou rode validate-session-write.py --check-latest."
        )
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(content, encoding='utf-8')
    logger.info(f"✅ Sessão criada: {session_file}")
    return session_file


def update_index(session_id: str, llc_step: float, llc_step_id: str, tags: list,
                 prp: str | None = None):
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            index = {"project": "", "sessions": []}
    else:
        index = {"project": "", "sessions": []}

    record = {
        "session_id": session_id,
        "file": f"{session_id}.md",
        "status": "in_progress",
        "llc_step": llc_step,
        "llc_step_id": llc_step_id,
        "tags": tags,
        "timestamp": datetime.now().isoformat()
    }
    if prp:
        record["prp"] = prp
    index["sessions"].append(record)

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info("✅ index.json atualizado")


def create_worktree(session_id: str, prp_id: str | None, wave: int) -> Path | None:
    """Cria um git worktree para isolar o workspace desta sessão."""
    WORKTREES_DIR.mkdir(parents=True, exist_ok=True)

    worktree_path = WORKTREES_DIR / session_id

    branch_name = f"prp-{prp_id}/wave-{wave}" if prp_id else f"session/{session_id}"

    logger.info(f"📂 Criando worktree: {worktree_path} (branch: {branch_name})")

    try:
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            capture_output=True, text=True, check=True
        )
        logger.info(f"✅ Worktree criado em {worktree_path}")
        return worktree_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Falha ao criar worktree: {e.stderr}")
        return None


def cleanup_orphan_worktrees() -> int:
    """Remove worktrees sem sessão correspondente."""
    if not WORKTREES_DIR.exists():
        return 0

    removed = 0
    for wt_path in WORKTREES_DIR.iterdir():
        if wt_path.is_dir():
            session_file = SESSIONS_DIR / f"{wt_path.name}.md"
            if not session_file.exists():
                logger.info(f"🧹 Removendo worktree órfão: {wt_path}")
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt_path)],
                    capture_output=True, text=True
                )
                removed += 1
    return removed
