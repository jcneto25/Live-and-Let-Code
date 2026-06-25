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
