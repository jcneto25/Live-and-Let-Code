#!/usr/bin/env python3
"""finalize_session — atualização do index.json."""

import json
from datetime import datetime

from .paths import INDEX_FILE, logger


def update_index(session_id: str, status: str = "completed",
                 files_touched: list = None, dry_run: bool = False):
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
            if files_touched:
                existing = session.get("tags", []) or []
                merged = list(existing)
                for f in files_touched:
                    if f not in merged:
                        merged.append(f)
                session["tags"] = merged
            updated = True
            break

    if not updated:
        logger.warning(f"⚠️  Sessão {session_id} não encontrada no index")
        return

    if not dry_run:
        INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info(f"✅ index.json atualizado (status: {status})")
