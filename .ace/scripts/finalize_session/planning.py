#!/usr/bin/env python3
"""finalize_session — reflexão de task_completed nos docs de planejamento."""

import re
from pathlib import Path

from .paths import PLANNING_DOCS, logger


STATUS_EMOJI = {
    "done": "✅",
    "partial": "🔄",
}


def map_status_emoji(status: str) -> str:
    """Converte status de <task_completed> no emoji da coluna Status do TASKS.md."""
    return STATUS_EMOJI.get(status, "✅")


def update_status_cell(content: str, id_to_emoji: dict) -> tuple[str, int]:
    """Atualiza tabelas markdown: para cada linha de dados sob um header com coluna
    "Status", se alguma célula da linha casar um task_id (word-boundary), substitui
    o conteúdo da célula Status pelo emoji mapeado. Retorna (novo_conteúdo, n)."""
    if not id_to_emoji:
        return content, 0

    id_patterns = {tid: re.compile(rf"\b{re.escape(tid)}\b") for tid in id_to_emoji}
    lines = content.split("\n")
    status_col = None
    updated = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            status_col = None
            continue

        parts = line.split("|")
        cells = [p.strip() for p in parts]

        if status_col is None:
            col = next((idx for idx, c in enumerate(cells) if c.lower() == "status"), None)
            if col is not None:
                status_col = col
            continue

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


def update_planning_docs(completed_tasks: list[dict], dry_run: bool = False) -> int:
    """Reflete task_completed nas tabelas de Status de TASKS.md, EXECUTION_WAVES.md e PLAN.md."""
    total = 0
    for path, label in PLANNING_DOCS:
        total += update_planning_doc(path, completed_tasks, dry_run, label)
    if total == 0 and completed_tasks:
        logger.info("ℹ️  Nenhum task_completed pôde ser refletido nos docs de planejamento "
                    "(IDs sem linha correspondente ou já marcados)")
    return total
