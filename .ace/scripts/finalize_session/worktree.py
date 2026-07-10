#!/usr/bin/env python3
"""finalize_session — worktree (merge/cleanup) e git commit."""

import subprocess

from .paths import WORKTREES_DIR, logger


def get_worktree_for_session(session_id: str) -> str | None:
    """Return the worktree path for a session if it exists."""
    worktree_path = WORKTREES_DIR / session_id
    return worktree_path if worktree_path.exists() else None


def merge_and_cleanup_worktree(session_id: str, decision: str, dry_run: bool = False) -> bool:
    """Se decision == 'approved': merge branch e remove worktree.
    Se decision == 'rejected': apenas remove worktree sem merge."""
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


def git_commit(session_id: str):
    try:
        subprocess.run(["git", "add", ".ace/"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"ace: session {session_id} completed"], check=True, capture_output=True)
        logger.info("✅ Git commit realizado")
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️  Git commit falhou: {e.stderr.decode()}")
