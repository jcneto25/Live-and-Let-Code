# ARCHITECTURE_PATTERNS_TEMPLATE.md

Template para documentação de padrões arquiteturais obrigatórios (Step 5a).
**Versão:** 1.0 | **Gerado por:** llc-step-5a-architecture-patterns

---

## 1. Clean Architecture Layers

### 1.1 Estrutura de Pastas Intra-Módulo (Obrigatório)

```
src/{modulo}/
├── domain/                    # Camada mais interna - PURO
│   ├── entities/              # Entidades de domínio com comportamento
│   ├── value-objects/         # Value Objects imutáveis
│   ├── events/                # Domain Events
│   ├── errors/                # Domain Errors tipados
│   ├── repositories/          # INTERFACES apenas (Ports)
│   └── dto/                   # DTOs de domínio (filters, pagination)
├── application/               # Camada de aplicação
│   ├── use-cases/             # Use Cases (uma operação por classe)
│   ├── dto/                   # Input/Output DTOs dos Use Cases
│   └── ports/                 # Input/Output ports (opcional)
├── infrastructure/            # Camada externa - Adapters
│   ├── repositories/          # Implementações concretas (Prisma, etc.)
│   ├── persistence/           # Prisma schema, migrations, seeds
│   ├── mappers/               # Conversão Prisma ↔ Domain
│   └── external/              # HTTP clients, message brokers
└── presentation/              # Camada de apresentação
    ├── controllers/           # REST Controllers
    ├── graphql/               # Resolvers (se aplicável)
    └── dto/                   # API DTOs (request/response)
```

### 1.2 Dependency Rule (Vinculante)

```
domain ← application ← infrastructure ← presentation
    ↑           ↑              ↑              ↑
  PURO       apenas          implementa     consome
  (sem       domain +        interfaces     Use Cases
  framework) shared          de domain
```

**Regras Proibidas (verificadas por Fitness Functions):**
- ❌ `domain/**` importa `@prisma/client`, `PrismaService`, `nestjs/*`, decorators
- ❌ `application/**` importa `PrismaService`, `infrastructure/**`, `presentation/**`
- ❌ `domain/**` importa `../outro-modulo/**` (exceto `shared/**`)
- ❌ `application/**` importa `../outro-modulo/**` (exceto `shared/**`)

---

## 2. Repository Pattern com Interfaces (Obrigatório)

### 2.1 Convenção de Naming

| Artefato | Convenção | Exemplo |
|----------|-----------|---------|
| Interface (Port) | `I{NomeAgregado}Repository` | `IAuditoriaRepository` |
| Arquivo Interface | `i{nome-agregado}.repository.ts` | `iauditoria.repository.ts` |
| Implementação (Adapter) | `Prisma{NomeAgregado}Repository` | `PrismaAuditoriaRepository` |
| Arquivo Impl | `prisma-{nome-agregado}.repository.ts` | `prisma-auditoria.repository.ts` |
| Mapper | `{NomeAgregado}Mapper` | `AuditoriaMapper` |
| Arquivo Mapper | `{nome-agregado}.mapper.ts` | `auditoria.mapper.ts` |

### 2.2 Template de Interface (Port)

```typescript
// src/{modulo}/domain/repositories/i{nome-agregado}.repository.ts
import { {NomeAgregado}Filter, {NomeAgregado}Pagination } from '../dto/{nome-agregado}-filters.dto';
import { {NomeAgregado} } from '../entities/{nome-agregado}.entity';

export interface I{NomeAgregado}Repository {
  // Commands
  save(entity: {NomeAgregado}): Promise<{NomeAgregado}>;
  delete(id: string): Promise<void>;
  
  // Queries
  findById(id: string): Promise<{NomeAgregado} | null>;
  findMany(filter: {NomeAgregado}Filter, pagination?: {NomeAgregado}Pagination): Promise<{NomeAgregado}[]>;
  count(filter: {NomeAgregado}Filter): Promise<number>;
  
  // Domain-specific (conforme necessidade)
  findBy{CampoUnico}(valor: string): Promise<{NomeAgregado} | null>;
  nextIdentificador(): Promise<string>;
  
  // Transações
  withTransaction<T>(fn: (repo: I{NomeAgregado}Repository) => Promise<T>): Promise<T>;
}
```

### 2.3 Template de Implementação (Adapter)

```typescript
// src/{modulo}/infrastructure/repositories/prisma-{nome-agregado}.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { I{NomeAgregado}Repository } from '../../domain/repositories/i{nome-agregado}.repository';
import { {NomeAgregado} } from '../../domain/entities/{nome-agregado}.entity';
import { {NomeAgregado}Filter, {NomeAgregado}Pagination } from '../../domain/dto/{nome-agregado}-filters.dto';
import { {NomeAgregado}Mapper } from '../mappers/{nome-agregado}.mapper';

@Injectable()
export class Prisma{NomeAgregado}Repository implements I{NomeAgregado}Repository {
  constructor(private readonly prisma: PrismaService) {}

  async save(entity: {NomeAgregado}): Promise<{NomeAgregado}> {
    const data = {NomeAgregado}Mapper.toPersistence(entity);
    const saved = await this.prisma.{nomeAgregado}.upsert({
      where: { id: entity.id.value },
      create: data,
      update: data,
    });
    return {NomeAgregado}Mapper.toDomain(saved);
  }

  async delete(id: string): Promise<void> {
    await this.prisma.{nomeAgregado}.delete({ where: { id } });
  }

  async findById(id: string): Promise<{NomeAgregado} | null> {
    const found = await this.prisma.{nomeAgregado}.findUnique({ where: { id } });
    return found ? {NomeAgregado}Mapper.toDomain(found) : null;
  }

  async findMany(filter: {NomeAgregado}Filter, pagination?: {NomeAgregado}Pagination): Promise<{NomeAgregado}[]> {
    const where = this.buildWhere(filter);
    const found = await this.prisma.{nomeAgregado}.findMany({
      where,
      skip: pagination?.skip,
      take: pagination?.take,
      orderBy: { createdAt: 'desc' },
    });
    return found.map({NomeAgregado}Mapper.toDomain);
  }

  async count(filter: {NomeAgregado}Filter): Promise<number> {
    return this.prisma.{nomeAgregado}.count({ where: this.buildWhere(filter) });
  }

  async findBy{CampoUnico}(valor: string): Promise<{NomeAgregado} | null> {
    const found = await this.prisma.{nomeAgregado}.findUnique({ where: { {campoUnico}: valor } });
    return found ? {NomeAgregado}Mapper.toDomain(found) : null;
  }

  async nextIdentificador(): Promise<string> {
    const count = await this.prisma.{nomeAgregado}.count();
    const year = new Date().getFullYear();
    return `{PREFIX}-${year}-${String(count + 1).padStart(4, '0')}`;
  }

  async withTransaction<T>(fn: (repo: I{NomeAgregado}Repository) => Promise<T>): Promise<T> {
    return this.prisma.$transaction(async (tx) => {
      const txRepo = new Prisma{NomeAgregado}Repository(tx as any);
      return fn(txRepo);
    });
  }

  private buildWhere(filter: {NomeAgregado}Filter) {
    const where: any = {};
    // Mapear filtros do DTO para where do Prisma
    return where;
  }
}
```

### 2.4 Template de Mapper

```typescript
// src/{modulo}/infrastructure/mappers/{nome-agregado}.mapper.ts
import { {NomeAgregado} } from '../../domain/entities/{nome-agregado}.entity';
import { {NomeAgregado} as Prisma{NomeAgregado} } from '@prisma/client';

export class {NomeAgregado}Mapper {
  static toDomain(prisma: Prisma{NomeAgregado}): {NomeAgregado} {
    return new {NomeAgregado}({
      id: {NomeAgregado}Id.fromString(prisma.id),
      // ... mapear todos os campos
      createdAt: prisma.createdAt,
      updatedAt: prisma.updatedAt,
    });
  }

  static toPersistence(domain: {NomeAgregado}): any {
    return {
      id: domain.id.value,
      // ... mapear todos os campos
    };
  }
}
```

### 2.5 Template de Module Binding

```typescript
// src/{modulo}/{modulo}.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { {Modulo}Controller } from './{modulo}.controller';
import { {Modulo}Service } from './{modulo}.service';
import { I{NomeAgregado}Repository } from './domain/repositories/i{nome-agregado}.repository';
import { Prisma{NomeAgregado}Repository } from './infrastructure/repositories/prisma-{nome-agregado}.repository';
// Use Cases
import { {Acao}{NomeAgregado}UseCase } from './application/use-cases/{acao}{nome-agregado}.use-case';

@Module({
  imports: [PrismaModule],
  controllers: [{Modulo}Controller],
  providers: [
    {Modulo}Service,
    // Repository Binding (OBRIGATÓRIO)
    { provide: I{NomeAgregado}Repository, useClass: Prisma{NomeAgregado}Repository },
    // Use Cases
    {Acao}{NomeAgregado}UseCase,
    // ... demais use cases
  ],
  exports: [{Modulo}Service, I{NomeAgregado}Repository],
})
export class {Modulo}Module {}
```

---

## 3. Domain Layer Puro (Obrigatório)

### 3.1 Entity Template

```typescript
// src/{modulo}/domain/entities/{nome-agregado}.entity.ts
import { Result, ok, err } from '../../../shared/result';
import { {NomeAgregado}Id } from '../value-objects/{nome-agregado}-id.vo';
import { {OutroVO} } from '../value-objects/{outro-vo}.vo';
import { {NomeAgregado}NaoEncontradaError } from '../errors/{nome-agregado}-nao-encontrada.error';
import { {RegraInvalida}Error } from '../errors/{regra-invalida}.error';
import { {NomeAgregado}{Acao}Event } from '../events/{nome-agregado}-{acao}.event';

export interface {NomeAgregado}Props {
  id: {NomeAgregado}Id;
  // ... demais props tipadas com VOs
  createdAt: Date;
  updatedAt: Date;
}

export class {NomeAgregado} {
  private _domainEvents: {NomeAgregado}{Acao}Event[] = [];
  private constructor(private readonly props: {NomeAgregado}Props) {}

  // Factory — valida invariantes
  static criar(props: Omit<{NomeAgregado}Props, 'id' | 'createdAt' | 'updatedAt'>): Result<{NomeAgregado}, Error> {
    // Validações de invariantes de negócio
    if (!props.campoObrigatorio) {
      return err(new Error('Campo obrigatório não preenchido'));
    }
    
    const agora = new Date();
    const entity = new {NomeAgregado}({
      ...props,
      id: {NomeAgregado}Id.generate(),
      createdAt: agora,
      updatedAt: agora,
    });
    
    entity._domainEvents.push(new {NomeAgregado}CriadoEvent(entity.props.id.value, ...));
    return ok(entity);
  }

  // Reconstituição (do banco) — sem validações, sem events
  static reconstitute(props: {NomeAgregado}Props): {NomeAgregado} {
    return new {NomeAgregado}(props);
  }

  // Getters (readonly)
  get id() { return this.props.id; }
  // ... demais getters

  // Comportamento de domínio — retorna Result
  {acao}(): Result<void, {RegraInvalida}Error> {
    if (!this.pode{Acao}()) {
      return err(new {RegraInvalida}Error(this.props.status, '{Acao}'));
    }
    this.props.status = {NovoStatus};
    this.props.updatedAt = new Date();
    this._domainEvents.push(new {NomeAgregado}{Acao}Event(this.props.id.value, ...));
    return ok(undefined);
  }

  // Domain Events
  get domainEvents() { return [...this._domainEvents]; }
  clearDomainEvents() { this._domainEvents = []; }

  equals(other: {NomeAgregado}): boolean {
    return other instanceof {NomeAgregado} && this.props.id.equals(other.props.id);
  }
}
```

### 3.2 Value Object Template

```typescript
// src/{modulo}/domain/value-objects/{nome-vo}.vo.ts
import { ValueObject } from '../../../shared/value-object';
import { Result, ok, err } from '../../../shared/result';

export class {NomeVO} extends ValueObject<{tipo}> {
  private constructor(value: {tipo}) {
    super(value);
  }

  static criar(value: {tipo}): Result<{NomeVO}, Error> {
    // Validação
    if (!value || value.length < min) {
      return err(new Error(`{NomeVO} inválido: ${value}`));
    }
    return ok(new {NomeVO}(value));
  }

  // Métodos de domínio específicos do VO
  // ...
}
```

### 3.3 Domain Event Template

```typescript
// src/{modulo}/domain/events/{nome-agregado}-{acao}.event.ts
import { DomainEvent } from '../../../shared/domain/domain-event';

export class {NomeAgregado}{Acao}Event extends DomainEvent {
  constructor(
    aggregateId: string,
    public readonly {campo1}: {tipo},
    public readonly {campo2}: {tipo},
  ) {
    super(aggregateId, '{NomeAgregado}');
  }

  static eventName = '{nome-agregado}.{acao}';
}
```

### 3.4 Domain Error Template

```typescript
// src/{modulo}/domain/errors/{nome-agregado}-{erro}.error.ts
import { DomainError } from '../../../shared/errors/domain-error';

export class {NomeAgregado}{Erro}Error extends DomainError {
  constructor(
    public readonly {contexto1}: {tipo},
    public readonly {contexto2}: {tipo},
  ) {
    super(`Mensagem descritiva: ${contexto1} -> ${contexto2}`, '{CODIGO_ERRO_UNICO}');
  }
}
```

---

## 4. Use Cases (Application Layer) (Obrigatório para Core Modules)

### 4.1 Convenção

| Artefato | Convenção | Exemplo |
|----------|-----------|---------|
| Classe | `{Acao}{NomeAgregado}UseCase` | `AbrirAuditoriaUseCase` |
| Arquivo | `{acao}{nome-agregado}.use-case.ts` | `abrir-auditoria.use-case.ts` |
| Input DTO | `{Acao}{NomeAgregado}Input` | `AbrirAuditoriaInput` |
| Output DTO | `{Acao}{NomeAgregado}Output` | `AbrirAuditoriaOutput` |

### 4.2 Template

```typescript
// src/{modulo}/application/use-cases/{acao}{nome-agregado}.use-case.ts
import { Injectable } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { I{NomeAgregado}Repository } from '../../domain/repositories/i{nome-agregado}.repository';
import { {NomeAgregado} } from '../../domain/entities/{nome-agregado}.entity';
import { {OutroRepo} } from '../../../{outro-modulo}/domain/repositories/i{outro}.repository';

export interface {Acao}{NomeAgregado}Input {
  {campo1}: {tipo};
  {campo2}: {tipo};
}

export interface {Acao}{NomeAgregado}Output {
  {nomeAgregado}: {NomeAgregado};
}

@Injectable()
export class {Acao}{NomeAgregado}UseCase {
  constructor(
    private readonly {nomeAgregado}Repo: I{NomeAgregado}Repository,
    private readonly {outro}Repo: {OutroRepo},
    private readonly eventEmitter: EventEmitter2,
  ) {}

  async execute(input: {Acao}{NomeAgregado}Input): Promise<{Acao}{NomeAgregado}Output> {
    // 1. Validações de negócio (cross-aggregate)
    const relacionado = await this.{outro}Repo.findById(input.{campoRelacionado});
    if (!relacionado) {
      throw new {NomeAgregado}NaoEncontradaError(`Relacionado ${input.{campoRelacionado}} não encontrado`);
    }
    if (!regraDeNegocio(relacionado)) {
      throw new Error('Regra de negócio violada');
    }

    // 2. Cria/Modifica entidade (factory valida invariantes)
    const result = {NomeAgregado}.criar({ ... });
    if (result.isErr()) throw result.error;

    // 3. Persiste
    const saved = await this.{nomeAgregado}Repo.save(result.value);

    // 4. Emite domain events
    for (const event of saved.domainEvents) {
      this.eventEmitter.emit(event.constructor.eventName, event);
    }
    saved.clearDomainEvents();

    return { {nomeAgregado}: saved };
  }
}
```

---

## 5. Event Bus (Obrigatório)

### 5.1 Stack
- **Monólito Modular:** `@nestjs/event-emitter` (in-process)
- **Microserviços:** RabbitMQ / Redis Streams / Kafka (fora do escopo do MVP)

### 5.2 Base Event Class

```typescript
// src/shared/domain/domain-event.ts
export abstract class DomainEvent {
  public readonly eventId: string;
  public readonly aggregateId: string;
  public readonly aggregateType: string;
  public readonly occurredAt: Date;

  constructor(aggregateId: string, aggregateType: string) {
    this.eventId = crypto.randomUUID();
    this.aggregateId = aggregateId;
    this.aggregateType = aggregateType;
    this.occurredAt = new Date();
  }
}
```

### 5.3 Matriz de Eventos (Preencher por Módulo)

| Evento | Publisher (Use Case) | Subscriber (Handler) | Módulo Handler |
|--------|---------------------|---------------------|----------------|
| `{modulo}.{acao}` | `{Acao}{Modulo}UseCase` | `{Acao}Handler` | `{modulo-handler}` |

---

## 6. Módulos Core (Enforcement Block)

| Módulo | Aggregate Roots | Enforcement | Justificativa |
|--------|----------------|-------------|---------------|
| `auth` | Usuario, Sessao | `error` | Segurança crítica |
| `usuarios` | Usuario, Perfil | `error` | Core domain |
| `auditorias` | Auditoria, Achado | `error` | Workflow complexo |
| `achados` | Achado, Manifestacao | `error` | Workflow complexo |
| `planos` | Plano, ItemPlano | `error` | Core domain |

---

## 7. ADRs Gerados (Mínimo)

| ADR | Título | Status |
|-----|--------|--------|
| ADR-008 | Repository Pattern com Interfaces | Proposed |
| ADR-009 | Domain Layer Puro (Entities, VOs, Events, Errors) | Proposed |
| ADR-010 | Use Cases como Application Layer | Proposed |
| ADR-011 | Event Bus para Cross-Module Communication | Proposed |

---

## 8. Checklist de Validação (Gate 6)

- [ ] Estrutura de pastas `domain/`, `application/`, `infrastructure/`, `presentation/` definida
- [ ] Dependency Rule documentada e exemplificada
- [ ] Repository Pattern template preenchido para cada módulo
- [ ] Domain Layer templates (Entity, VO, Event, Error) definidos
- [ ] Use Case template definido
- [ ] Event Bus stack e base class definidos
- [ ] Matriz de eventos publisher/subscriber preenchida
- [ ] Módulos core listados com enforcement `error`
- [ ] `.ace/arch-config.yaml` gerado com rules correspondentes
- [ ] ADRs criados como arquivos separados em `docs/architecture/adr/`
- [ ] ARCHITECTURE.md §7, §8, §9 atualizados