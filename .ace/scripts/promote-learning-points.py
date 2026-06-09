#!/usr/bin/env python3
"""
Promove learning_points de alta prioridade para memory/learning_points.md.

NOTA: extract_learning_points() é idêntica à função em finalize_session.py.
      Se modificar uma, modifique a outra.

Uso:
    python .ace/scripts/promote-learning-points.py
    python .ace/scripts/promote-learning-points.py --all
    python .ace/scripts/promote-learning-points.py --session 2026-06-09-001
    python .ace/scripts/promote-learning-points.py --dry-run --json
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
SESSIONS_DIR = ACE_DIR / "sessions"
MEMORY_DIR = ACE_DIR / "memory"
LEARNING_POINTS_FILE = MEMORY_DIR / "learning_points.md"


def extract_learning_points(content: str) -> list[dict]:
    pattern = r'<learning_point([^>]*)>(.*?)</learning_point>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({
            "priority": attrs.get("priority", "medium"),
            "content": body.strip()
        })
    return results


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def load_existing_learning_points() -> dict[str, str]:
    if not LEARNING_POINTS_FILE.exists():
        return {}
    content = LEARNING_POINTS_FILE.read_text(encoding='utf-8')
    sections = re.findall(r'## ([^\n]+)\n\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    existing = {}
    for source, text in sections:
        existing[normalize_text(text)] = text
    return existing


def promote_from_session(session_file: Path, existing: dict[str, str]) -> list[dict]:
    content = session_file.read_text(encoding='utf-8')
    learnings = extract_learning_points(content)
    high_priority = [l for l in learnings if l["priority"] == "high"]

    promoted = []
    for learning in high_priority:
        normalized = normalize_text(learning["content"])
        if normalized not in existing:
            promoted.append({"source": session_file.stem, "content": learning["content"]})
            existing[normalized] = learning["content"]

    return promoted


def append_learning_points(promoted: list[dict], dry_run: bool = False):
    """Appenda novos learning_points ao arquivo (nunca reescreve conteúdo existente)."""
    if not promoted:
        logger.info("ℹ️  Nenhum learning_point novo para promover")
        return 0

    MEMORY_DIR.mkdir(exist_ok=True)

    if not dry_run:
        with open(LEARNING_POINTS_FILE, "a", encoding="utf-8") as f:
            for item in promoted:
                f.write(f"\n## {item['source']}\n\n{item['content']}\n")
        logger.info(f"✅ {len(promoted)} learning_point(s) appenado(s)")
    else:
        logger.info(f"🔍 [DRY RUN] {len(promoted)} learning_point(s) seriam promovidos:")
        for item in promoted:
            logger.info(f"   - {item['source']}: {item['content'][:80]}...")

    return len(promoted)


def main():
    parser = argparse.ArgumentParser(description="Promove learning_points de alta prioridade")
    parser.add_argument("--all", action="store_true", help="Processa todas as sessões")
    parser.add_argument("--session", type=str, help="Processa apenas uma sessão específica")
    parser.add_argument("--dry-run", action="store_true", help="Mostra sem escrever")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    args = parser.parse_args()

    if not SESSIONS_DIR.exists():
        logger.error("❌ Diretório .ace/sessions/ não encontrado")
        return 1

    existing = load_existing_learning_points()
    logger.info(f"📚 {len(existing)} learning_points já consolidados")

    if args.session:
        session_files = [SESSIONS_DIR / f"{args.session}.md"]
    elif args.all:
        session_files = sorted(SESSIONS_DIR.glob("*.md"))
    else:
        session_files = sorted(SESSIONS_DIR.glob("*.md"))[-1:]

    if not session_files:
        logger.error("❌ Nenhuma sessão encontrada")
        return 1

    logger.info(f"🔍 Processando {len(session_files)} sessão(ões)")

    all_promoted = []
    for session_file in session_files:
        if not session_file.exists():
            logger.warning(f"⚠️  Arquivo não encontrado: {session_file}")
            continue
        all_promoted.extend(promote_from_session(session_file, existing))

    count = append_learning_points(all_promoted, args.dry_run)

    if args.json:
        print(json.dumps({
            "promoted": len(all_promoted),
            "total_consolidated": len(existing) + len(all_promoted),
            "items": [{"source": p["source"], "content": p["content"][:120]} for p in all_promoted]
        }, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"{'🔍 DRY RUN CONCLUÍDO' if args.dry_run else '✅ PROMOÇÃO CONCLUÍDA'}")
        print(f"{'='*60}")
        print(f"Promovidos nesta execução: {len(all_promoted)}")
        print(f"Total consolidado: {len(existing) + len(all_promoted)}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
