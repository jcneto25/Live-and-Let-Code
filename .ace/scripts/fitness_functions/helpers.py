#!/usr/bin/env python3
"""Helpers compartilhados das fitness functions."""

import re
from pathlib import Path

from .config import SRC_DIR


def find_ts_files(base: Path) -> list[Path]:
    return list(base.rglob("*.ts")) + list(base.rglob("*.tsx"))


def module_name_from_path(path: Path, src: Path = SRC_DIR) -> str | None:
    """Extrai o nome do módulo do caminho (ex: src/auditorias/service.ts → 'auditorias')."""
    try:
        rel = path.relative_to(src)
        parts = rel.parts
        if len(parts) >= 1 and parts[0] != "common":
            return parts[0]
        if len(parts) >= 2:
            return parts[1]
        return None
    except ValueError:
        return None


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def count_effective_lines(content: str) -> int:
    """Conta linhas efetivas de código (exclui imports, decorators, blank lines, braces)."""
    lines = content.split("\n")
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        if (
            stripped.startswith("@")
            or stripped.startswith("export class")
            or stripped.startswith("export interface")
        ):
            continue
        if stripped in ("{", "}", "};", "})"):
            continue
        if (
            stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        ):
            continue
        count += 1
    return count


def extract_constructor_params(content: str) -> list[str]:
    """Extrai parâmetros do constructor de uma classe."""
    # Match constructor(...params)
    match = re.search(r"constructor\s*\(([^)]*)\)", content, re.DOTALL)
    if not match:
        return []
    params_str = match.group(1)
    # Simple extraction - split by comma, get the parameter names
    params = []
    for p in params_str.split(","):
        p = p.strip()
        if not p:
            continue
        # Remove decorators, types, defaults
        p = re.sub(r"^\w+\s+", "", p)  # remove public/private/readonly
        p = p.split(":")[0].strip()  # remove type annotation
        p = p.split("=")[0].strip()  # remove default value
        if p:
            params.append(p)
    return params
