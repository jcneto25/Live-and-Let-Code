"""conftest para testes do llc_wizard.

Segue o padrão de .ace/scripts/test_llc_wave.py: expõe .ace/scripts no sys.path
para que os testes importem o pacote llc_wizard.
"""
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    ace = tmp_path / ".ace"
    (ace / "config").mkdir(parents=True)
    (ace / "sessions").mkdir(parents=True)
    make_index = ace / "index.json"
    make_index.write_text('{"sessions": []}', encoding="utf-8")
    (ace / "config" / "gates.json").write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.fixture
def make_index():
    def _make(root: Path, sessions: list[dict]):
        import json

        (root / ".ace" / "index.json").write_text(
            json.dumps({"sessions": sessions}), encoding="utf-8"
        )

    return _make


@pytest.fixture
def make_gates():
    def _make(root: Path, gates: dict):
        import json

        (root / ".ace" / "config" / "gates.json").write_text(
            json.dumps(gates), encoding="utf-8"
        )

    return _make