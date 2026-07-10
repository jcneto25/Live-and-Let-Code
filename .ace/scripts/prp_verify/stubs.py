#!/usr/bin/env python3
"""Detecção de stub (impl e test) no prp_verify."""

import re

from .consistency import STUB_PATTERNS, detect_language, read_config


def is_stub_by_pattern(file_path: str, config: dict) -> bool:
    """Stub por PADRÃO POSITIVA apenas (return [], TODO, NotImplementedError, ...).

    Diferente de consistency-check.is_stub_file, NÃO usa o critério "≤3 linhas
    significativas" — este é um gate BLOQUEANTE (CRITICAL), então compact code real
    não pode ser falsamente marcado. Exige um sinal positivo de stub. Arquivos
    pequenos sem padrão de stub não são flagados aqui."""
    full = Path(file_path)
    if not full.exists():
        return True
    content = full.read_bytes()
    lang = detect_language(file_path)
    patterns: list[str] = []
    patterns.extend(
        config.get("stub_patterns", {}).get("any", STUB_PATTERNS.get("any", []))
    )
    patterns.extend(config.get("stub_patterns", {}).get(lang, []))
    patterns.extend(STUB_PATTERNS.get(lang, []))
    for pat in patterns:
        try:
            if re.search(pat.encode(), content, re.MULTILINE):
                return True
        except re.error:
            continue
    return False


# ── Padrões de stub-TEST (teatro de testes) — distintos dos stubs de impl ──

STUB_TEST_PATTERNS: dict[str, list[str]] = {
    "typescript": [
        r"\.toBeDefined\(\)",
        r"\.toBeNull\(\)",
        r"\.toBeTruthy\(\)",
        r"\.toBeFalsy\(\)",
        r"\.toEqual\(\s*\[\s*\]\s*\)",
        r"\.toEqual\(\s*\{\s*\}\s*\)",
    ],
    "javascript": [
        r"\.toBeDefined\(\)",
        r"\.toBeNull\(\)",
        r"\.toEqual\(\s*\[\s*\]\s*\)",
    ],
    "python": [
        r"\bassert True\b",
    ],
}


def is_stub_test_file(path) -> tuple[bool, str]:
    """Heurística conservadora de teatro de testes.

    Flag apenas se: há blocos de teste (it/test/def test_) mas NENHUMA asserção
    real — só asserções triviais (toBeDefined/toBeNull/toEqual([])/assert True).
    Retorna (é_stub, motivo)."""
    from pathlib import Path

    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists() or not path.is_file():
        return False, ""
    lang = detect_language(str(path))
    patterns = STUB_TEST_PATTERNS.get(lang, [])
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, ""

    # Conta blocos de teste
    if lang in ("typescript", "javascript"):
        test_blocks = len(re.findall(r"\b(?:it|test)\s*\(", content))
        real_asserts = len(re.findall(r"\bexpect\s*\(", content))
    elif lang == "python":
        test_blocks = len(re.findall(r"\bdef\s+test_\w+", content))
        real_asserts = len(re.findall(r"\bassert\s+", content))
    else:
        return False, ""  # não medimos outras langs por ora

    if test_blocks == 0:
        return False, ""

    trivial = 0
    for pat in patterns:
        trivial += len(re.findall(pat, content))
    real_asserts_real = max(0, real_asserts - trivial)

    if trivial > 0 and real_asserts_real == 0:
        return True, (
            f"{test_blocks} bloco(s) de teste, {trivial} asserção(ões) trivial(is) "
            f"(toBeDefined/toEqual([])/...) e nenhuma asserção real"
        )
    return False, ""
