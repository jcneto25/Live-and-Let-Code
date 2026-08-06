#!/usr/bin/env python3
"""Checks de governança de dependências externas (ADR-0006 §5.1 / PRP-GOV-T3).

Cinco verificações sobre .ace/config/dependencies.yaml × imports reais:
1. Todo import de terceiro em .ace/scripts/ está registrado (block)
2. Toda dependência tem versão pinada — nunca latest (block)
3. Toda dependência tem licença registrada (block)
4. Nenhuma dependência com revisão expirada (warn — ADR-0006 §2.7)
5. Nenhuma dependência N2/N3 importada no caminho crítico .ace/scripts/ (block)

Escopo da varredura: .ace/scripts/**/*.py exceto test_*.py e __pycache__
(governança de código de produção; testes usam pytest — registrado como dev).
"""

import ast
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

DEPENDENCIES_YAML = Path(".ace/config/dependencies.yaml")
SCRIPTS_DIR = Path(".ace/scripts")

# import raiz -> nome do pacote registrado
_IMPORT_ALIAS = {"yaml": "pyyaml"}

_DEFAULT_REVIEW_DAYS = 90


def _third_party_imports(scripts_dir: Path) -> set:
    """Imports não-stdlib e não-first-party em scripts_dir (exceto test_*.py)."""
    stdlib = set(sys.stdlib_module_names)
    first_party = set()
    if scripts_dir.exists():
        first_party = {
            p.name for p in scripts_dir.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()
        }
        first_party |= {p.stem for p in scripts_dir.glob("*.py")}

    found = set()
    for f in sorted(scripts_dir.rglob("*.py")):
        if "__pycache__" in f.parts or f.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [n.name for n in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            else:
                names = []
            for name in names:
                root = name.split(".")[0]
                if root and root not in stdlib and root not in first_party:
                    found.add(root)
    return found


def _result(violations: list) -> dict:
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "dependency_governance",
        "label": "Dependency Governance (ADR-0006)",
        "description": (
            "Dependências registradas, pinadas, licenciadas, revisadas "
            "e fora do caminho crítico"
        ),
        "passed": len(violations) == 0,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


def _violation(yaml_path: Path, severity: str, detail: str, fix: str) -> dict:
    return {
        "file": str(yaml_path),
        "module": "governance",
        "severity": severity,
        "detail": detail,
        "fix": fix,
    }


def _check_dependency_governance(root: Path, today: date | None = None) -> dict:
    """Núcleo testável — avalia root (repo real ou fixture tmp_path)."""
    today = today or date.today()
    yaml_path = root / DEPENDENCIES_YAML
    scripts_dir = root / ".ace" / "scripts"

    if not yaml_path.exists():
        return _result([
            _violation(yaml_path, "block",
                       "dependencies.yaml não encontrado",
                       "Criar .ace/config/dependencies.yaml (PRP-GOV-T1)")
        ])

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    deps = data.get("dependencies") or []
    registered = {d.get("name"): d for d in deps if isinstance(d, dict)}
    review_days = int(data.get("review_interval_days", _DEFAULT_REVIEW_DAYS))

    violations = []
    imports = sorted(_third_party_imports(scripts_dir))

    # V1 — todo import de terceiro registrado
    for imp in imports:
        pkg = _IMPORT_ALIAS.get(imp, imp)
        if pkg not in registered:
            violations.append(_violation(
                yaml_path, "block",
                f"Import '{imp}' em .ace/scripts/ não registrado em dependencies.yaml",
                "Registrar conforme ADR-0006 §2.3 (checklist de admissão) ou remover o import"))

    # V2/V3/V4 — por entrada registrada
    for name, dep in registered.items():
        version = str(dep.get("version", "")).strip()
        if not version or version.lower() == "latest":
            violations.append(_violation(
                yaml_path, "block",
                f"'{name}' sem versão pinada ('{version or 'ausente'}')",
                "Pinar versão testada — nunca latest (ADR-0006 D5)"))

        if not dep.get("license"):
            violations.append(_violation(
                yaml_path, "block",
                f"'{name}' sem licença registrada",
                "Verificar licença na fonte oficial e registrar (ADR-0006 D2/D3)"))

        last = dep.get("last_reviewed")
        try:
            last_date = date.fromisoformat(str(last))
            if last_date + timedelta(days=review_days) < today:
                violations.append(_violation(
                    yaml_path, "warn",
                    f"'{name}' com revisão expirada ({last_date} + {review_days}d)",
                    "Revisar licença/versão/bus factor e atualizar last_reviewed (ADR-0006 §2.7)"))
        except (TypeError, ValueError):
            violations.append(_violation(
                yaml_path, "warn",
                f"'{name}' sem last_reviewed válido ('{last}')",
                "Preencher last_reviewed no formato ISO (YYYY-MM-DD)"))

    # V5 — N2/N3 não pode ser importado no caminho crítico (.ace/scripts/)
    for imp in imports:
        pkg = _IMPORT_ALIAS.get(imp, imp)
        dep = registered.get(pkg)
        if dep is None:
            continue
        try:
            level = int(dep.get("level", 1) or 1)
        except (TypeError, ValueError):
            level = 1
        if level >= 2:
            violations.append(_violation(
                yaml_path, "block",
                f"'{imp}' é N{level} (ferramenta externa) mas é importado em "
                f".ace/scripts/ (caminho crítico)",
                "N2/N3 só em skills/UI com feature detection + fallback (ADR-0006 D10)"))

    return _result(violations)


def check_dependency_governance(config: dict, verbose: bool = False) -> dict:
    """Wrapper registrado no runner — avalia o repositório atual."""
    return _check_dependency_governance(Path("."))
