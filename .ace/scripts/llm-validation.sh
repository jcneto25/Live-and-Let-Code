#!/bin/bash
# llm-validation.sh — Self-Validation pós-geração (Ação 8 do Harness Preventivo LLC §2.8)
#
# Propósito: o agente executa este script ANTES de reportar uma task como concluída.
# Também é chamado pelo pre-commit hook (ace-llm-validation) como barreira local.
#
# 8 verificações:
#   1. Hardcoded secrets (JWT, API keys)          ❌ block
#   2. SQL com template literals (injection)       ❌ block
#   3. return null em services                     ❌ block
#   4. SQL fora de repositories                    ❌ block
#   5. Placeholder tests (expect(true).toBe(true)) ❌ block
#   6. Hardcoded delays em testes (setTimeout)     ⚠️  warn
#   7. any em public signatures                    ⚠️  warn
#   8. console.log/console.error (usar logger)     ⚠️  warn
#
# Exit 1 se houver qualquer bloqueio (❌). Exit 0 se só houver advertências (⚠️).
#
# Uso:
#   bash .ace/scripts/llm-validation.sh                 # arquivos staged (default)
#   bash .ace/scripts/llm-validation.sh src/a.ts src/b.ts  # arquivos explícitos
#   bash .ace/scripts/llm-validation.sh --all           # varre todo src/ (ou cwd)

set -uo pipefail

ERRORS=0
WARNINGS=0

# ── Seleção de arquivos ──────────────────────────────────────────────────────
FILES=""
if [ "${1:-}" = "--all" ]; then
  SCAN_ROOT="src"
  [ -d "$SCAN_ROOT" ] || SCAN_ROOT="."
  FILES=$(find "$SCAN_ROOT" -type f \
    \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" \) \
    2>/dev/null | grep -vE "node_modules|__pycache__|/vendor/|/.git/" || true)
elif [ "$#" -gt 0 ]; then
  FILES="$*"
else
  # staged; se vazio, cai para modificados vs HEAD + untracked
  FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
  if [ -z "$FILES" ]; then
    FILES=$(
      { git diff --name-only HEAD 2>/dev/null;
        git ls-files --others --exclude-standard 2>/dev/null; } | sort -u || true
    )
  fi
fi

# Helpers de classificação de arquivo
is_source()   { echo "$1" | grep -qE "\.(ts|tsx|js|jsx|py|go)$"; }
is_test()     { echo "$1" | grep -qE "\.(test|spec)\.(ts|tsx|js|jsx)$|test_.*\.py$|.*_test\.(py|go)$"; }
is_excluded() { echo "$1" | grep -qE "node_modules|__pycache__|/vendor/|\.git/|/mock|\.mock\.|/example|\.env\.example"; }
is_repository() { echo "$1" | grep -qiE "repositor(y|ies)|/persistence/|\.repo\.|repository\."; }

report_block() { echo "❌ [$1] $2"; ERRORS=$((ERRORS + 1)); }
report_warn()  { echo "⚠️  [$1] $2"; WARNINGS=$((WARNINGS + 1)); }

# Lê a versão do arquivo no working tree (validação pós-geração, pré-stage)
read_file() { cat "$1" 2>/dev/null || true; }

echo "🤖 LLM Self-Validation — verificando código gerado..."
echo ""

if [ -z "$FILES" ]; then
  echo "   Nenhum arquivo para validar (working tree limpo)."
  echo "✅ LLM Self-Validation: nada a verificar."
  exit 0
fi

# ── Patterns ─────────────────────────────────────────────────────────────────
SECRET_PATTERNS=(
  "sk-[0-9a-zA-Z]{20,}"
  "sk-proj-[0-9a-zA-Z]{20,}"
  "ghp_[0-9a-zA-Z]{36}"
  "AIza[0-9A-Za-z_-]{35}"
  "SG\.[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+"
  "JWT_SECRET\s*=\s*['\"][^'\"]{8,}['\"]"
  "jwt_secret\s*=\s*['\"][^'\"]{8,}['\"]"
  "SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]"
  "api[_-]?key\s*=\s*['\"][^'\"]{8,}['\"]"
  "password\s*=\s*['\"][^'\"]{1,}['\"]"
  "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY"
)

# SQL com interpolação (template literal ${...} ou concatenação) contendo verbo SQL
SQL_INJECTION_PATTERN="(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*(\\\$\{|['\"]\s*\+)"
# Qualquer SQL cru (para o check 4 — SQL fora de repository)
SQL_ANY_PATTERN="(query|execute|raw|\\\$queryRaw|\\\$executeRaw)\s*\(.*(SELECT|INSERT|UPDATE|DELETE)"

for file in $FILES; do
  [ -z "$file" ] && continue
  [ -f "$file" ] || continue
  is_source "$file" || continue
  is_excluded "$file" && continue

  CONTENT=$(read_file "$file")
  [ -z "$CONTENT" ] && continue

  # ── 1. Hardcoded secrets (não em testes/mocks/example) ─────────────────────
  if ! is_test "$file"; then
    for pattern in "${SECRET_PATTERNS[@]}"; do
      MATCHES=$(echo "$CONTENT" | grep -nE "$pattern" 2>/dev/null || true)
      if [ -n "$MATCHES" ]; then
        LINE_NUM=$(echo "$MATCHES" | head -1 | cut -d: -f1)
        report_block "secrets" "$file:$LINE_NUM — secret hardcoded (use env var / secrets manager)"
      fi
    done
  fi

  # ── 2. SQL com template literals (possível injection) ──────────────────────
  SQL_INJ=$(echo "$CONTENT" | grep -nE "$SQL_INJECTION_PATTERN" 2>/dev/null || true)
  if [ -n "$SQL_INJ" ]; then
    LINE_NUM=$(echo "$SQL_INJ" | head -1 | cut -d: -f1)
    report_block "sql-injection" "$file:$LINE_NUM — SQL com interpolação (use parâmetros ? / prepared statements)"
  fi

  # ── 3. return null em services ─────────────────────────────────────────────
  if echo "$file" | grep -qiE "service|use-case|usecase"; then
    NULL_RET=$(echo "$CONTENT" | grep -nE "return\s+null\s*;?" 2>/dev/null || true)
    if [ -n "$NULL_RET" ]; then
      LINE_NUM=$(echo "$NULL_RET" | head -1 | cut -d: -f1)
      report_block "null-return" "$file:$LINE_NUM — return null em service (use Result<T,E> / Optional / throw)"
    fi
  fi

  # ── 4. SQL fora de repositories ────────────────────────────────────────────
  if ! is_repository "$file" && ! is_test "$file"; then
    SQL_RAW=$(echo "$CONTENT" | grep -nE "$SQL_ANY_PATTERN" 2>/dev/null || true)
    if [ -n "$SQL_RAW" ]; then
      LINE_NUM=$(echo "$SQL_RAW" | head -1 | cut -d: -f1)
      report_block "sql-outside-repo" "$file:$LINE_NUM — SQL fora de repository (mova acesso a dados para a camada de persistência)"
    fi
  fi

  # ── 5. Placeholder tests ───────────────────────────────────────────────────
  if is_test "$file"; then
    PLACEHOLDER=$(echo "$CONTENT" | grep -nE "expect\s*\(\s*true\s*\)\s*\.\s*toBe\s*\(\s*true\s*\)|expect\s*\(\s*1\s*\)\s*\.\s*toBe\s*\(\s*1\s*\)" 2>/dev/null || true)
    if [ -n "$PLACEHOLDER" ]; then
      LINE_NUM=$(echo "$PLACEHOLDER" | head -1 | cut -d: -f1)
      report_block "placeholder-test" "$file:$LINE_NUM — teste placeholder (expect(true).toBe(true)) — escreva asserção real"
    fi
  fi

  # ── 6. Hardcoded delays em testes ──────────────────────────────────────────
  if is_test "$file"; then
    DELAY=$(echo "$CONTENT" | grep -nE "setTimeout\s*\(|setInterval\s*\(|sleep\s*\(" 2>/dev/null || true)
    if [ -n "$DELAY" ]; then
      LINE_NUM=$(echo "$DELAY" | head -1 | cut -d: -f1)
      report_warn "test-delay" "$file:$LINE_NUM — delay hardcoded em teste (use waitFor() / findBy*)"
    fi
  fi

  # ── 7. any em public signatures ────────────────────────────────────────────
  if echo "$file" | grep -qE "\.(ts|tsx)$" && ! is_test "$file"; then
    ANY_SIG=$(echo "$CONTENT" | grep -vE "^[[:space:]]*(//|\*)" | grep -nE ":\s*any\b|<any>|\bas any\b" 2>/dev/null || true)
    if [ -n "$ANY_SIG" ]; then
      LINE_NUM=$(echo "$ANY_SIG" | head -1 | cut -d: -f1)
      report_warn "any-in-public" "$file:$LINE_NUM — 'any' em signature pública (use tipo explícito / unknown)"
    fi
  fi

  # ── 8. console.log/console.error (usar logger) ─────────────────────────────
  if ! is_test "$file"; then
    CONSOLE=$(echo "$CONTENT" | grep -nE "console\.(log|error|warn|info|debug)\s*\(" 2>/dev/null || true)
    if [ -n "$CONSOLE" ]; then
      LINE_NUM=$(echo "$CONSOLE" | head -1 | cut -d: -f1)
      report_warn "console-log" "$file:$LINE_NUM — console.* em código de produção (use logger estruturado)"
    fi
  fi
done

# ── Resultado ────────────────────────────────────────────────────────────────
echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "❌ LLM Self-Validation FALHOU: $ERRORS bloqueio(s), $WARNINGS advertência(s)."
  echo ""
  echo "   Bloqueios (❌) DEVEM ser corrigidos antes de reportar a task como concluída."
  echo "   Advertências (⚠️) devem ser corrigidas ou registradas em dívida técnica."
  echo "   Override emergencial (só falsos positivos documentados): git commit --no-verify"
  exit 1
fi

if [ "$WARNINGS" -gt 0 ]; then
  echo "🟡 LLM Self-Validation passou com $WARNINGS advertência(s)."
  echo "   Corrija ou registre as advertências em dívida técnica antes do merge."
else
  echo "✅ LLM Self-Validation passou — sem bloqueios, sem advertências."
fi

exit 0
