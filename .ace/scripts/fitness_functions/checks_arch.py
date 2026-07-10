#!/usr/bin/env python3
"""Checks arquiteturais (Ports & Adapters, dependências, interfaces, domínio)."""

import re
from collections import defaultdict
from pathlib import Path

from .config import SRC_DIR, check_mode, is_core_module
from .helpers import (
    find_ts_files,
    module_name_from_path,
    read_file_safe,
)


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
