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

> **Colunas obrigatórias para verificação mecânica:** `Teste(s)` e `Arquivo(s) impl` são lidas por `prp_verify.py` (Step 11.2) para cruzar cada RF com arquivos reais. Preencha com caminhos relativos separados por vírgula.

| ID | Requisito | Critérios de Aceitação (Gherkin) | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------------------|------------|--------|----------|-----------------|
| RF-{XXX}.1 | {Descrição clara, linguagem do usuário} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado mensurável} | Must | ⏳ | `{service}.spec.ts` | `src/{module}/{service}.ts` |
| RF-{XXX}.2 | {Descrição clara} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Must | ⏳ | `{service}.spec.ts` | `src/{module}/{service}.ts` |
| RF-{XXX}.3 | {Descrição clara} | **Dado** {contexto}, **Quando** {ação}, **Então** {resultado} | Should | ⏳ | `{service}.spec.ts` | `src/{module}/{service}.ts` |

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
>
> ⚠️ **TDD para UI:** Este Spec deve ser escrito **antes** de qualquer código do componente.
> Cada estado listado abaixo vira um caso de teste (RED). O componente é implementado
> depois (GREEN). Ver `llc-step-11.md §2 — TDD para Frontend`.

> **Checklist de TDD para UI (preencher antes de codar):**
> - [ ] Spec escrito e todos os estados (loading, empty, error, happy, edge) declarados
> - [ ] Para cada estado, há pelo menos um caso de teste planeado na coluna "Teste"
> - [ ] Testes de acessibilidade (jest-axe, keyboard nav) previstos no REFACTOR

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

**Estados (cada estado vira um caso de teste — RED phase):**
| Estado | Trigger | UI esperada | Arquivo de teste |
|--------|---------|-------------|------------------|
| `loading` | Inicialização / fetch | Skeleton / Spinner | `{Nome}.test.tsx` |
| `empty` | Dados vazios | Mensagem + CTA | `{Nome}.test.tsx` |
| `error` | Fetch falhou | Toast + Retry button | `{Nome}.test.tsx` |
| `happy` | Dados carregados | Renderização completa | `{Nome}.test.tsx` |
| `edge: {caso}` | {trigger específico} | {UI esperada} | `{Nome}.test.tsx` |

**Comportamento:**
- {O que acontece quando o usuário clica em X}
- {O que acontece em caso de erro de rede}
- {Como validação de formulário funciona}

**Acessibilidade (REFACTOR phase):**
- [ ] jest-axe: nenhuma violação de acessibilidade
- [ ] Navegação por teclado: todos os elementos interativos são alcançáveis com Tab
- [ ] Focus trap: modais e dialogs mantêm foco no ciclo correto
- [ ] Screen reader: conteúdo dinâmico anuncia via `aria-live`
- [ ] Contraste: atende WCAG 2.1 AA (ratio ≥ 4.5:1)

**Design Reference:**
- Figma: `{link ou nome do frame}`
- Design System tokens: `{cores, tipografia, espaçamento}`

---

## 7. Data Model

> **Defina o modelo de dados deste PRP.** Cada entidade deve ter seus campos listados individualmente com tipo, nulabilidade e fallback. Esta seção é a fonte primária para validação de null safety (Step 12).

### 7.1 Entidade: `{nome_tabela}`

| Campo | Tipo | Nulabilidade | Fallback (se NULL) |
|-------|------|:------------:|--------------------|
| {id} | {UUID PK} | NOT NULL | N/A |
| {campo_obrigatorio} | {tipo} | NOT NULL | N/A |
| {campo_opcional} | {tipo} | NULL | {valor default ou → PRP-NNN §7.1 campo} |
| {campo_com_default} | {tipo} | DEFAULT {valor} | — |

**Legenda:**
- `NOT NULL` — campo obrigatório, nunca é nulo. Fallback: N/A.
- `NULL` — campo pode ser nulo; **exige fallback** documentado na coluna ao lado.
- `DEFAULT <valor>` — banco atribui valor padrão na INSERT; código nunca vê null vindo do DB. Fallback: —.

### 7.N Entidade: `{outra_tabela}`
{Repetir estrutura acima para cada entidade neste PRP.}

---

## 8. Database Changes (se aplicável)

> **Se este PRP não altera banco, escreva "N/A — apenas lógica/frontend."**
> A definição detalhada dos campos de cada tabela está na seção §7 (Data Model). Esta seção documenta apenas operações de migration e índices.

| Operação | Tabela | Índice | Migration | Dados sensíveis? |
|----------|--------|--------|-----------|------------------|
| CREATE | {users} | {idx_email, idx_org} | {20240601_add_users} | {Sim — password_hash} |
| ALTER | {patients} | — | {20240602_add_diagnosis} | {Sim — dados de saúde} |
| CREATE | {sessions} | {idx_patient_created} | {20240603_add_sessions} | {Sim — dados de saúde} |

**Regras de migração:**
- {Ex: Migration deve ser reversível (down script testado)}
- {Ex: Dados existentes precisam de default value ou backfill?}
- {Ex: Novo campo sensível precisa ser criptografado?}

---

## 9. Test Strategy (TDD Estruturado)

> **⚠️ REGRA DE OURO: Escreva estes testes ANTES do código de produção.**
> **Se não consegue listar os testes, o PRP não está pronto para ser executado.**

### 9.1 Unit Tests

| # | Descrição | Entrada | Saída Esperada | Factory / Mock | Arquivo |
|---|-----------|---------|-----------------|----------------|---------|
| 1 | Deve criar {entidade} com dados válidos | `{ campo: "valor" }` | `{ id, ... }` | `create{Entity}()` | `{service}.spec.ts` |
| 2 | Deve rejeitar {campo} duplicado | `{ campo: "dup" }` | `Throw ConflictException` | `create{Entity}({ campo: "dup" })` | `{service}.spec.ts` |
| 3 | Deve validar {regra de negócio} | `{ campo: "inválido" }` | `Throw BadRequestException` | `mock{Dependency}()` | `{service}.spec.ts` |
| 4 | Deve aplicar RBAC (role X não pode Y) | `{ user: { role: THERAPIST } }` | `Throw ForbiddenException` | `mockAuthContext(THERAPIST)` | `{guard}.spec.ts` |

### 9.2 Integration Tests

| # | Descrição | Setup | Banco | Arquivo |
|---|-----------|-------|-------|---------|
| 1 | POST {/rota} retorna 201 com dados válidos | `TestContainers(Postgres)` | Reset por teste | `{module}.e2e-spec.ts` |
| 2 | POST {/rota} retorna 400 com payload inválido | `TestContainers(Postgres)` | Reset por teste | `{module}.e2e-spec.ts` |
| 3 | GET {/rota} requer autenticação | `app without auth` | — | `{module}.e2e-spec.ts` |
| 4 | GET {/rota} isola por organization_id | `2 orgs + 2 users` | Dados de ambas | `{module}.e2e-spec.ts` |

### 9.3 E2E Tests (Frontend / Mobile)

> ⚠️ **Cada cenário E2E deve ter sua spec escrita antes da implementação.**
> Use o template do `TESTING_GUIDE.md §10 — E2E Spec Template`.
> PRPs com upload de arquivo (multipart) EXIGEM cenário E2E-FILE específico.

| # | ID E2E | Fluxo do usuário | Multipart? | Ferramenta | Arquivo |
|---|--------|------------------|:----------:|------------|---------|
| 1 | E2E-{SIG}-001 | {Login → Ação → Resultado esperado} | Não | Playwright / Detox | `{fluxo}.spec.ts` |
| 2 | E2E-{SIG}-002 | {Upload de arquivo → Validação → Confirmação} | **Sim** | Playwright / Detox | `{fluxo}.upload.spec.ts` |
| 3 | E2E-{SIG}-003 | {Fluxo de erro — rede/timeout} | Não | Playwright / Detox | `{fluxo}.error.spec.ts` |
| 4 | E2E-{SIG}-004 | {Ação offline → Sync → Verificação} | Não | Detox | `{sync}.spec.ts` |

> **Regra:** Todo PRP com endpoint HTTP ou fluxo de usuário: ≥ 1 fluxo feliz + ≥ 1 erro.
> Se envolve upload de arquivo (multipart): +1 cenário de upload + 1 de limite excedido.

> **📌 Alinhamento com CCC (§13):** Antes de finalizar esta seção, verifique a
> seção 13 (Cross-Cutting Concerns). Todo CCC marcado como "implementa" deve ter
> pelo menos um caso de teste correspondente nesta seção. Ex: se o CCC "AuthGuard"
> está marcado como implementado, deve haver ao menos 1 teste de guarda no §9.1.

### 9.4 Factories e Mocks Compartilhados

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

## 10. Riscos e Mitigações

| ID | Risco | Probabilidade | Impacto | Mitigação | Status |
|----|-------|---------------|---------|-----------|--------|
| RSK-{XXX}-01 | {Risco técnico ou de negócio} | {Baixa/Média/Alta} | {Baixo/Médio/Alto} | {Ação preventiva ou contingência} | {Monitorado/Mitigado} |
| RSK-{XXX}-02 | {Ex: WatermelonDB sync falha em batch > 1000} | Média | Alto | Limitar batch size a 500; paginar sync | Monitorado |
| RSK-{XXX}-03 | {Ex: Performance do endpoint em alta carga} | Baixa | Médio | Adicionar índice composto; testar k6 | Planejado |

---

## 11. Dívida Técnica e Decisões

> **Registre aqui decisões tomadas durante o desenvolvimento e dívidas conscientes.**

| Data | Decisão / Dívida | Contexto | Impacto | Ação futura | Status |
|------|------------------|----------|---------|-------------|--------|
| {YYYY-MM-DD} | {Ex: Usar raw query ao invés de Prisma para performance} | {Ex: Prisma gerava N+1 no aggregate} | {Ex: Menos type-safe} | {Ex: Refatorar para Prisma quando suportar groupBy} | {Pendente} |
| {YYYY-MM-DD} | {Ex: Simplificar validação de CPF no MVP} | {Ex: Lib de validação aumentava bundle em 50KB} | {Ex: Validação básica apenas} | {Ex: Adicionar lib no PRP-00X} | {Pendente} |

---

## 12. Execution Log

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

## 13. Cross-Cutting Concerns (CCC)

> **⚠️ REGRA: Preenchimento obrigatório para TODO PRP.** Liste aqui os requisitos
> não-funcionais transversais que este PRP DEVE implementar. O objetivo é garantir que
> artefatos compartilhados (auth, testes, logs, segurança) não fiquem de fora por
> pertencerem a "nenhum PRP específico".
>
> **Como preencher:** Revise cada linha abaixo e marque se este PRP implementa, consome
> ou é indiferente àquele CCC. Para cada CCC marcado como "implementa", deve haver
> tarefa correspondente na seção §6 (Componentes/UX) ou §9 (Testes).
>
> **Fonte para verificação:** O Step 6 (Tasks) usa esta seção para garantir que as
> tarefas transversais sejam geradas. O Step 11 (Execução) verifica se os CCCs foram
> implementados antes de marcar o PRP como completo.

### 13.1 Matriz de CCC

| # | CCC | Este PRP implementa? | Este PRP consome? | Tarefa correspondente |
|---|-----|:--------------------:|:-----------------:|-----------------------|
| 1 | **AuthService** — serviço centralizado de autenticação | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 2 | **AuthGuard** — guarda de rota autenticada | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 3 | **Token Refresh Interceptor** — renovação automática de JWT | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 4 | **Testes unitários** de controllers e services (ver §9) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 5 | **Testes de integração** de endpoints HTTP (ver §9) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 6 | **Audit logging** para operações críticas (CREATE, UPDATE, DELETE) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 7 | **Input validation** (Zod, Pydantic, class-validator) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 8 | **Rate limiting** (endpoints expostos) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 9 | **Error handling padronizado** (tratamento de exceções, respostas de erro consistentes) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |
| 10 | **Acessibilidade** (WCAG, axe-core, keyboard nav) | ☐ Sim / ☐ Não | ☐ Sim / ☐ Não | `TASK-{NNN}` |

### 13.2 Decisões de CCC

| Decisão | Justificativa |
|---------|---------------|
| {Ex: Auth não será implementado neste PRP porque já existe no PRP-002} | {Ex: PRP-002 já implementa AuthService + AuthGuard + interceptor} |
| {Ex: Rate limiting adiado para PRP-020} | {Ex: MVP sem exposição pública} |

---

## 14. Definition of Done (DoD) — Checklist Final

> **Este PRP só pode ser marcado como ✅ Complete se TODOS os itens obrigatórios estiverem checkados.**
> **Itens opcionais são marcados com [O].**

### CCC
- [ ] Cross-Cutting Concerns (seção 13) foram implementados ou têm justificativa registrada
- [ ] Nenhum CCC marcado como "implementa" ficou sem tarefa correspondente

### Funcional
- [ ] Todos os RF listados na seção 2 estão implementados e testados (verificado mecanicamente por `prp_verify.py` — colunas Teste(s)/Arquivo(s) impl da §2 preenchidas)
- [ ] API Contracts (seção 5) refletem exatamente o código entregue
- [ ] Component Spec (seção 6) reflete exatamente o UI entregue
- [ ] Data Model (seção 7) definido para todas as entidades deste PRP
- [ ] Database Changes (seção 8) estão aplicados e testados em staging

### Técnico
- [ ] Todos os testes da seção 9 estão escritos e passando
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
- [ ] Dívida técnica registrada na seção 11 (se houver)
- [ ] Deploy em staging validado e acessível
- [ ] Changelog atualizado (se houver breaking change)

---

## 15. 📖 user_docs — Documentacao de Usuario

> Preenchimento obrigatorio se o PRP envolver interface de usuario ou fluxo
> visivel ao usuario final. Deixar vazio para PRPs puramente internos (infra, CI/CD).
>
> As paginas aqui declaradas serao geradas automaticamente como arquivos Markdown
> em `docs/user-guide/[modulo]/` durante a execucao do PRP (Step 11).

### Paginas

| Arquivo | Titulo | Perfil |
|---------|--------|--------|
| `modulo/pagina.md` | Titulo Amigavel | {Nome do Perfil} |

### `modulo/pagina.md`

#### Topicos
- [ ] Topico 1 — o que o usuario aprende
- [ ] Topico 2 — passo a passo
- [ ] ...

#### Capturas de Tela (se aplicavel)
- [ ] 📸 Tela: [nome da tela] — [o que o usuario ve]
- [ ] 📸 Tela: [nome da tela] — [o que o usuario ve]

> **📸 Capturas de Tela:**
> - Se **Playwright, Puppeteer ou Selenium** estiver instalado, screenshots PNG sao geradas automaticamente em `docs/user-guide/[modulo]/img/`.
> - Caso contrario, **diagramas Mermaid** do fluxo da tela sao gerados inline no arquivo `.md`.
> - Se nenhum dos dois estiver disponivel, uma **descricao textual estruturada** e gerada.
> - Para adicionar screenshots manualmente, veja a secao de FAQ.

---

> **Nota:** Este PRP é um documento vivo. Atualize a "Última atualização" e "Versão" sempre que houver mudança. A versão no repositório (`docs/prps/PRP-XXX.md`) é a fonte da verdade.
