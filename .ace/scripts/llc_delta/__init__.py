#!/usr/bin/env python3
"""llc_delta — suporte ao fluxo delta (mudancas em sistema existente).

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - paths:    constantes de caminho (DELTA_REPORT.md, skip-notes)
  - report:   leitura/parsing do DELTA_REPORT.md
  - skip:     ALWAYS_RUN + smart-skip (E-12) e geracao de skip notes
  - plan:     integracao com o pipeline (steps a executar no modo delta)

Este __init__ re-exporta a API completa para manter
`import llc_delta` e `from llc_delta import ...` funcionando para llc.py,
llc_harness/pipeline.py e os testes.
"""

from .paths import DELTA_REPORT_PATH, SKIP_NOTES_DIR
from .report import delta_report_exists, parse_delta_report
from .skip import (
    ALWAYS_RUN,
    _canonical_step_id,
    generate_skip_note,
    get_skip_reason,
    is_step_skipped,
)
from .plan import get_delta_steps

__all__ = [
    "DELTA_REPORT_PATH",
    "SKIP_NOTES_DIR",
    "delta_report_exists",
    "parse_delta_report",
    "ALWAYS_RUN",
    "_canonical_step_id",
    "is_step_skipped",
    "get_skip_reason",
    "generate_skip_note",
    "get_delta_steps",
]
