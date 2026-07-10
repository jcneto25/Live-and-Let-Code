#!/usr/bin/env python3
"""Cobertura de teste em nível de projeto (P0)."""

import json
import subprocess
from pathlib import Path

DEFAULT_COVERAGE_THRESHOLDS = {
    "statements": 80,
    "branches": 70,
    "functions": 80,
    "lines": 80,
}

# Stack markers → (marker file, coverage tool prefix). Detectado antes de
# tentar gerar cobertura para evitar desperdício de timeout em stack errado.
_JS_MARKERS = ("package.json",)
_PY_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "tox.ini")
_GO_MARKERS = ("go.mod",)


def _detect_stack(cwd: Path) -> str:
    """Detecta o stack do projeto pela presença de marker files (F-13).
    Retorna 'js', 'python', 'go' ou 'unknown'."""
    for marker in _JS_MARKERS:
        if (cwd / marker).exists():
            return "js"
    for marker in _PY_MARKERS:
        if (cwd / marker).exists():
            return "python"
    for marker in _GO_MARKERS:
        if (cwd / marker).exists():
            return "go"
    return "unknown"


def check_project_coverage(
    thresholds: dict = None, strict: bool = False
) -> tuple[int, list]:
    """Verifica cobertura de teste em nível de projeto.

    Retorna (exit_code, findings_list).
    - exit_code: 0 = OK, 1 = WARN (cobertura abaixo do threshold), 2 = CRITICAL (arquivos sem teste)
    - findings: lista de dicionários com detalhes
    """
    if thresholds is None:
        thresholds = DEFAULT_COVERAGE_THRESHOLDS

    findings = []
    exit_code = 0

    # Tenta executar cobertura — só para stacks JS (vitest/jest via npx).
    # Projetos Python/Go/unknown pulam direto para WARN (F-13: evitar
    # desperdício de timeout 120s×2 em `npx` para stacks não-JS).
    coverage_file = Path("coverage/coverage-final.json")
    if not coverage_file.exists():
        stack = _detect_stack(Path.cwd())
        if stack == "js":
            try:
                result = subprocess.run(
                    [
                        "npx",
                        "vitest",
                        "run",
                        "--coverage",
                        "--reporter=json",
                        "--outputFile=coverage/coverage-final.json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    # Tenta com jest
                    result = subprocess.run(
                        [
                            "npx",
                            "jest",
                            "--coverage",
                            "--coverageReporters=json",
                            "--outputFile=coverage/coverage-final.json",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    if not coverage_file.exists():
        findings.append(
            {
                "severity": "WARN",
                "code": "coverage_not_generated",
                "message": "Relatório de cobertura não encontrado. Execute testes com --coverage primeiro.",
                "file": "coverage/coverage-final.json",
            }
        )
        return (1 if strict else 0, findings)

    try:
        data = json.loads(coverage_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        findings.append(
            {
                "severity": "WARN",
                "code": "coverage_parse_error",
                "message": f"Erro ao ler relatório de cobertura: {e}",
                "file": str(coverage_file),
            }
        )
        return (1 if strict else 0, findings)

    # Analisa cobertura por arquivo
    uncovered_files = []
    low_coverage_files = []
    total_statements = 0
    covered_statements = 0

    for file_path, file_data in data.items():
        # Ignora arquivos de teste e node_modules
        if any(
            part in file_path
            for part in [
                "node_modules",
                ".test.",
                ".spec.",
                "_test.",
                "__tests__",
                "__mocks__",
            ]
        ):
            continue

        # Ignora arquivos de configuração e tipos
        if file_path.endswith((".d.ts", ".config.ts", ".config.js", ".json", ".md")):
            continue

        stmt = file_data.get("s", {})
        if not stmt:
            continue

        file_total = len(stmt)
        file_covered = sum(1 for v in stmt.values() if v > 0)
        file_pct = (file_covered / file_total * 100) if file_total > 0 else 100

        total_statements += file_total
        covered_statements += file_covered

        # Arquivo com 0% de cobertura = sem testes
        if file_covered == 0 and file_total > 0:
            uncovered_files.append(file_path)
        # Arquivo com cobertura baixa
        elif file_pct < thresholds.get("statements", 80):
            low_coverage_files.append((file_path, file_pct))

    # Cobertura global
    global_pct = (
        (covered_statements / total_statements * 100) if total_statements > 0 else 100
    )

    # CRITICAL: arquivos de implementação sem NENHUM teste
    if uncovered_files:
        for f in uncovered_files:
            findings.append(
                {
                    "severity": "CRITICAL",
                    "code": "file_uncovered",
                    "message": f"Arquivo de implementação sem cobertura: {f}",
                    "file": f,
                }
            )
        exit_code = 2

    # WARN: arquivos com cobertura baixa
    for f, pct in low_coverage_files:
        findings.append(
            {
                "severity": "WARN",
                "code": "file_low_coverage",
                "message": f"Arquivo com cobertura baixa ({pct:.1f}%): {f}",
                "file": f,
            }
        )
    if low_coverage_files and exit_code < 1:
        exit_code = 1

    # WARN: cobertura global abaixo do threshold
    if global_pct < thresholds.get("statements", 80):
        findings.append(
            {
                "severity": "WARN",
                "code": "global_coverage_low",
                "message": f"Cobertura global de statements: {global_pct:.1f}% (threshold: {thresholds.get('statements', 80)}%)",
                "file": "global",
            }
        )
        if exit_code < 1:
            exit_code = 1

    findings.append(
        {
            "severity": "OK" if exit_code == 0 else "INFO",
            "code": "coverage_summary",
            "message": f"Cobertura global: {global_pct:.1f}% ({covered_statements}/{total_statements} statements), {len(uncovered_files)} arquivos sem teste, {len(low_coverage_files)} com cobertura baixa",
            "file": "global",
        }
    )

    return (exit_code, findings)
