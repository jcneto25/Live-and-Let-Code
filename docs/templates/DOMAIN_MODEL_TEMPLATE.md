# DOMAIN_MODEL_TEMPLATE.md

Template para modelagem de domínio (Entities, Value Objects, Domain Events, Domain Errors, Use Cases).
**Versão:** 1.0 | **Gerado por:** llc-step-11a-domain-modeling | **Usado em:** Step 11a

---

## Visão Geral

Este template define a estrutura obrigatória para o modelo de domínio de cada PRP com regras de negócio.
Segue os princípios de **Domain-Driven Design** (Evans, Vernon, Stemmler) e **Clean Architecture** (Martin).

**Camadas:**
- `domain/` — Puro, sem framework, sem Prisma, sem decorators NestJS
- `application/` — Use Cases, orquestra repositórios e emite eventos
- `infrastructure/` — Implementações concretas (Prisma, mappers, handlers)

---

## Estrutura de Arquivos por Aggregate Root

```
src/{modulo}/
├── domain/
│   ├── entities/
│   │   └── {nome-agregado}.entity.ts
│   ├── value-objects/
│   │   ├── {nome-agregado}-id.vo.ts
│   │   ├── {vo-especifico}.vo.ts
│   │   └── index.ts
│   ├── events/
│   │   ├── {nome-agregado}-{acao}.event.ts
│   │   └── index.ts
│   ├── errors/
│   │   ├── {nome-agregado}-nao-encontrada.error.ts
│   │   ├── {nome-agregado}-{regra}.error.ts
│   │   └── index.ts
│   ├── repositories/
│   │   └── i{nome-agregado}.repository.ts     # JÁ EXISTE (Step 8b)
│   ├── dto/
│   │   └── {nome-agregado}-filters.dto.ts
│   └── index.ts
├── application/
│   └── use-cases/
│       ├── {acao}{nome-agregado}.use-case.ts
│       └── index.ts
└── infrastructure/
    ├── mappers/
    │   └── {nome-agregado}.mapper.ts          # JÁ EXISTE (Step 8b)
    └── repositories/
        └── prisma-{nome-agregado}.repository.ts  # JÁ EXISTE (Step 8b)
```

---

## 1. Shared Kernel (Base Classes)

Estas classes base devem existir em `src/shared/` e ser reutilizadas:

### 1.1 Result Type — `shared/result.ts`

```typescript
// src/shared/result.ts
export type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };

export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

export function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

export function isErr<T, E>(result: Result<T, E>): result is { ok: false; error: E } {
  return !result.ok;
}
```

### 1.2 Value Object Base — `shared/value-object.ts`

```typescript
// src/shared/value-object.ts
export abstract class ValueObject<T> {
  protected readonly value: T;

  constructor(value: T) {
    this.value = Object.freeze(value);
  }

  getValue(): T {
    return this.value;
  }

  equals(other: ValueObject<T>): boolean {
    if (!other) return false;
    if (!(other instanceof this.constructor)) return false;
    return JSON.stringify(this.value) === JSON.stringify(other.value);
  }

  toString(): string {
    return JSON.stringify(this.value);
  }
}
```

### 1.3 Domain Event Base — `shared/domain/domain-event.ts`

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

### 1.4 Domain Error Base — `shared/errors/domain-error.ts`

```typescript
// src/shared/errors/domain-error.ts
export abstract class DomainError extends Error {
  public readonly code: string;
  public readonly timestamp: Date;

  constructor(message: string, code: string) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.timestamp = new Date();
    Object.setPrototypeOf(this, DomainError.prototype);
  }
}
```

---

## 2. Entity Template — `domain/entities/{nome-agregado}.entity.ts`

```typescript
// src/{modulo}/domain/entities/{nome-agregado}.entity.ts
import { Result, ok, err } from '../../../shared/result';
import { {NomeAgregado}Id } from '../value-objects/{nome-agregado}-id.vo';
import { {VO1} } from '../value-objects/{vo1}.vo';
import { {VO2} } from '../value-objects/{vo2}.vo';
import { {NomeAgregado}NaoEncontradaError } from '../errors/{nome-agregado}-nao-encontrada.error';
import { {RegraInvalida}Error } from '../errors/{regra-invalida}.error';
import { {NomeAgregado}{Acao1}Event } from '../events/{nome-agregado}-{acao1}.event';
import { {NomeAgregado}{Acao2}Event } from '../events/{nome-agregado}-{acao2}.event';

export interface {NomeAgregado}Props {
  id: {NomeAgregado}Id;
  // Identidade
  identificadorUnico: {VO1};           // ex: NumeroAuditoria, Email, CPF
  // Estado
  status: {StatusVO};                  // Value Object com transições válidas
  // Dados de negócio
  {campo1}: {tipo};
  {campo2}: {tipo};
  // Relacionamentos (apenas IDs ou VOs de identidade)
  {relacionamento1}Id: {Relacionamento1}Id;
  {relacionamento2}Ids: {Relacionamento2}Id[];
  // Auditoria
  criadoPorId: string;
  atualizadoPorId: string;
  createdAt: Date;
  updatedAt: Date;
}

export class {NomeAgregado} {
  private _domainEvents: DomainEvent[] = [];
  private constructor(private readonly props: {NomeAgregado}Props) {}

  // ========== Factory Methods ==========
  
  /**
   * Cria nova instância validando invariantes de negócio
   * Retorna Result para evitar exceptions em regras de domínio
   */
  static criar(props: Omit<{NomeAgregado}Props, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'identificadorUnico'>): Result<{NomeAgregado}, Error> {
    // Validações de invariantes
    if (!props.{campoObrigatorio} || props.{campoObrigatorio}.trim().length < min) {
      return err(new Error(`{CampoObrigatorio} deve ter pelo menos ${min} caracteres`));
    }
    
    if (!props.{relacionamento1}Id) {
      return err(new Error('{Relacionamento1} é obrigatório'));
    }

    // Validações cross-field
    if (props.{campo1} && props.{campo2} && !regraCrossField(props.{campo1}, props.{campo2})) {
      return err(new Error('Regra cross-field violada'));
    }

    const agora = new Date();
    const entity = new {NomeAgregado}({
      ...props,
      id: {NomeAgregado}Id.generate(),
      identificadorUnico: {VO1}.generate(), // Será sobrescrito pelo repo se necessário
      status: {StatusVO}.criar('ESTADO_INICIAL').value, // Estado inicial válido
      criadoPorId: props.criadoPorId,
      atualizadoPorId: props.criadoPorId,
      createdAt: agora,
      updatedAt: agora,
    });

    // Domain Event: fato ocorrido
    entity._domainEvents.push(new {NomeAgregado}CriadoEvent(
      entity.props.id.value,
      entity.props.identificadorUnico.value,
      // ... dados relevantes do evento
    ));

    return ok(entity);
  }

  /**
   * Reconstitui entidade a partir do banco (sem validações, sem events)
   * Usado pelo Repository Mapper
   */
  static reconstitute(props: {NomeAgregado}Props): {NomeAgregado} {
    return new {NomeAgregado}(props);
  }

  // ========== Getters (Read-only) ==========
  
  get id() { return this.props.id; }
  get identificadorUnico() { return this.props.identificadorUnico; }
  get status() { return this.props.status; }
  get {campo1}() { return this.props.{campo1}; }
  get {campo2}() { return this.props.{campo2}; }
  get {relacionamento1}Id() { return this.props.{relacionamento1}Id; }
  get {relacionamento2}Ids() { return [...this.props.{relacionamento2}Ids]; } // defensive copy
  get criadoPorId() { return this.props.criadoPorId; }
  get atualizadoPorId() { return this.props.atualizadoPorId; }
  get createdAt() { return this.props.createdAt; }
  get updatedAt() { return this.props.updatedAt; }

  // ========== Comportamento de Domínio (Mutações Controladas) ==========
  
  /**
   * Transição de estado: Estado Inicial → Em Execução
   * Regras: só pode iniciar se estiver no estado inicial
   */
  {acao1}(): Result<void, {RegraInvalida}Error> {
    if (!this.props.status.podeTransicionarPara({StatusVO}.criar('EM_EXECUCAO').value)) {
      return err(new {RegraInvalida}Error(this.props.status.value, 'EM_EXECUCAO'));
    }
    
    this.props.status = {StatusVO}.criar('EM_EXECUCAO').value;
    this.props.{dataInicio} = new Date();
    this.props.updatedAt = new Date();
    
    this._domainEvents.push(new {NomeAgregado}{Acao1}Event(
      this.props.id.value,
      this.props.identificadorUnico.value,
      // ... dados do evento
    ));
    
    return ok(undefined);
  }

  /**
   * Transição: Em Execução → Concluído
   */
  {acao2}(): Result<void, {RegraInvalida}Error> {
    if (!this.props.status.podeTransicionarPara({StatusVO}.criar('CONCLUIDO').value)) {
      return err(new {RegraInvalida}Error(this.props.status.value, 'CONCLUIDO'));
    }
    
    this.props.status = {StatusVO}.criar('CONCLUIDO').value;
    this.props.{dataFim} = new Date();
    this.props.updatedAt = new Date();
    
    this._domainEvents.push(new {NomeAgregado}{Acao2}Event(
      this.props.id.value,
      this.props.identificadorUnico.value,
    ));
    
    return ok(undefined);
  }

  /**
   * Atualização de campo com validação
   */
  atualizar{Campo}(novoValor: {tipo}): Result<void, Error> {
    if (!validar{NovoValor}(novoValor)) {
      return err(new Error('Valor inválido'));
    }
    this.props.{campo} = novoValor;
    this.props.updatedAt = new Date();
    return ok(undefined);
  }

  /**
   * Adiciona relacionamento (ex: adicionar membro à equipe)
   */
  adicionar{Relacionamento2}(id: {Relacionamento2}Id): Result<void, Error> {
    if (this.props.{relacionamento2}Ids.some(existing => existing.equals(id))) {
      return err(new Error('{Relacionamento2} já associado'));
    }
    this.props.{relacionamento2}Ids.push(id);
    this.props.updatedAt = new Date();
    return ok(undefined);
  }

  // ========== Domain Events ==========
  
  get domainEvents(): DomainEvent[] {
    return [...this._domainEvents];
  }

  clearDomainEvents(): void {
    this._domainEvents = [];
  }

  // ========== Equality ==========
  
  equals(other: {NomeAgregado}): boolean {
    return other instanceof {NomeAgregado} && this.props.id.equals(other.props.id);
  }
}
```

---

## 3. Value Object Templates

### 3.1 ID Value Object — `domain/value-objects/{nome-agregado}-id.vo.ts`

```typescript
// src/{modulo}/domain/value-objects/{nome-agregado}-id.vo.ts
import { ValueObject } from '../../../shared/value-object';
import { Result, ok, err } from '../../../shared/result';

export class {NomeAgregado}Id extends ValueObject<string> {
  private constructor(value: string) {
    super(value);
  }

  static criar(value: string): Result<{NomeAgregado}Id, Error> {
    if (!value || value.trim().length === 0) {
      return err(new Error('{NomeAgregado}Id não pode ser vazio'));
    }
    // Validar formato UUID se aplicável
    // if (!uuidRegex.test(value)) return err(new Error('ID deve ser UUID válido'));
    return ok(new {NomeAgregado}Id(value.trim()));
  }

  static generate(): {NomeAgregado}Id {
    return new {NomeAgregado}Id(crypto.randomUUID());
  }

  static fromString(value: string): {NomeAgregado}Id {
    return new {NomeAgregado}Id(value);
  }

  toString(): string {
    return this.value;
  }
}
```

### 3.2 Status/State VO com Transições — `domain/value-objects/{status}.vo.ts`

```typescript
// src/{modulo}/domain/value-objects/{status}.vo.ts
import { ValueObject } from '../../../shared/value-object';
import { Result, ok, err } from '../../../shared/result';

export class {StatusVO} extends ValueObject<string> {
  private static readonly VALIDOS = ['ESTADO_1', 'ESTADO_2', 'ESTADO_3', 'ESTADO_4'] as const;
  private static readonly TRANSICOES: Record<string, string[]> = {
    'ESTADO_1': ['ESTADO_2', 'ESTADO_4'],      // Inicial → Em Execução, Cancelado
    'ESTADO_2': ['ESTADO_3', 'ESTADO_4'],      // Em Execução → Concluído, Cancelado
    'ESTADO_3': [],                            // Concluído → terminal
    'ESTADO_4': ['ESTADO_1', 'ESTADO_2'],      // Cancelado → pode reabrir
  };

  private constructor(value: string) {
    super(value);
  }

  static criar(value: string): Result<{StatusVO}, Error> {
    const upper = value.toUpperCase();
    if (!{StatusVO}.VALIDOS.includes(upper as any)) {
      return err(new Error(`Status inválido: ${value}. Válidos: ${[...{StatusVO}.VALIDOS].join(', ')}`));
    }
    return ok(new {StatusVO}(upper));
  }

  // Getters estáticos para estados
  static get ESTADO_1() { return new {StatusVO}('ESTADO_1'); }
  static get ESTADO_2() { return new {StatusVO}('ESTADO_2'); }
  static get ESTADO_3() { return new {StatusVO}('ESTADO_3'); }
  static get ESTADO_4() { return new {StatusVO}('ESTADO_4'); }

  podeTransicionarPara(novoStatus: {StatusVO}): boolean {
    return {StatusVO}.TRANSICOES[this.value]?.includes(novoStatus.value) ?? false;
  }

  ehTerminal(): boolean {
    return {StatusVO}.TRANSICOES[this.value].length === 0;
  }
}
```

### 3.3 VO Genérico — `domain/value-objects/{vo-especifico}.vo.ts`

```typescript
// src/{modulo}/domain/value-objects/{vo-especifico}.vo.ts
import { ValueObject } from '../../../shared/value-object';
import { Result, ok, err } from '../../../shared/result';

export class {VOEspecifico} extends ValueObject<{tipo}> {
  private constructor(value: {tipo}) {
    super(value);
  }

  static criar(value: {tipo}): Result<{VOEspecifico}, Error> {
    // Validações específicas
    if (!value) {
      return err(new Error('{VOEspecifico} não pode ser vazio'));
    }
    // regex, length, range, etc.
    return ok(new {VOEspecifico}(value));
  }

  // Métodos de domínio do VO
  // ex: format(), combine(other), isValidFor(operation)
}
```

---

## 4. Domain Events — `domain/events/{nome-agregado}-{acao}.event.ts`

```typescript
// src/{modulo}/domain/events/{nome-agregado}-{acao}.event.ts
import { DomainEvent } from '../../../shared/domain/domain-event';

export class {NomeAgregado}{Acao}Event extends DomainEvent {
  constructor(
    aggregateId: string,
    public readonly {campo1}: {tipo},
    public readonly {campo2}: {tipo},
    // ... dados relevantes do evento (imutáveis)
  ) {
    super(aggregateId, '{NomeAgregado}');
  }

  static eventName = '{nome-agregado}.{acao}';
}
```

### Index de Eventos — `domain/events/index.ts`

```typescript
// src/{modulo}/domain/events/index.ts
export * from './{nome-agregado}-criado.event';
export * from './{nome-agregado}-{acao1}.event';
export * from './{nome-agregado}-{acao2}.event';
// ...
```

---

## 5. Domain Errors — `domain/errors/{nome-agregado}-{erro}.error.ts`

```typescript
// src/{modulo}/domain/errors/{nome-agregado}-nao-encontrada.error.ts
import { DomainError } from '../../../shared/errors/domain-error';

export class {NomeAgregado}NaoEncontradaError extends DomainError {
  constructor(identifier: string) {
    super(`{NomeAgregado} não encontrado: ${identifier}`, '{NOME_AGREGADO}_NAO_ENCONTRADA');
  }
}

// src/{modulo}/domain/errors/{regra-invalida}.error.ts
export class {RegraInvalida}Error extends DomainError {
  constructor(
    public readonly estadoAtual: string,
    public readonly estadoTentado: string,
  ) {
    super(`Transição inválida de '${estadoAtual}' para '${estadoTentado}'`, 'REGRA_TRANSICAO_INVALIDA');
  }
}
```

### Index de Erros — `domain/errors/index.ts`

```typescript
// src/{modulo}/domain/errors/index.ts
export * from './{nome-agregado}-nao-encontrada.error';
export * from './{regra-invalida}.error';
// ...
```

---

## 6. Use Case Template — `application/use-cases/{acao}{nome-agregado}.use-case.ts`

```typescript
// src/{modulo}/application/use-cases/{acao}{nome-agregado}.use-case.ts
import { Injectable } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { I{NomeAgregado}Repository } from '../../domain/repositories/i{nome-agregado}.repository';
import { {NomeAgregado} } from '../../domain/entities/{nome-agregado}.entity';
import { {NomeAgregado}NaoEncontradaError } from '../../domain/errors/{nome-agregado}-nao-encontrada.error';
import { {OutroModulo}Repository } from '../../../{outro-modulo}/domain/repositories/i{outro}.repository';

export interface {Acao}{NomeAgregado}Input {
  {campo1}: {tipo};
  {campo2}: {tipo};
  // IDs de relacionamentos
  {relacionamento}Id: string;
  // Contexto de execução
  executorId: string;
}

export interface {Acao}{NomeAgregado}Output {
  {nomeAgregado}: {NomeAgregado};
}

@Injectable()
export class {Acao}{NomeAgregado}UseCase {
  constructor(
    private readonly {nomeAgregado}Repo: I{NomeAgregado}Repository,
    private readonly {outroModulo}Repo: {OutroModulo}Repository,
    private readonly eventEmitter: EventEmitter2,
  ) {}

  async execute(input: {Acao}{NomeAgregado}Input): Promise<{Acao}{NomeAgregado}Output> {
    // ========== 1. Validações Cross-Aggregate ==========
    const relacionado = await this.{outroModulo}Repo.findById(input.{relacionamento}Id);
    if (!relacionado) {
      throw new {NomeAgregado}NaoEncontradaError(`Relacionado ${input.{relacionamento}Id} não encontrado`);
    }
    
    if (!regraDeNegocioCrossAggregate(relacionado)) {
      throw new Error('Regra de negócio cross-aggregate violada');
    }

    // ========== 2. Cria/Modifica Entidade (Domain Logic) ==========
    const result = {NomeAgregado}.criar({
      {campo1}: input.{campo1},
      {campo2}: input.{campo2},
      {relacionamento1}Id: relacionado.id,
      criadoPorId: input.executorId,
    });

    if (result.isErr()) {
      throw result.error;
    }

    const entity = result.value;

    // ========== 3. Persiste ==========
    const saved = await this.{nomeAgregado}Repo.save(entity);

    // ========== 4. Emite Domain Events ==========
    for (const event of saved.domainEvents) {
      this.eventEmitter.emit(event.constructor.eventName, event);
    }
    saved.clearDomainEvents();

    return { {nomeAgregado}: saved };
  }
}
```

### Use Cases Obrigatórios por Aggregate Root (Core Modules)

| Use Case | Input | Output | Descrição |
|----------|-------|--------|-----------|
| `Criar{NomeAgregado}UseCase` | CreateDto + executorId | Entity | Factory + persist + event |
| `{Acao1}{NomeAgregado}UseCase` | Input + executorId | Entity | Transição estado 1→2 |
| `{Acao2}{NomeAgregado}UseCase` | Input + executorId | Entity | Transição estado 2→3 |
| `Atualizar{NomeAgregado}UseCase` | UpdateDto + executorId | Entity | Atualização campos |
| `Listar{NomeAgregado}UseCase` | Filter + Pagination | Entity[] | Query otimizada |

---

## 7. Checklist de Validação por PRP (Gate 11-pre)

Para cada Aggregate Root modelado:

### Entity
- [ ] Classe em `domain/entities/{nome}.entity.ts`
- [ ] `criar()` factory method com validações de invariantes → retorna `Result`
- [ ] `reconstitute()` para hidratação do banco → sem validações, sem events
- [ ] Getters readonly para todas as props
- [ ] Métodos de comportamento (mutações) → retornam `Result<void, DomainError>`
- [ ] `_domainEvents` array + `domainEvents` getter + `clearDomainEvents()`
- [ ] `equals()` por ID
- [ ] **Zero imports** de: `@nestjs/*`, `@prisma/client`, `PrismaService`, decorators

### Value Objects
- [ ] Estendem `ValueObject<T>` de `shared/`
- [ ] `criar()` factory com validação → `Result`
- [ ] Imutáveis (Object.freeze no construtor)
- [ ] `equals()` por valor
- [ ] Status VO: `TRANSICOES` definidas + `podeTransicionarPara()`

### Domain Events
- [ ] Estendem `DomainEvent` de `shared/domain/`
- [ ] `eventName` static property (ex: `auditoria.aberta`)
- [ ] Imutáveis, com `occurredAt`, `aggregateId`, `aggregateType`
- [ ] Dados relevantes para handlers (não a entidade inteira)

### Domain Errors
- [ ] Estendem `DomainError` de `shared/errors/`
- [ ] `code` único e descritivo
- [ ] Contexto relevante no construtor (estado atual, tentado, etc.)

### Use Cases
- [ ] Em `application/use-cases/{acao}{nome}.use-case.ts`
- [ ] Classe `{Acao}{NomeAgregado}UseCase`
- [ ] Injetam: Repository Interfaces + `EventEmitter2` + outros Repos (cross-aggregate)
- [ ] **NÃO injetam:** `PrismaService`, Controllers, outros Use Cases, Services de infra
- [ ] `execute(input)` retorna `Promise<Output>`
- [ ] Validações cross-aggregate ANTES de criar/modificar entidade
- [ ] Usa `entity.criar()` ou métodos da entidade (domain logic)
- [ ] Persiste via repository interface
- [ ] Emite `domainEvents` via `EventEmitter2`
- [ ] Limpa events com `clearDomainEvents()`

---

## 8. Exemplo Concreto: Módulo Auditorias

### Entity: `src/auditorias/domain/entities/auditoria.entity.ts`

```typescript
export class Auditoria {
  private _domainEvents: DomainEvent[] = [];
  private constructor(private readonly props: AuditoriaProps) {}

  static criar(props: Omit<AuditoriaProps, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'numero'>): Result<Auditoria, Error> {
    if (!props.objetivo || props.objetivo.trim().length < 10) {
      return err(new Error('Objetivo deve ter pelo menos 10 caracteres'));
    }
    if (!props.auditorLiderId) {
      return err(new Error('Auditor líder é obrigatório'));
    }
    
    const entity = new Auditoria({
      ...props,
      id: AuditoriaId.generate(),
      numero: NumeroAuditoria.generate(), // placeholder
      status: StatusAuditoria.criar('ABERTA').value,
      createdAt: new Date(),
      updatedAt: new Date(),
    });
    
    entity._domainEvents.push(new AuditoriaAbertaEvent(
      entity.props.id.value,
      entity.props.numero.value,
      entity.props.unidadeAuditadaId.value,
    ));
    
    return ok(entity);
  }

  static reconstitute(props: AuditoriaProps): Auditoria {
    return new Auditoria(props);
  }

  // Getters...
  get id() { return this.props.id; }
  get numero() { return this.props.numero; }
  get status() { return this.props.status; }
  // ...

  iniciarExecucao(): Result<void, TransicaoStatusInvalidaError> {
    if (!this.props.status.podeTransicionarPara(StatusAuditoria.EM_EXECUCAO)) {
      return err(new TransicaoStatusInvalidaError(this.props.status.value, 'EM_EXECUCAO'));
    }
    this.props.status = StatusAuditoria.EM_EXECUCAO;
    this.props.dataInicio = new Date();
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaIniciadaEvent(this.props.id.value, this.props.numero.value));
    return ok(undefined);
  }

  concluir(): Result<void, TransicaoStatusInvalidaError> {
    if (!this.props.status.podeTransicionarPara(StatusAuditoria.CONCLUIDA)) {
      return err(new TransicaoStatusInvalidaError(this.props.status.value, 'CONCLUIDA'));
    }
    this.props.status = StatusAuditoria.CONCLUIDA;
    this.props.dataFim = new Date();
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaConcluidaEvent(this.props.id.value, this.props.numero.value));
    return ok(undefined);
  }

  suspender(motivo: string): Result<void, TransicaoStatusInvalidaError> {
    if (!['ABERTA', 'EM_EXECUCAO'].includes(this.props.status.value)) {
      return err(new TransicaoStatusInvalidaError(this.props.status.value, 'SUSPENSA'));
    }
    this.props.status = StatusAuditoria.SUSPENSA;
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaSuspensaEvent(this.props.id.value, this.props.numero.value, motivo));
    return ok(undefined);
  }

  // Domain Events
  get domainEvents() { return [...this._domainEvents]; }
  clearDomainEvents() { this._domainEvents = []; }

  equals(other: Auditoria): boolean {
    return other instanceof Auditoria && this.props.id.equals(other.props.id);
  }
}
```

### VO: `src/auditorias/domain/value-objects/status-auditoria.vo.ts`

```typescript
export class StatusAuditoria extends ValueObject<string> {
  private static readonly VALIDOS = ['ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'SUSPENSA', 'CANCELADA'] as const;
  private static readonly TRANSICOES = {
    'ABERTA': ['EM_EXECUCAO', 'SUSPENSA', 'CANCELADA'],
    'EM_EXECUCAO': ['CONCLUIDA', 'SUSPENSA'],
    'CONCLUIDA': [],
    'SUSPENSA': ['ABERTA', 'EM_EXECUCAO', 'CANCELADA'],
    'CANCELADA': [],
  };

  static criar(value: string): Result<StatusAuditoria, Error> { /* ... */ }
  static get ABERTA() { return new StatusAuditoria('ABERTA'); }
  static get EM_EXECUCAO() { return new StatusAuditoria('EM_EXECUCAO'); }
  static get CONCLUIDA() { return new StatusAuditoria('CONCLUIDA'); }
  static get SUSPENSA() { return new StatusAuditoria('SUSPENSA'); }
  static get CANCELADA() { return new StatusAuditoria('CANCELADA'); }

  podeTransicionarPara(novo: StatusAuditoria): boolean {
    return StatusAuditoria.TRANSICOES[this.value]?.includes(novo.value) ?? false;
  }
}
```

### Use Case: `src/auditorias/application/use-cases/abrir-auditoria.use-case.ts`

```typescript
@Injectable()
export class AbrirAuditoriaUseCase {
  constructor(
    private readonly auditoriaRepo: IAuditoriaRepository,
    private readonly planoRepo: IPlanoRepository,
    private readonly eventEmitter: EventEmitter2,
  ) {}

  async execute(input: AbrirAuditoriaInput): Promise<AbrirAuditoriaOutput> {
    const itemPlano = await this.planoRepo.findItemById(input.itemPlanoId);
    if (!itemPlano) throw new AuditoriaNaoEncontradaError(`Item do plano ${input.itemPlanoId} não encontrado`);
    if (!['APROVADO', 'PUBLICADO'].includes(itemPlano.plano.status)) {
      throw new Error('Item do plano deve pertencer a um plano aprovado ou publicado');
    }

    const result = Auditoria.criar({
      itemPlanoId: input.itemPlanoId,
      tipo: input.tipo || 'CONFORMIDADE',
      auditorLiderId: input.auditorLiderId,
      equipeIds: input.equipeIds,
      unidadeAuditadaId: itemPlano.unidadeId,
      objetivo: itemPlano.objetivo,
    });

    if (result.isErr()) throw result.error;

    const auditoria = result.value;
    auditoria.props.numero = await this.auditoriaRepo.nextNumero();
    const saved = await this.auditoriaRepo.save(auditoria);

    for (const event of saved.domainEvents) {
      this.eventEmitter.emit(event.constructor.eventName, event);
    }
    saved.clearDomainEvents();

    return { auditoria: saved };
  }
}
```

---

## 9. Greenfield vs Brownfield

| Cenário | Ação |
|---------|------|
| **Greenfield** (PRP novo) | Aplicar template completo para todos aggregate roots do PRP |
| **Brownfield** (PRP-A amendment) | 1. Ler código existente<br>2. Estender/adaptar entidades existentes<br>3. Adicionar novos VOs, Events, Errors conforme necessário<br>4. Criar novos Use Cases para nova funcionalidade<br>5. Marcar código legacy com `// LEGACY` e criar issue de migração |

---

## 10. Referências Cruzadas

| Template | Localização | Uso |
|----------|-------------|-----|
| `ARCHITECTURE_PATTERNS_TEMPLATE.md` | `docs/templates/` | Step 5a — Define padrões globais |
| `REPOSITORY_PATTERN_TEMPLATE.md` | `docs/templates/` | Step 8b — Repository interfaces já existem |
| `FITNESS_FUNCTION_TEMPLATE.md` | `docs/templates/` | Step 11b — Regras de validação |
| `ADR_TEMPLATE.md` | `docs/templates/` | Step 5a/10 — Decisões arquiteturais |