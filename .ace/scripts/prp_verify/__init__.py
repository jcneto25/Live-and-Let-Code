#!/usr/bin/env python3
"""prp_verify — verificação mecânica de aceite de PRP (Step 11.2 do LLC).

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - constants:    caminhos/raízes e severidades (CRITICAL/WARN)
  - models:       dataclasses Finding / VerifyResult
  - consistency:  ponte com consistency-check.py (detect_language, is_stub_file, ...)
  - stubs:        detecção de stub de impl e de teatro de testes
  - coverage:     checagem de cobertura em nível de projeto (P0)
  - paths:        resolução de caminhos declarados no PRP
  - parsing:      extração de seções/tabelas e parsers por § (RF/endpoint/componente/teste)
  - checks:       checkers de aceite (RF/impl/teste/componente/endpoint)
  - verify:       orquestração por PRP + discover/resolve
  - cli:          entrypoint de linha de comando

Este __init__ re-exporta a API completa para manter importações e o
runner `prp_verify.py` (subprocess) funcionando.
"""

from .constants import (
    ARCHITECTURE_FILE,
    CRITICAL,
    EXCLUDE_PARTS,
    PRP_DIR,
    SEARCH_ROOTS,
    WARN,
)
from .models import Finding, VerifyResult
from .consistency import (
    STUB_PATTERNS,
    detect_language,
    is_stub_file,
    read_config,
)
from .stubs import (
    STUB_TEST_PATTERNS,
    is_stub_by_pattern,
    is_stub_test_file,
)
from .coverage import DEFAULT_COVERAGE_THRESHOLDS, check_project_coverage
from .paths import _is_excluded, resolve_path
from .parsing import (
    ENDPOINT_RE,
    LOCALIZACAO_RE,
    RF_ID_RE,
    _all_tables,
    _first_table,
    _get_section,
    _split_paths,
    parse_components,
    parse_endpoints,
    parse_rf_table,
    parse_test_files,
)
from .checks import (
    _collect_code_text,
    _looks_like_test,
    _route_found,
    check_components,
    check_endpoints,
    check_rf_evidence,
    check_tests,
)
from .verify import discover_prps, resolve_prp_path, verify_prp
from .cli import main

__all__ = [
    "ARCHITECTURE_FILE",
    "CRITICAL",
    "EXCLUDE_PARTS",
    "PRP_DIR",
    "SEARCH_ROOTS",
    "WARN",
    "Finding",
    "VerifyResult",
    "STUB_PATTERNS",
    "detect_language",
    "is_stub_file",
    "read_config",
    "STUB_TEST_PATTERNS",
    "is_stub_by_pattern",
    "is_stub_test_file",
    "DEFAULT_COVERAGE_THRESHOLDS",
    "check_project_coverage",
    "_is_excluded",
    "resolve_path",
    "ENDPOINT_RE",
    "LOCALIZACAO_RE",
    "RF_ID_RE",
    "_all_tables",
    "_first_table",
    "_get_section",
    "_split_paths",
    "parse_components",
    "parse_endpoints",
    "parse_rf_table",
    "parse_test_files",
    "_collect_code_text",
    "_looks_like_test",
    "_route_found",
    "check_components",
    "check_endpoints",
    "check_rf_evidence",
    "check_tests",
    "discover_prps",
    "resolve_prp_path",
    "verify_prp",
    "main",
]
