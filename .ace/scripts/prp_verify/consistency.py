#!/usr/bin/env python3
"""Ponte com consistency-check.py (nome com hífen → importlib).

Expose detect_language / is_stub_file / STUB_PATTERNS / read_config, com
fallbacks seguros se o módulo não estiver presente.
"""

import importlib.util
from pathlib import Path


def _load_consistency_check():
    # __file__ está em prp_verify/; consistency-check.py vive no dir de scripts (parent.parent).
    cc_path = Path(__file__).resolve().parent.parent / "consistency-check.py"
    if not cc_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("consistency_check", cc_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CC = _load_consistency_check()
detect_language = _CC.detect_language if _CC else (lambda p: "any")
is_stub_file = _CC.is_stub_file if _CC else (lambda p, c: False)
STUB_PATTERNS = _CC.STUB_PATTERNS if _CC else {}
read_config = (
    _CC.read_config
    if _CC
    else (lambda: {"prp_services": {}, "skip_task_patterns": [], "stub_patterns": {}})
)
