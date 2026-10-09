"""llc_trace.hashing — hashes canonicos e estaveis para Decision Records.

Fase 0 (LLC 2.0): tudo que entra num Decision Record precisa ser comparavel
entre execucoes. Isso exige uma serializacao *canonica* (chaves ordenadas,
sem espacos, sem dependencia de ordem de insercao) antes do sha256.

Regras:
  - `canonical_json` nunca levanta (default=str para objetos exoticos);
  - strings e bytes tem caminho proprio (nao passam por JSON);
  - todo retorno e prefixado ("sha256:...") para que o algoritmo seja
    explicito no proprio dado — trocar de algoritmo nao invalida silently
    registros antigos.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ALGORITHM = "sha256"
PREFIX = f"{ALGORITHM}:"


def canonical_json(obj: Any) -> str:
    """Serializacao canonica: sort_keys + separadores minimos + default=str."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def sha256_hex(data: str | bytes) -> str:
    """sha256 de str (utf-8) ou bytes. Retorna hex sem prefixo."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def input_hash(payload: Any) -> str:
    """Hash canonico de um payload arbitrario (dict/list/str/bytes/escalar).

    `str` e `bytes` tem caminho direto (evita custo e ambiguidade de JSON).
    Demais tipos passam por `canonical_json`.
    """
    if isinstance(payload, (str, bytes)):
        return f"{PREFIX}{sha256_hex(payload)}"
    return f"{PREFIX}{sha256_hex(canonical_json(payload))}"


def hash_file(path: str | Path) -> str | None:
    """Hash do conteudo de um arquivo. None se inexistente/ilegivel.

    Usado para evidencia (ex.: gates.json) — nunca levanta.
    """
    try:
        data = Path(path).read_bytes()
    except (OSError, ValueError):
        return None
    return f"{PREFIX}{sha256_hex(data)}"
