#!/usr/bin/env python3
"""finalize_session — promoção de learning_points e skill_feedback."""

from pathlib import Path

from .paths import LEARNING_POINTS_FILE, MEMORY_DIR, SKILL_FEEDBACK_FILE, logger
from .extract import extract_learning_points


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
