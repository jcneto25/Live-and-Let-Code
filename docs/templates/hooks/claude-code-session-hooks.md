# Snippet — Hooks do Claude Code para Registro Garantido de Sessões ACE

**Propósito:** garantir que toda edição de código aconteça dentro de uma sessão ACE
aberta, **independentemente de o agente "lembrar"** de abrir a sessão.

> **Framing importante:** o mecanismo **tool-agnostic** que realmente garante o
> registro no `.ace` é o **pre-commit do git** (`.ace/scripts/pre-commit.sh` +
> `validate-tags.py --coverage`) — o git o executa não importa qual cliente de IA
> fez o commit. Os hooks abaixo são **por cliente (Claude Code)**: oferecem
> enforcement/UX *durante* a sessão, antes do commit. Use os dois em camadas.

## Pré-requisitos (no projeto-alvo)

- `.ace/scripts/` com `initialize_session.py`, `finalize_session.py`, `validate-tags.py`, `llc.py`.
- `jq` instalado (leitura do `.ace/index.json`).
- Pre-commit do git instalado: `cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`
  (ou `pre-commit install` se usar o framework).

---

## Snippet A — Guarda PreToolUse (recomendado)

Bloqueia `Edit`/`Write`/`MultiEdit` quando **não há sessão `in_progress`**. Esta é a
camada que previne diretamente o modo de falha "onda executada sem sessão": o agente
simplesmente não consegue editar código sem antes abrir a sessão.

**1. Wrapper** — copie `require-ace-session.sh` (ao lado deste arquivo) para o projeto-alvo:

```bash
mkdir -p .ace/scripts/hooks
cp docs/templates/hooks/require-ace-session.sh .ace/scripts/hooks/require-ace-session.sh
chmod +x .ace/scripts/hooks/require-ace-session.sh
```

**2. Registre em `.claude/settings.json`** (projeto) ou `~/.claude/settings.json` (usuário):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .ace/scripts/hooks/require-ace-session.sh"
          }
        ]
      }
    ]
  }
}
```

Com isso, qualquer tentativa de editar código sem uma sessão `in_progress` é negada
pelo harness do Claude Code, com a mensagem instruindo o agente a abrir a sessão.

---

## Snippet B — Auto-abrir sessão no SessionStart (opcional, conveniência)

Abre automaticamente uma sessão ao iniciar a conversa, para que o agente já comece
"dentro" do ciclo ACE. `--step`/`--task` vem de variáveis de ambiente ou de defaults.

`.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .ace/scripts/initialize_session.py --step ${LLC_STEP:-11} --task \"${LLC_TASK:-auto}\" --json"
          }
        ]
      }
    ]
  }
}
```

> **Não** automatize o `finalize_session.py` em `Stop`: esse evento dispara a cada
> parada do agente (incluindo meio da conversa), fechando sessões prematuramente.
> Mantenha o `finalize` explícito ao fim real do trabalho, ou confie no gate do
> pre-commit para garantir o registro.

---

## Instalação rápida (resumo)

```bash
# 1. Wrapper de guarda (Snippet A)
mkdir -p .ace/scripts/hooks
cp docs/templates/hooks/require-ace-session.sh .ace/scripts/hooks/
chmod +x .ace/scripts/hooks/require-ace-session.sh

# 2. Registrar hook(s) em .claude/settings.json (cole o JSON acima)

# 3. Garantia tool-agnostic (pre-commit do git)
cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#   ou: pre-commit install
```

---

## Caveats

- **Schema de hooks do Claude Code evolui.** O mecanismo de bloqueio via **exit code 2**
  (`require-ace-session.sh`) é a forma estável; a forma JSON (`permissionDecision: deny`)
  também existe, mas verifique o schema corrente na documentação do Claude Code da sua versão.
- **Bypass:** hooks de cliente podem ser desabilitados pelo usuário. A camada que não pode
  ser "esquecida" é o pre-commit do git (contornável só com `git commit --no-verify`).
- **`.claude/` é per-clone** (gitignore do LLC). Ajuste o wrapper para um path versionado
  (`.ace/scripts/hooks/`) e referencie-o a partir do `.claude/settings.json`.
- **Outros clientes (Codex, Cursor, opencode):** cada um tem seu mecanismo de hook/automação
  equivalente. O contrato é o mesmo — "exigir sessão ACE antes de editar/commitar código" —
  expresso em `AGENTS.md`. O pre-commit do git cobre todos.
