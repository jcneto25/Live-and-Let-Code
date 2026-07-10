#!/usr/bin/env python3
"""Checks de Clean Code (funções, classes, erros, smells, type safety)."""

import re
from pathlib import Path

from .config import SRC_DIR, check_mode
from .helpers import (
    count_effective_lines,
    extract_constructor_params,
    find_ts_files,
    module_name_from_path,
    read_file_safe,
)


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

        function_pattern = r"^\s+(async\s+)?(public|private|protected)?\s*(async\s+)?\w+\s*\([^)]*\)\s*[:\{]"
        lines = content.split("\n")

        in_function = False
        function_start = 0
        function_name = "unknown"
        brace_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_function and re.match(function_pattern, line):
                in_function = True
                function_start = i
                match = re.search(r"(\w+)\s*\(", line)
                function_name = match.group(1) if match else "unknown"
                brace_count = 0

            if in_function:
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0 and i > function_start:
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

    var_pattern = re.compile(
        r"(?:const|let|var)\s+(" + "|".join(forbidden) + r")\s*[=:]", re.IGNORECASE
    )
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


def check_dip_violation(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith((".service.ts", ".usecase.ts")):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

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


def check_no_empty_exceptions(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

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


def check_no_empty_catch(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

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


def check_no_magic_numbers(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
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

        allowed = {0, 1, -1, 2, 3, 10, 100, 1000, 60, 3600, 86400}

        for i, line in enumerate(lines):
            if line.strip().startswith("//") or line.strip().startswith("/*"):
                continue

            line_no_strings = re.sub(r'["\'].*?["\']', "", line)

            numbers = re.findall(r"\b(\d+)\b", line_no_strings)
            for num_str in numbers:
                num = int(num_str)
                if num not in allowed and num > 10:
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


def check_prefer_const(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        let_vars = {}

        for i, line in enumerate(lines):
            stripped = line.strip()

            let_match = re.match(r"(let|const)\s+(\w+)\s*[=:]", stripped)
            if let_match:
                keyword, var_name = let_match.groups()
                if keyword == "let":
                    let_vars[var_name] = {
                        "line": i + 1,
                        "reassigned": False,
                        "original_line": line,
                    }

            for var_name in let_vars:
                if re.search(rf"\b{var_name}\s*[+\-*/%]?=", stripped) and not re.match(
                    r"(let|const)\s+{var_name}\s*=", stripped
                ):
                    let_vars[var_name]["reassigned"] = True

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


def check_readmodel_exists(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(".repository.ts") or "prisma-" in ts_file.name:
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

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


def check_repo_returns_readmodel(config: dict, verbose: bool = False) -> dict:
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(".repository.ts") or "prisma-" in ts_file.name:
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)

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

            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

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

            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            if re.search(r"\bas\s+any\b", stripped):
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
