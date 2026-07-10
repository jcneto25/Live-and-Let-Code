#!/usr/bin/env python3
"""Shared constants and gate-config loader for the llc_harness package."""

import json
from pathlib import Path

# common.py vive em .ace/scripts/llc_harness/common.py — 2 .parent para chegar
# em .ace/scripts/, depois 1 .parent para chegar em .ace/.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
ACE_DIR = SCRIPTS_DIR.parent
CONFIG_DIR = ACE_DIR / "config"
SKILLS_DIR = Path("docs/skills")
AGENTS_FILE = Path("AGENTS.md")
GATES_FILE = CONFIG_DIR / "gates.json"

_gates_config = None


def load_gates_config() -> dict:
    """Carrega gates.json sob demanda (cacheado em memória)."""
    global _gates_config
    if _gates_config is None:
        if GATES_FILE.exists():
            _gates_config = json.loads(GATES_FILE.read_text(encoding="utf-8"))
        else:
            _gates_config = {"gates": {}, "step_to_gate": {}}
    return _gates_config
