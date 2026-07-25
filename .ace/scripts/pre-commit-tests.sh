#!/bin/bash
# pre-commit-tests.sh — Test Gate & Quality Checks
# Ação 5b do Harness Preventivo LLC (§2.5)
# Instalação via pre-commit: configurado em .pre-commit-config.yaml (hook: test-gate)
# Execução manual: bash .ace/scripts/pre-commit-tests.sh

set -e

ERRORS=0
WARNINGS=0
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")

echo "🧪 Validando qualidade de testes..."

# ── 1. Detectar stack e adaptar comandos ────────────────────────────────────
detect_test_runner() {
  if [ -f "package.json" ]; then
    if grep -q '"jest"' package.json 2>/dev/null; then
      echo "jest"
    elif grep -q '"vitest"' package.json 2>/dev/null; then
      echo "vitest"
    else
      echo "npm"
    fi
  elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    echo "pytest"
  elif [ -f "go.mod" ]; then
    echo "go"
  else
    echo "unknown"
  fi
}

RUNNER=$(detect_test_runner)

# ── 2. Placeholder Detection ─────────────────────────────────────────────────
echo "🔍 Verificando placeholders em arquivos de teste..."

PLACEHOLDER_PATTERNS=(
  "expect\s*\(\s*true\s*\)\s*\.\s*toBe\s*\(\s*true\s*\)"   # expect(true).toBe(true)
  "expect\s*\(\s*1\s*\)\s*\.\s*toBe\s*\(\s*1\s*\)"           # expect(1).toBe(1)
  "expect\s*\(\s*null\s*\)\s*\.\s*toBe\s*\(\s*null\s*\)"     # expect(null).toBe(null)
  "it\s*\(\s*['\"][^'\"]*['\"]\s*\)"                         # it("desc") — empty callback
  "it\s*\(\s*['\"][^'\"]*['\"]\s*,\s*\)"                     # it("desc",) — trailing comma, no fn
  "test\s*\(\s*['\"][^'\"]*['\"]\s*,\s*\)"                   # test("desc",) — same
  "\.skip\s*\(\s*['\"]"                                       # it.skip / describe.skip sem TODO
)

for pattern in "${PLACEHOLDER_PATTERNS[@]}"; do
  if [ -n "$STAGED_FILES" ]; then
    for file in $STAGED_FILES; do
      # Apenas arquivos de teste
      if echo "$file" | grep -qE "\.(test|spec)\.(ts|tsx|js|jsx|py)$"; then
        if git show ":$file" 2>/dev/null | grep -nP "$pattern" 2>/dev/null; then
          echo "❌ Placeholder detectado em $file (pattern: $pattern)"
          ERRORS=$((ERRORS + 1))
        fi
      fi
    done
  fi
done

# Verificar it.skip sem TODO(#issue)
if [ -n "$STAGED_FILES" ]; then
  for file in $STAGED_FILES; do
    if echo "$file" | grep -qE "\.(test|spec)\.(ts|tsx|js|jsx)$"; then
      # Encontrar linhas com it.skip/test.skip/describe.skip sem TODO(#\d+) por perto
      SKIP_LINES=$(git show ":$file" 2>/dev/null | grep -nP "(it|test|describe)\.skip\s*\(" 2>/dev/null || true)
      if [ -n "$SKIP_LINES" ]; then
        while IFS= read -r skip_line; do
          LINE_NUM=$(echo "$skip_line" | cut -d: -f1)
          # Verificar se há TODO(#digito) nas próximas 2 linhas
          CONTEXT=$(git show ":$file" 2>/dev/null | sed -n "$((LINE_NUM)),$((LINE_NUM + 2))p")
          if ! echo "$CONTEXT" | grep -qP "TODO\s*\(\s*#\s*\d+\s*\)"; then
            echo "⚠️  it.skip sem TODO(#issue) em $file:$LINE_NUM"
            WARNINGS=$((WARNINGS + 1))
          fi
        done <<< "$SKIP_LINES"
      fi
    fi
  done
fi

# ── 3. Hardcoded Delay Detection ─────────────────────────────────────────────
echo "🔍 Verificando delays hardcoded em testes..."

DELAY_PATTERNS=(
  "setTimeout\s*\("           # setTimeout(
  "setInterval\s*\("          # setInterval(
  "sleep\s*\("                # sleep(
  "\.wait\s*\("               # .wait(
  "new Promise.*setTimeout"   # new Promise(r => setTimeout(r, ...))
)

for pattern in "${DELAY_PATTERNS[@]}"; do
  if [ -n "$STAGED_FILES" ]; then
    for file in $STAGED_FILES; do
      if echo "$file" | grep -qE "\.(test|spec)\.(ts|tsx|js|jsx|py)$"; then
        if git show ":$file" 2>/dev/null | grep -nP "$pattern" 2>/dev/null; then
          echo "⚠️  Delay hardcoded em $file (pattern: $pattern)"
          WARNINGS=$((WARNINGS + 1))
        fi
      fi
    done
  fi
done

# ── 4. Test Execution (stack-aware) ──────────────────────────────────────────
echo "🏃 Executando testes nos arquivos modificados..."

case "$RUNNER" in
  jest)
    if [ -n "$STAGED_FILES" ]; then
      TEST_FILES=$(echo "$STAGED_FILES" | grep -E "\.(test|spec)\.(ts|tsx|js|jsx)$" || true)
      if [ -n "$TEST_FILES" ]; then
        echo "   Jest — findRelatedTests (${TEST_FILES})..."
        npx jest --findRelatedTests $TEST_FILES --passWithNoTests --silent 2>&1 || {
          echo "❌ Testes Jest falharam nos arquivos modificados"
          ERRORS=$((ERRORS + 1))
        }
      else
        echo "   Nenhum arquivo de teste modificado — pulando execução"
      fi
    else
      echo "   Nenhum arquivo staged — pulando execução"
    fi
    ;;
  vitest)
    if [ -n "$STAGED_FILES" ]; then
      TEST_FILES=$(echo "$STAGED_FILES" | grep -E "\.(test|spec)\.(ts|tsx|js|jsx)$" || true)
      if [ -n "$TEST_FILES" ]; then
        echo "   Vitest — related tests..."
        npx vitest related $TEST_FILES --passWithNoTests --silent 2>&1 || {
          echo "❌ Testes Vitest falharam nos arquivos modificados"
          ERRORS=$((ERRORS + 1))
        }
      else
        echo "   Nenhum arquivo de teste modificado — pulando execução"
      fi
    else
      echo "   Nenhum arquivo staged — pulando execução"
    fi
    ;;
  pytest)
    if [ -n "$STAGED_FILES" ]; then
      TEST_FILES=$(echo "$STAGED_FILES" | grep -E "test_.*\.py|.*_test\.py$" || true)
      if [ -n "$TEST_FILES" ]; then
        echo "   Pytest..."
        python -m pytest $TEST_FILES -q 2>&1 || {
          echo "❌ Testes pytest falharam nos arquivos modificados"
          ERRORS=$((ERRORS + 1))
        }
      else
        echo "   Nenhum arquivo de teste modificado — pulando execução"
      fi
    else
      echo "   Nenhum arquivo staged — pulando execução"
    fi
    ;;
  go)
    if [ -n "$STAGED_FILES" ]; then
      TEST_FILES=$(echo "$STAGED_FILES" | grep -E "_test\.go$" || true)
      if [ -n "$TEST_FILES" ]; then
        echo "   go test..."
        go test ./... 2>&1 || {
          echo "❌ Testes Go falharam"
          ERRORS=$((ERRORS + 1))
        }
      else
        echo "   Nenhum arquivo de teste modificado — pulando execução"
      fi
    else
      echo "   Nenhum arquivo staged — pulando execução"
    fi
    ;;
  npm)
    echo "   Runner genérico (npm test)..."
    npm test 2>&1 || {
      echo "⚠️  npm test falhou — verifique"
      WARNINGS=$((WARNINGS + 1))
    }
    ;;
  *)
    echo "   Stack não detectada — pulando execução automática de testes"
    echo "   Adicione script de teste ao package.json/pyproject.toml/go.mod"
    ;;
esac

# ── 5. Resultado ─────────────────────────────────────────────────────────────
echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "❌ Test Gate falhou com $ERRORS erro(s)."
  echo ""
  echo "   Problemas encontrados:"
  echo "   - Placeholders (expect(true).toBe(true)) devem ser substituídos por asserções reais"
  echo "   - it.skip sem TODO(#issue) deve referenciar ticket com justificativa"
  echo "   - Testes falhando nos arquivos modificados"
  echo ""
  echo "   Corrija os problemas ou use --no-verify para bypass emergencial."
  exit 1
fi

if [ "$WARNINGS" -gt 0 ]; then
  echo "🟡 Test Gate passou com $WARNINGS alerta(s)."
  echo "   Delays hardcoded (setTimeout) devem ser substituídos por waitFor()/findBy*."
  echo "   Commit permitido — registre os alertas em dívida técnica."
else
  echo "✅ Test Gate passou — sem placeholders, sem delays, testes OK."
fi

exit 0
