# PRP-A-{XXX}: [{Nome Descritivo da Alteração}]

> **Tipo:** Amendment (alteração de PRP existente)
> **PRP Original:** PRP-{YYY} — [{Nome do PRP Original}]
> **Iteração:** v{Atual} → v{Nova}
> **ID:** PRP-A-{XXX} | **Prioridade:** {Crítico / Alto / Médio / Baixo}
> **Complexidade:** {Baixa / Média / Alta}
> **Estimativa:** {X dias}
> **Status:** ⏳ Pending | 🔄 In Progress | 👀 Review | ✅ Complete | 🛑 Blocked
> **Criado em:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD} | **Versão:** {v1.0}

---

## 1. Contexto da Mudança

### 1.1 Por que esta alteração é necessária?
{Explique em 1-2 parágrafos o problema de negócio ou técnico que motiva a alteração. Referencie o DELTA_REPORT.md e/ou os novos documentos de mudança.}

### 1.2 Resumo do Delta
| Dimensão | Status | Descrição |
|----------|--------|-----------|
| RFs alterados | {N} | IDs: RF-{XXX}.1, RF-{XXX}.3 |
| RFs adicionados | {N} | IDs: RF-{XXX}.5, RF-{XXX}.6 |
| RFs removidos | {N} | IDs: RF-{XXX}.2 (deprecated) |
| Contratos de API | {Alterados / Inalterados} | Breaking: {Sim / Não} |
| Modelo de dados | {Alterado / Inalterado} | {N} migrations |
| UI | {Alterada / Inalterada} | {N} componentes afetados |
| Testes existentes | {N} precisam ser atualizados |

### 1.3 O que NÃO muda (reafirmação de escopo)
{Liste explicitamente o que permanece igual do PRP original. Isso evita re-trabalho e alinha expectativas.}

- ✅ {Funcionalidade X permanece exatamente como está}
- ✅ {Contrato Y não é alterado}
- ✅ {Testes Z continuam válidos sem modificação}

---

## 2. Requisitos Funcionais — Delta

> **Convenção:** Apenas o que MUDA em relação ao PRP original.
> RFs do PRP original que não aparecem aqui permanecem inalterados.

### 2.1 RFs Novos

| ID | Requisito | Critérios de Aceitação (Gherkin) | Prioridade | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------------------|------------|----------|-----------------|
| RF-{YYY}.5 | {Descrição do novo requisito} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Must | `{service}.spec.ts` | `src/{module}/{service}.ts` |
| RF-{YYY}.6 | {Descrição} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Should | `{service}.spec.ts` | `src/{module}/{service}.ts` |

### 2.2 RFs Alterados

| ID | Requisito Original | Alteração | Novo Critério de Aceitação | Impacto em Testes Existentes |
|----|-------------------|-----------|---------------------------|------------------------------|
| RF-{YYY}.1 | {Descrição original} | {O que muda} | **Dado** {novo contexto}, **Quando** {ação}, **Então** {novo resultado} | {TEST-001 precisa ser atualizado} |
| RF-{YYY}.3 | {Descrição original} | {O que muda} | **Dado** {novo contexto}, **Quando** {ação}, **Então** {novo resultado} | {TEST-003 permanece válido} |

### 2.3 RFs Removidos

| ID | Requisito Original | Motivo da Remoção | Alternativa (se houver) |
|----|-------------------|-------------------|------------------------|
| RF-{YYY}.2 | {Descrição original} | {Funcionalidade deprecated — substituída por PRP-N-XXX} | Módulo de BI (PRP-N-XXX) |

---

## 3. Requisitos Não-Funcionais — Delta

| ID | RNF | Mudança | Impacto |
|----|-----|---------|---------|
| RNF-{YYY}.1 | Performance < 200ms P95 | **Alterado** para < 150ms P95 | Pode exigir otimização de query |
| RNF-{YYY}.2 | {RNF} | **Mantido** | Nenhum |
| RNF-NOVO.1 | {Novo RNF} | **Adicionado** | {Impacto} |

---

## 4. Dependências

### 4.1 Dependências do PRP Original (herdadas, salvo alteração)

| PRP | Nome | Status | Observação |
|-----|------|--------|------------|
| PRP-{001} | {Nome} | ✅ | Mantida |
| PRP-{002} | {Nome} | ✅ | Mantida |

### 4.2 Novas Dependências (deste PRP-A)

| PRP | Nome | Tipo | Motivo |
|-----|------|------|--------|
| PRP-N-{001} | {Nome} | Bloqueia | PRP-A depende do novo módulo |
| PRP-A-{002} | {Nome} | Desbloqueia | Este PRP-A desbloqueia outra alteração |

---

## 5. API Contracts — Delta

> **Apenas o que MUDA em relação ao PRP original.**
> Endpoints não listados aqui permanecem inalterados.

### 5.1 Endpoint Alterado: {MÉTODO} {/rota}

| Aspecto | Valor Atual | Novo Valor | Breaking? |
|---------|-------------|------------|:---------:|
| **Request body** | `{campo_antigo}` | `{campo_novo}` | Sim / Não |
| **Response body** | `{campo: "tipo"}` | `{campo: "novo_tipo"}` | Sim / Não |
| **Status codes** | `200, 400` | `200, 400, 422` | Não |
| **Rate limit** | `100/min` | `60/min` | Não |
| **Autenticação** | `JWT` | `JWT` | Não |

**Detalhamento da mudança:**
```diff
- {campo_antigo}: "tipo"
+ {campo_novo}: "novo_tipo"
+ {campo_adicional}: "tipo" // novo campo obrigatório
```

### 5.2 Endpoint Novo: {MÉTODO} {/rota}

{Descreva apenas se houver endpoint totalmente novo neste PRP-A}

### 5.3 Endpoint Removido: {MÉTODO} {/rota}

| Endpoint | Motivo | Alternativa |
|----------|--------|-------------|
| `DELETE /api/antigo` | Substituído por `POST /api/novo/remover` | `POST /api/novo/remover` |

---

## 6. Data Model — Delta

> **Apenas o que MUDA em relação ao modelo de dados do PRP original.**

### 6.1 Entidade: `{nome_tabela}` — Campos Alterados

| Campo | Tipo Anterior | Tipo Novo | Nulabilidade | Migração |
|-------|---------------|-----------|:------------:|----------|
| `{campo}` | `{tipo_antigo}` | `{tipo_novo}` | NOT NULL | `ALTER COLUMN {campo} TYPE {novo_tipo}` |
| `{campo}` | — | `{tipo_novo}` | NULL (default: null) | `ADD COLUMN {campo} {tipo}` |

### 6.2 Entidade: `{nome_tabela}` — Campos Removidos

| Campo | Motivo | Dados Existentes |
|-------|--------|------------------|
| `{campo_antigo}` | Substituído por `{campo_novo}` | Migrar para `{campo_novo}` ou descartar |

### 6.3 Entidade: `{nova_tabela}` — Nova Tabela

{Se o PRP-A criar uma nova tabela, documente aqui seguindo o formato do §7 do PRP template original}

---

## 7. Arquivos a Modificar vs Criar vs Remover

| Operação | Arquivo | PRP Original | Motivo |
|----------|---------|-------------|--------|
| ✏️ **Modificar** | `src/{module}/{service}.ts` | PRP-{YYY} | Adicionar campo `{campo}` no create/update |
| ✏️ **Modificar** | `src/{module}/{controller}.ts` | PRP-{YYY} | Novo endpoint `POST /api/novo` |
| ✏️ **Modificar** | `src/{module}/{service}.spec.ts` | PRP-{YYY} | Atualizar testes para novo comportamento |
| ➕ **Criar** | `src/{module}/{novo_service}.ts` | — | Novo serviço auxiliar |
| ➕ **Criar** | `src/{module}/{novo_service}.spec.ts` | — | Testes do novo serviço |
| ➕ **Criar** | `prisma/migrations/{nova_migration}` | — | Migração do modelo de dados |
| 🗑️ **Remover** | `src/{module}/{legacy_service}.ts` | PRP-{YYY} | Substituído pelo novo serviço |
| 🗑️ **Remover** | `src/{module}/{legacy_service}.spec.ts` | PRP-{YYY} | Testes do serviço removido |

---

## 8. Estratégia de Testes (Delta)

### 8.1 Testes Existentes que Precisam ser Atualizados

| Teste Original | Mudança Necessária | Risco de Regressão |
|----------------|-------------------|:------------------:|
| `TEST-{001}` (unit) | Atualizar assertion para novo formato de resposta | Baixo |
| `TEST-{003}` (integration) | Adicionar novo campo no payload de teste | Baixo |
| `TEST-{005}` (E2E) | Fluxo de remoção precisa ser removido | Médio |

### 8.2 Novos Testes (para o delta)

| # | Descrição | Tipo | Entrada | Saída Esperada | Arquivo |
|---|-----------|------|---------|----------------|---------|
| 1 | Deve criar {entidade} com novo campo {campo} | Unit | `{ campo: "valor", novo_campo: "valor" }` | `{ id, novo_campo }` | `{service}.spec.ts` |
| 2 | Deve rejeitar {campo} sem {novo_campo} | Unit | `{ campo: "valor" }` | `Throw ValidationError` | `{service}.spec.ts` |
| 3 | Deve migrar dados do endpoint antigo para novo | Integration | Request no endpoint antigo | 301 redirect ou 200 com novo formato | `{module}.e2e-spec.ts` |

### 8.3 Garantia de Não Regressão

- [ ] Todos os testes do PRP original que NÃO estão na lista "a atualizar" continuam passando sem alteração
- [ ] Cobertura de testes do PRP original não regrediu
- [ ] `code-health.py` sem regressão (Copy/Paste, Moved Code, Legacy Touch estáveis)

---

## 9. Riscos e Mitigações

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RSK-{AXXX}-01 | Breaking change afeta consumidores não documentados da API | Média | Alto | Mapear consumidores; versionar API se necessário; comunicar com antecedência |
| RSK-{AXXX}-02 | Migração de dados pode causar downtime | Baixa | Médio | Script em múltiplos passos; validar em staging antes de produção |
| RSK-{AXXX}-03 | Testes existentes quebram com a mudança | Alta | Alto | Executar suite completa antes do merge; incluir no DoD |
| RSK-{AXXX}-04 | Regressão em funcionalidade não relacionada | Média | Alto | `code-health.py` + suite de regressão automatizada |

---

## 10. Dívida Técnica e Decisões

| Data | Decisão / Dívida | Contexto | Impacto | Ação futura | Status |
|------|------------------|----------|---------|-------------|--------|
| {YYYY-MM-DD} | {Optou-se por manter compatibilidade retroativa no endpoint} | {Consumidores externos não podem ser atualizados simultaneamente} | {Código mais complexo, duas versões do parser} | {Remover versão antiga na iteração v3} | Pendente |

---

## 11. Definition of Done (DoD) — Checklist de Aceitação

### Específicos do Delta
- [ ] Todos os RFs novos (seção 2.1) implementados e testados
- [ ] Todos os RFs alterados (seção 2.2) refletem o novo comportamento
- [ ] RFs removidos (seção 2.3) não estão mais acessíveis (ou estão redirecionados)
- [ ] Contratos de API alterados (seção 5) refletem o código entregue
- [ ] Breaking changes documentados e comunicados (se houver)
- [ ] Migração de dados executada e testada (up e down)

### Integridade do Sistema
- [ ] **Testes do PRP original que não foram alterados continuam passando** (≥ 1 execução completa)
- [ ] Novos testes (seção 8.2) escritos e passando
- [ ] Testes atualizados (seção 8.1) refletem o novo comportamento
- [ ] Cobertura ≥ threshold do PRP original (não regrediu)
- [ ] Compilação sem erros (`tsc --noEmit` / equivalente)
- [ ] Lint e formatação passando

### Documentação
- [ ] `docs/planning/DELTA_REPORT.md` reflete a execução deste PRP-A
- [ ] PRP original atualizado com referência a este PRP-A
- [ ] `TASKS.md` atualizado com as tarefas deste PRP-A
- [ ] `CLAUDE.md` / `AGENTS.md` atualizados se houve mudança de stack ou regras

### Segurança
- [ ] `code-health.py` sem regressão estrutural
- [ ] `prp_verify.py --prp PRP-A-{XXX}` passando (0 CRITICAL)
- [ ] Nenhum `<blocker resolved="false">` aberto

---

> **Nota:** Este PRP-A é um documento complementar. O PRP original (PRP-{YYY}) continua sendo a fonte da verdade para as partes não alteradas. Para entender o sistema completo, leia ambos.
