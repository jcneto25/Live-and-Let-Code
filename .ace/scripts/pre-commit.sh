#!/bin/bash
# ACE Pre-Commit Hook — Valida integridade do histórico de sessões
# Instalação manual: cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
# Instalação via pre-commit: pre-commit install (usa .pre-commit-config.yaml)

set -e

ACE_DIR=".ace"
INDEX="$ACE_DIR/index.json"
SESSIONS="$ACE_DIR/sessions"
ERRORS=0

echo "🔍 Validando integridade ACE..."

# 0. Cobertura de sessão (garantia de registro no .ace)
#    Commit com código exige sessão ACE registrada — previne trabalho feito fora do
#    ciclo init→finalize (ex.: onda de scaffolding executada "direto"). Tool-agnostic:
#    o git roda este hook independente do cliente de IA que fez o commit.
echo "🔒 Verificando cobertura de sessão ACE..."
if python .ace/scripts/validate-tags.py --coverage; then
  echo "✅ Cobertura de sessão OK"
else
  echo ""
  echo "❌ Commit bloqueado: há código no commit sem sessão ACE correspondente."
  echo "   Enrole o trabalho numa sessão antes de commitar:"
  echo "     python .ace/scripts/initialize_session.py --step N --task \"...\""
  echo "   ...ou use o harness (tool-agnostic):"
  echo "     python .ace/scripts/llc.py run --step N"
  echo "   Override emergencial: git commit --no-verify (NÃO recomendado)."
  exit 1
fi

# 1. Verificar se index.json existe e é JSON válido
if [ ! -f "$INDEX" ]; then
  echo "⚠️  $INDEX não encontrado — pulando validação (primeira execução?)"
  exit 0
fi

if ! jq empty "$INDEX" 2>/dev/null; then
  echo "❌ $INDEX não é JSON válido"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ $INDEX — JSON válido"
fi

# 2. Verificar se todas as sessões do índice existem em disco
for session_file in $(jq -r '.sessions[].file' "$INDEX" 2>/dev/null); do
  if [ ! -f "$SESSIONS/$session_file" ]; then
    echo "❌ $session_file listado no índice mas não encontrado em $SESSIONS/"
    ERRORS=$((ERRORS + 1))
  fi
done

# 3. Verificar se todos os arquivos no diretório estão no índice
for md_file in "$SESSIONS"/*.md; do
  [ -f "$md_file" ] || continue
  filename=$(basename "$md_file")
  if ! jq -e --arg f "$filename" '.sessions[] | select(.file == $f)' "$INDEX" > /dev/null 2>&1; then
    echo "❌ $filename existe em $SESSIONS/ mas não está em $INDEX"
    ERRORS=$((ERRORS + 1))
  fi
done

# 4. Verificar context_seed em sessões completed
for session_file in "$SESSIONS"/*.md; do
  [ -f "$session_file" ] || continue
  filename=$(basename "$session_file")
  
  status=$(jq -r --arg f "$filename" '.sessions[] | select(.file == $f) | .status' "$INDEX" 2>/dev/null)
  
  if [ "$status" = "completed" ]; then
    if ! grep -q "<context_seed>" "$session_file"; then
      echo "❌ $filename — status=completed mas sem <context_seed>"
      ERRORS=$((ERRORS + 1))
    else
      # Verificar campos obrigatórios no context_seed
      for field in state pending blockers next_action; do
        if ! grep -A10 "<context_seed>" "$session_file" | grep -q "^$field:"; then
          echo "❌ $filename — <context_seed> sem campo obrigatório '$field'"
          ERRORS=$((ERRORS + 1))
        fi
      done
    fi
  fi
done

# 5. Verificar balanceamento de tags XML
for session_file in "$SESSIONS"/*.md; do
  [ -f "$session_file" ] || continue
  filename=$(basename "$session_file")
  
  for tag in action action_log thinking learning_point gate_result blocker context_seed; do
    open_count=$(grep -c "<$tag" "$session_file" 2>/dev/null || echo 0)
    close_count=$(grep -c "</$tag>" "$session_file" 2>/dev/null || echo 0)
    
    if [ "$open_count" -ne "$close_count" ]; then
      echo "❌ $filename — tags <$tag> desbalanceadas (abre: $open_count, fecha: $close_count)"
      ERRORS=$((ERRORS + 1))
    fi
  done
done

# 6. Análise de impacto nos artefatos LLC (informativo — não bloqueia)
echo ""
echo "📊 Analisando impacto nos artefatos LLC..."
python .ace/scripts/impact-analyzer.py --staged --json 2>/dev/null && echo "✅ Análise de impacto concluída" || echo "⚠️  Impact analyzer não executou (verifique PyYAML)"

# 7. Fitness Functions — verificação arquitetural (alerta informativo — não bloqueia)
echo ""
echo "🏗️  Verificando conformidade arquitetural (fitness functions)..."
if [ -f ".ace/scripts/fitness-functions.py" ]; then
  python .ace/scripts/fitness-functions.py --all --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data['summary']['total']
passed = data['summary']['passed']
blocked = data['summary']['blocked']
print(f'   Fitness: {passed}/{total} checks passaram' + (' 🔴 BLOQUEIO' if blocked else ''))
" 2>/dev/null || echo "⚠️  Fitness functions não executou (verifique dependências)"
else
  echo "⚠️  fitness-functions.py não encontrado — pulando"
fi

# 8. Secret Scanning — detecção de secrets hardcoded (Ação 5a — Harness Preventivo LLC §2.5)
echo ""
echo "🔐 Verificando secrets hardcoded nos arquivos staged..."
SECRET_ERRORS=0

# Patterns de secrets (regex POSIX extended — compatível com grep -E)
# Cada pattern cobre um tipo específico de secret comum
SECRET_PATTERNS=(
  "sk-[0-9a-zA-Z]{20,}"                          # OpenAI API key
  "sk-proj-[0-9a-zA-Z]{20,}"                      # OpenAI project key
  "ghp_[0-9a-zA-Z]{36}"                           # GitHub personal access token (classic)
  "gho_[0-9a-zA-Z]{36}"                           # GitHub OAuth token
  "ghu_[0-9a-zA-Z]{36}"                           # GitHub user-to-server token
  "ghs_[0-9a-zA-Z]{36}"                           # GitHub server-to-server token
  "ghr_[0-9a-zA-Z]{36}"                           # GitHub refresh token
  "AIza[0-9A-Za-z_-]{35}"                        # Google API key
  "SG\.[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+"           # SendGrid API key
  "JWT_SECRET\s*=\s*['\"][^'\"]{8,}['\"]"        # JWT secret assignment
  "jwt_secret\s*=\s*['\"][^'\"]{8,}['\"]"        # JWT secret (lowercase)
  "SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]"         # Django/similar secret key
  "secret_key\s*=\s*['\"][^'\"]{8,}['\"]"         # secret key (lowercase)
  "private\s*.*key.*=\s*['\"][^'\"]{10,}['\"]"    # Private key assignment
  "api[_-]?key\s*=\s*['\"][^'\"]{8,}['\"]"        # API key assignment (api_key, api-key, apikey)
  "password\s*=\s*['\"][^'\"]{1,}['\"]"           # Password assignment (não .env.example)
  "DATABASE_URL\s*=\s*['\"][^'\"]{10,}['\"]"      # Database URL with credentials
  "mongodb(\+srv)?://[^:]+:[^@]+@"                 # MongoDB URI with credentials
  "postgres://[^:]+:[^@]+@"                        # PostgreSQL URI with credentials
  "mysql://[^:]+:[^@]+@"                           # MySQL URI with credentials
  "redis://[^:]+:[^@]+@"                           # Redis URI with credentials
  "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY" # Private key block
)

# Arquivos/diretórios excluídos da varredura
SECRET_EXCLUDE=(
  "**/mock/**"
  "**/test/**"
  "**/spec/**"
  "**/example/**"
  "**/.env.example"
  "**/*.test.*"
  "**/*.spec.*"
  "**/*.mock.*"
  "**/node_modules/**"
  "**/vendor/**"
  "**/.git/**"
  "**/.ace/sessions/**"
  "**/__pycache__/**"
)

if [ -n "$STAGED_FILES_SECRET" ] || STAGED_FILES_SECRET=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null); then
  for file in $STAGED_FILES_SECRET; do
    [ -z "$file" ] && continue

    # Verificar exclusões
    EXCLUDED=0
    for exclude_pattern in "${SECRET_EXCLUDE[@]}"; do
      # Padrão simplificado — verificar substring no path
      clean_pattern=$(echo "$exclude_pattern" | sed 's/\*\*\///g' | sed 's/\*//g' | sed 's/\./\\\\./g')
      if echo "$file" | grep -qE "$clean_pattern" 2>/dev/null; then
        EXCLUDED=1
        break
      fi
    done
    [ "$EXCLUDED" -eq 1 ] && continue

    # Apenas arquivos de código fonte (não binários)
    if ! echo "$file" | grep -qE "\.(ts|tsx|js|jsx|py|go|rb|java|kt|swift|yaml|yml|json|toml|env|cfg|ini|sh|bash|zsh)$"; then
      continue
    fi

    for pattern in "${SECRET_PATTERNS[@]}"; do
      # Usar git show para ler versão staged
      MATCHES=$(git show ":$file" 2>/dev/null | grep -nE "$pattern" 2>/dev/null || true)
      if [ -n "$MATCHES" ]; then
        while IFS= read -r match_line; do
          LINE_NUM=$(echo "$match_line" | cut -d: -f1)
          # Sanitizar output (não mostrar o valor real do secret)
          SANITIZED=$(echo "$match_line" | cut -d: -f2- | sed 's/=.*/=****/g' | sed 's/:\/\/[^@]*@/:\/\/****@/g')
          echo "❌ Secret suspeito em $file:$LINE_NUM — $SANITIZED"
          SECRET_ERRORS=$((SECRET_ERRORS + 1))
        done <<< "$MATCHES"
      fi
    done
  done
else
  echo "   Nenhum arquivo staged — pulando"
fi

if [ "$SECRET_ERRORS" -gt 0 ]; then
  echo ""
  echo "🔴 $SECRET_ERRORS secret(s) suspeito(s) detectado(s)."
  echo "   Verifique se são secrets reais ou falsos positivos (ex: .env.example)."
  echo "   Secrets reais devem ser removidos e substituídos por variáveis de ambiente."
  echo "   Override: git commit --no-verify (apenas se forem falsos positivos documentados)."
  # Não bloqueia automaticamente — humano decide
  # Para bloquear, descomente: SECRET_ERRORS=0; ERRORS=$((ERRORS + 1))
else
  echo "✅ Nenhum secret detectado nos arquivos staged"
fi

# Resultado final
if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "❌ Validação ACE falhou com $ERRORS erro(s)."
  echo "   Corrija os problemas acima antes de commitar."
  echo "   Dica: use 'git commit --no-verify' para pular esta validação (não recomendado)."
  exit 1
fi

echo ""
echo "✅ Validação ACE passou — todas as verificações OK."
exit 0
