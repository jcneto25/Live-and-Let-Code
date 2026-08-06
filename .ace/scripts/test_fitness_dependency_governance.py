#!/usr/bin/env python3
"""PRP-GOV-T3 / ADR-0006 §5.1: fitness function dependency-governance.

5 verificações: import não registrado (block) · versão não pinada (block) ·
licença ausente (block) · revisão expirada (warn) · N2/N3 no caminho crítico
de .ace/scripts/ (block). Escopo de varredura: .ace/scripts/**/*.py exceto
test_*.py e __pycache__ (governança de código de produção).
"""
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from fitness_functions.checks_governance import _check_dependency_governance


def _mk_repo(tmp_path: Path, deps: list, imports: dict | None = None,
             review_days: int = 90) -> Path:
    """Fixture: .ace/config/dependencies.yaml + .ace/scripts/*.py com imports."""
    cfg = tmp_path / ".ace" / "config"
    cfg.mkdir(parents=True)
    (cfg / "dependencies.yaml").write_text(
        yaml.safe_dump({"version": 1, "review_interval_days": review_days,
                        "dependencies": deps}), encoding="utf-8")
    scripts = tmp_path / ".ace" / "scripts"
    scripts.mkdir(parents=True)
    for fname, content in (imports or {}).items():
        (scripts / fname).write_text(content, encoding="utf-8")
    return tmp_path


DEP = {"name": "goodlib", "version": ">=1.0,<2.0", "level": 1, "license": "MIT",
       "bus_factor": "community", "purpose": "x", "critical_path": False,
       "fallback": "y", "last_reviewed": str(date.today())}


class TestUnregisteredImport:
    def test_block(self, tmp_path):
        root = _mk_repo(tmp_path, [], {"mod_x.py": "import unregistered_lib\n"})
        r = _check_dependency_governance(root)
        assert any(v["severity"] == "block" and "unregistered_lib" in v["detail"]
                   for v in r["violations"])
        assert r["blocked"]

    def test_registered_passes(self, tmp_path):
        root = _mk_repo(tmp_path, [DEP], {"mod_x.py": "import goodlib\n"})
        r = _check_dependency_governance(root)
        assert r["violations"] == []
        assert r["passed"]

    def test_yaml_alias_maps_to_pyyaml(self, tmp_path):
        pyyaml = {**DEP, "name": "pyyaml"}
        root = _mk_repo(tmp_path, [pyyaml], {"mod_x.py": "import yaml\n"})
        assert _check_dependency_governance(root)["passed"]

    def test_stdlib_ignored(self, tmp_path):
        root = _mk_repo(tmp_path, [],
                        {"mod_x.py": "import json, sys\nfrom pathlib import Path\n"})
        assert _check_dependency_governance(root)["passed"]

    def test_first_party_ignored(self, tmp_path):
        root = _mk_repo(tmp_path, [],
                        {"llc_fake.py": "x = 1\n", "mod_x.py": "import llc_fake\n"})
        assert _check_dependency_governance(root)["passed"]

    def test_test_files_out_of_scope(self, tmp_path):
        root = _mk_repo(tmp_path, [], {"test_x.py": "import anything_unregistered\n"})
        assert _check_dependency_governance(root)["passed"]


class TestPinning:
    def test_latest_block(self, tmp_path):
        bad = {**DEP, "version": "latest"}
        root = _mk_repo(tmp_path, [bad])
        r = _check_dependency_governance(root)
        assert any("pinada" in v["detail"] and v["severity"] == "block"
                   for v in r["violations"])

    def test_missing_version_block(self, tmp_path):
        bad = {k: v for k, v in DEP.items() if k != "version"}
        root = _mk_repo(tmp_path, [bad])
        assert any(v["severity"] == "block"
                   for v in _check_dependency_governance(root)["violations"])


class TestLicense:
    def test_missing_license_block(self, tmp_path):
        bad = {**DEP, "license": ""}
        root = _mk_repo(tmp_path, [bad])
        r = _check_dependency_governance(root)
        assert any("licença" in v["detail"] for v in r["violations"])


class TestReview:
    def test_expired_warn_not_block(self, tmp_path):
        old = {**DEP, "last_reviewed": str(date.today() - timedelta(days=120))}
        root = _mk_repo(tmp_path, [old])
        r = _check_dependency_governance(root)
        assert any("revisão expirada" in v["detail"] and v["severity"] == "warn"
                   for v in r["violations"])
        assert not r["blocked"]

    def test_fresh_passes(self, tmp_path):
        root = _mk_repo(tmp_path, [DEP])
        assert _check_dependency_governance(root)["passed"]


class TestCriticalPath:
    def test_n2_imported_block(self, tmp_path):
        n2 = {**DEP, "name": "herdr", "level": 2}
        root = _mk_repo(tmp_path, [n2], {"mod_x.py": "import herdr\n"})
        r = _check_dependency_governance(root)
        assert any("N2" in v["detail"] and v["severity"] == "block"
                   for v in r["violations"])

    def test_n2_registered_not_imported_passes(self, tmp_path):
        n2 = {**DEP, "name": "herdr", "level": 2}
        root = _mk_repo(tmp_path, [n2])
        assert _check_dependency_governance(root)["passed"]


class TestMissingYaml:
    def test_no_yaml_block(self, tmp_path):
        (tmp_path / ".ace" / "scripts").mkdir(parents=True)
        r = _check_dependency_governance(tmp_path)
        assert r["blocked"]


class TestRealRepo:
    def test_current_repo_not_blocked(self):
        """Integração: o repositório atual (pós GOV-T1/T2) não pode ter
        nenhuma violação block — é o critério de saída da Trilha 0."""
        r = _check_dependency_governance(Path("."))
        assert not r["blocked"], f"Violações block no repo real: {r['violations']}"
