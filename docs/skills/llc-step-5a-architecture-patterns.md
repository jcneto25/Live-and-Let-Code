---
name: llc-step-5a-architecture-patterns
description: Pipeline LLC Step 5a — Define e valida padrões arquiteturais obrigatórios: Clean Architecture layers, Repository Pattern com interfaces, Domain Layer puro, Use Cases, Event Bus. Gera ARCHITECTURE.md com decisões vinculantes + .ace/arch-config.yaml para fitness functions.
version: 1.0.0
tags: [architecture, patterns, clean-architecture, repository-pattern, domain-driven-design, llc-pipeline]
---

# LLC Skill: Step 5a — Architecture Patterns Mandatory

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Architecture (sub-step of Step 5)  
**Depende de:** Step 5 (Architecture Overview validado)  
**Executa antes de:** Step 8 (Setup)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5a` ou "Execute a skill llc-step-5a".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 5a --task "Definir padrões arquiteturais obrigatórios"`.

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — overview arquitetural (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — template expandido v1.0+
- [ ] `docs/business/specs/requisitos_nao_funcionais.md` — RNFs para justificar decisões
- [ ] `docs/planning/PLAN.md` — ondas e milestones (para identificar módulos core)
- [ ] `docs/business/specs/perfis_permissoes.md` — para definir módulos de auth/authorization

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 5a** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-5a.md`:
     ```markdown
     # Skip Note: Step 5a — Architecture Patterns
     **Decisão:** Step pulado — padrões arquiteturais inalterados desde última execução.
     **Gate:** ✅ Auto-aprovado (reaproveitando aprovação anterior de {data})
     ```
   - **PARE** e informe: "Step 5a pulado via Smart Skip. Padrões arquiteturais existentes reaproveitados. Gate auto-aprovado."
3. Se **Step 5a** estiver listado como "executar": atualize `ARCHITECTURE.md` e `.ace/arch-config.yaml` apenas nas seções alteradas, mantendo histórico de decisões.
4. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-5a-architecture-patterns` do pipeline LLC. Seu objetivo é **definir e documentar os padrões arquiteturais obrigatórios** que o time (e LLM) deve seguir durante toda a execução (Steps 8–11). Estes padrões são **vinculantes** e serão verificados por fitness functions automatizadas.

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack, C4, ADRs já definidos no Step 5
- `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — estrutura a seguir
- `docs/planning/PLAN.md` — identifique módulos core (wave 1) que terão enforcement block
- `docs/business/specs/requisitos_nao_funcionais.md` — RNFs que justificam cada padrão

### 2. Defina os Padrões Obrigatórios (preencha o template)

O `ARCHITECTURE_PATTERNS_TEMPLATE.md` contém seções para cada padrão. Para cada seção:

#### 2.1 Clean Architecture Layers (obrigatório)
- Defina a estrutura de pastas intra-módulo:
  ```
  src/{modulo}/
  ├── domain/           # Puro — sem framework, sem Prisma, sem decorators
  │   ├── entities/
  │   ├── value-objects/
  │   ├── events/
  │   ├── errors/
  │   └── repositories/ # INTERFACES apenas (Ports)
  ├── application/      # Use Cases
  │   ├── use-cases/
  │   ├── dto/
  │   └── ports/        # Input/Output ports (opcional, se separar)
  ├── infrastructure/   # Adapters
  │   ├── repositories/ # Implementações concretas (Prisma, etc.)
  │   ├── persistence/  # Prisma schema, migrations
  │   └── external/     # HTTP clients, message brokers
  └── presentation/     # Controllers, GraphQL resolvers, DTOs de API
  ```
- Documente a **Dependency Rule**: `domain` ← `application` ← `infrastructure` ← `presentation`
  - `domain` NÃO importa de `infrastructure`, `presentation`, `@prisma/client`, `nestjs/*` (exceto tipos puros)
  - `application` importa apenas `domain` e `shared`
  - `infrastructure` implementa interfaces de `domain/repositories`

#### 2.2 Repository Pattern com Interfaces (obrigatório)
- Para cada Aggregate Root identificado nos PRPs:
  - Interface: `I{NomeAgregado}Repository` em `domain/repositories/`
  - Implementação: `Prisma{NomeAgregado}Repository` em `infrastructure/repositories/`
  - Binding DI: `{ provide: I{NomeAgregado}Repository, useClass: Prisma{NomeAgregado}Repository }` no module
- **Regra:** Services/Use Cases **NUNCA** injetam `PrismaService` diretamente

#### 2.3 Domain Layer Puro (obrigatório)
- **Entities:** Classes com comportamento (métodos de negócio), não anêmicas
  - Validações de invariantes no construtor/métodos
  - Retornam `Result<T, Error>` (never throw para regras de negócio)
- **Value Objects:** Imutáveis, equality por valor, validação no construtor
- **Domain Events:** Classes que extendem `DomainEvent` base, imutáveis, com `occurredAt`, `aggregateId`
- **Domain Errors:** Classes customizadas extendendo `DomainError`, tipadas por aggregate

#### 2.4 Use Cases (Application Layer) (obrigatório para módulos com regras de negócio)
- Um Use Case por operação de negócio (Single Responsibility)
- Naming: `{Acao}{Agregado}UseCase` (ex: `AbrirAuditoriaUseCase`, `ListarAuditoriasUseCase`)
- Signature: `async execute(dto: InputDto, context?: ExecutionContext): Promise<OutputDto>`
- Injetam apenas interfaces de repositório (Ports) + `EventEmitter2` para domain events
- **NÃO** injetam: `PrismaService`, Controllers, outros Use Cases, Services de infra

#### 2.5 Event Bus para Cross-Module Communication (obrigatório)
- Stack: `@nestjs/event-emitter` (monólito modular) — sem mensageria externa no MVP
- Base event class: `DomainEvent` com `aggregateId`, `aggregateType`, `occurredAt`, `eventId`
- Módulos **NÃO** importam outros módulos de domínio (exceto `shared/`)
- Comunicação **apenas** via eventos:
  - Publisher: `this.eventEmitter.emit('auditoria.aberta', new AuditoriaAbertaEvent(...))`
  - Subscriber: `@OnEvent('auditoria.aberta')` em handler no módulo `notificacoes`

#### 2.6 Módulos Core (Enforcement Block)
- Liste os módulos que terão fitness functions com **threshold zero violations** (block no CI):
  - Ex.: `auth`, `usuarios`, `auditorias`, `achados`, `planos`
- Módulos non-core (CRUD puro): enforcement `warning` apenas

### 3. Gere os Artefatos de Saída

#### 3.1 `docs/architecture/ARCHITECTURE.md` — Atualize as seções:
- **§7 Camada de Domínio e Ports & Adapters** — preencha com estrutura definida
- **§8 Comunicação entre Módulos** — matriz de eventos publisher/subscriber
- **§9 Fitness Functions** — referencie `.ace/arch-config.yaml`

#### 3.2 `.ace/arch-config.yaml` — Configuração das Fitness Functions
```yaml
version: "1.0"
generated_by: "llc-step-5a"
last_updated: "2025-01-15T10:00:00Z"
core_modules:
  - auth
  - usuarios
  - auditorias
  - achados
  - planos
enforcement:
  core: "error"      # block no CI
  non_core: "warning" # apenas warning
rules:
  # Dependency Rule
  - name: "no-prisma-in-domain"
    pattern: "import.*@prisma/client"
    forbidden_in: ["**/domain/**"]
    message: "Domain layer cannot import Prisma client"
  
  - name: "no-prisma-in-use-cases"
    pattern: "import.*PrismaService"
    forbidden_in: ["**/application/**", "**/use-cases/**"]
    message: "Use cases cannot inject PrismaService directly"
  
  - name: "no-cross-module-imports"
    pattern: "from ['\"]../[^/]+/"
    forbidden_in: ["**/domain/**", "**/application/**"]
    message: "Domain/Application cannot import from sibling modules"
    allowed_except: ["**/shared/**", "**/domain/**", "**/application/**", "**/dto/**"]
  
  - name: "repository-interface-exists"
    check: "file_exists"
    path: "**/domain/repositories/I*Repository.ts"
    message: "Each aggregate root must have a repository interface"
  
  - name: "use-case-naming"
    pattern: "UseCase\.ts$"
    required_in: ["**/application/use-cases/**"]
    message: "Use cases must end with UseCase suffix"
  
  - name: "event-emitter-usage"
    pattern: "EventEmitter2"
    required_in: ["**/application/use-cases/**"]
    message: "Use cases must emit domain events via EventEmitter2"

event_bus:
  library: "@nestjs/event-emitter"
  base_event_class: "src/shared/domain/domain-event.ts"
  modules_with_handlers:
    - notificacoes
    - auditorias
    - achados
```

#### 3.3 `docs/architecture/adr/ADR-008-repository-pattern.md` (e outros ADRs novos)
- Crie ADRs para cada decisão arquitetural nova usando `ADR_TEMPLATE.md`
- Mínimo: Repository Pattern, Domain Layer, Use Cases, Event Bus

---

## ⚠️ REGRAS CRÍTICAS

1. **Vinculante:** O que for definido aqui vira regra de fitness function — não mude depois sem ADR
2. **Greenfield vs Brownfield:**
   - **Greenfield:** Aplique a todos os módulos desde o início
   - **Brownfield:** Aplique apenas a **novos módulos** e **módulos alterados** (PRP-A). Módulos legados podem manter estrutura antiga mas devem ser marcados com `// LEGACY` e ter plano de migração
3. **Pragmatismo:** Módulos CRUD puros (sem regras de negócio) podem usar Service direto sem Use Case, mas **ainda devem ter Repository Interface**
4. **Consistência:** Naming conventions são obrigatórias — use os sufixos padrão
5. **Documentação viva:** `.ace/arch-config.yaml` deve ser versionado e atualizado a cada nova onda

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os artefatos, **PARE** e apresente:

1. **Resumo dos Padrões:** Tabela com cada padrão, status (obrigatório/opcional), módulos afetados
2. **Arquivos Gerados/Atualizados:**
   - `docs/architecture/ARCHITECTURE.md` (seções 7, 8, 9 atualizadas)
   - `.ace/arch-config.yaml` (configuração fitness functions)
   - `docs/architecture/adr/ADR-008-repository-pattern.md`
   - `docs/architecture/adr/ADR-009-domain-layer.md`
   - `docs/architecture/adr/ADR-010-use-cases.md`
   - `docs/architecture/adr/ADR-011-event-bus.md`
3. **Módulos Core:** Lista dos módulos com enforcement `error`
4. **Matriz de Eventos:** Tabela publisher → subscriber por evento
5. **Estratégia Brownfield:** Como módulos legados serão tratados
6. **Próximos Passos:** Perguntas para validação humana (foco em trade-offs, viabilidade de migração legacy)

**NÃO prossiga para o Step 8. Aguarde validação humana (Gate 6).**