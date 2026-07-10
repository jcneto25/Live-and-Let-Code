#!/usr/bin/env python3
"""Checkers de aceite de PRP (RFs, testes, componentes, endpoints)."""

import re
from pathlib import Path

from .constants import CRITICAL, WARN
from .consistency import read_config
from .models import Finding
from .paths import _is_excluded, resolve_path
from .stubs import is_stub_by_pattern, is_stub_test_file


def _looks_like_test(path: str) -> bool:
    name = Path(path).name.lower()
    return (
        ".spec." in name
        or ".test." in name
        or name.startswith("test_")
        or "_test." in name
    )


def check_rf_evidence(rows, has_trace, section9_files, result):
    """CRITICAL se arquivo declarado ausente/stub; WARN se RF sem evidência ou teste fora do §9."""
    if not rows:
        return
    if not has_trace:
        for r in rows:
            result.findings.append(
                Finding(
                    WARN,
                    "rf_legacy_no_traceability",
                    f"{r['id']}: PRP legado sem colunas de rastreabilidade (Teste(s)/Arquivo(s) impl) "
                    f"— verifique manualmente a implementação",
                    rf=r["id"],
                )
            )
        return

    section9_set = set(section9_files)
    for r in rows:
        declared = r["testes"] + r["impl"]
        if not declared:
            result.findings.append(
                Finding(
                    WARN,
                    "rf_no_evidence",
                    f"{r['id']}: sem arquivos de teste/impl declarados — não verificável mecanicamente",
                    rf=r["id"],
                )
            )
            continue
        for decl in declared:
            resolved = resolve_path(decl)
            if resolved is None:
                result.findings.append(
                    Finding(
                        CRITICAL,
                        "rf_file_missing",
                        f"{r['id']}: arquivo declarado ausente: {decl}",
                        rf=r["id"],
                        file=decl,
                    )
                )
            else:
                # stub de impl (não de teste) ⇒ CRITICAL (padrão positivo apenas)
                if not _looks_like_test(decl) and is_stub_by_pattern(
                    str(resolved), read_config()
                ):
                    result.findings.append(
                        Finding(
                            CRITICAL,
                            "rf_file_stub",
                            f"{r['id']}: arquivo declarado é stub: {decl}",
                            rf=r["id"],
                            file=decl,
                        )
                    )
        for tp in r["testes"]:
            if tp not in section9_set and resolve_path(tp):
                result.findings.append(
                    Finding(
                        WARN,
                        "rf_test_not_in_section9",
                        f"{r['id']}: teste {tp} não está listado na §9 do PRP",
                        rf=r["id"],
                        file=tp,
                    )
                )


def check_tests(section9_files, result):
    """CRITICAL se arquivo de teste declarado ausente; WARN se for stub-test."""
    for decl in section9_files:
        resolved = resolve_path(decl)
        if resolved is None:
            result.findings.append(
                Finding(
                    CRITICAL,
                    "test_file_missing",
                    f"arquivo de teste da §9 ausente: {decl}",
                    file=decl,
                )
            )
            continue
        is_stub, reason = is_stub_test_file(resolved)
        if is_stub:
            result.findings.append(
                Finding(
                    WARN,
                    "stub_test",
                    f"possível teatro de testes em {decl}: {reason}",
                    file=decl,
                )
            )


def check_components(comps, result):
    """CRITICAL se Localização ausente ou teste de estado ausente."""
    for path, state_tests in comps:
        resolved = resolve_path(path)
        if resolved is None:
            result.findings.append(
                Finding(
                    CRITICAL,
                    "component_missing",
                    f"componente declarado (Localização) ausente: {path}",
                    file=path,
                )
            )
        for st in state_tests:
            if resolve_path(st) is None:
                result.findings.append(
                    Finding(
                        CRITICAL,
                        "component_state_test_missing",
                        f"teste de estado do componente ausente: {st} (Localização: {path})",
                        file=st,
                    )
                )


def check_endpoints(endpoints, result):
    """WARN-only até calibração per-stack: procura a rota no código sob apps/src."""
    if not endpoints:
        return
    haystack = _collect_code_text()
    if not haystack:
        return  # sem código para cruzar — não emite WARN falso
    for method, route in endpoints:
        if _route_found(route, haystack):
            continue
        result.findings.append(
            Finding(
                WARN,
                "endpoint_not_found",
                f"endpoint declarado não localizado no código (pré-calibração): "
                f"{method} {route}",
            )
        )


def _collect_code_text() -> str:
    """Concatena código-fonte sob apps/src/packages para busca de rotas (bounded)."""
    chunks = []
    for root in ("apps", "src", "packages"):
        base = Path(root)
        if not base.exists():
            continue
        for hit in base.rglob("*"):
            if not hit.is_file() or _is_excluded(hit):
                continue
            if hit.suffix not in (".ts", ".tsx", ".js", ".jsx", ".py", ".go"):
                continue
            try:
                chunks.append(hit.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if sum(len(c) for c in chunks) > 2_000_000:  # teto de 2 MB
                break
    return "\n".join(chunks)


def _route_found(route: str, haystack: str) -> bool:
    """Normaliza parâmetros de rota e procura o prefixo no código."""
    norm = re.sub(r":\w+|{\w+}|\[\w+\]", "", route).rstrip("/")
    if not norm:
        return True
    # procura o path (ou sufixo dele) como literal
    return norm in haystack
