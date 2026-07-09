#!/usr/bin/env python3
"""llc_wave — Wave execution orchestrator for the Live and Let Code pipeline.

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - models:  WaveInfo, PrpInfo
  - parsing: parsers de EXECUTION_WAVES.md / TASKS.md + format_wave_list
  - checks:  validação pré/pós-onda (build, contratos, aceite de PRP)
  - run:     run_wave (orquestração de execução)

Este __init__ re-exporta a API completa para manter `from llc_wave import ...`
e `import llc_wave; llc_wave.<nome>` funcionando para llc.py, testes e os
Proof commands do BEHAVIOR_BASELINE.
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from .checks import (
    PRE_WAVE_CHECK_SCRIPT,
    UI_KEYWORDS,
    _is_ui_prp,
    _load_stub_detector,
    _post_wave_check,
    _post_wave_build_health,
    _post_wave_consistency,
    _post_wave_prp_acceptance,
    _pre_wave_check,
    _prp_to_keywords,
    _run_bash_script,
    _verify_backend_contracts,
)
from .models import PrpInfo, WaveInfo
from .parsing import (
    EXECUTION_WAVES_FILE,
    TASKS_FILE,
    _find_prp_headings,
    _find_tasks_in_section,
    _find_wave_headings,
    _strip_placeholders,
    format_wave_list,
    parse_execution_waves,
    parse_tasks,
)
from .run import run_wave

__all__ = [
    "PrpInfo",
    "WaveInfo",
    "Path",
    "EXECUTION_WAVES_FILE",
    "TASKS_FILE",
    "PRE_WAVE_CHECK_SCRIPT",
    "UI_KEYWORDS",
    "_is_ui_prp",
    "_load_stub_detector",
    "_post_wave_check",
    "_post_wave_build_health",
    "_post_wave_consistency",
    "_post_wave_prp_acceptance",
    "_pre_wave_check",
    "_prp_to_keywords",
    "_run_bash_script",
    "_verify_backend_contracts",
    "_find_prp_headings",
    "_find_tasks_in_section",
    "_find_wave_headings",
    "_strip_placeholders",
    "format_wave_list",
    "parse_execution_waves",
    "parse_tasks",
    "run_wave",
]
