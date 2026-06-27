---
name: llc-step-11
description: Pipeline LLC Step 11 — Execução dos PRPs. Implementa uma feature por PRP usando TDD estrito, registra deltas via ACE (<action>/<file_delta>), emite <task_completed> e gera <context_seed>. É a skill do step numérico 11 (execução), distinta de 11-security (gate pré-execução) e 11-owasp (hardening pós-código).
version: 1.0.0
tags: [execution, implementation, tdd, prp, ace, llc-pipeline]
---

# LLC Skill: Step 11 — Execução dos PRPs

**Pipeline:** Live and Let Code (LLC)
**Fase:** Implementation (Step 11)
**Depende de:** Step 3 (PRPs), Step 6 (TASKS.md), Step 9 (TESTING_GUIDE.md), Step 11-Security (gate pré-execução APROVADO), Step 12-Null-Safety (contratos de dados APROVADOS)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11` ou "Execute a skill llc-step-11".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 11 --prp PRP-001 --wave 1 --task "Implementar PRP-001"`.

## 📋 Pré-requisitos

- [ ] `docs/prps/PRP-*.md` — PRPs com **Definition of Done (DoD)**, lista de tarefas e especificação de testes (Step 3)
- [ ] `docs/planning/TASKS.md` — tarefas com IDs na coluna ID (Step 6)
- [ ] `docs/planning/EXECUTION_WAVES.md` — PRPs agrupados por onda (Step 4/6)
- [ ] `docs/testing/TESTING_GUIDE.md` — estratégia de testes e thresholds (Step 9)
- [ ] `docs/security/SECURITY_AUDIT_REPORT.md` — gate 11-SEC **APROVADO** (Step 11-Security)
- [ ] `docs/security/NULL_SAFETY_REPORT.md` — gate 12-NULL **APROVADO** (Step 12-Null-Safety)
- [ ] `code-health.py` com baseline registrado (Step 8)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11` do pipeline LLC. Seu objetivo é **implementar um PRP** (unidade autossuficiente de trabalho) usando TDD estrito, registrando cada passo no protocolo ACE para rastreabilidade entre sessões.

### Delimitação de escopo (leia antes de começar)

| Step | Skill | Quando |
|------|-------|--------|
| **11** | **`llc-step-11` (esta)** | **Execução**: implementar o PRP (código + testes) |
| 11-Security | `llc-step-11-security` | **Gate pré-execução**: SCA+SAST+secrets (já deve estar APROVADO) |
| 11-OWASP | `llc-step-11-owasp-security` | **Hardening pós-código**: roda APÓS todos os PRPs implementados |

Esta skill **não** faz auditoria de segurança (isso é pré-gate) nem hardening OWASP (isso é pós-código). Se encontrar um problema de segurança durante a implementação, registre como `<blocker>` e escale — não tente resolver ad-hoc.

### 1. Defina o Escopo da Sessão

Uma sessão do Step 11 executa **um PRP** (ou uma onda de PRPs independentes). Antes de codar:

- Identifique o PRP alvo (ex.: `PRP-001`) a partir de `EXECUTION_WAVES.md`.
- Leia o PRP: **DoD**, **lista de tarefas**, **especificação de testes**, **§7 Data Model** (contratos já validados no Step 12).
- Cruze com `TASKS.md` para obter os **IDs das tarefas** (ex.: `FDN-001`, `SEC-001`) — você os usará nos `<task_completed>`.
- Confirme com o humano: *"Vou implementar PRP-001 (ondas 1). Primeira ação: [X]. Prosseguir?"*

> **Grafo de dependências:** O `<dependencies>` no context_seed da sessão já contém
> o subgrafo relevante do `.ace/dependency-graph.yaml` para este step — NÃO leia
> o YAML diretamente. O subgrafo lista os artefatos de documentação que podem
> precisar de revisão após alterações de código. Consulte-o para saber quais docs
> atualizar ao final do PRP.

### 2. Ciclo TDD (obrigatório — sem exceções)

Para cada tarefa do PRP, siga Red → Green → Refactor:

1. 🔴 **RED:** escreva o teste **antes** do código (`.test.ts` / `*_test.py` conforme stack). **Rode o teste — ele DEVE falhar.** Mostre o output.
2. 🟢 **GREEN:** escreva o código **mínimo** que faz o teste passar. **Rode o teste — ele DEVE passar.** Mostre o output.
3. 🔵 **REFACTOR:** melhore o código mantendo os testes verdes.

> **REGRA DURA:** se você escrever implementação antes do teste, você violou o TDD. Apague a implementação, escreva o teste primeiro. Sem exceções (ver `AGENTS.md` §TDD Enforcement Protocol).

> **TDD para scaffolding (Onda 0 / PRPs de fundação):** Quando o PRP não tem testes
> unitários ainda (setup de projeto, configuração de build, Docker, CI), o ciclo
> RED/GREEN equivalente é a **compilação**:
> 1. 🔴 **RED:** escreva o arquivo de configuração (`tsconfig.json`, `package.json`,
>    `Dockerfile`). Rode `tsc --noEmit` (ou equivalente) — **deve falhar** (dependência
>    ausente, configuração incompleta). Mostre o erro.
> 2. 🟢 **GREEN:** corrija o erro (instale a dependência, ajuste a config). Recompile —
>    **deve passar**. Mostre o output limpo.
> 3. 🔵 **REFACTOR:** ajuste nomes, organize imports, padronize versões — mantendo a
>    compilação verde.
>
> O mesmo princípio vale para bootstrap: o RED é a aplicação não iniciar; o GREEN é
> o log `"successfully started"`. O propósito do TDD é o mesmo — ter uma falha
> observável antes de declarar sucesso — só muda o mecanismo de verificação.

> **TDD para Frontend (Componentes de UI):** Componentes de UI (telas, componentes,
> hooks visuais) exigem especificar o contrato visual *antes* de codar — o TDD
> genérico (teste → código) não é suficiente porque um componente tem múltiplos
> estados que precisam ser previstos. O ciclo correto é:
> 1. 📋 **SPEC:** escreva o Component Spec no PRP (§6) — props, estados (loading,
>    empty, error, happy, edge cases), interações do usuário, requisitos de
>    acessibilidade. **Não codifique nada ainda.**
> 2. 🔴 **RED:** para cada estado declarado no Spec, escreva um teste. Rode os
>    testes — **todos devem falhar** (o componente não existe). Mostre o output.
> 3. 🟢 **GREEN:** implemente o componente estado por estado até que **todos os
>    testes passem**. Mostre o output.
> 4. 🔵 **REFACTOR:** adicione testes de acessibilidade (jest-axe, navegação por
>    teclado, focus trap) e ajuste o componente. Mantenha os testes verdes.
>
> **REGRA:** se o Spec não declara todos os estados (loading, empty, error, happy,
> edge cases), o componente não está pronto para ser implementado. Volte ao Spec
> e complete-o. Cada estado da tabela do §6 do PRP deve ter um caso de teste
> correspondente — validado no DoD.

### 3. Registre no ACE (durante a sessão)

Cada alteração relevante é registrada no arquivo da sessão atual (`.ace/sessions/YYYY-MM-DD-NNN.md`), **append-only**:

**Delta de arquivo:**
```xml
<action type="file_modify"><file_delta>src/modules/auth/jwt.strategy.ts</file_delta><description>adiciona validação de expiração do token</description></action>
```

**Tarefa concluída** (`finalize_session.py` reflete isto em `TASKS.md`/`EXECUTION_WAVES.md`/`PLAN.md`):
```xml
<task_completed id="FDN-001" prp="PRP-001" status="done">validação de expiração JWT implementada com testes</task_completed>
```
- `id` **DEVE** corresponder à coluna ID de `TASKS.md`.
- `status`: `done` (→ ✅) ou `partial` (→ 🔄).
- Só marque `status="done"` quando a tarefa estiver de fato completa e testada.

**Bloqueador ativo** (se houver):
```xml
<blocker resolved="false">PRP-002 depende do contrato de PRP-001 §7.1, ainda não finalizado</blocker>
```

### 4. Verifique a Definition of Done (DoD) do PRP

Antes de declarar o PRP pronto, confira **todos** os critérios do DoD:

- [ ] Todas as tarefas do PRP com `<task_completed status="done">`
- [ ] Todos os testes do PRP passando (unitários + integração onde aplicável)
- [ ] Cobertura ≥ threshold do `TESTING_GUIDE.md`
- [ ] **Projeto compila sem erros** (`tsc --noEmit`, `npm run build`, `go build`, etc.)
- [ ] **Aplicação bootstrapa com sucesso** (`node dist/main.js`, `go run .`, etc. — até o log de "started")
- [ ] **Health check responde** (`curl http://localhost:PORT/api/v1/health` ou equivalente)
- [ ] **Para componentes de UI:** cada estado declarado no §6 Component Spec tem um caso de teste correspondente (loading, empty, error, happy, edge cases)
- [ ] **Para componentes de UI:** testes de acessibilidade (jest-axe) sem violações
- [ ] `code-health.py` sem regressão (Moved Code / Copy-Paste / Legacy Touch estáveis)
- [ ] Nenhum `<blocker resolved="false">` aberto
- [ ] Sem segredos/credenciais no código (Issues reais → escalar, não commitar)

> **Smoke test de scaffolding (Onda 0):** Para PRPs de fundação (setup, config, infra), os checks
> de compilação + bootstrap + health substituem os testes unitários como critério de DoD —
> a primeira evidência de que o arcabouço está íntegro é ele compilar e iniciar. O teste
> unitário vem no PRP seguinte.

> **Consistência documentação ↔ código:** Se o projeto tem mapeamento PRP→serviços
> configurado (`.ace/consistency-config.yaml` ou seção 6.5 do `ARCHITECTURE.md`),
> rode `consistency-check.py` para verificar se tarefas marcadas como ✅ no `TASKS.md`
> têm implementação real (não são stub). Divergências devem ser registradas como
> `<learning_point priority="high">` ou blocker antes de finalizar.

### 5. Verificação de Consistência (TASKS.md × Código)

Antes de encerrar o PRP, execute:
```bash
python .ace/scripts/consistency-check.py --strict
```
Este comando cruza as tarefas concluídas no `TASKS.md` com o código real dos serviços
mapeados na seção 6.5 do `ARCHITECTURE.md`. Se uma tarefa está marcada como ✅ mas o
serviço correspondente ainda é stub (`return []`, `TODO`, `NotImplementedError`), o
script reporta a divergência.

- Se passar (`exit 0`): documentação e código estão consistentes.
- Se falhar (`exit 1`): registre como blocker e corrija antes de finalizar.

> **Integração com ondas:** Quando executado via `llc wave run --wave N`, o
> `consistency-check.py --strict` é chamado automaticamente no pós-onda junto com
> o `pre-wave-check.sh`.

### 6. Code Health

Após cada onda de implementação, rode:
```bash
python .ace/scripts/code-health.py --since "30 days ago"
```
Se houver regressão estrutural (Moved Code, Copy/Paste, Legacy Touch piorando), registre como `<learning_point priority="high">` antes de finalizar.

### 7. Gere o `<context_seed>` (encerramento)

Ao final do trabalho na sessão, produza o handoff ACE de 4 campos:

```
state: PRP-001 implementado. jwt.strategy.ts + jwt.strategy.test.ts. 8/8 testes passando.
pending: PRP-002 (depende do contrato de PRP-001, já disponível).
blockers: nenhum ativo.
next_action: executar PRP-002 na próxima onda; ao fim de todos os PRPs, rodar llc-step-11-owasp-security.
```

Finalize pelo harness: `python .ace/scripts/llc.py session end --approve` (ou o harness fecha automaticamente ao fim do `llc run`).

---

## ⚠️ REGRAS CRÍTICAS

1. **Anti-alucinação:** Rode os testes de verdade e leia o output — nunca declare "testes passando" sem executá-los. Se um teste falha, o código NÃO está pronto.
2. **TDD é obrigatório:** Sem teste vermelho antes, sem implementação. Mostrar output do teste é mandatório.
3. **Escopo do PRP:** Implemente apenas o que o PRP define. Mudanças fora do escopo (nova tabela, nova dependência, mudança de assinatura pública) são **escaladas** como arquitetura (ver `AGENTS.md` §Architectural Escalation), não decididas ad-hoc.
4. **Traceabilidade:** Todo arquivo tocado deve ter `<file_delta>` na sessão. É o que prova que a sessão **cobre** aquele código (validado pelo `pre-commit` / `validate-tags.py --coverage`).
5. **`task_completed` honesto:** `status="done"` só quando concluído e testado. Use `partial` caso contrário — não inflacione progresso.
6. **Idempotência/Zonas:** Código em `src/` é zona 🟡; decisions de schema/config/auth são 🔴 (exigem gate humano). Status aplicado pelo harness (Progress Reflection) é a exceção sancionada.
7. **Component Spec antes de UI:** Para componentes de frontend, o Spec (§6 do PRP) deve ser escrito antes de qualquer código de UI. Violação = violação de TDD.
8. **Estados vs Testes:** Cada estado na tabela do §6 (loading, empty, error, happy, edge) deve ter pelo menos um teste verificando a renderização correta. Se um estado não tem teste, o componente não está completo.

---

## 📤 SAÍDA ESPERADA

- Código de implementação + testes (RED→GREEN→REFACTOR).
- Sessão `.ace/sessions/YYYY-MM-DD-NNN.md` com `<action>`/`<file_delta>` e `<task_completed>` registrados.
- `TASKS.md`/`EXECUTION_WAVES.md`/`PLAN.md` com status refletidos (aplicados por `finalize_session.py`).
- `<context_seed>` de 4 campos para a próxima sessão.

---

### Próximos Passos

- **PRP parcial/pendente:** continue na próxima sessão com `llc run --step 11 --prp <PRP> --wave <N>`.
- **Todos os PRPs da onda concluídos:** avance para a próxima onda em `EXECUTION_WAVES.md`.
- **Todos os PRPs implementados:** execute a skill `llc-step-11-owasp-security` (hardening pós-código, Gate 11-OWASP) antes de considerar o Step 11 concluído.
