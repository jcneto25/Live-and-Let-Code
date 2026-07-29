#!/usr/bin/env python3
"""Checks de Segurança (secrets, SQL injection, AsyncStorage, client-only auth, user_id).

Estes 5 checks implementam as Fitness Functions de Segurança do Step 5d
(Secure-by-Design), executadas via `fitness-functions.py --check-security`.

Ref: Harness Preventivo LLC §2.1 — Ação 1 (Skill llc-step-5d-secure-by-design §4).
"""

import re
from pathlib import Path

from .config import SRC_DIR, check_mode
from .helpers import find_ts_files, module_name_from_path, read_file_safe

# Diretórios/arquivos onde secrets e padrões inseguros são tolerados (fixtures)
_EXCLUDED_PARTS = {
    "test", "tests", "__tests__", "spec", "specs",
    "mock", "mocks", "example", "examples", "fixtures",
}


def _is_excluded(path: Path) -> bool:
    if any(part.lower() in _EXCLUDED_PARTS for part in path.parts):
        return True
    name = path.name.lower()
    return ".test." in name or ".spec." in name or name == ".env.example"


# ── 1. no-hardcoded-secrets ──────────────────────────────────────────────────

_SECRET_PATTERNS = [
    (re.compile(r"JWT_SECRET\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE), "JWT secret"),
    (re.compile(r"SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE), "secret key"),
    (re.compile(r"sk-[0-9a-zA-Z]{20,}"), "OpenAI API key"),
    (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub token"),
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "Google API key"),
    (re.compile(r"private[_-]?key\s*=\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE), "private key"),
    (re.compile(r"api[_-]?key\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE), "API key"),
    (re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "password"),
]


def check_no_hardcoded_secrets(config: dict, verbose: bool = False) -> dict:
    """Detecta secrets hardcoded (JWT, API keys, passwords) no código fonte.

    Exceção: arquivos de teste/mock/example e .env.example.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            for pattern, kind in _SECRET_PATTERNS:
                if pattern.search(line):
                    mode = check_mode("no_hardcoded_secrets", module, config)
                    violations.append({
                        "file": str(ts_file),
                        "module": module,
                        "severity": mode,
                        "detail": f"Possível {kind} hardcoded na linha {i + 1}",
                        "fix": (
                            "Derivar de process.env / secrets manager / "
                            "SecureStore (mobile). Nunca commitar o valor real."
                        ),
                        "line": i + 1,
                    })
                    break  # 1 violação por linha basta

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_hardcoded_secrets",
        "label": "No Hardcoded Secrets",
        "description": "Secrets/keys/passwords devem vir de env vars ou secrets manager",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 2. no-sql-injection ──────────────────────────────────────────────────────

_SQL_INJECTION_PATTERNS = [
    re.compile(r"`\s*(SELECT|INSERT|UPDATE|DELETE)\s.*\$\{"),
    re.compile(r"`\s*(SELECT|INSERT|UPDATE|DELETE)\s.*\+\s*[a-zA-Z]"),
]


def check_no_sql_injection(config: dict, verbose: bool = False) -> dict:
    """Detecta SQL montado com template literals/concat (possível injection).

    Queries devem usar parâmetros (?). Interpolação só é tolerada em
    repositories (onde o padrão parametrizado é verificado por review).
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        if "repositories" in {p.lower() for p in ts_file.parts}:
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if any(p.search(line) for p in _SQL_INJECTION_PATTERNS):
                mode = check_mode("no_sql_injection", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"SQL com interpolação na linha {i + 1}: {stripped[:80]}",
                    "fix": "Usar query parametrizada: db.query('... WHERE id = ?', [id])",
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_sql_injection",
        "label": "No SQL Injection",
        "description": "SQL não deve interpolar valores — usar parâmetros (?)",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 3. no-asyncstorage-tokens ────────────────────────────────────────────────

_ASYNCSTORAGE_SENSITIVE = re.compile(
    r"AsyncStorage\s*\.\s*(setItem|getItem)\s*\([^)]*"
    r"(token|secret|password|passwd|credential|jwt|api[_-]?key|auth)",
    re.IGNORECASE,
)


def check_no_asyncstorage_tokens(config: dict, verbose: bool = False) -> dict:
    """Detecta dados sensíveis (tokens, secrets) em AsyncStorage.

    AsyncStorage é plaintext — dados sensíveis exigem SecureStore/Keychain.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            if _ASYNCSTORAGE_SENSITIVE.search(line):
                mode = check_mode("no_asyncstorage_tokens", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Dado sensível em AsyncStorage na linha {i + 1}",
                    "fix": "Usar expo-secure-store / Keychain (iOS) / Keystore (Android)",
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_asyncstorage_tokens",
        "label": "No AsyncStorage Tokens",
        "description": "Tokens/secrets não devem ir para AsyncStorage — usar SecureStore/Keychain",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 4. no-client-only-auth ───────────────────────────────────────────────────

_ENTITLEMENT_STATE = re.compile(r"(?i)(premium|entitle|subscri|\bisPro\b)")
_BACKEND_INDICATORS = re.compile(
    r"(?i)(api\s*\.|fetch\s*\(|axios|https?:|supabase|firebase|firestore|"
    r"graphql|trpc|Purchases\s*\.|getCustomerInfo|backend)"
)


def check_no_client_only_auth(config: dict, verbose: bool = False) -> dict:
    """Heurística: entitlement/premium mantido só em estado local do client.

    Componentes (.tsx) com useState de premium/entitlement sem nenhuma
    chamada a backend no arquivo — backend deve ser a fonte de verdade.
    """
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if ts_file.suffix != ".tsx" or _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        if "useState" not in content:
            continue
        if not _ENTITLEMENT_STATE.search(content):
            continue
        if _BACKEND_INDICATORS.search(content):
            continue

        mode = check_mode("no_client_only_auth", module, config)
        violations.append({
            "file": str(ts_file),
            "module": module,
            "severity": mode,
            "detail": (
                "Estado de entitlement/premium sem chamada backend no arquivo — "
                "validação apenas no client"
            ),
            "fix": "Validar entitlements no backend (fonte de verdade) e refletir no client",
        })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_client_only_auth",
        "label": "No Client-Only Auth",
        "description": "Entitlements/premium não podem ser validados apenas no client",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 5. user-id-in-tables ─────────────────────────────────────────────────────

# Tabelas de sistema/lookup e a própria tabela de usuários — isentas
_SYSTEM_TABLES = {
    "users", "user", "accounts", "account", "tenants", "tenant",
    "migrations", "schema_migrations", "_prisma_migrations",
    "sequelize_meta", "knex_migrations", "knex_migrations_lock",
    "roles", "permissions", "role_permissions", "settings", "config",
    "configurations", "translations", "plans", "features", "feature_flags",
}
_EXEMPT_PRISMA_MODELS = {
    "user", "account", "tenant", "role", "permission",
    "migration", "setting", "config", "plan", "feature",
}
_OWNERSHIP_COLUMNS = re.compile(
    r"(?i)\b(user_?id|owner_?id|tenant_?id|account_?id|created_?by)\b"
)
_SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".ace", "coverage"}


def _schema_files() -> list[Path]:
    files = []
    for pattern in ("*.sql", "*.prisma"):
        for path in Path(".").rglob(pattern):
            if any(part.lower() in _SKIP_DIRS for part in path.parts):
                continue
            if _is_excluded(path):
                continue
            files.append(path)
    return files


def check_user_id_in_tables(config: dict, verbose: bool = False) -> dict:
    """Tabelas/modelos de domínio devem ter coluna de ownership (user_id/owner_id).

    Varre migrations SQL (CREATE TABLE) e schemas Prisma (model). Tabelas de
    sistema (migrations, roles, settings...) e a tabela de usuários são isentas.
    """
    violations = []

    def _add(path: Path, kind: str, name: str):
        module = module_name_from_path(path) or ""
        mode = check_mode("user_id_in_tables", module, config)
        violations.append({
            "file": str(path),
            "module": module or path.parts[0] if path.parts else "",
            "severity": mode,
            "detail": f"{kind} '{name}' sem coluna user_id/owner_id — isolamento por dono ausente",
            "fix": f"Adicionar user_id/owner_id (FK) a '{name}' ou isentar em arch-config.yaml",
        })

    for path in _schema_files():
        content = read_file_safe(path)

        if path.suffix == ".sql":
            for m in re.finditer(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?\s*\(([^;]*?)\)\s*;",
                content,
                re.IGNORECASE | re.DOTALL,
            ):
                table, body = m.group(1), m.group(2)
                if table.lower() in _SYSTEM_TABLES:
                    continue
                if not _OWNERSHIP_COLUMNS.search(body):
                    _add(path, "Tabela", table)

        elif path.suffix == ".prisma":
            for m in re.finditer(r"model\s+(\w+)\s*\{([^}]*)\}", content):
                model, body = m.group(1), m.group(2)
                if model.lower() in _EXEMPT_PRISMA_MODELS:
                    continue
                if not _OWNERSHIP_COLUMNS.search(body):
                    _add(path, "Model Prisma", model)

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "user_id_in_tables",
        "label": "User ID in Tables",
        "description": "Tabelas de domínio devem ter user_id/owner_id (isolamento por dono)",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }
