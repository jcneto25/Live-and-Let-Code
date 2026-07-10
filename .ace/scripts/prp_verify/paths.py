#!/usr/bin/env python3
"""Resolução de caminhos declarados no PRP."""

from pathlib import Path

from .constants import EXCLUDE_PARTS, SEARCH_ROOTS


def _is_excluded(p: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in p.parts)


def resolve_path(declared: str) -> Path | None:
    """Resolve um caminho declarado no PRP para um Path existente (ou None).

    Tenta o caminho literal; se não existir, busca pelo basename sob raízes
    limitadas (apps/src/packages/.), excluindo node_modules/.ace/dist. Placeholders
    com `{` (ex: `{service}.spec.ts`) não resolvem → None."""
    if not declared:
        return None
    p = declared.strip().strip("`").strip().strip('"').strip("'")
    if not p or "{" in p:
        return None

    cand = Path(p)
    if cand.exists() and not _is_excluded(cand):
        return cand

    name = Path(p).name
    if not name:
        return None
    for root in SEARCH_ROOTS:
        base = Path(root)
        if not base.exists() or not base.is_dir():
            continue
        try:
            for hit in base.glob(f"**/{name}"):
                if hit.is_file() and not _is_excluded(hit):
                    return hit
        except (OSError, PermissionError):
            continue
    return None
