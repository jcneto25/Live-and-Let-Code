#!/usr/bin/env python3
"""Shared learning-point extraction (used by promote-learning-points e finalize_session).

Evita a duplicação de extract_learning_points() que existia em ambos os módulos.
"""

import re
from pathlib import Path

LEARNING_POINT_RE = re.compile(r"<learning_point([^>]*)>(.*?)</learning_point>", re.DOTALL)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def extract_learning_points(content: str) -> list[dict]:
    """Extrai learning_points de um conteúdo de sessão.

    Cada tag <learning_point priority="...">...</learning_point> vira
    {"priority": str, "content": str}.
    """
    results = []
    for attrs_str, body in LEARNING_POINT_RE.findall(content):
        attrs: dict[str, str] = {
            m.group(1): m.group(2) for m in ATTR_RE.finditer(attrs_str)
        }
        results.append({"priority": attrs.get("priority", "medium"), "content": body.strip()})
    return results


def normalize_text(text: str) -> str:
    """Normaliza texto para comparação de duplicatas (minúsculo, espaços únicos)."""
    return " ".join(text.lower().split())


def load_existing_learning_points(file_path: Path) -> dict[str, str]:
    """Carrega learning_points já consolidados como {texto_normalizado: texto}."""
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8")
    sections = re.findall(r"## ([^\n]+)\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    return {normalize_text(text): text for _, text in sections}
