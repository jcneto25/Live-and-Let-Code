# PRP: [{F0.X}] — [{Nome Descritivo}]

> **ID:** PRP-{XXX} | **Fase:** {Phase N} | **Onda:** {Onda M}
> **Owner:** {Dev responsável} | **Reviewer:** {Tech Lead / Senior Dev}
> **Estimativa:** {X dias} | **Status:** {⏳ Pending / 🔄 In Progress / 👀 Review / ✅ Complete / 🛑 Blocked}
> **Prioridade:** {Crítico / Alto / Médio / Baixo}
> **Complexidade:** {Baixa / Média / Alta}
> **Criado em:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD} | **Versão:** {v1.0}

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?
{Explique em 1-2 parágrafos o problema de negócio ou técnico que este PRP resolve. Use linguagem do usuário final, não técnica.}

> **Exemplo:** *"Terapeutas precisam registrar sessões com crianças em locais sem internet. Este PRP entrega a gravação de sessão no mobile com timer, contadores de frequência e registro de mood, salvando localmente até o sync."*

### 1.2 O que é entregue?
{Liste em bullets o que o usuário final (ou sistema) poderá fazer após este PRP estar completo.}

- [ ] {Ação concreta 1}
- [ ] {Ação concreta 2}
- [ ] {Ação concreta 3}

### 1.3 O que NÃO está no escopo (será feito em PRPs futuros)
{Explicitamente liste o que NÃO será feito aqui. Isso evita scope creep e alinha expectativas.}

- ❌ {Feature futura 1} → PRP-{YYY}
- ❌ {Feature futura 2} → PRP-{ZZZ}
- ❌ {Feature futura 3} → PRP-{WWW}

> **Exemplo:** *"NÃO inclui: upload de fotos durante a sessão (PRP-031), notificações push pós-sessão (PRP-030), relatório PDF automático (PRP-025)."*

---

## 2. Requisitos Funcionais (RF)

> **Formato obrigatório:** Gherkin (Dado/Quando/Então) para eliminar ambiguidade.

| ID | Requisito | Critérios de Aceitação (Gherkin) | Prioridade | Status |
|----|-----------|----------------------------------|------------|--------|
| RF-{XXX}.1 | {Descrição clara, linguagem do usuário} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado mensurável} | Must | ⏳ |
| RF-{XXX}.2 | {Descrição clara} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Must | ⏳ |
| RF-{XXX}.3 | {Descrição clara} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Should | ⏳ |

---

## 3. Requisitos Não-Funcionais (RNF)

> **Específicos deste PRP.** Não copie do SPEC — adapte para o escopo deste PRP.

| ID | Requisito | Métrica | Como verificar | Status |
|----|-----------|---------|----------------|--------|
| RNF-{XXX}.1 | Performance | {Ex: < 200ms P95 na API} | k6 / Lighthouse / React Profiler | ⏳ |
| RNF-{XXX}.2 | Segurança | {Ex: Sem vulnerabilidades críticas} | `npm audit` / Snyk | ⏳ |
| RNF-{XXX}.3 | Acessibilidade | {Ex: WCAG 2.1 AA} | axe-core / Lighthouse | ⏳ |
| RNF-{XXX}.4 | Offline | {Ex: 100% funcional sem rede} | Teste em modo avião | ⏳ |

---

## 4. Dependências

### 4.1 Bloqueado por (must be complete BEFORE this PRP)

| PRP | ID | Nome | Status | Motivo (por que é necessário) |
|-----|----|------|--------|------------------------------|
| {F0.1} | PRP-{001} | {Nome} | ✅ | {Ex: Estrutura de monorepo precisa existir} |
| {F1.1} | PRP-{003} | {Nome} | ✅ | {Ex: Tabela patients precisa existir no banco} |

### 4.2 Desbloqueia (this PRP must be complete BEFORE)

| PRP | ID | Nome | Status | Motivo (por que depende deste) |
|-----|----|------|--------|--------------------------------|
| {F1.6} | PRP-{010} | {Nome} | ⏳ | {Ex: UI de Users precisa da API de Users} |
| {F2.1} | PRP-{013} | {Nome} | ⏳ | {Ex: Mobile Auth precisa do mesmo JWT logic} |

> **💡 Nota:** "Pode Rodar em Paralelo" é definido no **Development Plan** (Dependency Matrix / Ondas), não aqui.

---

## 5. API Contracts (se aplicável)

> **Se este PRP não expõe APIs, escreva "N/A — apenas frontend/mobile changes."**

### 5.1 Endpoint: {MÉTODO} {/rota}

**Descrição:** {O que este endpoint faz em uma frase}
**Módulo:** {auth / patients / goals / etc.}
**Autenticação:** {JWT / Público / API Key}
**Rate Limit:** {X req/min}
**Roles permitidas:** {ADMIN / THERAPIST / PARENT / SCHOOL / ORGANIZATION_ADMIN}

**Request Body:**
```json
{
  "campo_obrigatorio": "string | number | boolean | uuid",
  "campo_opcional": "tipo // opcional"
}
```

**Response 200 / 201:**
```json
{
  "id": "uuid",
  "campo": "valor",
  "created_at": "2026-06-03T15:45:00Z"
}
```

**Response 400 (Bad Request):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Campo X é obrigatório",
  "code": "FIELD_REQUIRED",
  "field": "x"
}
```

**Response 403 (Forbidden):**
```json
{
  "error": "FORBIDDEN",
  "message": "User does not have access to this patient",
  "code": "PATIENT_ACCESS_DENIED"
}
```

**Response 429 (Rate Limited):**
```json
{
  "error": "RATE_LIMITED",
  "retry_after": 60
}
```

### 5.2 Endpoint: {MÉTODO} {/rota}
{Repetir estrutura acima para cada endpoint deste PRP.}

---

## 6. Component Spec (se aplicável — Frontend / Mobile)

> **Se este PRP não tem UI, escreva "N/A — apenas backend changes."**

### 6.1 {Nome do Componente / Screen}

**Responsabilidade:** {O que este componente faz e o que NÃO faz}
**Localização:** `apps/web/src/components/{Dominio}/{Nome}.tsx` ou `apps/mobile/src/screens/{NomeScreen}.tsx`

**Props / Interface:**
```typescript
interface {Nome}Props {
  patientId: string;           // obrigatório
  onSave?: (data: FormData) => void; // opcional
  readOnly?: boolean;          // default: false
}
```

**Estados:**
| Estado | Trigger | UI |
|--------|---------|-----|
| `loading` | Inicialização / fetch | Skeleton / Spinner |
| `empty` | Dados vazios | Mensagem + CTA |
| `error` | Fetch falhou | Toast + Retry button |
| `editing` | User clica "Editar" | Form com validação |
| `saving` | Submit do form | Botão desabilitado + spinner |
| `success` | Save OK | Toast + transição |

**Comportamento:**
- {O que acontece quando o usuário clica em X}
- {O que acontece em caso de erro de rede}
- {Como validação de formulário funciona (Zod schema)}

**Design Reference:**
- Figma: `{link ou nome do frame}`
- Design System tokens: `{cores, tipografia, espaçamento}`
- Acessibilidade: `{ARIA labels, focus trap, keyboard navigation}`

---

## 7. Database Changes (se aplicável)

> **Se este PRP não altera banco, escreva "N/A — apenas lógica/frontend."**

| Operação | Tabela | Campos (novos/alterados) | Índice | Migration | Dados sensíveis? |
|----------|--------|--------------------------|--------|-----------|------------------|
| CREATE | {users} | {id, email, password_hash, role, organization_id} | {idx_email, idx_org} | {20240601_add_users} | {Sim — password_hash} |
| ALTER | {patients} | {ADD diagnosis_level (enum)} | — | {20240602_add_diagnosis} | {Sim — dados de saúde} |
| CREATE | {sessions} | {id, patient_id, duration, mood, created_at} | {idx_patient_created} | {20240603_add_sessions} | {Sim — dados de saúde} |

**Regras de migração:**
- {Ex: Migration deve ser reversível (down script testado)}
- {Ex: Dados existentes precisam de default value ou backfill?}
- {Ex: Novo campo sensível precisa ser criptografado?}

---

## 8. Test Strategy (TDD Estruturado)

> **⚠️ REGRA DE OURO: Escreva estes testes ANTES do código de produção.**
> **Se não consegue listar os testes, o PRP não está pronto para ser executado.**

### 8.1 Unit Tests

| # | Descrição | Entrada | Saída Esperada | Factory / Mock | Arquivo |
|---|-----------|---------|-----------------|----------------|---------|
| 1 | Deve criar {entidade} com dados válidos | `{ campo: "valor" }` | `{ id, ... }` | `create{Entity}()` | `{service}.spec.ts` |
| 2 | Deve rejeitar {campo} duplicado | `{ campo: "dup" }` | `Throw ConflictException` | `create{Entity}({ campo: "dup" })` | `{service}.spec.ts` |
| 3 | Deve validar {regra de negócio} | `{ campo: "inválido" }` | `Throw BadRequestException` | `mock{Dependency}()` | `{service}.spec.ts` |
| 4 | Deve aplicar RBAC (role X não pode Y) | `{ user: { role: THERAPIST } }` | `Throw ForbiddenException` | `mockAuthContext(THERAPIST)` | `{guard}.spec.ts` |

### 8.2 Integration Tests

| # | Descrição | Setup | Banco | Arquivo |
|---|-----------|-------|-------|---------|
| 1 | POST {/rota} retorna 201 com dados válidos | `TestContainers(Postgres)` | Reset por teste | `{module}.e2e-spec.ts` |
| 2 | POST {/rota} retorna 400 com payload inválido | `TestContainers(Postgres)` | Reset por teste | `{module}.e2e-spec.ts` |
| 3 | GET {/rota} requer autenticação | `app without auth` | — | `{module}.e2e-spec.ts` |
| 4 | GET {/rota} isola por organization_id | `2 orgs + 2 users` | Dados de ambas | `{module}.e2e-spec.ts` |

### 8.3 E2E Tests (Frontend / Mobile)

| # | Fluxo do usuário | Ferramenta | Arquivo |
|---|------------------|------------|---------|
| 1 | {Login → Ação → Resultado esperado} | Playwright / Detox | `{fluxo}.spec.ts` |
| 2 | {Ação offline → Sync → Verificação no web} | Detox | `{sync}.spec.ts` |

### 8.4 Factories e Mocks Compartilhados

```typescript
// Factory obrigatória para este PRP:
export function create{Entity}(overrides?: Partial<{Entity}>): {Entity} {
  return {
    id: faker.string.uuid(),
    campo: faker.lorem.word(),
    organizationId: faker.string.uuid(),
    createdAt: new Date(),
    ...overrides,
  };
}

// Mock obrigatório:
export const mock{Dependency} = () => ({
  metodo: jest.fn().mockResolvedValue({ ... }),
});
```

---

## 9. Riscos e Mitigações

| ID | Risco | Probabilidade | Impacto | Mitigação | Status |
|----|-------|---------------|---------|-----------|--------|
| RSK-{XXX}-01 | {Risco técnico ou de negócio} | {Baixa/Média/Alta} | {Baixo/Médio/Alto} | {Ação preventiva ou contingência} | {Monitorado/Mitigado} |
| RSK-{XXX}-02 | {Ex: WatermelonDB sync falha em batch > 1000} | Média | Alto | Limitar batch size a 500; paginar sync | Monitorado |
| RSK-{XXX}-03 | {Ex: Performance do endpoint em alta carga} | Baixa | Médio | Adicionar índice composto; testar k6 | Planejado |

---

## 10. Dívida Técnica e Decisões

> **Registre aqui decisões tomadas durante o desenvolvimento e dívidas conscientes.**

| Data | Decisão / Dívida | Contexto | Impacto | Ação futura | Status |
|------|------------------|----------|---------|-------------|--------|
| {YYYY-MM-DD} | {Ex: Usar raw query ao invés de Prisma para performance} | {Ex: Prisma gerava N+1 no aggregate} | {Ex: Menos type-safe} | {Ex: Refatorar para Prisma quando suportar groupBy} | {Pendente} |
| {YYYY-MM-DD} | {Ex: Simplificar validação de CPF no MVP} | {Ex: Lib de validação aumentava bundle em 50KB} | {Ex: Validação básica apenas} | {Ex: Adicionar lib no PRP-00X} | {Pendente} |

---

## 11. Execution Log

> **Atualize este log a cada mudança de status ou descoberta importante.**
> **Não apague entradas antigas — append only.**

### Status History

| Data | Status Anterior | Status Novo | Responsável | Motivo |
|------|-----------------|-------------|-------------|--------|
| {YYYY-MM-DD} | — | ⏳ Pending | {PM} | PRP criado e priorizado |
| {YYYY-MM-DD} | ⏳ Pending | 🔄 In Progress | {Dev} | Dependências resolvidas |
| {YYYY-MM-DD} | 🔄 In Progress | 🛑 Blocked | {Dev} | {Ex: Aguardando merge de PRP-003} |
| {YYYY-MM-DD} | 🛑 Blocked | 🔄 In Progress | {Dev} | {Ex: PRP-003 mergeado} |
| {YYYY-MM-DD} | 🔄 In Progress | 👀 Review | {Dev} | PR aberto #{N} |
| {YYYY-MM-DD} | 👀 Review | ✅ Complete | {Reviewer} | DoD atendido, mergeado em `{branch}` |

### Blockers Encontrados

| Data | Bloqueador | Impacto | Resolução | Data Resolução |
|------|------------|---------|-----------|----------------|
| {YYYY-MM-DD} | {Ex: Prisma não suporta X} | {Alto} | {Ex: Usar raw query temporariamente} | {YYYY-MM-DD} |

### Decisões Técnicas Registradas

| Data | Decisão | Alternativa considerada | Por que escolhemos esta | Quem decidiu |
|------|---------|------------------------|------------------------|--------------|
| {YYYY-MM-DD} | {Ex: Usar Zod ao invés de class-validator no frontend} | {class-validator} | {Ex: Melhor integração com React Hook Form} | {Tech Lead} |

---

## 12. Definition of Done (DoD) — Checklist Final

> **Este PRP só pode ser marcado como ✅ Complete se TODOS os itens obrigatórios estiverem checkados.**
> **Itens opcionais são marcados com [O].**

### Funcional
- [ ] Todos os RF listados na seção 2 estão implementados e testados
- [ ] API Contracts (seção 5) refletem exatamente o código entregue
- [ ] Component Spec (seção 6) reflete exatamente o UI entregue
- [ ] Database Changes (seção 7) estão aplicados e testados em staging

### Técnico
- [ ] Todos os testes da seção 8 estão escritos e passando
- [ ] Cobertura de testes unitários ≥ 80% neste PRP
- [ ] Testes E2E críticos passando (se aplicável)
- [ ] Sem regressões — testes de PRPs anteriores continuam verdes
- [ ] Lint (ESLint) e formatação (Prettier) passando
- [ ] TypeScript strict sem erros (`noEmit` check)
- [ ] Migration de banco testada (up e down)
- [ ] [O] Performance dentro do RNF definido (seção 3)
- [ ] [O] Acessibilidade verificada com axe-core (se aplicável)
- [ ] [O] Security scan limpo (`npm audit` sem críticas)

### Documentação e Processo
- [ ] Código revisado (Code Review aprovado por 1+ dev sênior)
- [ ] Este PRP documento foi atualizado para refletir o que foi entregue
- [ ] Dívida técnica registrada na seção 10 (se houver)
- [ ] Deploy em staging validado e acessível
- [ ] Changelog atualizado (se houver breaking change)

---

> **Nota:** Este PRP é um documento vivo. Atualize a "Última atualização" e "Versão" sempre que houver mudança. A versão no repositório (`docs/prps/PRP-XXX.md`) é a fonte da verdade.
