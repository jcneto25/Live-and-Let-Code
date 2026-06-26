#!/usr/bin/env python3
"""
Valida se um arquivo de sessão ACE pode ser criado sem sobrescrever existentes.

Uso:
    python .ace/scripts/validate-session-write.py --filename 2026-06-26-001.md
    python .ace/scripts/validate-session-write.py --check-latest

Comportamento:
    - Lê o diretório .ace/sessions/ (NÃO o index.json, que pode estar stale)
      para determinar o próximo número de sequência disponível (max+1).
    - Se o arquivo já existir em disco, retorna erro com o próximo disponível.
    - Se não existir, retorna sucesso.

Saída (JSON):
    {"status": "ok", "filename": "2026-06-26-003.md"}
    {"status": "ok", "next_available": "2026-06-26-003.md", "date": "2026-06-26"}
    {"status": "error", "error": "Arquivo 2026-06-26-001.md já existe em ...",
     "existing": ["2026-06-26-001.md", "2026-06-26-002.md"],
     "next_available": "2026-06-26-003.md",
     "suggestion": "Use 2026-06-26-003.md em vez de 2026-06-26-001.md"}

Exit code: 0 (ok/info), 1 (arquivo já existe).
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ACE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ACE_DIR / "sessions"


def get_next_sequence(today: str) -> str:
    """Próximo nome disponível para a data (max+1, verificado contra o disco).

    Usa max(numeros)+1 — não len+1 — para não colide quando uma sessão do meio
    é deletada. Mantenha em sincronia com initialize_session.get_next_session_id.
    """
    if not SESSIONS_DIR.exists():
        return f"{today}-001.md"

    pattern = re.compile(rf"^{re.escape(today)}-(\d{{3}})\.md$")
    existing_numbers = []
    for f in SESSIONS_DIR.iterdir():
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                existing_numbers.append(int(m.group(1)))

    next_num = (max(existing_numbers) + 1) if existing_numbers else 1
    candidate = f"{today}-{next_num:03d}.md"
    while (SESSIONS_DIR / candidate).exists():  # guard contra race/criação manual
        next_num += 1
        candidate = f"{today}-{next_num:03d}.md"
    return candidate


def main():
    parser = argparse.ArgumentParser(description="Valida escrita de sessão ACE")
    parser.add_argument("--filename", help="Nome do arquivo de sessão pretendido")
    parser.add_argument(
        "--check-latest",
        action="store_true",
        help="Verifica qual é o próximo arquivo disponível",
    )
    args = parser.parse_args()

    today = date.today().isoformat()

    if args.check_latest:
        next_file = get_next_sequence(today)
        print(json.dumps({"status": "ok", "next_available": next_file, "date": today}))
        sys.exit(0)

    if not args.filename:
        next_file = get_next_sequence(today)
        print(json.dumps({
            "status": "info",
            "message": "Nenhum --filename fornecido. Use --check-latest para obter o próximo.",
            "suggestion": next_file,
            "date": today,
        }))
        sys.exit(0)

    filepath = SESSIONS_DIR / args.filename

    if filepath.exists():
        existing = sorted(
            f.name for f in SESSIONS_DIR.iterdir()
            if f.is_file() and f.name.startswith(today)
        )
        next_file = get_next_sequence(today)
        print(json.dumps({
            "status": "error",
            "error": f"Arquivo {args.filename} já existe em {SESSIONS_DIR}",
            "existing": existing,
            "next_available": next_file,
            "suggestion": f"Use {next_file} em vez de {args.filename}",
        }, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps({"status": "ok", "filename": args.filename}))


if __name__ == "__main__":
    main()
