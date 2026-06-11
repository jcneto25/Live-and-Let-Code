#!/usr/bin/env python3
"""
Exibe sugestões de melhoria de skills pendentes, agrupadas por skill e prioridade.
O mantenedor revisa, edita o skill manualmente, e marca como [applied] ou [dismissed].

Uso:
    python .ace/scripts/promote-skill-feedback.py
    python .ace/scripts/promote-skill-feedback.py --skill llc-step-0-5
    python .ace/scripts/promote-skill-feedback.py --mark applied --id "2026-06-10-001"
"""

import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict

FEEDBACK_FILE = Path(".ace/memory/skill_feedback.md")


def parse_feedback() -> list[dict]:
    if not FEEDBACK_FILE.exists():
        return []

    content = FEEDBACK_FILE.read_text(encoding='utf-8')
    pattern = r'## \[(\w+)\] (\S+) — (\S+)\n\n(.*?)\n<!-- status: (\w+) -->'
    matches = re.findall(pattern, content, re.DOTALL)

    results = []
    for i, (priority, skill, session_id, text, status) in enumerate(matches):
        results.append({
            "index": i,
            "priority": priority,
            "skill": skill,
            "session_id": session_id,
            "content": text.strip(),
            "status": status
        })
    return results


def mark_status(items: list[dict], target_session: str, new_status: str):
    if not FEEDBACK_FILE.exists():
        print("❌ Nenhum feedback registrado.")
        return

    content = FEEDBACK_FILE.read_text(encoding='utf-8')
    updated = 0
    for item in items:
        if item["session_id"] == target_session:
            old = f"<!-- status: {item['status']} -->"
            new = f"<!-- status: {new_status} -->"
            content = content.replace(old, new, 1)
            updated += 1

    if updated:
        FEEDBACK_FILE.write_text(content, encoding='utf-8')
        print(f"✅ {updated} feedback(s) da sessão {target_session} marcados como [{new_status}]")
    else:
        print(f"ℹ️  Nenhum feedback encontrado para a sessão {target_session}")


def display(items: list[dict], filter_skill: str = None, filter_status: str = "pending"):
    filtered = [i for i in items if i["status"] == filter_status]
    if filter_skill:
        filtered = [i for i in filtered if i["skill"] == filter_skill]

    if not filtered:
        print(f"✅ Nenhum feedback pendente{' para ' + filter_skill if filter_skill else ''}.")
        return

    by_skill = defaultdict(list)
    for item in filtered:
        by_skill[item["skill"]].append(item)

    icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    for skill, feedbacks in sorted(by_skill.items()):
        print(f"\n{'─'*60}")
        print(f"📦 {skill} ({len(feedbacks)} sugestões)")
        print(f"{'─'*60}")
        for fb in feedbacks:
            icon = icons.get(fb["priority"], "⚪")
            print(f"  {icon} [{fb['priority']}] Sessão: {fb['session_id']}")
            print(f"     {fb['content'][:200]}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Gerencia sugestões de melhoria de skills LLC")
    parser.add_argument("--skill", type=str, help="Filtrar por skill específico")
    parser.add_argument("--mark", type=str, choices=["applied", "dismissed"],
                        help="Marcar feedback como applied ou dismissed")
    parser.add_argument("--id", type=str, help="Session ID para marcar (ex: 2026-06-10-001)")
    args = parser.parse_args()

    items = parse_feedback()

    if args.mark and args.id:
        mark_status(items, args.id, args.mark)
    else:
        display(items, args.skill)

    return 0


if __name__ == "__main__":
    sys.exit(main())
