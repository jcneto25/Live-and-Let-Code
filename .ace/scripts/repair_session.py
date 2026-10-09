#!/usr/bin/env python3
"""Reparação histórica explícita de uma única sessão ACE autorizada."""

from dataclasses import dataclass
from pathlib import Path
import re

ALLOWED_TARGET = "2026-10-09-006"
FILES_TOUCHED_TARGETS = {"2026-10-09-004", "2026-10-09-005"}


class RepairRefused(RuntimeError):
    """A reparação não atende às pré-condições de segurança."""


@dataclass(frozen=True)
class RepairResult:
    changed: bool
    backup: Path


def _seed_from_source(source: Path) -> str:
    content = source.read_text(encoding="utf-8")
    matches = re.findall(
        r"^[ \t]*<context_seed>[ \t]*$\n(.*?)^[ \t]*</context_seed>[ \t]*$",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not matches:
        raise RepairRefused("seed estrutural não encontrado na sessão-fonte")
    return matches[-1].strip()


def repair_session(target: Path, source: Path, session_id: str) -> RepairResult:
    if session_id != ALLOWED_TARGET:
        raise RepairRefused(f"somente {ALLOWED_TARGET} pode ser reparada")
    if target.name != f"{ALLOWED_TARGET}.md":
        raise RepairRefused("arquivo-alvo não corresponde ao ID autorizado")
    if not target.exists() or not source.exists():
        raise RepairRefused("arquivo-alvo ou fonte não existe")

    content = target.read_text(encoding="utf-8")
    if "\\s*<\\/context_seed>" not in content:
        return RepairResult(False, target.with_suffix(target.suffix + ".bak"))

    seed = _seed_from_source(source)
    repaired, count = re.subn(
        r"(?ms)^(\*\*Sessão anterior:\*\*.*?\n\n)<context_seed>.*?</learning_point>",
        rf"\1<context_seed>\n{seed}\n</context_seed>",
        content,
        count=1,
    )
    if count != 1 or repaired == content:
        raise RepairRefused("padrão corrompido não correspondeu exatamente uma vez")

    backup = target.with_suffix(target.suffix + ".bak")
    if backup.exists():
        raise RepairRefused(f"backup já existe: {backup}")
    backup.write_text(content, encoding="utf-8")
    target.write_text(repaired, encoding="utf-8")
    return RepairResult(True, backup)


def repair_files_touched(target: Path, session_id: str) -> RepairResult:
    """Preenche o trailer somente nas duas sessões históricas autorizadas."""
    if session_id not in FILES_TOUCHED_TARGETS:
        raise RepairRefused(f"files_touched não autorizado para {session_id}")
    if target.name != f"{session_id}.md" or not target.exists():
        raise RepairRefused("arquivo-alvo inválido ou inexistente")

    content = target.read_text(encoding="utf-8")
    if not re.search(r"(?m)^files_touched:\s*\[\]\s*$", content):
        return RepairResult(False, target.with_suffix(target.suffix + ".bak"))

    clean = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    files = []
    for raw in re.findall(r"<file_delta>(.*?)</file_delta>", clean, flags=re.DOTALL):
        path = raw.strip()
        if path and path not in files:
            files.append(path)
    if not files:
        raise RepairRefused("nenhum file_delta confiável encontrado")

    value = "[" + ", ".join(files) + "]"
    repaired, count = re.subn(
        r"(?m)^(files_touched:\s*)\[\]\s*$",
        rf"\g<1>{value}",
        content,
        count=1,
    )
    if count != 1:
        raise RepairRefused("trailer files_touched não correspondeu exatamente uma vez")

    backup = target.with_suffix(target.suffix + ".bak")
    if backup.exists():
        raise RepairRefused(f"backup já existe: {backup}")
    backup.write_text(content, encoding="utf-8")
    target.write_text(repaired, encoding="utf-8")
    return RepairResult(True, backup)
