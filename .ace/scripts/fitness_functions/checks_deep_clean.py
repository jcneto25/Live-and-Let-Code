#!/usr/bin/env python3
"""Checks Deep Clean (CQS, null, data clumps, flags, primitives, pass-through, validation, deep line limit).

Estes 8 checks complementam os 21 checks de Clean Code existentes (checks_clean.py),
cobrindo anti-padrões de design mais sutis que LLMs geram com frequência.

Ref: Harness Preventivo LLC §2.4 — Ação 4 (Expansão Fitness Functions Deep Clean).
"""

import re
from collections import defaultdict
from pathlib import Path

from .config import SRC_DIR, check_mode
from .helpers import count_effective_lines, find_ts_files, module_name_from_path, read_file_safe


# ── 1. no-cqs-violation ──────────────────────────────────────────────────────

def check_no_cqs_violation(config: dict, verbose: bool = False) -> dict:
    """Command-Query Separation: command methods (create/update/delete) should not return data.

    Detecta métodos create*/update*/delete* com return type != void + side effects
    (eventEmitter.emit, notificationService.*, etc.).
    """
    violations = []

    command_prefixes = (
        "create", "update", "delete", "remove", "save", "publish",
        "send", "execute", "process", "register", "cancel", "approve",
        "reject", "enable", "disable", "activate", "deactivate",
    )

    side_effect_patterns = [
        r"\.emit\s*\(",
        r"eventEmitter\s*\.\s*emit",
        r"notification\w*Service\s*\.\s*send",
        r"\.publish\s*\(",
    ]

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".controller.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        # Encontrar métodos
        method_pattern = re.compile(
            r"^\s+(async\s+)?(public\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*(\S+))?\s*\{?"
        )

        in_method = False
        method_name = ""
        method_return = ""
        method_start = 0
        method_body = []
        brace_depth = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_method:
                m = method_pattern.match(line)
                if m:
                    method_name = m.group(3)
                    return_type = m.group(4) or ""
                    method_return = return_type.strip()
                    method_start = i
                    method_body = []
                    brace_depth = line.count("{") - line.count("}")
                    in_method = True
            else:
                brace_depth += line.count("{") - line.count("}")
                method_body.append(line)

                if brace_depth <= 0 and i > method_start:
                    # Fim do método — analisar
                    is_command = any(
                        method_name.lower().startswith(prefix)
                        for prefix in command_prefixes
                    )
                    returns_value = bool(method_return) and not any(
                        void_like in method_return.lower()
                        for void_like in ("void", "promise<void>", "never")
                    )
                    has_side_effect = any(
                        re.search(pat, "".join(method_body)) if method_body else False
                        for pat in side_effect_patterns
                    )

                    if is_command and returns_value and has_side_effect:
                        mode = check_mode("no_cqs_violation", module, config)
                        violations.append({
                            "file": str(ts_file),
                            "module": module,
                            "severity": mode,
                            "detail": (
                                f"Command '{method_name}' retorna '{method_return}' "
                                f"e tem side effect — viola CQS. "
                                f"Command deve retornar void/Promise<void>."
                            ),
                            "fix": (
                                f"Separar em: command (void) que emite evento + "
                                f"query separada que retorna {method_return}."
                            ),
                            "line": method_start + 1,
                            "method": method_name,
                            "return_type": method_return,
                        })

                    in_method = False
                    method_name = ""
                    method_return = ""

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_cqs_violation",
        "label": "No CQS Violation",
        "description": "Commands (create/update/delete) não devem retornar dados se têm side effects",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 2. no-null-return ────────────────────────────────────────────────────────

def check_no_null_return(config: dict, verbose: bool = False) -> dict:
    """Proíbe `return null` em services, repositories, use cases.

    Métodos públicos devem retornar Result<T,E>, throw, ou valor garantido.
    Null gera NPEs silenciosos e viola fail-fast.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts")
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

            if re.search(r"\breturn\s+null\b", stripped):
                mode = check_mode("no_null_return", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"'return null' na linha {i + 1}: {stripped[:80]}",
                    "fix": (
                        "Retornar Optional<T>, Result<T, NotFoundError>, "
                        "ou throw NotFoundError com mensagem descritiva"
                    ),
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_null_return",
        "label": "No Null Return",
        "description": "Services/repositories não devem retornar null — usar Optional<T> ou Result<T,E>",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 3. no-data-clump ─────────────────────────────────────────────────────────

def _normalize_param_name(name: str) -> str:
    """Normaliza nome de parâmetro: remove prefixos/sufixos comuns, camelCase -> lowercase."""
    name = name.lower().strip()
    # Remove prefixes comuns
    for pfx in ("the", "a", "an", "new", "old", "target", "source"):
        if name.startswith(f"{pfx}_"):
            name = name[len(pfx) + 1:]
    return name


def check_no_data_clump(config: dict, verbose: bool = False) -> dict:
    """Detecta data clumps: 3+ parâmetros que aparecem juntos em 5+ assinaturas.

    Algoritmo:
    1. Extrai todos os parâmetros de cada função.
    2. Normaliza nomes.
    3. Para cada função, gera todos os pares de parâmetros.
    4. Agrupa pares que co-ocorrem; constrói clusters por afinidade.
    5. Reporta clusters com 3+ parâmetros em 5+ funções.
    """
    violations = []
    clump_threshold = config.get("checks", {}).get("no_data_clump", {}).get("min_fields", 3)
    occurrences_threshold = config.get("checks", {}).get("no_data_clump", {}).get("min_occurrences", 5)

    # Passo 1: extrair parâmetros de cada função
    func_params = {}  # (file, func_name) -> list[str]
    func_signatures = []  # list of (file, module, func_name, params, line)

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
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue

            # Match function declarations with parameters
            m = re.match(
                r"^\s+(?:async\s+)?(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:async\s+)?(\w+)\s*\(([^)]*)\)",
                line,
            )
            if not m:
                continue

            func_name = m.group(1)
            params_str = m.group(2).strip()

            if not params_str:
                continue

            # Extrair nomes de parâmetros (ignorar tipos e defaults)
            raw_params = []
            depth = 0
            current = []
            for char in params_str:
                if char in "<([{":
                    depth += 1
                elif char in ">)]}":
                    depth -= 1
                elif char == "," and depth == 0:
                    raw_params.append("".join(current).strip())
                    current = []
                else:
                    current.append(char)
            if current:
                raw_params.append("".join(current).strip())

            param_names = []
            for p in raw_params:
                # Extrair só o nome (remove tipo e default)
                p = p.strip()
                if not p:
                    continue
                # Remove decorators
                p = re.sub(r"@\w+\s*", "", p)
                # Pega só o nome (antes de : ou =)
                name = p.split(":")[0].split("=")[0].strip()
                if name and not name.startswith("..."):
                    name = _normalize_param_name(name)
                    param_names.append(name)

            if len(param_names) >= 2:
                func_signatures.append((ts_file, module, func_name, param_names, i + 1))

    # Passo 2: contar co-ocorrência de pares de parâmetros
    pair_counts = defaultdict(set)  # (param_a, param_b) -> set of (file, func)
    for (ts_file, module, func_name, params, line) in func_signatures:
        sig_key = (str(ts_file), func_name)
        for a_idx, a in enumerate(params):
            for b in params[a_idx + 1:]:
                # Ordenar para (a,b) ser canônico
                pair = tuple(sorted([a, b]))
                pair_counts[pair].add(sig_key)

    # Passo 3: construir clusters por afinidade (greedy)
    # Um parâmetro pertence a um cluster se co-ocorre com todos os membros existentes
    # em pelo menos occurrences_threshold funções
    reported_clumps = set()

    # Encontrar cliques de parâmetros que co-ocorrem
    for (a, b), sigs in pair_counts.items():
        if len(sigs) < occurrences_threshold:
            continue

        # Verificar se {a,b} + {c} forma um clump
        cluster = {a, b}
        for c in set(p for pair in pair_counts for p in pair):
            if c in cluster:
                continue
            # c pertence ao cluster se co-ocorre com todos os membros atuais
            # em pelo menos occurrences_threshold funções
            belongs = True
            for member in cluster:
                pair_c_member = tuple(sorted([c, member]))
                if len(pair_counts.get(pair_c_member, set())) < occurrences_threshold:
                    belongs = False
                    break
            if belongs:
                cluster.add(c)

        if len(cluster) >= clump_threshold:
            cluster_key = tuple(sorted(cluster))
            if cluster_key in reported_clumps:
                continue
            reported_clumps.add(cluster_key)

            # Encontrar funções que usam este clump
            clump_sigs = set()
            for sig in func_signatures:
                _, _, _, params, _ = sig
                if len(set(params) & set(cluster)) >= clump_threshold:
                    clump_sigs.add(sig)

            if clump_sigs:
                example_sig = next(iter(clump_sigs))
                example_file, module, example_func, example_params, example_line = example_sig

                mode = check_mode("no_data_clump", module, config)
                violations.append({
                    "file": str(example_file),
                    "module": module,
                    "severity": mode,
                    "detail": (
                        f"Data clump detectado: {', '.join(sorted(cluster))} "
                        f"aparecem juntos em {len(clump_sigs)} assinaturas. "
                        f"Exemplo: '{example_func}' na linha {example_line}."
                    ),
                    "fix": (
                        f"Extrair para objeto: {{ {', '.join(sorted(cluster))} }} → "
                        f"criar interface/type dedicado (ex: {example_func.title().replace('_', '')}Params)"
                    ),
                    "line": example_line,
                    "clump_fields": sorted(cluster),
                    "occurrences": len(clump_sigs),
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_data_clump",
        "label": "No Data Clump",
        "description": f"Parâmetros que aparecem juntos em {occurrences_threshold}+ assinaturas devem ser extraídos para objeto",
        "passed": passed,
        "blocked": blocked,
        "clump_threshold": clump_threshold,
        "occurrences_threshold": occurrences_threshold,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 4. no-flag-arguments ─────────────────────────────────────────────────────

def check_no_flag_arguments(config: dict, verbose: bool = False) -> dict:
    """Proíbe parâmetros booleanos em métodos públicos.

    Boolean flag arguments indicam que o método faz duas coisas diferentes.
    Deve ser split em dois métodos ou usar enum/strategy.
    Ref: Martin, Clean Code, Cap. 3.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts", ".controller.ts")
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

            m = re.match(
                r"^\s+(?:async\s+)?(?:public\s+)?(?:async\s+)?(\w+)\s*\(([^)]*)\)",
                line,
            )
            if not m:
                continue

            func_name = m.group(1)
            params_str = m.group(2)

            # Verificar se NÃO é private/protected
            if re.search(r"private\s+|protected\s+", line):
                continue

            # Procurar parâmetros booleanos
            bool_params = re.findall(
                r"(\w+)\s*\??\s*:\s*boolean\b", params_str
            )

            for param_name in bool_params:
                mode = check_mode("no_flag_arguments", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": (
                        f"Flag boolean '{param_name}' em método público "
                        f"'{func_name}' na linha {i + 1}"
                    ),
                    "fix": (
                        f"Dividir '{func_name}' em dois métodos: "
                        f"um para true, outro para false. "
                        f"Ou usar enum/strategy pattern."
                    ),
                    "line": i + 1,
                    "method": func_name,
                    "param": param_name,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_flag_arguments",
        "label": "No Flag Arguments",
        "description": "Métodos públicos não devem ter parâmetros booleanos (flag arguments)",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 5. no-primitive-obsession ────────────────────────────────────────────────

_PRIMITIVE_SMELLS = [
    # (primitive type pattern, domain concept, suggested replacement)
    (r":\s*string\b", "identifier/id/email/phone/url/currency", "value object"),
    (r":\s*number\b", "money/percentage/quantity/age/distance", "value object"),
    (r":\s*Date\b", "timestamp/deadline/birthday/expiry", "DateTime value object"),
]

_DOMAIN_KEYWORD_MAP = {
    "email": "Email",
    "phone": "PhoneNumber",
    "url": "Url",
    "currency": "Money",
    "money": "Money",
    "price": "Money",
    "amount": "Money",
    "percentage": "Percentage",
    "quantity": "Quantity",
    "cpf": "CPF",
    "cnpj": "CNPJ",
    "cep": "CEP",
    "uuid": "UUID",
    "id": "EntityId",
    "token": "AuthToken",
    "password": "Password",
    "hash": "Hash",
}


def check_no_primitive_obsession(config: dict, verbose: bool = False) -> dict:
    """Detecta tipos primitivos onde tipos de domínio seriam adequados.

    Busca nomes de parâmetros/campos semanticamente ricos (email, cpf, money, etc.)
    tipados como string/number/Date — sugerindo value object.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        # Apenas arquivos de domínio/core
        if not any(
            p in str(ts_file)
            for p in ["/domain/", "/entities/", "/models/", ".entity.ts", ".dto.ts"]
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
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue

            # Encontrar campos tipados como string/number
            for keyword, domain_type in _DOMAIN_KEYWORD_MAP.items():
                # Pattern: fieldName: string ou fieldName: number
                pattern = rf"\b({keyword})\s*\??\s*:\s*(?:string|number)\b"
                m = re.search(pattern, stripped, re.IGNORECASE)
                if m:
                    mode = check_mode("no_primitive_obsession", module, config)
                    violations.append({
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": (
                            f"Campo '{m.group(1)}' tipado como primitivo na linha {i + 1}. "
                            f"Deve ser value object '{domain_type}'."
                        ),
                        "fix": (
                            f"Criar value object {domain_type} com validação + "
                            f"métodos de domínio (ex: Email.validate(), Money.add())"
                        ),
                        "line": i + 1,
                        "field": m.group(1),
                        "suggested_type": domain_type,
                    })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_primitive_obsession",
        "label": "No Primitive Obsession",
        "description": "Campos semanticamente ricos não devem usar tipos primitivos — usar value objects",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 6. max-function-lines-deep ───────────────────────────────────────────────

def check_max_function_lines_deep(config: dict, verbose: bool = False) -> dict:
    """Verifica funções > 30 linhas em módulos non-core.

    Mais permissivo que o check function_max_lines (20 linhas, apenas core),
    este check varre TODOS os módulos com threshold de 30 linhas. Severidade warn.
    """
    violations = []
    max_lines = (
        config.get("checks", {})
        .get("max_function_lines_deep", {})
        .get("max_lines", 30)
    )

    for ts_file in find_ts_files(SRC_DIR):
        # Escanear todos os arquivos .ts, não apenas services
        if not ts_file.name.endswith(".ts") or ts_file.name.endswith(".spec.ts") or ts_file.name.endswith(".test.ts"):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        function_pattern = r"^\s+(async\s+)?(public|private|protected)?\s*(static\s+)?(async\s+)?\w+\s*\([^)]*\)\s*[:\{]"

        in_function = False
        function_start = 0
        function_name = "unknown"
        brace_count = 0

        for i, line in enumerate(lines):
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
                        mode = check_mode(
                            "max_function_lines_deep", module, config
                        )
                        violations.append({
                            "file": str(ts_file),
                            "module": module,
                            "severity": mode,
                            "detail": (
                                f"Função '{function_name}' tem {func_lines} linhas "
                                f"(max deep: {max_lines})"
                            ),
                            "fix": f"Extrair lógica para funções menores ou use cases separados",
                            "line_count": func_lines,
                        })
                    in_function = False

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "max_function_lines_deep",
        "label": "Max Function Lines (Deep)",
        "description": f"Funções não devem exceder {max_lines} linhas em nenhum módulo",
        "passed": passed,
        "blocked": blocked,
        "max_lines": max_lines,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 7. no-missing-validation ─────────────────────────────────────────────────

def check_no_missing_validation(config: dict, verbose: bool = False) -> dict:
    """Métodos create/update em services devem chamar validação explícita.

    Detecta métodos create*/update* que não chamam assertValid*, validate*, check*
    ou equivalentes.
    """
    violations = []

    validation_patterns = [
        r"\bassertValid\w*\s*\(",
        r"\bvalidate\w*\s*\(",
        r"\bcheck\w*\s*\(",
        r"\bguard\w*\s*\(",
        r"\bensure\w*\s*\(",
        r"\.validate\s*\(",
        r"\.isValid\b",
    ]

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        method_pattern = re.compile(
            r"^\s+(async\s+)?(public\s+)?(?:async\s+)?(create\w*|update\w*|save\w*)\s*\([^)]*\)"
        )

        in_method = False
        method_name = ""
        method_start = 0
        method_body = []
        brace_depth = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_method:
                m = method_pattern.match(line)
                if m:
                    method_name = m.group(3)
                    method_start = i
                    method_body = []
                    brace_depth = line.count("{") - line.count("}")
                    in_method = True
            else:
                brace_depth += line.count("{") - line.count("}")
                method_body.append(line)

                if brace_depth <= 0 and i > method_start:
                    body_text = "".join(method_body)
                    has_validation = any(
                        re.search(pat, body_text) for pat in validation_patterns
                    )

                    if not has_validation:
                        mode = check_mode("no_missing_validation", module, config)
                        violations.append({
                            "file": str(ts_file),
                            "module": module,
                            "severity": mode,
                            "detail": (
                                f"Método '{method_name}' (create/update) sem validação "
                                f"explícita na linha {method_start + 1}"
                            ),
                            "fix": (
                                f"Adicionar assertValid{method_name.replace('create', '').replace('update', '')} "
                                f"ou this.validate(input) no início do método"
                            ),
                            "line": method_start + 1,
                            "method": method_name,
                        })

                    in_method = False

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_missing_validation",
        "label": "No Missing Validation",
        "description": "Métodos create/update em services devem chamar validação explícita",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 8. no-pass-through ────────────────────────────────────────────────────────

def check_no_pass_through(config: dict, verbose: bool = False) -> dict:
    """Detecta métodos que apenas delegam sem adicionar lógica.

    Um pass-through é um método público que:
    1. Tem 1-3 linhas
    2. Contém apenas uma chamada a outro método (sem transformação, validação, logging)
    3. Não tem condicionais, loops, ou operações

    Estes métodos são indireção desnecessária — o caller pode chamar o delegate diretamente.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if not ts_file.name.endswith(
            (".service.ts", ".usecase.ts", ".repository.ts", ".controller.ts")
        ):
            continue

        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        lines = content.split("\n")

        method_pattern = re.compile(
            r"^\s+(async\s+)?(public\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\S+)?\s*\{"
        )

        in_method = False
        method_name = ""
        method_start = 0
        method_body = []
        brace_depth = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_method:
                m = method_pattern.match(line)
                if m:
                    # Skip constructor, getters, setters
                    func = m.group(3)
                    if func in ("constructor",) or func.startswith("get") or func.startswith("set"):
                        continue

                    method_name = func
                    method_start = i
                    method_body = []
                    brace_depth = line.count("{") - line.count("}")
                    in_method = True
            else:
                brace_depth += line.count("{") - line.count("}")
                method_body.append(line)

                if brace_depth <= 0 and i > method_start:
                    # Analisar corpo do método
                    effective = [
                        l.strip()
                        for l in method_body
                        if l.strip()
                        and not l.strip().startswith("//")
                        and not l.strip().startswith("/*")
                        and l.strip() not in ("{", "}", "};", "});")
                    ]

                    # Pass-through: 1-3 linhas efetivas, sem condicionais/loops
                    body_text = "\n".join(method_body)
                    has_logic = (
                        re.search(r"\bif\s*\(", body_text) or
                        re.search(r"\belse\b", body_text) or
                        re.search(r"\bfor\s*\(", body_text) or
                        re.search(r"\bwhile\s*\(", body_text) or
                        re.search(r"\bswitch\s*\(", body_text) or
                        re.search(r"\btry\s*\{", body_text) or
                        re.search(r"\bthrow\b", body_text) or
                        re.search(r"\breturn\s+\w+\.", body_text) is None
                    )

                    is_passthrough = (
                        len(effective) <= 3
                        and not has_logic
                        and re.search(r"\b(?:this\.\w+|repository\.|service\.)\w*\s*\(", body_text)
                    )

                    if is_passthrough:
                        mode = check_mode("no_pass_through", module, config)
                        violations.append({
                            "file": str(ts_file),
                            "module": module,
                            "severity": mode,
                            "detail": (
                                f"Método '{method_name}' é pass-through — "
                                f"apenas delega sem lógica adicional "
                                f"({len(effective)} linhas efetivas)"
                            ),
                            "fix": (
                                f"Remover '{method_name}' e expor o delegate diretamente. "
                                f"Se serve como facade, documentar justificativa com comentário."
                            ),
                            "line": method_start + 1,
                            "method": method_name,
                            "effective_lines": len(effective),
                        })

                    in_method = False

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_pass_through",
        "label": "No Pass-Through Methods",
        "description": "Métodos que apenas delegam sem lógica adicional são indireção desnecessária",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }
