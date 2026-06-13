# Tasks — Backlog de Desenvolvimento

> **Versão:** {X.Y} | **Última atualização:** {YYYY-MM-DD} | **Status:** {Em execução / Finalizado}
> **Projeto:** {Nome do Projeto} | **Metodologia:** PRP-Based Development + Dependency Matrix
> **Autor:** {Tech Lead / EM / PM} | **Referências:** `{Development Plan}`, `{Dependency Matrix}`, `{Execution Waves}`

---

## 📋 Checklist Pré-Preenchimento

Este documento é a **fonte da verdade operacional** do que precisa ser feito. Antes de preencher:
- [ ] Development Plan aprovado com fases e PRPs definidos
- [ ] Dependency Matrix validada (ondas e dependências)
- [ ] Capacidade do time definida (quantos devs, quantas tarefas paralelas)
- [ ] Definition of Done (DoD) acordada com o time
- [ ] Template de PRP revisado e disponível (`docs/prps/PRP-XXX.md`)

---

## 1. Visão Geral do Backlog

### 1.1 Propósito
Este documento é o **backlog operacional** do projeto. Ele organiza todas as tarefas por PRP, fase e onda, servindo como:
- **Ponto de entrada** para devs saberem o que trabalhar
- **Fonte da verdade** para status de cada PRP
- **Relatório** para stakeholders de progresso
- **Histórico** para auditoria e retrospectivas

> **Exemplo (NeuroHub):** *"Backlog de 35 PRPs organizados em 6 fases e 8 ondas de execução. 30 PRPs completos, 5 planejados para Ondas 7-8."*

### 1.2 Resumo Executivo

| Métrica | Valor | Tendência | Observação |
|---------|-------|-----------|------------|
| **Total PRPs** | {X} | — | Do Development Plan |
| **Completos** | {Y} | {↑/↓/→} | DoD 100% atendido |
| **Em andamento** | {Z} | {↑/↓/→} | Com owner atribuído |
| **Planejados** | {W} | — | Especificados, não iniciados |
| **Bloqueados** | {V} | {↑/↓/→} | Impedimento ativo |
| **Progresso geral** | {Y/X %} | — | — |
| **Ondas completas** | {N} | — | Do Execution Waves |
| **Onda atual** | {Onda M} | — | {Nome da onda} |
| **Velocity média** | {PRPs/semana} | — | Baseado em Execution Waves |
| **Cobertura de testes** | {X%} | {↑/↓/→} | Target: 80% |
| **Débito técnico** | {N itens} | {↑/↓/→} | Da seção 10 dos PRPs |

---

## 2. Legenda e Convenções

### 2.1 Status de PRP

| Símbolo | Status | Definição | Quem altera | Quando alterar |
|---------|--------|-----------|-------------|----------------|
| ✅ | Complete | DoD 100% atendido, mergeado na branch principal, deploy staging OK | Tech Lead | Após validação final |
| 🔄 | In Progress | Dev iniciou, código em desenvolvimento, PR pode estar aberto | Dev Owner | Quando começar a codar |
| ⏳ | Planned | Especificado no PRP, priorizado, mas não iniciado | PM | Quando priorizado |
| 🛑 | Blocked | Impedimento técnico ou de negócio ativo | Tech Lead | Quando impedimento identificado |
| ❌ | Cancelled | Removido do escopo, documentar razão | PM | Quando escopo muda |
| ⏸️ | Paused | Suspensão temporária, documentar razão | Tech Lead | Quando necessário pausar |

### 2.2 Status de Tarefa (dentro do PRP)

| Símbolo | Status | Definição |
|---------|--------|-----------|
| [x] | Done | Tarefa concluída |
| [ ] | Todo | Tarefa pendente |
| [~] | In Progress | Tarefa em execução |
| [-] | N/A | Não aplicável a este PRP |
| [?] | Blocked | Bloqueada por dependência externa |

### 2.3 Prioridade

| Nível | Definição | Impacto no release |
|-------|-----------|-------------------|
| **Crítico** | Sem isso, o release não sai | Bloqueante |
| **Alto** | Importante para MVP, mas release pode sair sem | Patch posterior aceitável |
| **Médio** | Desejável, se houver tempo | Backlog próximo |
| **Baixo** | Nice to have, reconhecidamente fora do escopo desta versão | vNext |

### 2.4 Complexidade

| Nível | Estimativa (dias) | Características |
|-------|-------------------|-----------------|
| **Baixa** | 1-2 | CRUD simples, UI com componentes existentes, testes triviais |
| **Média** | 3-5 | Lógica de negócio, integração com 1 serviço, testes de integração |
| **Alta** | 6-10 | Algoritmo complexo, múltiplas integrações, sync, performance, segurança |

---

## 3. Fases e PRPs

> **Estrutura obrigatória:** Cada fase contém PRPs. Cada PRP contém tarefas detalhadas.
> **Use o template de PRP (`docs/prps/PRP-XXX.md`) para a especificação completa de cada PRP.**

---

### Phase 0: {Nome da Fase} (Sprint {N})

**Objetivo:** {Uma frase descrevendo o valor entregue}
**Persona principal:** {Quem se beneficia}
**Onda(s):** {Onda 1}
**Status da fase:** {✅ Completa / 🔄 Em andamento / ⏳ Planejada}

#### PRP-001: F0.1 — {Project Foundation & Setup}

> **ID:** PRP-001 | **Onda:** 1 | **Prioridade:** Crítico | **Complexidade:** Baixa
> **Owner:** {Nome} | **Estimativa:** 3 dias | **Real:** 3 dias | **Status:** ✅ Complete
> **Depende de:** — (primeiro PRP) | **Desbloqueia:** F0.2, F0.3, F0.4

**Resumo:** {Uma frase do que este PRP entrega}

**Tarefas:**
- [x] Setup Monorepo (Turborepo) — Web, Mobile, API
- [x] Configurar Docker e Docker Compose (PostgreSQL, Redis)
- [x] Setup NestJS (Backend) — Estrutura de pastas, ConfigService, Logger
- [x] Setup React (Web) — Vite, Tailwind, Shadcn/UI
- [x] Setup React Native (Mobile) — Expo, NativeWind
- [x] Setup Database (PostgreSQL) — Migrations (Prisma)
- [x] CI pipeline base (GitHub Actions)

**Arquivos criados/alterados:**
- `apps/api/` — Estrutura NestJS
- `apps/web/` — Vite + React
- `apps/mobile/` — Expo + React Native
- `docker-compose.yml` — PostgreSQL + Redis
- `.github/workflows/ci.yml` — Pipeline base

**Notas:**
- {Ex: Turborepo remote cache configurado}
- {Ex: TypeScript strict mode habilitado}

---

#### PRP-002: F0.2 — {Authentication & Authorization}

> **ID:** PRP-002 | **Onda:** 1 | **Prioridade:** Crítico | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F0.1 ✅ | **Desbloqueia:** F1.2, F1.5, F2.1, F3.1

**Resumo:** {Autenticação JWT com Passport, login/register, guards e bypass para dev}

**Tarefas:**
- [x] Auth Local (NestJS JWT/Passport) — Login, Register
- [x] JWT Guard global
- [x] Auth Bypass para desenvolvimento (`AUTH_ENABLED=false`)
- [x] Frontend login page e AuthContext
- [x] Mobile login screen e AuthContext
- [x] Testes unitários (auth.service.spec.ts)
- [x] Testes E2E (auth.e2e-spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/auth/` — Module, Service, Controller, Guards, DTOs
- `apps/web/src/context/AuthContext.tsx`
- `apps/mobile/src/context/AuthContext.tsx`
- `apps/web/src/app/login/page.tsx`
- `apps/mobile/src/screens/LoginScreen.tsx`

**Notas:**
- {Ex: Auth bypass facilita desenvolvimento local, mas é débito técnico (DT-001)}

---

#### PRP-003: F1.1 — {Database Setup & Schema}

> **ID:** PRP-003 | **Onda:** — | **Prioridade:** Crítico | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F0.1 ✅ | **Desbloqueia:** F1.2, F1.3, F1.4, F0.4

**Resumo:** {Schema Prisma com 24+ entidades, multi-tenancy, audit trail}

**Tarefas:**
- [x] Definir schema Prisma (24+ entidades)
- [x] Configurar PrismaService com repository pattern
- [x] Multi-tenancy (`organization_id` em todas as queries)
- [x] Migrations iniciais
- [x] Seed scripts base
- [x] Testes de integração (PrismaService)

**Arquivos criados/alterados:**
- `apps/api/prisma/schema.prisma`
- `apps/api/prisma/migrations/`
- `apps/api/src/prisma/prisma.service.ts`

**Notas:**
- {Ex: Schema evoluiu durante o projeto — manter migrations versionadas}

---

#### PRP-004: F0.3 — {CI/CD Pipeline}

> **ID:** PRP-004 | **Onda:** 1 | **Prioridade:** Crítico | **Complexidade:** Baixa
> **Owner:** {Nome} | **Estimativa:** 3 dias | **Real:** 2 dias | **Status:** ✅ Complete
> **Depende de:** F0.1 ✅ | **Desbloqueia:** — (infraestrutura)

**Resumo:** {Pipeline completo: lint, type-check, testes, validação Prisma, E2E}

**Tarefas:**
- [x] GitHub Actions: Lint (ESLint + Prettier)
- [x] GitHub Actions: Type Check (TypeScript strict)
- [x] GitHub Actions: Testes unitários + coverage
- [x] GitHub Actions: Validação Prisma (schema + migrations)
- [x] GitHub Actions: E2E tests (Playwright)
- [ ] Deploy em staging/production ⬜ (pendente — fora do escopo desta PRP)

**Arquivos criados/alterados:**
- `.github/workflows/ci.yml`
- `.github/workflows/e2e.yml`
- `turbo.json` — Pipelines de build/test/lint

**Notas:**
- {Ex: Deploy em produção será PRP futuro (infra)}

---

#### PRP-005: F0.4 — {Seed Data}

> **ID:** PRP-005 | **Onda:** 1 | **Prioridade:** Médio | **Complexidade:** Baixa
> **Owner:** {Nome} | **Estimativa:** 2 dias | **Real:** 2 dias | **Status:** ✅ Complete
> **Depende de:** F1.1 ✅ | **Desbloqueia:** —

**Resumo:** {Dados de exemplo para desenvolvimento e testes}

**Tarefas:**
- [x] Seed de organização padrão
- [x] Seed de usuários (admin, terapeuta, pai, escola)
- [x] Seed de pacientes de exemplo
- [x] Seed de metas e lições de exemplo
- [x] Documentação de como usar seeds

**Arquivos criados/alterados:**
- `apps/api/prisma/seed.ts`
- `apps/api/src/test-helpers/factories/`

**Notas:**
- {Ex: Seeds simplificados para MVP — dados realistas serão adicionados posteriormente}

---

### Phase 1: {Nome da Fase} (Sprint {N-M})

**Objetivo:** {Permitir cadastro de pacientes, terapeutas e criação de PEI}
**Persona principal:** {Coordenador, Terapeuta}
**Onda(s):** {Onda 2, Onda 3}
**Status da fase:** {✅ Completa}

#### PRP-006: F1.2 — {Users CRUD API}

> **ID:** PRP-006 | **Onda:** 2 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F0.2 ✅, F1.1 ✅ | **Desbloqueia:** F1.6

**Resumo:** {CRUD de usuários com perfis especializados e RBAC}

**Tarefas:**
- [x] CRUD API de usuários (POST, GET, PATCH, DELETE /users)
- [x] Perfis especializados (TherapistProfile, ParentProfile, SchoolProfile)
- [x] RBAC (ADMIN, THERAPIST, PARENT, SCHOOL, ORGANIZATION_ADMIN)
- [x] Multi-tenancy (`organization_id` em todas as queries)
- [x] Audit logging (CREATE, UPDATE, DELETE)
- [x] Testes unitários (users.service.spec.ts)
- [x] Testes E2E (users.e2e-spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/users/` — Module, Service, Controller, DTOs
- `apps/api/src/users/entities/` — User entities
- `apps/api/src/test-helpers/factories/user.factory.ts`

**Notas:**
- {Ex: Perfis armazenados como JSONB para flexibilidade}

---

#### PRP-007: F1.3 — {Patients CRUD API}

> **ID:** PRP-007 | **Onda:** 2 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F1.1 ✅ | **Desbloqueia:** F1.7, F2.2, F3.1

**Resumo:** {CRUD de pacientes com escopo por organização}

**Tarefas:**
- [x] CRUD API de pacientes (POST, GET, PATCH, DELETE /patients)
- [x] Campos de perfil (diagnóstico, nível de suporte, comorbidades — parcial)
- [x] Multi-tenancy (`organization_id` em todas as queries)
- [x] Relação com usuários (terapeuta responsável, pais vinculados)
- [x] Audit logging
- [x] Testes unitários e E2E

**Arquivos criados/alterados:**
- `apps/api/src/patients/` — Module, Service, Controller, DTOs
- `apps/api/src/test-helpers/factories/patient.factory.ts`

**Notas:**
- {Ex: Campos de diagnóstico/comorbidades básicos — detalhamento pendente para vNext}

---

#### PRP-008: F1.4 — {Goals/PEI CRUD API}

> **ID:** PRP-008 | **Onda:** 2 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 6 dias | **Real:** 6 dias | **Status:** ✅ Complete
> **Depende de:** F1.1 ✅ | **Desbloqueia:** F1.8

**Resumo:** {Hierarquia PEI: Meta LP → Objetivo MP → Lição CP}

**Tarefas:**
- [x] CRUD de metas (goals) com hierarquia LP/MP/CP
- [x] CRUD de lições (lessons) sob meta CP
- [x] Relações pai-filho no schema (self-referencing)
- [x] Validação de hierarquia (LP não pode ter pai, CP não pode ter filho)
- [x] Multi-tenancy
- [x] Audit logging
- [x] Testes unitários e E2E

**Arquivos criados/alterados:**
- `apps/api/src/goals/` — Module, Service, Controller, DTOs
- `apps/api/prisma/schema.prisma` — Relações goals/lessons

**Notas:**
- {Ex: Hierarquia validada no service, não apenas no banco}

---

#### PRP-009: F1.5 — {Web Dashboard Layout}

> **ID:** PRP-009 | **Onda:** 2 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F0.2 ✅ | **Desbloqueia:** F1.6, F1.7, F1.8

**Resumo:** {Layout base do dashboard com sidebar, header e AuthContext}

**Tarefas:**
- [x] DashboardLayout component (sidebar + header + main content area)
- [x] Sidebar navigation com roles (mostra/esconde itens por role)
- [x] Header com user info, logout, notifications (placeholder)
- [x] AuthContext provider (JWT, refresh, logout)
- [x] Roteamento protegido (redirect se não autenticado)
- [x] Design System tokens aplicados (cores, tipografia, espaçamento)

**Arquivos criados/alterados:**
- `apps/web/src/components/Dashboard/DashboardLayout.tsx`
- `apps/web/src/components/Sidebar/Sidebar.tsx`
- `apps/web/src/components/Header/Header.tsx`
- `apps/web/src/context/AuthContext.tsx`
- `apps/web/src/app/dashboard/layout.tsx`

**Notas:**
- {Ex: Layout responsivo — sidebar colapsa em mobile}

---

#### PRP-010: F1.6 — {Users Management UI}

> **ID:** PRP-010 | **Onda:** 3 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F1.2 ✅, F1.5 ✅ | **Desbloqueia:** —

**Resumo:** {Interface web para gestão de usuários}

**Tarefas:**
- [x] UsersList component (tabela com paginação, filtros)
- [x] UserForm component (criar/editar com validação Zod)
- [x] UserModal component (visualização detalhada)
- [x] useUsers hook (CRUD via API)
- [x] Página `/dashboard/users`
- [x] Testes unitários (React Testing Library)
- [x] Testes E2E (Playwright)

**Arquivos criados/alterados:**
- `apps/web/src/components/Users/UsersList.tsx`
- `apps/web/src/components/Users/UserForm.tsx`
- `apps/web/src/components/Users/UserModal.tsx`
- `apps/web/src/hooks/useUsers.ts`
- `apps/web/src/app/dashboard/users/page.tsx`

**Notas:**
- {Ex: Filtro por role e organização}

---

#### PRP-011: F1.7 — {Patients Management UI}

> **ID:** PRP-011 | **Onda:** 3 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F1.3 ✅, F1.5 ✅ | **Desbloqueia:** —

**Resumo:** {Interface web para gestão de pacientes}

**Tarefas:**
- [x] PatientsList component (cards + tabela)
- [x] PatientForm component (criar/editar)
- [x] PatientModal component (visualização detalhada)
- [x] usePatients hook (CRUD via API)
- [x] Página `/dashboard/patients`
- [x] Testes unitários e E2E

**Arquivos criados/alterados:**
- `apps/web/src/components/Patients/PatientsList.tsx`
- `apps/web/src/components/Patients/PatientForm.tsx`
- `apps/web/src/components/Patients/PatientModal.tsx`
- `apps/web/src/hooks/usePatients.ts`
- `apps/web/src/app/dashboard/patients/page.tsx`

**Notas:**
- {Ex: Cards mostram foto, nome, idade, terapeuta responsável}

---

#### PRP-012: F1.8 — {PEI Editor UI}

> **ID:** PRP-012 | **Onda:** 3 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 6 dias | **Real:** 6 dias | **Status:** ✅ Complete
> **Depende de:** F1.4 ✅, F1.5 ✅ | **Desbloqueia:** —

**Resumo:** {Editor visual da hierarquia PEI com árvore interativa}

**Tarefas:**
- [x] PEITree component (árvore hierárquica LP → MP → CP)
- [x] GoalForm component (criar/editar meta)
- [x] LessonForm component (criar/editar lição)
- [x] Drag-and-drop para reordenar (se aplicável)
- [x] useGoals hook (CRUD via API)
- [x] Página `/dashboard/patients/[id]/pei`
- [x] Testes unitários e E2E

**Arquivos criados/alterados:**
- `apps/web/src/components/PEI/PEITree.tsx`
- `apps/web/src/components/PEI/GoalForm.tsx`
- `apps/web/src/components/PEI/LessonForm.tsx`
- `apps/web/src/hooks/useGoals.ts`
- `apps/web/src/app/dashboard/patients/[id]/pei/page.tsx`

**Notas:**
- {Ex: Tree component cresceu muito — considerar dividir em sub-componentes}

---

### Phase 2: {Nome da Fase} (Sprint {N-M})

**Objetivo:** {Coleta de dados em sessão (offline-first)}
**Persona principal:** {Terapeuta}
**Onda(s):** {Onda 2, Onda 3, Onda 4}
**Status da fase:** {✅ Completa}

#### PRP-013: F2.1 — {Mobile Auth & Sync}

> **ID:** PRP-013 | **Onda:** 2 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F0.2 ✅ | **Desbloqueia:** F2.2, F2.4

**Resumo:** {Autenticação mobile e contexto de sync}

**Tarefas:**
- [x] LoginScreen (mobile) com email/senha
- [x] AuthContext (mobile) com JWT e refresh
- [x] Integração com API de login
- [x] Cache de credenciais (secure storage)
- [x] Logout e limpeza de cache
- [x] Testes unitários (React Native Testing Library)

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/LoginScreen.tsx`
- `apps/mobile/src/context/AuthContext.tsx`
- `apps/mobile/src/lib/api.ts`

**Notas:**
- {Ex: Secure storage usa Keychain (iOS) e Keystore (Android)}

---

#### PRP-014: F2.2 — {Mobile Home Screen}

> **ID:** PRP-014 | **Onda:** 3 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F2.1 ✅, F1.3 ✅ | **Desbloqueia:** F2.3

**Resumo:** {Tela inicial com lista de pacientes e menu rápido}

**Tarefas:**
- [x] HomeScreen com lista de pacientes
- [x] Busca e filtro de pacientes
- [x] Menu rápido (nova sessão, daily log, etc.)
- [x] Stats do dia (sessões agendadas, pendentes)
- [x] Offline — cache de pacientes no login
- [x] Testes unitários

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/HomeScreen.tsx`
- `apps/mobile/src/components/PatientCard.tsx`
- `apps/mobile/src/hooks/usePatients.ts`

**Notas:**
- {Ex: Cache de pacientes limitado a 50 para performance inicial}

---

#### PRP-015: F2.3 — {Session Recording}

> **ID:** PRP-015 | **Onda:** 4 | **Prioridade:** Crítico | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 6 dias | **Real:** 6 dias | **Status:** ✅ Complete
> **Depende de:** F2.2 ✅ | **Desbloqueia:** F2.5, F2.6, F4.1

**Resumo:** {Gravação de sessão com timer, contadores, mood e notas}

**Tarefas:**
- [x] SessionScreen com timer (start/pause/stop)
- [x] Frequency counter (increment/decrement)
- [x] Mood selector (emoji scale)
- [x] Behavior notes (texto livre)
- [x] Seleção de meta/lição do PEI
- [x] Salvamento local (WatermelonDB) — offline-first
- [x] Testes unitários

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/SessionScreen.tsx`
- `apps/mobile/src/components/Timer.tsx`
- `apps/mobile/src/components/FrequencyCounter.tsx`
- `apps/mobile/src/components/MoodSelector.tsx`
- `apps/mobile/src/database/models.ts` — Session model

**Notas:**
- {Ex: Timer usa `setInterval` com correção de drift}
- {Ex: Dados salvos a cada 30s para evitar perda}

---

#### PRP-016: F2.4 — {WatermelonDB Schema}

> **ID:** PRP-016 | **Onda:** 3 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 3 dias | **Real:** 3 dias | **Status:** ✅ Complete
> **Depende de:** F2.1 ✅ | **Desbloqueia:** F2.5, F3.2, F3.4

**Resumo:** {Schema local SQLite com WatermelonDB para offline-first}

**Tarefas:**
- [x] Schema de pacientes (patients table)
- [x] Schema de metas e lições (goals, lessons tables)
- [x] Schema de daily logs (daily_logs table)
- [x] Schema de sessões (sessions table)
- [x] Schema de sync records (sync_records table)
- [x] Models com decorators (@field, @relation)
- [x] Configuração de sync (push/pull)
- [x] Testes de integração

**Arquivos criados/alterados:**
- `apps/mobile/src/database/schema.ts`
- `apps/mobile/src/database/models.ts`
- `apps/mobile/src/database/sync.ts`

**Notas:**
- {Ex: Schema evoluiu — adicionar migrations locais para vNext}
- {Ex: Performance testada com 1000 registros — OK}

---

#### PRP-017: F2.5 — {API Sync Endpoint}

> **ID:** PRP-017 | **Onda:** 4 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F2.3 ✅, F2.4 ✅ | **Desbloqueia:** —

**Resumo:** {Endpoint de sync batch com resolução de conflitos}

**Tarefas:**
- [x] POST /api/sync/batch (recebe batch de registros)
- [x] Validação de schema por entidade
- [x] Resolução de conflitos (Last-Write-Wins para dados brutos)
- [x] Audit logging para alterações sensíveis
- [x] GET /api/sync/status/:id (status do sync)
- [x] Testes unitários (sync.service.spec.ts)
- [x] Testes E2E (sync.e2e-spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/sync/` — Module, Service, Controller, DTOs
- `apps/api/src/sync/dto/sync-batch.dto.ts`
- `apps/api/src/sync/dto/sync-result.dto.ts`

**Notas:**
- {Ex: Batch limitado a 500 registros para performance}
- {Ex: Conflitos de PEI usam manual merge + flag}

---

#### PRP-018: F2.6 — {Post-Session Summary}

> **ID:** PRP-018 | **Onda:** 4 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F2.3 ✅ | **Desbloqueia:** —

**Resumo:** {Resumo pós-sessão com estatísticas e métricas}

**Tarefas:**
- [x] SessionSummaryScreen (stats da sessão)
- [x] Duração total, contadores, mood médio
- [x] Comparação com sessões anteriores
- [x] Notas consolidadas
- [x] Opção de editar antes de sync
- [x] Testes unitários

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/SessionSummaryScreen.tsx`
- `apps/mobile/src/components/SessionStats.tsx`

**Notas:**
- {Ex: Stats calculadas localmente — não dependem de API}

---

### Phase 3: {Nome da Fase} (Sprint {N-M})

**Objetivo:** {Engajamento da família e escola}
**Persona principal:** {Pai, Coordenador escolar}
**Onda(s):** {Onda 3, Onda 4}
**Status da fase:** {✅ Completa}

#### PRP-019: F3.1 — {Daily Log Backend}

> **ID:** PRP-019 | **Onda:** 3 | **Prioridade:** Médio | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F1.3 ✅, F0.2 ✅ | **Desbloqueia:** F3.2, F3.3

**Resumo:** {CRUD de daily logs com audit logging}

**Tarefas:**
- [x] CRUD API de daily logs (POST, GET, PATCH, DELETE)
- [x] Campos: mood, sleep, appetite, medications, notes
- [x] Filtros por data, paciente, tipo
- [x] Audit logging completo
- [x] Multi-tenancy
- [x] Testes unitários e E2E

**Arquivos criados/alterados:**
- `apps/api/src/daily-logs/` — Module, Service, Controller, DTOs
- `apps/api/src/test-helpers/factories/daily-log.factory.ts`

**Notas:**
- {Ex: Daily logs são dados sensíveis — audit trail completo}

---

#### PRP-020: F3.2 — {Daily Log Mobile}

> **ID:** PRP-020 | **Onda:** 4 | **Prioridade:** Médio | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F3.1 ✅, F2.4 ✅ | **Desbloqueia:** —

**Resumo:** {Formulário mobile de daily log}

**Tarefas:**
- [x] DailyLogFormScreen (mood, sleep, appetite, medications)
- [x] Slider/selector para cada campo
- [x] Salvamento local (WatermelonDB)
- [x] Sync automático quando online
- [x] Testes unitários

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/DailyLogFormScreen.tsx`
- `apps/mobile/src/components/DailyLogForm.tsx`

**Notas:**
- {Ex: Form otimizado para preenchimento rápido (< 2 min)}

---

#### PRP-021: F3.3 — {Task Analysis Generator}

> **ID:** PRP-021 | **Onda:** 4 | **Prioridade:** Médio | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F3.1 ✅ | **Desbloqueia:** —

**Resumo:** {Formulário web de Análise de Tarefa (ABC: Antecedent-Behavior-Consequence)}

**Tarefas:**
- [x] TaskAnalysisForm component (Antecedent, Behavior, Consequence)
- [x] Seleção de paciente e contexto
- [x] Salvamento e edição
- [x] Visualização histórica
- [x] Testes unitários (React Testing Library)

**Arquivos criados/alterados:**
- `apps/web/src/components/TaskAnalysis/TaskAnalysisForm.tsx`
- `apps/web/src/app/dashboard/task-analysis/page.tsx`

**Notas:**
- {Ex: Form usado por coordenadores e terapeutas}

---

#### PRP-022: F3.4 — {PLACHECK Tool}

> **ID:** PRP-022 | **Onda:** 4 | **Prioridade:** Médio | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F2.4 ✅ | **Desbloqueia:** —

**Resumo:** {Ferramenta PLACHECK com timer de intervalo e tracking de engajamento}

**Tarefas:**
- [x] PLACHECKScreen (interval timer)
- [x] Quick count de engajamento
- [x] Registro por intervalo
- [x] Salvamento local
- [x] Testes unitários

**Arquivos criados/alterados:**
- `apps/mobile/src/screens/PLACHECKScreen.tsx`
- `apps/mobile/src/components/IntervalTimer.tsx`
- `apps/mobile/src/components/EngagementTracker.tsx`

**Notas:**
- {Ex: Timer de intervalo configurável (15s, 30s, 60s)}

---

### Phase 4: {Nome da Fase} (Sprint {N-M})

**Objetivo:** {Inteligência de dados e escala}
**Persona principal:** {Coordenador, Terapeuta, Pai}
**Onda(s):** {Onda 5}
**Status da fase:** {✅ Completa}

#### PRP-023: F4.1 — {Analytics Aggregation}

> **ID:** PRP-023 | **Onda:** 5 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F2.3 ✅ | **Desbloqueia:** F4.2, F4.3

**Resumo:** {Endpoints de analytics por paciente, terapeuta e organização}

**Tarefas:**
- [x] GET /api/analytics/patient/:id (stats do paciente)
- [x] GET /api/analytics/therapist/:id (stats do terapeuta)
- [x] GET /api/analytics/organization (stats da org)
- [x] Agregações: sessões, progresso, mood trends
- [x] Otimização de queries (índices, raw SQL se necessário)
- [x] Testes unitários (analytics.service.spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/analytics/` — Module, Service, Controller
- `apps/api/src/analytics/analytics.service.ts`

**Notas:**
- {Ex: Queries complexas usam raw SQL para performance}
- {Ex: Dados anonimizados para analytics}

---

#### PRP-024: F4.2 — {Analytics Dashboard}

> **ID:** PRP-024 | **Onda:** 5 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F4.1 ✅ | **Desbloqueia:** —

**Resumo:** {Dashboard web com cards e estatísticas visuais}

**Tarefas:**
- [x] AnalyticsDashboard component (cards com stats)
- [x] Gráficos de tendência (Recharts)
- [x] Filtros por período, paciente, terapeuta
- [x] useAnalytics hook
- [x] Testes unitários (React Testing Library)

**Arquivos criados/alterados:**
- `apps/web/src/components/Analytics/AnalyticsDashboard.tsx`
- `apps/web/src/hooks/useAnalytics.ts`
- `apps/web/src/app/dashboard/analytics/page.tsx`

**Notas:**
- {Ex: Cards responsivos com Skeleton enquanto carrega}

---

#### PRP-025: F4.3 — {PDF Report Generation}

> **ID:** PRP-025 | **Onda:** 5 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 6 dias | **Real:** 6 dias | **Status:** ✅ Complete
> **Depende de:** F4.1 ✅ | **Desbloqueia:** —

**Resumo:** {Geração de relatórios PDF de paciente e progresso}

**Tarefas:**
- [x] ReportsModule (NestJS)
- [x] Relatório de paciente (dados cadastrais + histórico)
- [x] Relatório de progresso (percentuais por meta/lição)
- [x] Template PDF (header, footer, branding)
- [x] GET /api/reports/patient/:id
- [x] GET /api/reports/patient/:id/progress
- [x] Testes unitários (reports.service.spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/reports/` — Module, Service, Controller
- `apps/api/src/reports/templates/` — PDF templates

**Notas:**
- {Ex: Usar Puppeteer + HTML template para PDF}
- {Ex: Relatórios em português, formato A4}

---

#### PRP-INFRA: {Audit Module (Global)}

> **ID:** PRP-INFRA | **Onda:** 5 | **Prioridade:** Crítico | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 3 dias | **Real:** 3 dias | **Status:** ✅ Complete
> **Depende de:** F0.1 ✅ | **Desbloqueia:** Todos os módulos de domínio

**Resumo:** {Módulo global de audit logging para todas as operações de escrita}

**Tarefas:**
- [x] AuditModule com @Global() decorator
- [x] AuditService com métodos log(), findByEntity()
- [x] Ações suportadas: CREATE, UPDATE, DELETE, EXPORT, LOGIN
- [x] Integração com todos os módulos de domínio
- [x] Schema: who, what, when, old_val, new_val
- [x] Testes unitários (audit.service.spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/audit/` — Module, Service
- `apps/api/src/audit/audit.service.ts`

**Notas:**
- {Ex: Audit logs append-only — nunca deletar}
- {Ex: Particionar por mês se volume > 1M/ano}

---

### Phase 5: {Nome da Fase} (Sprint {N})

**Objetivo:** {Completar fluxos das personas prioritárias para MVP demonstrável}
**Persona principal:** {Coordenador, Pai}
**Onda(s):** {Onda 6}
**Status da fase:** {✅ Completa}

#### PRP-026: F5.1 — {Feedback Dimensions API}

> **ID:** PRP-026 | **Onda:** 6 | **Prioridade:** Alto | **Complexidade:** Alta
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** Ondas 1-5 ✅ | **Desbloqueia:** F5.2, F5.4

**Resumo:** {Feedbacks estruturados em 8 dimensões de desenvolvimento}

**Tarefas:**
- [x] CRUD de feedbacks (POST, GET, PATCH, DELETE)
- [x] 8 dimensões: Comunicação, Social, Pedagógica, Psicomotora, Comportamento, Sensorial, Adaptativa, Cognitiva
- [x] Templates de feedback por role (campos dinâmicos via JSON)
- [x] Resumo por paciente (cobertura, último feedback, avg mood)
- [x] GET /api/feedbacks/patient/:id/summary
- [x] GET /api/feedbacks/templates/:role
- [x] Testes unitários (feedback-dimensions.service.spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/feedback-dimensions/` — Module, Service, Controller, DTOs
- `apps/api/prisma/schema.prisma` — feedbacks, feedback_templates

**Notas:**
- {Ex: Templates JSON permitem campos dinâmicos sem migration}

---

#### PRP-027: F5.2 — {Coordinator Coverage Matrix}

> **ID:** PRP-027 | **Onda:** 6 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 5 dias | **Real:** 5 dias | **Status:** ✅ Complete
> **Depende de:** F5.1 ✅ | **Desbloqueia:** —

**Resumo:** {Dashboard da coordenadora com visão Crianças × 8 Dimensões + gaps}

**Tarefas:**
- [x] CoverageMatrix component (cards com 8 dimensões)
- [x] Indicadores de gaps (dimensão sem feedback recente)
- [x] GET /api/analytics/coverage-matrix
- [x] useCoverageMatrix hook
- [x] Testes unitários (CoverageMatrix.test.tsx)
- [x] Testes do hook (useCoverageMatrix.test.ts)

**Arquivos criados/alterados:**
- `apps/web/src/components/Dashboard/CoverageMatrix.tsx`
- `apps/web/src/hooks/useCoverageMatrix.ts`
- `apps/api/src/analytics/analytics.service.ts` — getCoverageMatrix()

**Notas:**
- {Ex: Gap = sem feedback nos últimos 14 dias}
- {Ex: Cores: verde (coberto), amarelo (atrasado), vermelho (gap)}

---

#### PRP-028: F5.3 — {Invite & Onboarding}

> **ID:** PRP-028 | **Onda:** 6 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F0.2 ✅ | **Desbloqueia:** —

**Resumo:** {Sistema de convite com token 48h, aceite e cadastro}

**Tarefas:**
- [x] POST /api/invites (criar convite com token 48h)
- [x] GET /api/invites/validate/:token (validar token)
- [x] POST /api/invites/accept/:token (aceitar + criar usuário)
- [x] Email de convite (template)
- [x] Página de aceite (`/invite/[token]`)
- [x] Onboarding pós-aceite (perfil, organização)
- [x] Testes unitários (invites.service.spec.ts)

**Arquivos criados/alterados:**
- `apps/api/src/invites/` — Module, Service, Controller, DTOs
- `apps/web/src/app/invite/[token]/page.tsx`
- `apps/web/src/components/Invite/InviteAcceptForm.tsx`

**Notas:**
- {Ex: Token JWT com expiração de 48h}
- {Ex: Email enviado via SendGrid}

---

#### PRP-029: F5.4 — {Parent Dashboard}

> **ID:** PRP-029 | **Onda:** 6 | **Prioridade:** Alto | **Complexidade:** Média
> **Owner:** {Nome} | **Estimativa:** 4 dias | **Real:** 4 dias | **Status:** ✅ Complete
> **Depende de:** F5.1 ✅ | **Desbloqueia:** —

**Resumo:** {Portal simplificado para pais com progresso visual}

**Tarefas:**
- [x] ParentProgress component (cards com emoji dimensions)
- [x] Mood scores e weekly summary
- [x] GET /api/analytics/parent-progress
- [x] useParentProgress hook
- [x] Página `/dashboard/parent`
- [x] Testes unitários (ParentProgress.test.tsx)
- [x] Testes do hook (useParentProgress.test.ts)

**Arquivos criados/alterados:**
- `apps/web/src/components/Dashboard/ParentProgress.tsx`
- `apps/web/src/hooks/useParentProgress.ts`
- `apps/web/src/app/dashboard/parent/page.tsx`
- `apps/api/src/analytics/analytics.service.ts` — getParentProgress()

**Notas:**
- {Ex: Dashboard simplificado — apenas leitura para pais}
- {Ex: Emoji dimensions: 😊 Comunicação, 🤝 Social, 📚 Pedagógica, etc.}

---

## 4. PRPs Planejados (Não Iniciados)

> **Ondas futuras. Especificados no Development Plan, mas não priorizados para execução.**

### Onda 7: {Notificações e Mídia}

| PRP | ID | Nome | Prioridade | Complexidade | Status | Dependências |
|-----|----|------|------------|--------------|--------|--------------|
| F6.1 | PRP-030 | In-App Notifications | Alto | Média | ⏳ | Onda 6 completa |
| F6.2 | PRP-031 | Document/Media Upload | Alto | Média | ⏳ | Onda 6 completa |

**Resumo:**
- **PRP-030:** WebSocket gateway para notificações em tempo real, CRUD de notificações, notification bell UI.
- **PRP-031:** Upload de fotos/vídeos para feedbacks (S3/MinIO), captura nativa no mobile.

### Onda 8: {Comercial e Integrações}

| PRP | ID | Nome | Prioridade | Complexidade | Status | Dependências |
|-----|----|------|------------|--------------|--------|--------------|
| F7.1 | PRP-032 | Subscription & Billing | Médio | Alta | ⏳ | Onda 7 completa |
| F7.2 | PRP-033 | FHIR/ANS Integration | Médio | Alta | ⏳ | Onda 7 completa |
| F7.3 | PRP-034 | Professional Marketplace | Baixo | Alta | ⏳ | Onda 7 completa |

**Resumo:**
- **PRP-032:** Subscription management + billing (Stripe/MercadoPago).
- **PRP-033:** FHIR R4 API para interoperabilidade, exportação TISS/XML compatível com ANS.
- **PRP-034:** Marketplace de profissionais (busca, matching, verificação).

---

## 5. Tarefas Transversais (Não vinculadas a PRP específico)

> **Tarefas de infraestrutura, qualidade e débito técnico que afetam múltiplos PRPs.**

### Performance e Qualidade

| # | Tarefa | Prioridade | Status | Bloqueado por | Owner |
|---|--------|------------|--------|---------------|-------|
| 1 | Deploy workflow para staging/production | Alto | ⏳ | CI/CD completo | DevOps |
| 2 | Expandir cobertura de testes (~10% → 80%) | Alto | 🔄 | — | QA + Devs |
| 3 | TypeScript strict mode — remover warnings de `any` | Médio | 🔄 | — | Tech Lead |
| 4 | Query optimization e caching | Médio | ⏳ | Analytics completo | Backend Dev |
| 5 | Bundle size optimization (web + mobile) | Médio | ⏳ | — | Frontend Dev |
| 6 | Performance budgets no CI | Baixo | ⏳ | — | DevOps |

### Débito Técnico

| ID | Débito | Origem | Impacto | Onda de pagamento | Status |
|----|--------|--------|---------|-------------------|--------|
| DT-001 | Auth bypass em dev (`AUTH_ENABLED=false`) | F0.2 | Baixo | Onda 7 (hardening) | ⏳ |
| DT-002 | Seed data sem dados realistas | F0.4 | Médio | Onda 8 | ⏳ |
| DT-003 | E2E mobile (Detox) não configurado | F2.x | Médio | Onda 7 | ⏳ |
| DT-004 | Raw SQL em analytics (não type-safe) | F4.1 | Médio | Onda 8 | ⏳ |

---

## 6. Documentação de Referência

### Documentos de Planejamento Criados

| Data | Documento | Status | Responsável |
|------|-----------|--------|-------------|
| {YYYY-MM-DD} | {Ex: Auth Bypass Design} | ✅ | {Nome} |
| {YYYY-MM-DD} | {Ex: Dependency Matrix Design} | ✅ | {Nome} |
| {YYYY-MM-DD} | {Ex: TDD Structured Design} | ✅ | {Nome} |
| {YYYY-MM-DD} | {Ex: Comprehensive Testing Guide} | ✅ | {Nome} |

### PRP Documents

| PRP | Arquivo | Última atualização | Status |
|-----|---------|-------------------|--------|
| PRP-001 | `docs/prps/PRP-001-Foundation.md` | {Data} | ✅ |
| PRP-002 | `docs/prps/PRP-002-Auth.md` | {Data} | ✅ |
| ... | ... | ... | ... |

---

## 7. Próximas Ações (Prioridade)

> **O que o time deve fazer AGORA. Lista ordenada.**

| # | Ação | PRP/Tarefa | Prioridade | Owner | Bloqueado por | Prazo |
|---|------|------------|------------|-------|---------------|-------|
| 1 | {Ex: Configurar deploy staging} | Tarefa transversal #1 | Alto | {DevOps} | — | {Data} |
| 2 | {Ex: Expandir test coverage para 80%} | Tarefa transversal #2 | Alto | {QA} | — | {Data} |
| 3 | {Ex: Iniciar PRP-030 (Notificações)} | PRP-030 | Alto | {Backend Dev} | Onda 6 completa | {Data} |
| 4 | {Ex: Iniciar PRP-031 (Mídia)} | PRP-031 | Alto | {Mobile Dev} | Onda 6 completa | {Data} |
| 5 | {Ex: Remover warnings TypeScript} | Tarefa transversal #3 | Médio | {Tech Lead} | — | {Data} |

---

## 📌 Revisões do Documento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 0.1 | {YYYY-MM-DD} | {Autor} | Rascunho inicial — Fases 0-3 |
| 0.2 | {YYYY-MM-DD} | {Autor} | Adicionadas Fases 4-5 + PRPs planejados |
| 0.3 | {YYYY-MM-DD} | {Autor} | Adicionadas tarefas transversais e próximas ações |
| 1.0 | {YYYY-MM-DD} | {Autor} | Backlog completo — 30 PRPs completos, 5 planejados |

---

## ✅ Checklist de Manutenção do Backlog

- [ ] Atualizar status de PRPs diariamente (daily standup)
- [ ] Atualizar estimativas vs. reais semanalmente (sprint review)
- [ ] Revisar PRPs bloqueados a cada 2 dias (unblock meeting)
- [ ] Atualizar velocity a cada sprint
- [ ] Revisar débito técnico a cada sprint
- [ ] Comunicar stakeholders quando onda é completada
- [ ] Arquivar PRPs cancelados com razão documentada
- [ ] Garantir que todo PRP em "In Progress" tem owner atribuído

---

> **Nota:** Este documento é a fonte da verdade operacional. Atualize diariamente. A versão no repositório (`docs/tasks.md`) é a referência oficial. Para especificação detalhada de cada PRP, consulte `docs/prps/PRP-XXX.md`.

---

### Tarefas de Seguranca (Obrigatorias)

Tarefas de seguranca sao fixas e executadas uma vez no inicio do Step 11, antes de qualquer PRP:

| ID | Tarefa | Agente | Paralelo? | Estimativa |
|----|--------|--------|-----------|------------|
| SEC-001 | Rodar auditoria de seguranca pre-execucao (SCA + SAST + secrets) | security_agent | ❌ Sequencial — antes de todos os PRPs | {X}h |
| SEC-002 | Revisar PRs de auth/security durante execucao | security_agent | ✅ Paralelo — sob demanda | {X}h |
