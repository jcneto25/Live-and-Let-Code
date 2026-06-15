#!/usr/bin/env python3
"""
Reconstrói .ace/index.json a partir dos YAML frontmatters em .ace/sessions/*.md.

Source-of-truth: arquivos de sessão individuais (não o index).
Recuperação de cenários onde index.json foi corrompido/deletado/divergiu
do conteúdo real do diretório sessions/ (ver §8.6 do llc-pipeline-design.md).

Uso:
    python .ace/scripts/rebuild-index.py            # reconstrói (com backup)
    python .ace/scripts/rebuild-index.py --dry-run  # mostra JSON sem escrever
    python .ace/scripts/rebuild-index.py --no-backup  # não cria .ace/index.json.bak

Campos regenerados (a partir de cada .ace/sessions/*.md):
  - session_id  ← frontmatter `session_id`
  - file        ← nome do arquivo
  - llc_step    ← frontmatter `llc_step`
  - status      ← inferido: "completed" se tem <context_seed>, senão "in_progress"
  - timestamp   ← frontmatter `created` ou derivado do session_id (YYYY-MM-DD)
  - tags        ← lista vazia (tags vivem no body, não no frontmatter)
  - project     ← frontmatter `project`

Sessões sem frontmatter válido são puladas com warning.
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
BACKUP_FILE = ACE_DIR / "index.json.bak"
SESSIONS_DIR = ACE_DIR / "sessions"

# Frontmatter é delimitado por --- no início e --- na próxima linha
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# session_id tem formato YYYY-MM-DD-NNN → podemos extrair a data como timestamp fallback
SESSION_ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-\d{3}$")
# Detecta bloco <context_seed> preenchido (heurística simples)
CONTEXT_SEED_RE = re.compile(r"<context_seed>\s*\n\s*\S", re.MULTILINE)


def parse_frontmatter(path: Path) -> Optional[dict]:
    """Extrai o YAML frontmatter como dict (parser minimalista, sem dependências).

    Suporta chaves top-level no formato `chave: valor`. Não suporta listas
    aninhadas, blocos ou tipos complexos — esses são raros no frontmatter
    de sessão e podem ser adicionados sob demanda.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error(f"❌ Não foi possível ler {path}: {e}")
        return None

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None

    entry: dict = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        # Suporta apenas chaves top-level (sem indentação)
        if line.startswith(" "):
            continue
        key, _, value = line.partition(":")
        entry[key.strip()] = value.strip().strip('"').strip("'")
    return entry


def infer_status(content: str) -> str:
    """Sessão com <context_seed> preenchido é considered 'completed'."""
    return "completed" if CONTEXT_SEED_RE.search(content) else "in_progress"


def infer_timestamp(frontmatter: dict, session_id: str) -> str:
    """Prioridade: frontmatter.created → data do session_id → agora (fallback)."""
    created = frontmatter.get("created")
    if created:
        return created
    m = SESSION_ID_RE.match(session_id)
    if m:
        return f"{m.group(1)}T00:00:00"
    return datetime.now().isoformat()


def build_session_entry(path: Path) -> Optional[dict]:
    """Monta uma entrada de índice a partir de um arquivo de sessão."""
    fm = parse_frontmatter(path)
    if not fm:
        logger.warning(f"⚠️  {path.name} sem frontmatter válido — pulando")
        return None

    session_id = fm.get("session_id") or path.stem
    if not session_id:
        logger.warning(f"⚠️  {path.name} sem session_id no frontmatter — pulando")
        return None

    try:
        llc_step = float(fm.get("llc_step", "0"))
    except ValueError:
        llc_step = 0.0

    content = path.read_text(encoding="utf-8")
    return {
        "session_id": session_id,
        "file": path.name,
        "status": infer_status(content),
        "llc_step": llc_step,
        "tags": [],
        "timestamp": infer_timestamp(fm, session_id),
    }


def rebuild_index(dry_run: bool = False, backup: bool = True) -> int:
    """Reconstrói o index. Retorna o número de sessões indexadas."""
    if not SESSIONS_DIR.exists():
        logger.error(f"❌ Diretório {SESSIONS_DIR} não existe — nada a reconstruir")
        return 0

    entries: list[dict] = []
    skipped: list[str] = []
    for path in sorted(SESSIONS_DIR.glob("*.md")):
        entry = build_session_entry(path)
        if entry is None:
            skipped.append(path.name)
        else:
            entries.append(entry)

    index = {
        "project": "",
        "generated_at": datetime.now().isoformat(),
        "source": "rebuild-index.py",
        "sessions": entries,
    }

    if dry_run:
        print(json.dumps(index, indent=2, ensure_ascii=False))
        logger.info(f"🔍 DRY-RUN: {len(entries)} sessões seriam indexadas, {len(skipped)} puladas")
        return len(entries)

    if INDEX_FILE.exists() and backup:
        BACKUP_FILE.write_text(INDEX_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info(f"📦 Backup criado: {BACKUP_FILE}")

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    logger.info(
        f"✅ {INDEX_FILE} reconstruído: {len(entries)} sessões "
        f"({len(skipped)} puladas)"
    )
    if skipped:
        logger.warning(f"⚠️  Arquivos pulados: {', '.join(skipped)}")
    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconstrói .ace/index.json a partir dos arquivos de sessão.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o JSON resultante sem escrever em disco",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Não cria backup do index.json atual antes de sobrescrever",
    )
    args = parser.parse_args()

    n = rebuild_index(dry_run=args.dry_run, backup=not args.no_backup)
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
