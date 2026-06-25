#!/usr/bin/env bash
# Claude Code PreToolUse hook — bloqueia Edit/Write/MultiEdit se não há sessão ACE aberta.
#
# Garantia por cliente (Claude Code). A garantia tool-agnostic continua sendo o
# pre-commit do git (.ace/scripts/pre-commit.sh). Este hook é cinto-e-suspensório:
# evita que o agente comece a editar código sem ter aberto uma sessão.
#
# Instalação (no projeto-alvo): copie para .ace/scripts/hooks/require-ace-session.sh
# e registre em .claude/settings.json — ver claude-code-session-hooks.md.
#
# Bloqueio: exit code 2 (Claude Code PreToolUse) + mensagem em stderr.
set -uo pipefail

INDEX=".ace/index.json"

active=0
if [ -f "$INDEX" ] && command -v jq >/dev/null 2>&1; then
  active=$(jq '[.sessions[]? | select(.status=="in_progress")] | length' "$INDEX" 2>/dev/null || echo 0)
fi

if [ "${active:-0}" -eq 0 ]; then
  cat >&2 <<'MSG'
❌ Edição bloqueada: nenhuma sessão ACE in_progress.
Abra uma sessão antes de tocar em código:
  python .ace/scripts/initialize_session.py --step N --task "..." --project <projeto>
ou pelo harness (tool-agnostic):
  python .ace/scripts/llc.py run --step N
MSG
  exit 2  # exit 2 = bloquear (Claude Code PreToolUse)
fi

exit 0
