#!/usr/bin/env python3
"""
Fitness Functions para verificação arquitetural automatizada.

Baseado em Ingeno (Software Architect's Handbook, ch16) — verifica
características arquiteturais de forma automatizada e reproduzível.

Uso:
    python .ace/scripts/fitness-functions.py --all
    python .ace/scripts/fitness-functions.py --check-deps
    python .ace/scripts/fitness-functions.py --check-circular
    python .ace/scripts/fitness-functions.py --all --json
    python .ace/scripts/fitness-functions.py --all --strict  # exit 1 se violação
    python .ace/scripts/fitness-functions.py --all --verbose

    # Clean Code Checks
    python .ace/scripts/fitness-functions.py --check-functions
    python .ace/scripts/fitness-functions.py --check-naming
    python .ace/scripts/fitness-functions.py --check-classes
    python .ace/scripts/fitness-functions.py --check-errors
    python .ace/scripts/fitness-functions.py --check-smells
    python .ace/scripts/fitness-functions.py --check-readmodels
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ARCH_CONFIG_PATH = Path(".ace/arch-config.yaml")
DEFAULT_ARCH_CONFIG = {
    "version": "1.0",
    "core_modules": [],
    "checks": {
        "dependency_rule": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "circular_deps": {
            "enabled": True,
            "mode": "block",
        },
        "interface_coverage": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "threshold": 100,
        },
        "domain_isolation": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "use_case_size": {
            "enabled": True,
            "mode": "warn",
            "max_methods": 8,
        },
        "module_coverage": {
            "enabled": True,
            "mode": "warn",
            "threshold": 60,
        },
        # Clean Code Checks
        "function_max_lines": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_lines": 20,
        },
        "function_max_params": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_params": 3,
        },
        "no_generic_names": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "forbidden": [
                "data",
                "dto",
                "result",
                "info",
                "obj",
                "item",
                "entity",
                "model",
                "temp",
                "tmp",
                "value",
            ],
        },
        "class_max_lines": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_lines": 100,
        },
        "class_max_deps": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_deps": 5,
        },
        "dip_violation": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_empty_exceptions": {
            "enabled": True,
            "mode": "block",
        },
        "no_empty_catch": {
            "enabled": True,
            "mode": "block",
        },
        "no_magic_numbers": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_dead_code": {
            "enabled": True,
            "mode": "block",
        },
        "no_noise_comments": {
            "enabled": True,
            "mode": "warn",
        },
        "prefer_const": {
            "enabled": True,
            "mode": "warn",
        },
        "readmodel_exists": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "repo_returns_readmodel": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_any_in_public": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_as_any": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
    },
}

SRC_DIR = Path("src")


def load_arch_config() -> dict:
    if ARCH_CONFIG_PATH.exists():
        try:
            import yaml

            with open(ARCH_CONFIG_PATH) as f:
                return yaml.safe_load(f) or DEFAULT_ARCH_CONFIG
        except Exception:
            return dict(DEFAULT_ARCH_CONFIG)
    return dict(DEFAULT_ARCH_CONFIG)


def is_core_module(module_name: str, config: dict) -> bool:
    return module_name in config.get("core_modules", [])


def check_mode(check_name: str, module_name: str, config: dict) -> str:
    check = config.get("checks", {}).get(check_name, {})
    mode = check.get("mode", "warn")
    if mode == "hybrid":
        block_for = check.get("block_for", "core_modules")
        if block_for == "core_modules" and is_core_module(module_name, config):
            return "block"
        return "warn"
    return mode


def severity_label(mode: str) -> str:
    return "🔴" if mode == "block" else "🟡" if mode == "warn" else "🟢"


# ── Helpers ──────────────────────────────────────────────────────────────


def find_ts_files(base: Path) -> list[Path]:
    return list(base.rglob("*.ts")) + list(base.rglob("*.tsx"))


def module_name_from_path(path: Path, src: Path = SRC_DIR) -> str | None:
    """Extrai o nome do módulo do caminho (ex: src/auditorias/service.ts → 'auditorias')."""
    try:
        rel = path.relative_to(src)
        parts = rel.parts
        if len(parts) >= 1 and parts[0] != "common":
            return parts[0]
        if len(parts) >= 2:
            return parts[1]
        return None
    except ValueError:
        return None


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def count_effective_lines(content: str) -> int:
    """Conta linhas efetivas de código (exclui imports, decorators, blank lines, braces)."""
    lines = content.split("\n")
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        if (
            stripped.startswith("@")
            or stripped.startswith("export class")
            or stripped.startswith("export interface")
        ):
            continue
        if stripped in ("{", "}", "};", "})"):
            continue
        if (
            stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        ):
            continue
        count += 1
    return count


def extract_constructor_params(content: str) -> list[str]:
    """Extrai parâmetros do constructor de uma classe."""
    # Match constructor(...params)
    match = re.search(r"constructor\s*\(([^)]*)\)", content, re.DOTALL)
    if not match:
        return []
    params_str = match.group(1)
    # Simple extraction - split by comma, get the parameter names
    params = []
    for p in params_str.split(","):
        p = p.strip()
        if not p:
            continue
        # Remove decorators, types, defaults
        p = re.sub(r"^\w+\s+", "", p)  # remove public/private/readonly
        p = p.split(":")[0].strip()  # remove type annotation
        p = p.split("=")[0].strip()  # remove default value
        if p:
            params.append(p)
    return params


# ── Check 1: Dependency Rule ─────────────────────────────────────────────


def check_dependency_rule(config: dict, verbose: bool = False) -> dict:
    violations = []
    total_services = 0

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith((".service.ts", ".repository.ts", ".usecase.ts")):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        total_services += 1

        infra_imports = []
        patterns = [
            r"from ['\"]\.\./\.\./(prisma|infra|database)",
            r"from ['\"]src/(prisma|infra|database)",
            r"import.*PrismaService",
            r"import.*prisma",
            r"from ['\"].*prisma.*['\"]",
            r"from ['\"].*typeorm['\"]",
            r"from ['\"]@prisma",
        ]
        for p in patterns:
            matches = re.findall(p, content, re.IGNORECASE)
            infra_imports.extend(matches)

        if infra_imports:
            mode = check_mode("dependency_rule", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Importa diretamente: {', '.join(set(infra_imports))}",
                    "fix": f"Criar interface I{ts_file.stem.replace('.service', 'Repository').replace('.repository', '')} e usar injeção de dependência",
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "dependency_rule",
        "label": "Dependency Rule (Ports & Adapters)",
        "description": "Services não devem importar diretamente Prisma/infra — usar interfaces",
        "passed": passed,
        "blocked": blocked,
        "total_services": total_services,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Check 2: Circular Dependencies ──────────────────────────────────────


def check_circular_deps(config: dict, verbose: bool = False) -> dict:
    """Detecta dependências circulares entre módulos NestJS.
    Lê arquivos de módulo (module.ts) e constrói um grafo de dependências."""
    module_files = list(SRC_DIR.rglob("*.module.ts"))
    module_imports = defaultdict(set)

    for mf in module_files:
        module_name = module_name_from_path(mf)
        if module_name is None:
            continue
        content = read_file_safe(mf)
        imports = re.findall(
            r"(?:imports|imports:\s*\[)(.*?)(?:\])",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        for block in imports:
            for ref in re.findall(r"(\w+)Module", block):
                if ref != f"{module_name.title()}Module":
                    module_imports[module_name].add(ref.lower().replace("module", ""))

    cycles = []
    visited = set()
    path_stack = []

    def dfs(node, path):
        if node in path_stack:
            cycle_start = path_stack.index(node)
            cycle = path_stack[cycle_start:] + [node]
            cycles.append(" -> ".join(cycle))
            return
        if node in visited:
            return
        visited.add(node)
        path_stack.append(node)
        for neighbor in module_imports.get(node, set()):
            dfs(neighbor, path)
        path_stack.pop()

    for mod in list(module_imports.keys()):
        dfs(mod, [])

    cycles = list(set(cycles))
    mode = check_mode("circular_deps", "", config)
    passed = len(cycles) == 0
    return {
        "check": "circular_deps",
        "label": "Circular Dependencies",
        "description": "Módulos não devem ter dependências circulares entre si",
        "passed": passed,
        "blocked": not passed and mode == "block",
        "modules_analyzed": len(module_imports),
        "violations_count": len(cycles),
        "violations": [{"detail": c, "severity": mode} for c in cycles],
    }


# ── Check 3: Interface Coverage ─────────────────────────────────────────


def check_interface_coverage(config: dict, verbose: bool = False) -> dict:
    violations = []
    total_services = 0
    covered = 0

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(".service.ts"):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        total_services += 1
        dir_path = ts_file.parent
        stem = ts_file.stem.replace(".service", "")
        interface_stem = f"i{stem}.interface.ts"
        interface_path = dir_path / interface_stem

        if not interface_path.exists():
            mode = check_mode("interface_coverage", module, config)
            threshold = (
                config.get("checks", {})
                .get("interface_coverage", {})
                .get("threshold", 100)
            )
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Sem interface correspondente: esperado {interface_stem}",
                    "fix": f"Criar {interface_path} com as operacoes publicas do service",
                    "threshold": threshold,
                }
            )
        else:
            covered += 1

    ratio = (covered / total_services * 100) if total_services > 0 else 100
    passed = ratio >= 100
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "interface_coverage",
        "label": "Interface Coverage (DIP)",
        "description": "Todo Service deve ter uma interface correspondente (I{Nome}Interface)",
        "passed": passed,
        "blocked": blocked,
        "total_services": total_services,
        "covered": covered,
        "coverage_pct": round(ratio, 1),
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Check 4: Domain Isolation ───────────────────────────────────────────


def check_domain_isolation(config: dict, verbose: bool = False) -> dict:
    violations = []

    domain_files = list(SRC_DIR.rglob("domain/**/*.ts")) + list(
        SRC_DIR.rglob("**/domain/*.ts")
    )
    if not domain_files:
        domain_files = [f for f in find_ts_files(SRC_DIR) if "domain" in f.parts]

    for df in domain_files:
        module = module_name_from_path(df)
        if module is None:
            continue

        content = read_file_safe(df)
        infra_imports = []
        patterns = [
            r"from ['\"].*prisma.*['\"]",
            r"from ['\"].*infra.*['\"]",
            r"from ['\"].*database.*['\"]",
            r"import.*PrismaService",
            r"from ['\"].*typeorm['\"]",
            r"from ['\"]@prisma",
        ]
        for p in patterns:
            matches = re.findall(p, content, re.IGNORECASE)
            infra_imports.extend(matches)

        if infra_imports:
            mode = check_mode("domain_isolation", module, config)
            violations.append(
                {
                    "file": str(df),
                    "module": module,
                    "severity": mode,
                    "detail": f"Domínio importa infraestrutura: {', '.join(set(infra_imports))}",
                    "fix": "Extrair dependência para interface e inverter a dependência",
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "domain_isolation",
        "label": "Domain Isolation",
        "description": "Arquivos de domínio não devem importar infraestrutura (Prisma, TypeORM, database)",
        "passed": passed,
        "blocked": blocked,
        "files_analyzed": len(domain_files),
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Check 5: Use Case Size ──────────────────────────────────────────────


def check_use_case_size(config: dict, verbose: bool = False) -> dict:
    violations = []
    max_methods = (
        config.get("checks", {}).get("use_case_size", {}).get("max_methods", 8)
    )

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith((".service.ts", ".usecase.ts")):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        public_methods = re.findall(
            r"^\s+(async\s+)?\w+\s*\([^)]*\)\s*[:\{<]",
            content,
            re.MULTILINE,
        )
        count = len(public_methods)

        if count > max_methods:
            mode = check_mode("use_case_size", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"{count} metodos publicos (max: {max_methods})",
                    "fix": f"Extrair casos de uso em classes separadas (ex: Criar{ts_file.stem.replace('.service', '')}UseCase)",
                    "method_count": count,
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "use_case_size",
        "label": "Use Case Size",
        "description": f"Services/UseCases com mais de {max_methods} metodos publicos devem ser decompostos",
        "passed": passed,
        "blocked": blocked,
        "max_methods": max_methods,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Check 6: Module Coverage ────────────────────────────────────────────


def check_module_coverage(config: dict, verbose: bool = False) -> dict:
    violations = []
    threshold = config.get("checks", {}).get("module_coverage", {}).get("threshold", 60)

    lcov_paths = [
        Path("coverage/lcov.info"),
        Path("coverage/coverage-final.json"),
        Path(".ace/coverage/lcov.info"),
    ]
    lcov_file = None
    for p in lcov_paths:
        if p.exists():
            lcov_file = p
            break

    if lcov_file is None:
        return {
            "check": "module_coverage",
            "label": "Module Coverage",
            "description": f"Cobertura minima de {threshold}% por modulo",
            "passed": None,
            "blocked": False,
            "error": "Nenhum arquivo de cobertura encontrado. Execute os testes primeiro.",
            "violations_count": 0,
            "violations": [],
        }

    module_files = defaultdict(list)
    if lcov_file.suffix == ".info":
        content = read_file_safe(lcov_file)
        current_sf = None
        for line in content.split("\n"):
            if line.startswith("SF:"):
                current_sf = line[3:].strip()
            elif line.startswith("end_of_record") and current_sf:
                module = module_name_from_path(Path(current_sf))
                if module:
                    module_files[module].append(current_sf)
                current_sf = None

    module_hits = defaultdict(lambda: {"hit": 0, "found": 0})
    if lcov_file.suffix == ".info":
        content = read_file_safe(lcov_file)
        current_sf = None
        for line in content.split("\n"):
            if line.startswith("SF:"):
                current_sf = line[3:].strip()
            elif line.startswith("DA:") and current_sf:
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    module = module_name_from_path(Path(current_sf))
                    if module:
                        module_hits[module]["found"] += 1
                        if parts[1].strip() != "0":
                            module_hits[module]["hit"] += 1

    for mod, data in module_hits.items():
        pct = (data["hit"] / data["found"] * 100) if data["found"] > 0 else 0
        is_core = is_core_module(mod, config)
        effective_threshold = threshold if not is_core else max(threshold, 70)
        if pct < effective_threshold:
            mode = "block" if is_core and pct < 50 else "warn"
            violations.append(
                {
                    "module": mod,
                    "severity": mode,
                    "coverage_pct": round(pct, 1),
                    "threshold": effective_threshold,
                    "detail": f"Cobertura {pct:.1f}% (threshold: {effective_threshold}%)",
                    "fix": f"Adicionar testes para o modulo {mod}",
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "module_coverage",
        "label": "Module Coverage",
        "description": f"Cobertura minima de {threshold}% por modulo (core: ≥ 70%)",
        "passed": passed,
        "blocked": blocked,
        "threshold": threshold,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 7: Function Max Lines ──────────────────────────────


def check_function_max_lines(config: dict, verbose: bool = False) -> dict:
    violations = []
    max_lines = (
        config.get("checks", {}).get("function_max_lines", {}).get("max_lines", 20)
    )

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts", ".controller.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        # Find function/method definitions and count lines until next function or class end
        # Simple heuristic: look for function definitions and count lines to next function/class
        function_pattern = r"^\s+(async\s+)?(public|private|protected)?\s*(async\s+)?\w+\s*\([^)]*\)\s*[:\{]"
        lines = content.split("\n")

        in_function = False
        function_start = 0
        function_name = "unknown"
        brace_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for function start
            if not in_function and re.match(function_pattern, line):
                in_function = True
                function_start = i
                match = re.search(r"(\w+)\s*\(", line)
                function_name = match.group(1) if match else "unknown"
                brace_count = 0

            if in_function:
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0 and i > function_start:
                    # Function ended
                    func_lines = i - function_start + 1
                    if func_lines > max_lines:
                        mode = check_mode("function_max_lines", module, config)
                        violations.append(
                            {
                                "file": str(ts_file),
                                "module": module,
                                "severity": mode,
                                "detail": f"Função '{function_name}' tem {func_lines} linhas (max: {max_lines})",
                                "fix": f"Extrair lógica para funções menores ou use cases separados",
                                "line_count": func_lines,
                            }
                        )
                    in_function = False

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "function_max_lines",
        "label": "Function Max Lines",
        "description": f"Funções não devem exceder {max_lines} linhas",
        "passed": passed,
        "blocked": blocked,
        "max_lines": max_lines,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 8: Function Max Params ─────────────────────────────


def check_function_max_params(config: dict, verbose: bool = False) -> dict:
    violations = []
    max_params = (
        config.get("checks", {}).get("function_max_params", {}).get("max_params", 3)
    )

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts", ".controller.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        # Find function definitions with parameters
        func_matches = re.finditer(
            r"^\s+(async\s+)?(public|private|protected)?\s*(async\s+)?(\w+)\s*\(([^)]*)\)",
            content,
            re.MULTILINE,
        )

        for match in func_matches:
            func_name = match.group(4)
            params_str = match.group(5).strip()

            if not params_str:
                continue

            # Count parameters (split by comma, but ignore nested generics)
            # Simple heuristic: count commas at top level
            param_count = 1
            depth = 0
            for char in params_str:
                if char in "<([{":
                    depth += 1
                elif char in ">)]}":
                    depth -= 1
                elif char == "," and depth == 0:
                    param_count += 1

            if param_count > max_params:
                mode = check_mode("function_max_params", module, config)
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"Função '{func_name}' tem {param_count} parâmetros (max: {max_params})",
                        "fix": f"Usar objeto de parâmetros nomeado (ex: {func_name}Params)",
                        "param_count": param_count,
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "function_max_params",
        "label": "Function Max Parameters",
        "description": f"Funções não devem ter mais de {max_params} parâmetros",
        "passed": passed,
        "blocked": blocked,
        "max_params": max_params,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 9: No Generic Names ────────────────────────────────


def check_no_generic_names(config: dict, verbose: bool = False) -> dict:
    violations = []
    forbidden = (
        config.get("checks", {})
        .get("no_generic_names", {})
        .get(
            "forbidden",
            [
                "data",
                "dto",
                "result",
                "info",
                "obj",
                "item",
                "entity",
                "model",
                "temp",
                "tmp",
                "value",
            ],
        )
    )

    # Pattern to match variable declarations: const/let/var name = ...
    var_pattern = re.compile(
        r"(?:const|let|var)\s+(" + "|".join(forbidden) + r")\s*[=:]", re.IGNORECASE
    )

    # Pattern for function parameters: function name(param: type) or function (param: type)
    param_pattern = re.compile(
        r"\(\s*(" + "|".join(forbidden) + r")\s*:", re.IGNORECASE
    )

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Check variable declarations
            var_matches = var_pattern.finditer(line)
            for match in var_matches:
                mode = check_mode("no_generic_names", module, config)
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"Nome genérico '{match.group(1)}' na linha {i + 1}: {line.strip()[:80]}",
                        "fix": f"Usar nome semântico (ex: auditoriaEncontrada, criacaoDto, tokensGerados)",
                        "line": i + 1,
                        "name": match.group(1),
                    }
                )

            # Check function parameters
            param_matches = param_pattern.finditer(line)
            for match in param_matches:
                mode = check_mode("no_generic_names", module, config)
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"Parâmetro genérico '{match.group(1)}' na linha {i + 1}: {line.strip()[:80]}",
                        "fix": f"Usar nome semântico (ex: criacaoAuditoriaDto, atualizacaoPlanoDto)",
                        "line": i + 1,
                        "name": match.group(1),
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_generic_names",
        "label": "No Generic Names",
        "description": f"Proíbe variáveis/parâmetros genéricos: {', '.join(forbidden)}",
        "passed": passed,
        "blocked": blocked,
        "forbidden": forbidden,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 10: Class Max Lines ────────────────────────────────


def check_class_max_lines(config: dict, verbose: bool = False) -> dict:
    violations = []
    max_lines = (
        config.get("checks", {}).get("class_max_lines", {}).get("max_lines", 100)
    )

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (
                ".service.ts",
                ".usecase.ts",
                ".repository.ts",
                ".controller.ts",
                ".entity.ts",
            )
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        effective_lines = count_effective_lines(content)

        if effective_lines > max_lines:
            mode = check_mode("class_max_lines", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Classe tem {effective_lines} linhas efetivas (max: {max_lines})",
                    "fix": f"Extrair responsabilidades para classes separadas (services, use cases, entities)",
                    "line_count": effective_lines,
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "class_max_lines",
        "label": "Class Max Lines",
        "description": f"Classes não devem exceder {max_lines} linhas efetivas",
        "passed": passed,
        "blocked": blocked,
        "max_lines": max_lines,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 11: Class Max Deps ────────────────────────────────


def check_class_max_deps(config: dict, verbose: bool = False) -> dict:
    violations = []
    max_deps = config.get("checks", {}).get("class_max_deps", {}).get("max_deps", 5)

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts", ".controller.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        deps = extract_constructor_params(content)
        dep_count = len(deps)

        if dep_count > max_deps:
            mode = check_mode("class_max_deps", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Classe tem {dep_count} dependências no constructor (max: {max_deps}): {', '.join(deps)}",
                    "fix": f"Extrair responsabilidades para classes separadas",
                    "dep_count": dep_count,
                    "dependencies": deps,
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "class_max_deps",
        "label": "Class Max Dependencies",
        "description": f"Classes não devem ter mais de {max_deps} dependências injetadas",
        "passed": passed,
        "blocked": blocked,
        "max_deps": max_deps,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 12: DIP Violation ─────────────────────────────────


def check_dip_violation(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith((".service.ts", ".usecase.ts")):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        # Check for PrismaService injection in constructor
        if re.search(r"constructor\s*\([^)]*PrismaService", content):
            mode = check_mode("dip_violation", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": "Injeta PrismaService diretamente — viola DIP",
                    "fix": "Criar interface de repositório (I{Nome}Repository) e injetar a interface",
                }
            )

        # Check for @prisma/client imports in services/use-cases
        if re.search(r"from ['\"]@prisma/client", content) or re.search(
            r"import.*@prisma/client", content
        ):
            mode = check_mode("dip_violation", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": "Importa @prisma/client em service/use-case — viola DIP",
                    "fix": "Mover acesso a Prisma para implementação de repositório (infrastructure)",
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "dip_violation",
        "label": "DIP Violation (Prisma in Services)",
        "description": "Services/UseCases não devem injetar PrismaService nem importar @prisma/client",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 13: No Empty Exceptions ────────────────────────────


def check_no_empty_exceptions(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        # Pattern: throw new SomeException('') or throw new SomeException("")
        pattern = re.compile(r"throw\s+new\s+\w+Exception\s*\(\s*['\"]\s*['\"]\s*\)")

        for i, line in enumerate(lines):
            if pattern.search(line):
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "block",
                        "detail": f"Exception com mensagem vazia na linha {i + 1}: {line.strip()}",
                        "fix": "Adicionar mensagem descritiva com contexto (ex: `Auditoria ${id} não encontrada`)",
                        "line": i + 1,
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_empty_exceptions",
        "label": "No Empty Exception Messages",
        "description": "Exceptions nunca devem ter mensagens vazias",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 14: No Empty Catch ────────────────────────────────


def check_no_empty_catch(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        # Pattern: catch (e) { } or catch (e) { console.log(e) } or catch { }
        # Simple heuristic: catch followed by empty or near-empty block
        in_catch = False
        catch_start = 0
        brace_count = 0
        has_content = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_catch and re.match(r".*catch\s*\([^)]*\)\s*{?", stripped):
                in_catch = True
                catch_start = i
                brace_count = line.count("{") - line.count("}")
                has_content = False
                continue

            if in_catch:
                brace_count += line.count("{") - line.count("}")

                # Check if line has meaningful content (not just comments, blank, or closing brace)
                if (
                    stripped
                    and not stripped.startswith("//")
                    and not stripped.startswith("/*")
                    and stripped != "}"
                    and stripped != "};"
                ):
                    has_content = True

                if brace_count <= 0 and i > catch_start:
                    if not has_content:
                        violations.append(
                            {
                                "file": str(ts_file),
                                "module": module,
                                "severity": "block",
                                "detail": f"Bloco catch vazio ou só log na linha {catch_start + 1}-{i + 1}",
                                "fix": "Tratar erro adequadamente: logar com contexto, re-throw, ou retornar Result<T,E>",
                                "line": catch_start + 1,
                            }
                        )
                    in_catch = False

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_empty_catch",
        "label": "No Empty Catch Blocks",
        "description": "Blocos catch não devem ser vazios — sempre tratar ou logar com contexto",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 15: No Magic Numbers ──────────────────────────────


def check_no_magic_numbers(config: dict, verbose: bool = False) -> dict:
    violations = []

    # Numbers that are likely magic (not 0, 1, -1, 100, 1000, etc.)
    # Context: in business logic, not in constants, tests, or config
    for ts_file in find_ts_files(SRC_DIR):
        # Skip test files, config files, constant files
        if any(
            p in str(ts_file)
            for p in [
                ".spec.ts",
                ".test.ts",
                "config/",
                "constants.ts",
                ".constants.ts",
            ]
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        # Pattern: numeric literals in conditions, assignments, returns (not in comments)
        # Exclude: 0, 1, -1, 2, 3, 10, 100, 1000, 60, 1000, 3600 (common constants)
        allowed = {0, 1, -1, 2, 3, 10, 100, 1000, 60, 3600, 86400}

        # Find numeric literals: \b\d+\b but not in comments, strings, or allowed list
        for i, line in enumerate(lines):
            # Skip comment lines
            if line.strip().startswith("//") or line.strip().startswith("/*"):
                continue

            # Remove string literals to avoid false positives
            line_no_strings = re.sub(r'["\'].*?["\']', "", line)

            # Find numbers
            numbers = re.findall(r"\b(\d+)\b", line_no_strings)
            for num_str in numbers:
                num = int(num_str)
                if num not in allowed and num > 10:
                    # Check if it's in a constant declaration (const X = N)
                    if not re.search(rf"const\s+\w+\s*=\s*{num_str}\b", line):
                        violations.append(
                            {
                                "file": str(ts_file),
                                "module": module,
                                "severity": check_mode(
                                    "no_magic_numbers", module, config
                                ),
                                "detail": f"Magic number {num} na linha {i + 1}: {line.strip()[:80]}",
                                "fix": f"Extrair para constante nomeada em domain/constants.ts (ex: PRAZO_DIAS = {num})",
                                "line": i + 1,
                                "number": num,
                            }
                        )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_magic_numbers",
        "label": "No Magic Numbers",
        "description": "Números mágicos em lógica de negócio devem ser constantes nomeadas",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 16: No Dead Code ──────────────────────────────────


def check_no_dead_code(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Stub methods: throw new ...('não implementado') or throw new ...('not implemented')
            if re.search(
                r"throw\s+new\s+\w+\s*\(\s*['\"].*(não implementado|not implemented|não implementada).*['\"]",
                stripped,
                re.IGNORECASE,
            ):
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "block",
                        "detail": f"Stub não implementado na linha {i + 1}: {stripped[:80]}",
                        "fix": "Implementar o método OU remover se não usado. Se planejado para futuro, usar @TODO com issue number",
                        "line": i + 1,
                    }
                )

            # TODO comments in production code (not test files)
            if not any(p in str(ts_file) for p in [".spec.ts", ".test.ts"]):
                if re.search(
                    r"//\s*TODO|//\s*FIXME|//\s*HACK", stripped, re.IGNORECASE
                ):
                    violations.append(
                        {
                            "file": str(ts_file),
                            "module": module,
                            "severity": "warn",
                            "detail": f"Comentário TODO/FIXME/HACK na linha {i + 1}: {stripped[:80]}",
                            "fix": "Resolver o TODO ou criar issue. Remover comentário se resolvido.",
                            "line": i + 1,
                        }
                    )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_dead_code",
        "label": "No Dead Code / Stubs",
        "description": "Zero stubs 'não implementado' e zero TODO/FIXME/HACK em código de produção",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 17: No Noise Comments ─────────────────────────────


def check_no_noise_comments(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Section comments: // ── Section Name ────────────
            if re.match(r"//\s*[-_]{3,}\s*.+\s*[-_]{3,}", stripped):
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "warn",
                        "detail": f"Comentário de seção na linha {i + 1}: {stripped}",
                        "fix": "Remover — usar estrutura de pastas/arquivos para organizar código",
                        "line": i + 1,
                    }
                )

            # Commented code blocks (multiple lines of // code)
            # Heuristic: line starts with // and looks like code
            if re.match(
                r"//\s*(const|let|var|async|function|if|for|while|return|try|catch|throw)",
                stripped,
            ):
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "warn",
                        "detail": f"Código comentado na linha {i + 1}: {stripped[:80]}",
                        "fix": "Remover código comentado — usar git history se precisar recuperar",
                        "line": i + 1,
                    }
                )

            # Obvious comments: // incrementa contador, // retorna resultado
            if re.match(
                r"//\s*(incrementa|decrementa|retorna|atribui|define|verifica|valida)\s+\w+",
                stripped,
                re.IGNORECASE,
            ):
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "warn",
                        "detail": f"Comentário óbvio na linha {i + 1}: {stripped}",
                        "fix": "Remover — código auto-explicativo não precisa de comentário",
                        "line": i + 1,
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_noise_comments",
        "label": "No Noise Comments",
        "description": "Remove comentários de seção, código comentado, comentários óbvios",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 18: Prefer Const ──────────────────────────────────


def check_prefer_const(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        # Find let declarations that are never reassigned
        let_vars = {}  # var_name -> (line_num, reassigned)

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Match let/const declarations
            let_match = re.match(r"(let|const)\s+(\w+)\s*[=:]", stripped)
            if let_match:
                keyword, var_name = let_match.groups()
                if keyword == "let":
                    let_vars[var_name] = {
                        "line": i + 1,
                        "reassigned": False,
                        "original_line": line,
                    }

            # Check for reassignment (var = ...)
            for var_name in let_vars:
                if re.search(rf"\b{var_name}\s*[+\-*/%]?=", stripped) and not re.match(
                    r"(let|const)\s+{var_name}\s*=", stripped
                ):
                    let_vars[var_name]["reassigned"] = True

        # Report let vars that were never reassigned
        for var_name, info in let_vars.items():
            if not info["reassigned"]:
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": "warn",
                        "detail": f"'let {var_name}' na linha {info['line']} nunca reatribuído — usar 'const'",
                        "fix": f"Mudar 'let {var_name}' para 'const {var_name}'",
                        "line": info["line"],
                        "variable": var_name,
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "prefer_const",
        "label": "Prefer Const Over Let",
        "description": "Variáveis declaradas com 'let' que nunca são reatribuídas devem usar 'const'",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 19: ReadModel Exists ─────────────────────────────


def check_readmodel_exists(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(".repository.ts") or "prisma-" in ts_file.name:
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        # Check if interface defines a ReadModel return type
        # Look for ReadModel suffix in interface methods
        if "ReadModel" not in content:
            mode = check_mode("readmodel_exists", module, config)
            violations.append(
                {
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": "Interface de repositório não define ReadModel",
                    "fix": "Adicionar interface {Entidade}ReadModel e usar nos métodos de retorno",
                }
            )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "readmodel_exists",
        "label": "ReadModel Exists",
        "description": "Toda interface de repositório deve definir e retornar ReadModel tipado",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 20: Repo Returns ReadModel ────────────────────────


def check_repo_returns_readmodel(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(".repository.ts") or "prisma-" in ts_file.name:
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

        # Check method return types for 'any' or missing ReadModel
        method_returns = re.findall(r"\)\s*:\s*Promise<([^>]+)>", content)
        for ret in method_returns:
            if ret.strip() == "any" or "any[]" in ret:
                mode = check_mode("repo_returns_readmodel", module, config)
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"Método retorna {ret} — deve retornar ReadModel tipado",
                        "fix": "Definir {Entidade}ReadModel e usar como tipo de retorno",
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "repo_returns_readmodel",
        "label": "Repo Returns ReadModel",
        "description": "Métodos de repositório não devem retornar 'any' — usar ReadModel",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 21: No Any in Public ──────────────────────────────


def check_no_any_in_public(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".repository.ts", ".usecase.ts", ".dto.ts", ".service.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and strings
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Check for 'any' in public interface positions
            # : any, : any[], Promise<any>, <any>
            if re.search(r":\s*any(\[\]|<[^>]*>)?\b", stripped) or re.search(
                r"Promise<any\b", stripped
            ):
                mode = check_mode("no_any_in_public", module, config)
                violations.append(
                    {
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"'any' em interface pública na linha {i + 1}: {stripped[:80]}",
                        "fix": "Substituir por tipo explícito (ReadModel, DTO, Entity, etc.)",
                        "line": i + 1,
                    }
                )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_any_in_public",
        "label": "No 'any' in Public Interfaces",
        "description": "Interfaces públicas (repo, use case, dto, service) não devem usar 'any'",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Clean Code Check 22: No As Any ─────────────────────────────────────


def check_no_as_any(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Check for 'as any' cast
            if re.search(r"\bas\s+any\b", stripped):
                # Check if there's a justification comment on same or previous line
                has_justification = False
                if "//" in stripped and any(
                    kw in stripped for kw in ["TODO", "FIXME", "LEGACY", "TEMP", "HACK"]
                ):
                    has_justification = True
                elif (
                    i > 0
                    and "//" in lines[i - 1]
                    and any(
                        kw in lines[i - 1]
                        for kw in ["TODO", "FIXME", "LEGACY", "TEMP", "HACK"]
                    )
                ):
                    has_justification = True

                if not has_justification:
                    mode = check_mode("no_as_any", module, config)
                    violations.append(
                        {
                            "file": str(ts_file),
                            "module": module,
                            "severity": mode,
                            "detail": f"'as any' sem justificativa na linha {i + 1}: {stripped[:80]}",
                            "fix": "Remover cast ou adicionar comentário justificando (// LEGACY: ...) + criar issue de migração",
                            "line": i + 1,
                        }
                    )

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_as_any",
        "label": "No 'as any' Casts",
        "description": "Casts 'as any' são proibidos sem justificativa documentada",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── Runner ───────────────────────────────────────────────────────────────


def run_checks(requested: list[str], config: dict, verbose: bool = False) -> dict:
    all_checks = {
        # Architecture checks
        "dependency_rule": check_dependency_rule,
        "circular_deps": check_circular_deps,
        "interface_coverage": check_interface_coverage,
        "domain_isolation": check_domain_isolation,
        "use_case_size": check_use_case_size,
        "module_coverage": check_module_coverage,
        # Clean Code checks
        "function_max_lines": check_function_max_lines,
        "function_max_params": check_function_max_params,
        "no_generic_names": check_no_generic_names,
        "class_max_lines": check_class_max_lines,
        "class_max_deps": check_class_max_deps,
        "dip_violation": check_dip_violation,
        "no_empty_exceptions": check_no_empty_exceptions,
        "no_empty_catch": check_no_empty_catch,
        "no_magic_numbers": check_no_magic_numbers,
        "no_dead_code": check_no_dead_code,
        "no_noise_comments": check_no_noise_comments,
        "prefer_const": check_prefer_const,
        "readmodel_exists": check_readmodel_exists,
        "repo_returns_readmodel": check_repo_returns_readmodel,
        "no_any_in_public": check_no_any_in_public,
        "no_as_any": check_no_as_any,
    }

    if "all" in requested:
        requested = list(all_checks.keys())

    results = {}
    for name in requested:
        if name in all_checks:
            if verbose:
                print(f"  Running {name}...", file=sys.stderr)
            results[name] = all_checks[name](config, verbose=verbose)

    return results


def format_human(results: dict, verbose: bool = False):
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r.get("passed"))
    blocked = any(r.get("blocked") for r in results.values())
    failed_but_not_blocked = sum(
        1 for r in results.values() if not r.get("passed") and not r.get("blocked")
    )

    for name, result in results.items():
        status = "✅" if result.get("passed") else "🔴"
        if result.get("passed") is None:
            status = "⚠️"

        print(f"\n  {status} {result['label']}")
        print(f"     {result['description']}")

        if result.get("passed") is None and result.get("error"):
            print(f"     ⚠️  {result['error']}")
            continue

        if result.get("coverage_pct") is not None:
            print(
                f"     Cobertura: {result['coverage_pct']}% ({result.get('covered', '?')}/{result.get('total_services', '?')})"
            )
        if result.get("modules_analyzed") is not None:
            print(f"     Modulos analisados: {result['modules_analyzed']}")

        for v in result.get("violations", []):
            sev = severity_label(v.get("severity", "warn"))
            print(f"     {sev} {v.get('file', v.get('module', v.get('detail', '')))}")
            print(f"        {v['detail']}")
            if verbose and v.get("fix"):
                print(f"        💡 {v['fix']}")

        if not result.get("violations") and result.get("passed"):
            print(f"     ✅ Sem violacoes")

    print(f"\n{'=' * 50}")
    print(f"  Resultado: {passed_checks}/{total_checks} checks passaram")
    if blocked:
        print(f"  🔴 HA BLOQUEIOS — corrija antes do merge")
    elif failed_but_not_blocked > 0:
        print(f"  🟡 {failed_but_not_blocked} alerta(s) — registre em divida tecnica")
    else:
        print(f"  🟢 Tudo OK")
    print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(
        description="Fitness Functions — verificacao arquitetural automatizada"
    )
    # Architecture checks
    parser.add_argument("--all", action="store_true", help="Executa todos os checks")
    parser.add_argument("--check-deps", action="store_true", help="Dependency Rule")
    parser.add_argument(
        "--check-circular", action="store_true", help="Dependencias circulares"
    )
    parser.add_argument(
        "--check-interfaces", action="store_true", help="Cobertura de interfaces"
    )
    parser.add_argument(
        "--check-domain", action="store_true", help="Isolamento do dominio"
    )
    parser.add_argument(
        "--check-usecase", action="store_true", help="Tamanho dos use cases"
    )
    parser.add_argument(
        "--check-coverage", action="store_true", help="Cobertura por modulo"
    )
    # Clean Code checks
    parser.add_argument(
        "--check-functions",
        action="store_true",
        help="Clean Code: Functions (max lines, params, generic names)",
    )
    parser.add_argument(
        "--check-naming", action="store_true", help="Clean Code: Naming (generic names)"
    )
    parser.add_argument(
        "--check-classes",
        action="store_true",
        help="Clean Code: Classes (max lines, deps, DIP)",
    )
    parser.add_argument(
        "--check-errors",
        action="store_true",
        help="Clean Code: Errors (empty exceptions, empty catch)",
    )
    parser.add_argument(
        "--check-smells",
        action="store_true",
        help="Clean Code: Smells (magic numbers, dead code, noise comments, const)",
    )
    parser.add_argument(
        "--check-readmodels",
        action="store_true",
        help="Clean Code: ReadModels & Type Safety",
    )
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Exit code 1 se violacao ou bloqueio"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Detalhes e sugestoes de correcao"
    )
    args = parser.parse_args()

    requested = []
    if args.all:
        requested = ["all"]
    # Architecture
    if args.check_deps:
        requested.append("dependency_rule")
    if args.check_circular:
        requested.append("circular_deps")
    if args.check_interfaces:
        requested.append("interface_coverage")
    if args.check_domain:
        requested.append("domain_isolation")
    if args.check_usecase:
        requested.append("use_case_size")
    if args.check_coverage:
        requested.append("module_coverage")
    # Clean Code
    if args.check_functions:
        requested.extend(
            ["function_max_lines", "function_max_params", "no_generic_names"]
        )
    if args.check_naming:
        requested.append("no_generic_names")
    if args.check_classes:
        requested.extend(["class_max_lines", "class_max_deps", "dip_violation"])
    if args.check_errors:
        requested.extend(["no_empty_exceptions", "no_empty_catch"])
    if args.check_smells:
        requested.extend(
            ["no_magic_numbers", "no_dead_code", "no_noise_comments", "prefer_const"]
        )
    if args.check_readmodels:
        requested.extend(
            [
                "readmodel_exists",
                "repo_returns_readmodel",
                "no_any_in_public",
                "no_as_any",
            ]
        )

    if not requested:
        parser.print_help()
        sys.exit(0)

    config = load_arch_config()
    results = run_checks(requested, config, verbose=args.verbose)

    output = {
        "config": {
            "core_modules": config.get("core_modules", []),
        },
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.get("passed")),
            "blocked": any(r.get("blocked") for r in results.values()),
            "warnings": sum(
                1
                for r in results.values()
                if not r.get("passed")
                and not r.get("blocked")
                and r.get("passed") is not None
            ),
        },
    }

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        format_human(results, verbose=args.verbose)

    has_blocks = output["summary"]["blocked"]
    has_strict_fail = args.strict and (has_blocks or output["summary"]["warnings"] > 0)

    sys.exit(1 if has_strict_fail or has_blocks else 0)


if __name__ == "__main__":
    main()
