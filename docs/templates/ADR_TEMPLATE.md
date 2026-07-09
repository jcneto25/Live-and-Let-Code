# ADR_TEMPLATE.md

Architecture Decision Record Template (MADR - Markdown ADR).
**Versão:** 1.0 | **Usado por:** llc-step-5a-architecture-patterns, llc-step-adr-management | **Localização:** `docs/architecture/adr/`

---

## Formato do Arquivo

**Nome:** `ADR-{NNN}-{titulo-kebab-case}.md`
**Exemplos:**
- `ADR-001-angular-nestjs-fullstack.md`
- `ADR-008-repository-pattern.md`
- `ADR-009-domain-layer-pure.md`

---

## Template MADR

```markdown
# ADR-{NNN}: {T}: {Título da Decisão}

## Status
{Proposed | Accepted | Superseded | Deprecated}

## Contexto
{Descreva o problema que motiva esta decisão. Inclua:
- Qual era a situação atual?
- Quais foram os gatilhos para a decisão?
- Quais restrições (técnicas, organizacionais, temporais) existiam?
- Quais alternativas foram consideradas?}

## Decisão
{Descreva a decisão de forma clara e concisa. Use linguagem imperativa.
Ex: "Usaremos Repository Pattern com interfaces para todos os aggregate roots."
Ex: "Adotaremos @nestjs/event-emitter para comunicação cross-module no monólito."}

## Consequências

### Positivas
- {Benefício 1}
- {Benefício 2}
- {Benefício 3}

### Negativas / Riscos
- {Custo/Complexidade 1}
- {Custo/Complexidade 2}
- {Mitigação planejada para risco}

### Neutras
- {Observação neutra}

## Alternativas Consideradas

| Alternativa | Prós | Contras | Por que não escolhida |
|-------------|------|---------|----------------------|
| {Alt 1} | ... | ... | ... |
| {Alt 2} | ... | ... | ... |

## Implementação

### Artefatos Afetados
- `docs/architecture/ARCHITECTURE.md` — seção {X}
- `.ace/arch-config.yaml` — rules {Y}
- `docs/templates/{TEMPLATE}.md` — atualizado
- `src/shared/` — base classes {Z}

### Code Changes
- Novo padrão aplicado em: {módulos}
- Migration path para legacy: {descrição}

## Validação (Fitness Functions)

Esta decisão é enforceada pelas seguintes fitness functions:

| Rule | Arquivo | Severity |
|------|---------|----------|
| `{rule-name}` | `.ace/arch-config.yaml` | `error` / `warning` |

## Referências

- [Referência 1](url) — {descrição}
- [Referência 2](url) — {descrição}
- Livro/Artigo: {Autor, Título, Capítulo}

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | ADR-{NNN} |
| **Data** | {YYYY-MM-DD} |
| **Autor(es)** | {Nomes} |
| **Revisores** | {Nomes} |
| **Próxima Revisão** | {YYYY-MM-DD} |
| **Supersedes** | ADR-{XXX} (se aplicável) |
| **Superseded by** | ADR-{YYY} (se aplicável) |
```

---

## ADRs Obrigatórios Mínimos (Step 5a)

| ADR | Título Sugerido | Decisão Core |
|-----|-----------------|--------------|
| ADR-001 | Stack Frontend (Angular/React/Vue) | Framework + justificativa |
| ADR-002 | Stack Backend (NestJS/Express/Fastify) | Framework + justificativa |
| ADR-003 | Banco de Dados (PostgreSQL/MySQL/MongoDB) | SGBD + estratégia migração |
| ADR-004 | Autenticação/Autorização (JWT/OIDC/Keycloak) | Estratégia auth |
| ADR-005 | API First / OpenAPI / Contract Testing | Abordagem de contratos |
| ADR-006 | Repository Pattern com Interfaces | **Obrigatório** (Step 5a) |
| ADR-007 | Domain Layer Puro (Entities, VOs, Events, Errors) | **Obrigatório** (Step 5a) |
| ADR-008 | Use Cases como Application Layer | **Obrigatório** (Step 5a) |
| ADR-009 | Event Bus para Cross-Module Communication | **Obrigatório** (Step 5a) |
| ADR-010 | Fitness Functions Automatizadas | **Obrigatório** (Step 5a) |
| ADR-011 | Estratégia de Deploy / CI/CD | Pipeline + ambientes |

---

## Exemplo Preenchido: ADR-008-repository-pattern.md

```markdown
# ADR-008: Repository Pattern com Interfaces (Ports & Adapters)

## Status
Accepted

## Contexto
O projeto CONFORMITAS 3.0 identificou que services injetavam `PrismaService` diretamente, violando a Dependency Rule (Clean Architecture, Martin Ch22) e o Dependency Inversion Principle (Stemmler Ch6). Isso criava acoplamento forte à infraestrutura, dificultava testes unitários e impedia troca de ORM.

Alternativas consideradas:
1. **Manter PrismaService direto** — simples, mas acoplado
2. **Repository Pattern sem interfaces** — melhora separação, mas não inverte dependência
3. **Repository Pattern com interfaces (Ports & Adapters)** — DIP completo, testável, trocável

## Decisão
Implementaremos Repository Pattern com interfaces para todos os aggregate roots:
- Interface `I{Nome}Repository` em `domain/repositories/` (Port)
- Implementação `Prisma{Nome}Repository` em `infrastructure/repositories/` (Adapter)
- Binding DI no module: `{ provide: I{Nome}Repository, useClass: Prisma{Nome}Repository }`
- Services/Use Cases injetam apenas a interface

## Consequências

### Positivas
- Domain layer puro — zero dependências de infraestrutura
- Testes unitários com mocks da interface (não precisam de banco)
- Troca de ORM (Prisma → TypeORM → Drizzle) sem tocar domain/application
- Fitness function pode verificar ausência de `PrismaService` em domain/application

### Negativas
- Mais arquivos (~3 por aggregate root: interface, impl, mapper)
- Curva de aprendizado para time novo no padrão
- Boilerplate inicial

### Neutras
- Requer `ts-morph` ou ESLint para enforcement automatizado

## Alternativas Consideradas

| Alternativa | Prós | Contras | Por que não |
|-------------|------|---------|-------------|
| PrismaService direto | Menos código, rápido | Acoplado, hard to test, viola Dependency Rule | Violou princípio arquitetural |
| Repository sem interface | Separação parcial | Não inverte dependência, service ainda conhece impl | DIP não atendido |
| Active Record | Simples | Entidade anêmica + lógica de persistência misturada | Anti-pattern DDD |

## Implementação

### Artefatos Afetados
- `docs/architecture/ARCHITECTURE.md` — §7 Camada de Domínio e Ports & Adapters
- `.ace/arch-config.yaml` — rules: `no-prisma-in-domain`, `no-prisma-in-use-cases`, `repository-interface-exists`
- `docs/templates/REPOSITORY_PATTERN_TEMPLATE.md` — template completo

### Code Changes
- Novo padrão aplicado em: todos módulos (greenfield) / módulos novos e alterados (brownfield)
- Migration path: módulos legacy marcados `// LEGACY`, issue de migração criada

## Validação (Fitness Functions)

| Rule | Severity |
|------|----------|
| `no-prisma-in-domain` | `error` (core), `warning` (non-core) |
| `no-prisma-in-use-cases` | `error` (core), `warning` (non-core) |
| `repository-interface-exists` | `error` |
| `repository-binding-in-module` | `error` |

## Referências

- Martin, R. — *Clean Architecture*, Ch. 22: The Dependency Rule
- Stemmler, K. — *Software Design & Architecture Handbook*, Ch. 6: Dependency Inversion
- Vernon, V. — *DDD Distilled*, Ch. 5: Repositories

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | ADR-008 |
| **Data** | 2025-01-15 |
| **Autor(es)** | Arquiteto LLC, Tech Lead |
| **Revisores** | Time de Engenharia |
| **Próxima Revisão** | 2025-07-15 |
| **Supersedes** | — |
| **Superseded by** | — |
```

---

## Exemplo Preenchido: ADR-009-domain-layer-pure.md

```markdown
# ADR-009: Domain Layer Puro (Entities, Value Objects, Domain Events, Domain Errors)

## Status
Accepted

## Contexto
A análise do CONFORMITAS 3.0 mostrou regras de negócio misturadas com chamadas de ORM nos services, violando SRP (Martin Ch7) e o princípio de Use Case per Feature (Stemmler Ch11). Entidades eram anêmicas (apenas getters/setters).

## Decisão
Criaremos Domain Layer puro por módulo com:
- **Entities** com comportamento (métodos de negócio, validações de invariantes)
- **Value Objects** imutáveis com validação no construtor
- **Domain Events** para fatos ocorridos (imutáveis, com occurredAt, aggregateId)
- **Domain Errors** tipados extendendo `DomainError` base
- **Factory methods** retornando `Result<T, Error>` (never throw para regras de negócio)

## Consequências

### Positivas
- Regras de negócio centralizadas na entidade (não espalhadas em services)
- Value Objects garantem integridade de dados (ex: Email, CPF, Status com transições)
- Domain Events desacoplam side effects (notificações, auditoria)
- Testes de domínio puros, rápidos, sem mocks de infraestrutura

### Negativas
- Mais verboso que anemic entities
- Requer disciplina: nunca colocar lógica de infra no domain
- Curva de aprendizado: Result pattern, VOs, Events

## Implementação

### Artefatos Afetados
- `docs/architecture/ARCHITECTURE.md` — §7.3 Domain Layer Puro
- `.ace/arch-config.yaml` — rules: `entity-no-framework`, `vo-immutable`, `domain-event-structure`
- `docs/templates/DOMAIN_MODEL_TEMPLATE.md` — templates completos

## Validação

| Rule | Severity |
|------|----------|
| `entity-no-framework` | `error` |
| `entity-no-prisma` | `error` |
| `vo-immutable` | `error` |
| `domain-event-structure` | `error` |
| `domain-error-typed` | `error` |
```

---

## Checklist de Validação de ADR (Gate 6 / Step 5a)

Para cada ADR criado:

- [ ] **Formato MADR** seguido (todas as seções preenchidas)
- [ ] **Status** explícito (Proposed/Accepted/Superseded/Deprecated)
- [ ] **Contexto** descreve problema real, não solução
- [ ] **Decisão** em linguagem imperativa, clara
- [ ] **Consequências** honestas (positivas, negativas, neutras)
- [ ] **Alternativas** documentadas com tabela comparativa
- [ ] **Implementação** lista artefatos e code changes
- [ ] **Fitness Functions** mapeadas para rules no `.ace/arch-config.yaml`
- [ ] **Referências** a literatura/standards relevantes
- [ ] **Metadados** completos (ID, data, autor, revisor, próxima revisão)
- [ ] **Arquivo salvo** em `docs/architecture/adr/ADR-{NNN}-{titulo}.md`
- [ ] **Índice atualizado** em `docs/architecture/adr/README.md`
- [ ] **Linkado** no `ARCHITECTURE.md` §8 (tabela de ADRs)

---

## README.md do Diretório ADR — `docs/architecture/adr/README.md`

```markdown
# Architecture Decision Records (ADRs)

Diretório de decisões arquiteturais seguindo formato [MADR](https://adr.github.io/madr/).

## Índice

| ID | Título | Status | Data | Link |
|----|--------|--------|------|------|
| ADR-001 | Angular + NestJS Fullstack | Accepted | 2025-01-10 | [ADR-001](ADR-001-angular-nestjs-fullstack.md) |
| ADR-002 | NestJS como Backend | Accepted | 2025-01-10 | [ADR-002](ADR-002-nestjs-backend.md) |
| ADR-003 | PostgreSQL como Banco Principal | Accepted | 2025-01-10 | [ADR-003](ADR-003-postgresql.md) |
| ADR-004 | RBAC + ABAC para Autorização | Accepted | 2025-01-10 | [ADR-004](ADR-004-rbac-abac.md) |
| ADR-005 | API First com OpenAPI | Accepted | 2025-01-10 | [ADR-005](ADR-005-api-first-openapi.md) |
| ADR-006 | JWT + MFA + Keycloak | Accepted | 2025-01-10 | [ADR-006](ADR-006-jwt-mfa-keycloak.md) |
| ADR-007 | Docker Compose para Dev/Staging | Accepted | 2025-01-10 | [ADR-007](ADR-007-docker-compose.md) |
| **ADR-008** | **Repository Pattern com Interfaces** | **Accepted** | **2025-01-15** | **[ADR-008](ADR-008-repository-pattern.md)** |
| **ADR-009** | **Domain Layer Puro** | **Accepted** | **2025-01-15** | **[ADR-009](ADR-009-domain-layer-pure.md)** |
| **ADR-010** | **Use Cases como Application Layer** | **Accepted** | **2025-01-15** | **[ADR-010](ADR-010-use-cases.md)** |
| **ADR-011** | **Event Bus Cross-Module** | **Accepted** | **2025-01-15** | **[ADR-011](ADR-011-event-bus.md)** |
| **ADR-012** | **Fitness Functions Automatizadas** | **Accepted** | **2025-01-15** | **[ADR-012](ADR-012-fitness-functions.md)** |

## Como Criar Novo ADR

1. Copie `ADR_TEMPLATE.md` para `ADR-{NNN}-{titulo-kebab-case}.md`
2. Preencha todas as seções
3. Atualize esta tabela
4. Linke no `ARCHITECTURE.md` §8
5. Submeta para revisão (Gate 6)

## Convenções

- **NNN**: Número sequencial (001, 002, ...)
- **titulo-kebab-case**: lowercase, hyphens (ex: `repository-pattern`)
- **Status**: Proposed → Accepted → (Superseded/Deprecated)
- **Um ADR por decisão arquitetural significativa**
```