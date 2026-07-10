#!/usr/bin/env python3
"""code_health — análise de saúde estrutural do código via git history.

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - gitlog:     run_git_log, classify_changes, analyze_file_age
  - coverage:   parsing de relatórios + tendências de cobertura
  - thresholds: check_thresholds (gera alertas)
  - cli:        entrypoint de linha de comando

Este __init__ re-exporta a API completa para manter o runner
`code-health.py` (subprocess) funcionando.
"""

from .gitlog import (
    SCRIPTS_DIR,
    analyze_file_age,
    classify_changes,
    run_git_log,
)
from .coverage import (
    check_coverage_thresholds,
    check_coverage_trends,
    load_coverage_history,
    parse_coverage_report,
    save_coverage_history,
)
from .thresholds import check_thresholds
from .cli import main

__all__ = [
    "SCRIPTS_DIR",
    "analyze_file_age",
    "classify_changes",
    "run_git_log",
    "check_coverage_thresholds",
    "check_coverage_trends",
    "load_coverage_history",
    "parse_coverage_report",
    "save_coverage_history",
    "check_thresholds",
    "main",
]
