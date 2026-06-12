---
name: llc-ace-context
description: Protocolo ACE de gestão de contexto entre sessões — append-only, delta incremental, anti-amnésia.
version: 1.0.0
tags: [ace, context, session, memory, anti-amnesia, llc-pipeline]
---

# LLC Skill: ACE Context Engineering

Gerencia o histórico de sessões do pipeline LLC com **append-only delta incremental**, garantindo continuidade de contexto sem reescrever arquivos.

## Quando usar

**Sempre.** Esta skill é transversal — ative no início de toda sessão LLC e execute o protocolo de encerramento ao final.

## Estrutura `.ace/`

```
.ace/
├── index.json                    # Índice leve (append de 1 linha por sessão)
├── sessions/                     # Arquivos de sessão (append-only)
│   └── YYYY-MM-DD-NNN.md
├── memory/
│   ├── learning_points.md        # Promovidos de <learning_point priority="high">
│   ├── skill_feedback.md        # Sugestões de melhoria de skills via <skill_feedback>
│   └── architecture.md           # ADRs consolidados
├── scripts/
│   ├── session-init.py           # Inicialização
│   ├── session-finalize.py       # Encerramento + context_seed
│   └── promote-learning.py       # Promoção para memory/
└── templates/
    └── session.template.md
```

## Taxonomia de Tags XML

| Tag | Função | Regra |
|-----|--------|-------|
| `<action_log>` | Container de ações | Append-only — nunca editar |
| `<action type="...">` | Ação atômica | `type`: `git_commit`, `file_create`, `file_modify`, `file_delete`, `test_run`, `tool_call` |
| `<file_delta>` | Arquivo afetado | Prefixo `@` opcional (`@auth/jwt.ts`) |
| `<thinking ref="...">` | Chain-of-thought | `ref` opcional referencia ID de action |
| `<learning_point priority="...">` | Conhecimento validado | `priority`: `high`, `medium`, `low` |
| `<gate_result>` | Decisão humana no gate LLC | `step`, `decision` (`approved`/`rejected`/`conditional`) |
| `<blocker resolved="...">` | Impedimento | `resolved`: `true` ou `false` |
| `<task_completed id="..." prp="..." status="...">` | Tarefa concluída | `id`: TASK-NNN, `prp`: PRP-NNN, `status`: `done`/`partial` |
| `<context_seed>` | Estado comprimido para próxima sessão | **Escrito apenas no encerramento** |
| `<skill_feedback skill="..." priority="...">` | Sugestão de melhoria para um skill LLC | `skill`: nome do skill, `priority`: `high`/`medium`/`low` |

---

## Mecanismo de Append (COMO fazer)

**O append é sempre via escrita no final do arquivo. NUNCA via leitura + reescrita.**

| Ferramenta | Comando de append |
|-----------|-------------------|
| Bash/PowerShell | `echo '</action>' >> .ace/sessions/2026-06-09-001.md` |
| Python | `with open(file, "a") as f: f.write("...")` |
| Node.js | `fs.appendFileSync(file, "...")` |
| LLM tool call | Ferramenta "append" no final do arquivo (NUNCA "write" ou "edit" que substitua) |

**Se a ferramenta da IA não tiver append nativo**, use:
- Bash: `cat >> file << 'EOF'` (heredoc com append)
- Se absolutamente necessário ler+escrever: leia o arquivo, concatene o delta no final, reescreva. Registre no `<thinking>` que usou read+write, não append puro.

---

## Protocolo de 4 Fases

### FASE 1 — Inicialização (obrigatório antes de qualquer ação)

**Passos do agente:**

1. Verifique se `.ace/index.json` existe. Se não, crie:
   ```json
   {"project": "{{project_name}}", "sessions": []}
   ```

2. Leia `index.json`. Localize a última sessão com `status: "completed"`.

3. Se houver sessão anterior, extraia o `<context_seed>` do final do arquivo:
   ```
   Busque a última ocorrência de <context_seed>...</context_seed> no arquivo.
   ```

4. Determine o ID da nova sessão:
   - Formato: `YYYY-MM-DD-NNN` (ex: `2026-06-09-001`)
   - NNN = número de sessões já criadas hoje + 1

5. Crie o novo arquivo `.ace/sessions/YYYY-MM-DD-NNN.md` com o template vazio e o `context_seed` da sessão anterior.

6. Adicione ao `index.json`:
   ```json
   {"session_id": "2026-06-09-001", "file": "2026-06-09-001.md", "status": "in_progress", "llc_step": 5, "tags": [], "timestamp": "2026-06-09T10:00:00Z"}
   ```
   **Modo de append seguro para index.json:**
   - Leia o JSON, modifique o array `sessions` em memória, reescreva o arquivo inteiro.
   - `index.json` é o ÚNICO arquivo que pode ser reescrito — é um índice, não um log.

7. Internalize o `context_seed` ANTES de qualquer tool call.

### FASE 2 — Execução (append de deltas conforme age)

**Para cada ação atômica, appenda ao final do arquivo de sessão:**

```
<action type="file_modify">
  <file_delta>src/auth/jwt.ts</file_delta>
  <description>Migração para HttpOnly cookies</description>
  <lines_changed>+34 -12</lines_changed>
</action>

<thinking ref="action-1">
  HttpOnly cookies não são acessíveis via document.cookie.
  Custo aceitável: requer CSRF token explícito.
</thinking>
```

**Regras de append:**
- ✅ Escrever cada `<action>` e `<thinking>` IMEDIATAMENTE após a ação — não acumular em buffer
- ✅ `<thinking>` é opcional — use apenas quando houver decisão não-óbvia
- ✅ `<learning_point>` quando descobrir algo generalizável
- ✅ `<task_completed>` ao concluir uma tarefa do TASKS.md — o `finalize_session.py` atualiza automaticamente os checkboxes
- ✅ `<skill_feedback>` ao final da sessão se o skill executado puder ser melhorado — sugestões são consolidadas em `memory/skill_feedback.md`
- ❌ **NUNCA editar `<action>` anteriores** — o histórico é imutável
- ❌ **NUNCA reordenar ações**
- ❌ **NUNCA deletar ações** — mesmo erradas, registre a correção como nova ação

### FASE 3 — Gate LLC

**Ao completar uma etapa (0-10), antes de prosseguir:**

```
<gate_result step="5" decision="approved" reviewer="humano">
  Implementação aprovada. Prosseguir para refresh token.
</gate_result>
```

- `decision`: `approved` | `rejected` | `conditional`
- `rejected` → registre `<blocker resolved="false">` descrevendo o motivo
- Só prossiga após `<gate_result decision="approved">`

### FASE 4 — Encerramento (obrigatório antes de fechar)

**Passos do agente:**

1. Gere o `<context_seed>` com 4 campos OBRIGATÓRIOS:

```
<context_seed>
state: middleware de auth refatorado para HttpOnly cookies. 14/14 testes passando.
pending: implementar endpoint /auth/refresh com validação de exp
blockers: nenhum ativo
next_action: criar src/auth/refresh.ts com lógica de refresh token
</context_seed>
```

Formato fixo: `field: valor` — um por linha. Campos obrigatórios: `state`, `pending`, `blockers`, `next_action`.

2. Appenda o `<context_seed>` ao FINAL do arquivo de sessão.

3. Atualize o front matter: mude `status` para `completed` e preencha `duration_min` e `files_touched`.

4. Atualize `index.json`: mude `status` da sessão para `completed`.

5. Promova `learning_points` de prioridade `high` para `.ace/memory/learning_points.md`.

6. Commit: `ace: session YYYY-MM-DD-NNN completed — Step N`

---

## Automação por Cliente de IA

Os scripts ACE são invocados como tool calls do agente. O padrão é sempre o mesmo: executar o script Python com `--json` e capturar a saída.

### Inicialização (primeira ação de toda sessão)

```
python .ace/scripts/initialize_session.py --step <N> --task "<descrição>" --project "<nome>" --json
```

Exemplos por cliente:

| Cliente | Como o agente executa |
|---------|----------------------|
| **Claude Code** | Bash tool: `python .ace/scripts/initialize_session.py --step 5 --task "Refatoração JWT" --json` |
| **opencode** | Bash tool com `workdir` no projeto |
| **Codex** | `run_shell_command` com o comando acima |
| **Cursor CLI** | Terminal integrado: mesmo comando |

A saída JSON contém `session_id`, `file`, `context_seed`, `llc_step`. O agente DEVE internalizar o `context_seed` antes de qualquer ação.

### Finalização (última ação de toda sessão)

```
python .ace/scripts/finalize_session.py --json
```

Se o agente quiser fornecer o próprio context_seed (recomendado — o agente sabe o que é relevante):

```
python .ace/scripts/finalize_session.py --context-seed "state: auth refatorado
pending: refresh token
blockers: nenhum
next_action: implementar /auth/refresh" --json
```

### Promoção de Learning Points (parte da finalização)

`finalize_session.py` já promove automaticamente. Para executar manualmente:

```
python .ace/scripts/promote-learning-points.py --all --json
```

### Revisão de Feedback de Skills (pós-sessão)

Sugestões de melhoria registradas com `<skill_feedback>` são consolidadas em `.ace/memory/skill_feedback.md`. Para revisar e dar baixa:

```
python .ace/scripts/promote-skill-feedback.py                    # Lista pendentes
python .ace/scripts/promote-skill-feedback.py --skill llc-step-5 # Filtra por skill
python .ace/scripts/promote-skill-feedback.py --mark applied --id 2026-06-10-001
python .ace/scripts/promote-skill-feedback.py --mark dismissed --id 2026-06-10-001
```

### Git Bisect Automatizado (debug de regressões)

```
python .ace/scripts/git-bisect.py --good HEAD~20 --bad HEAD --test "pytest tests/auth/" --json --ace-session 2026-06-10-001
```

Automatiza `git bisect run`: identifica o commit que introduziu a regressão e reporta o diff completo. Registra `<action type="git_bisect">` na sessão ACE quando `--ace-session` é informado.

### Mapa Estrutural do Codebase (grounding)

```
python .ace/scripts/code-map.py --include "src/**.ts" --max-files 50 --json
python .ace/scripts/code-map.py --signatures-only --json
```

Gera índice estrutural do projeto (árvore de arquivos, assinaturas de funções/classes, imports) para evitar alucinações de API. Ideal para carregar no início da sessão antes de gerar código. Use `--include` para filtrar por linguagem/segmento.

### Isolamento com Worktrees (automatico para sessoes de execucao)

```
python .ace/scripts/initialize_session.py --step 11 --task "PRP-001: Cadastro de Usuarios" --prp PRP-001 --wave 2 --json
```

O isolate via git worktree e **automatico** quando `--prp` e informado ou `step >= 11`. O script cria um diretorio isolado em `.ace/worktrees/{session_id}/` no branch `prp-{id}/wave-{n}`. O `finalize_session.py` faz merge automatico se o gate for `approved` ou descarta o worktree se `rejected`.

Para desativar o isolamento em sessoes especificas:
```
python .ace/scripts/initialize_session.py --step 11 --task "..." --prp PRP-001 --no-worktree --json
```

**Vantagens:**
- PRPs em paralelo sem colisao de arquivos (cada agente em seu diretorio fisico)
- `node_modules`, `dist/`, `.env` isolados por worktree — versoes diferentes de dependencias sem conflito
- Sem stash/sem perda de contexto ao alternar entre features
- Commits unificados — um unico `.git/` compartilhado entre todos os worktrees

### Validação (antes de commit — hook automático)

O pre-commit hook executa automaticamente. Para validar manualmente:

```
python .ace/scripts/validate-tags.py --strict --json
```

### Fluxo Completo em uma Sessão

```
1. Agente lê llc-ace-context skill
2. Agente executa: python .ace/scripts/initialize_session.py --step N --task "..." --json
3. Agente internaliza context_seed do JSON de saída
4. Agente trabalha (append de <action>, <thinking>, <gate_result>)
5. Agente executa: python .ace/scripts/finalize_session.py --context-seed "..." --json
6. Sessão concluída — index.json atualizado, learning points promovidos
```

---

## ⚠️ Regras de Ouro

### ✅ O agente FAZ

- Lê `index.json` + `context_seed` ao iniciar
- Cria novo arquivo de sessão em branco
- Appenda deltas via escrita no final do arquivo
- Registra `<gate_result>` a cada etapa
- Escreve `<context_seed>` com 4 campos no encerramento
- Atualiza `index.json` (reescrita permitida — é índice, não log)

### ❌ O agente NUNCA FAZ

- **Nunca** reescreve um arquivo de sessão existente
- **Nunca** edita `<action_log>` retroativamente
- **Nunca** deleta ações (erro se registra como nova ação de correção)
- **Nunca** pula o `context_seed` da sessão anterior
- **Nunca** encerra sem escrever `<context_seed>`

---

## Template de Sessão

Arquivo: `.ace/templates/session.template.md`

```markdown
---
session_id: "{{session_id}}"
llc_step: {{llc_step}}
project: "{{project}}"
prev_session: "{{prev_session_id}}"
---

## Contexto

{{#if prev_context_seed}}
<context_seed>
{{prev_context_seed}}
</context_seed>
{{else}}
Primeira sessão do projeto.
{{/if}}

## Ações

<action_log>
</action_log>

## Aprendizados

<!-- <learning_point priority="high">...</learning_point> -->

## Gates

<!-- <gate_result step="N" decision="approved" reviewer="...">...</gate_result> -->

## Bloqueadores

<!-- <blocker resolved="false">...</blocker> -->

## Encerramento

<context_seed>
state: [preencher no encerramento]
pending: [preencher no encerramento]
blockers: [preencher no encerramento]
next_action: [preencher no encerramento]
</context_seed>

---
status: completed
duration_min: {{duration}}
files_touched: []
```

**Nota sobre o footer:** Campos mutáveis (`status`, `duration_min`, `files_touched`) vão ao final, após o `<context_seed>`, separados por `---`. O front matter YAML no topo permanece imutável durante a sessão.

---

## `index.json` — Schema

```json
{
  "project": "string",
  "sessions": [
    {
      "session_id": "string (YYYY-MM-DD-NNN)",
      "file": "string (YYYY-MM-DD-NNN.md)",
      "status": "in_progress | completed | abandoned",
      "llc_step": "integer (0-10)",
      "tags": ["string"],
      "timestamp": "string (ISO 8601)"
    }
  ]
}
```

---

## Integração com Gates LLC

| Gate | Ação ACE |
|------|----------|
| 👤 1–11 | `<gate_result step="N" decision="approved/rejected" reviewer="...">` |
| 🔴 CHECKPOINT VISUAL | `<gate_result step="subflow-F4" decision="approved" reviewer="...">` |
| Rejeitado | `<blocker resolved="false">` + não avança |
| Aprovado | `<gate_result>` + prosseguir |

---

## Métricas de Saúde

| Métrica | Alvo | Verificação |
|---------|------|-------------|
| Sessões com `context_seed` | 100% | `grep -L '<context_seed>' .ace/sessions/*.md` |
| Sessões imutáveis | 0 reescritas | `git log --diff-filter=M -- .ace/sessions/` |
| `index.json` consistente | 100% | `jq empty .ace/index.json` |
| Tags balanceadas | 100% | `<action>` = `</action>` count |

---

## Referência

- Spec completa: `docs/superpowers/specs/YYYY-MM-DD-ace-context-design.md`
- Scripts: `.ace/scripts/`
- Exemplo de sessão: `.ace/sessions/2026-06-09-001.md`
