#!/usr/bin/env python3
"""Shared session-sequence computation (used by validate-session-write e initialize_session).

Elimina a duplicação de get_next_sequence/get_next_session_id: ambos calculam
o próximo ID livre como max(numeros)+1, verificado contra o disco (não len+1,
para não colidir quando uma sessão do meio é deletada).
"""

import re
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"
_SESSION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{3})\.md$")


def get_next_session_id(today: str | None = None) -> str:
    """Próximo ID de sessão livre (sem extensão), formato YYYY-MM-DD-NNN.

    Usa max(numeros)+1 — não len+1 — para não colidir quando uma sessão do
    meio é deletada. Inclui guard contra criação manual/race.
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    if not SESSIONS_DIR.exists():
        return f"{today}-001"

    pattern = re.compile(rf"^{re.escape(today)}-(\d{{3}})\.md$")
    existing_numbers: list[int] = []
    for f in SESSIONS_DIR.iterdir():
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                existing_numbers.append(int(m.group(1)))

    next_num = (max(existing_numbers) + 1) if existing_numbers else 1
    candidate = f"{today}-{next_num:03d}"
    while (SESSIONS_DIR / f"{candidate}.md").exists():  # guard contra race/criação manual
        next_num += 1
        candidate = f"{today}-{next_num:03d}"
    return candidate
