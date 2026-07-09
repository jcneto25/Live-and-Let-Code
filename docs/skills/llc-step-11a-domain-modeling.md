---
name: llc-step-11a-domain-modeling
description: Pipeline LLC Step 11a — Domain Modeling per PRP. Para cada PRP com regras de negócio: gera Entities, Value Objects, Domain Events, Domain Errors, Use Cases usando templates. Executa ANTES da implementação (Step 11) para garantir arquitetura correta desde o primeiro código.
version: 1.0.0
tags: [domain-modeling, ddd, entities, value-objects, domain-events, use-cases, llc-pipeline]
---

# LLC Skill: Step 11a — Domain Modeling per PRP

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Implementation — Pre-Execution (sub-step of Step 11)  
**Depende de:** Step 5a (Architecture Patterns), Step 8b (Repository Pattern), Step 3 (PRPs com DoD)  
**Executa antes de:** Step 11 (Execution), Step 11b (Arch Fitness)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11a` ou "Execute a skill llc-step-11a".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 11a --prp PRP-001 --task "Domain modeling para PRP-001"`.

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — com §7 (Domain Layer), §8 (Event Bus), §9 (Fitness)
- [ ] `.ace/arch-config.yaml` — módulos core, naming conventions
- [ ] `docs/prps/PRP-{NNN}.md` — PRP alvo com **Definition of Done**, **§7 Data Model**, **§8 Business Rules**
- [ ] `docs/planning/TASKS.md` — tarefas do PRP com IDs
- [ ] `docs/templates/DOMAIN_MODEL_TEMPLATE.md` — template para geração
- [ ] Repository Pattern já implementado no módulo (Step 8b)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 11a** estiver listado como "skip" para o PRP alvo:
   - **PARE** e informe: "Step 11a pulado para este PRP — domain model já existe e não foi alterado no DELTA_REPORT."
3. Se **Step 11a** estiver listado como "executar" ou PRP é novo: prossiga normalmente.
4. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11a-domain-modeling` do pipeline LLC. Seu objetivo é **gerar o modelo de domínio completo** (Entities, Value Objects, Domain Events, Domain Errors, Use Cases) para **um PRP específico**, seguindo os padrões definidos no Step 5a e usando o `DOMAIN_MODEL_TEMPLATE.md`.

### 1. Leia o PRP Alvo e Identifique o que Modelar

Leia `docs/prps/PRP-{NNN}.md` e extraia:

- **§7 Data Model:** Entidades, Value Objects, relacionamentos, invariantes
- **§8 Business Rules:** Regras de negócio, transições de estado, validações
- **§9 Use Cases / Fluxos:** Operações que o usuário/sistema executa
- **DoD:** Critérios de aceite que definem o escopo

**Classifique o PRP:**
| Tipo | Ação |
|------|------|
| **Core Domain** (regras complexas, workflow, state machine) | Modelagem completa: Entity + VO + Domain Events + Errors + Use Cases |
| **Supporting Domain** (CRUD com algumas validações) | Entity + VO + Repository + Use Cases básicos |
| **Generic Domain** (CRUD puro, sem regras) | Apenas Entity + Repository Interface + Service (sem Use Cases) |

### 2. Gere o Modelo de Domínio (use `DOMAIN_MODEL_TEMPLATE.md`)

Para **cada Aggregate Root** identificado no PRP, crie a estrutura:

```
src/{modulo}/
├── domain/
│   ├── entities/
│   │   └── {entidade}.entity.ts
│   ├── value-objects/
│   │   └── {vo-name}.vo.ts
│   ├── events/
│   │   ├── {entidade}-{acao}.event.ts
│   │   └── index.ts
│   ├── errors/
│   │   ├── {entidade}-nao-encontrada.error.ts
│   │   ├── {entidade}-{regra-invalida}.error.ts
│   │   └── index.ts
│   ├── repositories/
│   │   └── i{entidade}.repository.ts     # JÁ EXISTE (Step 8b)
│   └── dto/
│       └── {entidade}-filters.dto.ts
├── application/
│   └── use-cases/
│       ├── {acao}{entidade}.use-case.ts
│       └── index.ts
└── infrastructure/
    ├── mappers/
    │   └── {entidade}.mapper.ts          # JÁ EXISTE (Step 8b)
    └── repositories/
        └── prisma-{entidade}.repository.ts  # JÁ EXISTE (Step 8b)
```

#### 2.1 Domain Entity — `domain/entities/{entidade}.entity.ts`

```typescript
// src/auditorias/domain/entities/auditoria.entity.ts
import { Result, ok, err } from '../../../shared/result';
import { AuditoriaId } from '../value-objects/auditoria-id.vo';
import { NumeroAuditoria } from '../value-objects/numero-auditoria.vo';
import { StatusAuditoria } from '../value-objects/status-auditoria.vo';
import { UnidadeId } from '../value-objects/unidade-id.vo';
import { AuditoriaNaoEncontradaError } from '../errors/auditoria-nao-encontrada.error';
import { TransicaoStatusInvalidaError } from '../errors/transicao-status-invalida.error';
import { AuditoriaAbertaEvent } from '../events/auditoria-aberta.event';
import { AuditoriaIniciadaEvent } from '../events/auditoria-iniciada.event';
import { AuditoriaConcluidaEvent } from '../events/auditoria-concluida.event';
import { AuditoriaSuspensaEvent } from '../events/auditoria-suspensa.event';

export interface AuditoriaProps {
  id: AuditoriaId;
  numero: NumeroAuditoria;
  status: StatusAuditoria;
  unidadeAuditadaId: UnidadeId;
  objetivo: string;
  tipo: TipoAuditoria;
  dataInicio?: Date;
  dataFim?: Date;
  auditorLiderId: string;
  equipeIds: string[];
  createdAt: Date;
  updatedAt: Date;
}

export class Auditoria {
  private _domainEvents: AuditoriaAbertaEvent | AuditoriaIniciadaEvent | AuditoriaConcluidaEvent | AuditoriaSuspensaEvent[] = [];
  private constructor(private readonly props: AuditoriaProps) {}

  // Factory method — valida invariantes na criação
  static criar(props: Omit<AuditoriaProps, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'numero'>): Result<Auditoria, Error> {
    // Validações de invariantes
    if (!props.objetivo || props.objetivo.trim().length < 10) {
      return err(new Error('Objetivo deve ter pelo menos 10 caracteres'));
    }
    if (!props.auditorLiderId) {
      return err(new Error('Auditor líder é obrigatório'));
    }

    const agora = new Date();
    const entity = new Auditoria({
      ...props,
      id: AuditoriaId.generate(),
      numero: NumeroAuditoria.generate(), // será sobrescrito pelo repo
      status: StatusAuditoria.criar('ABERTA').value,
      createdAt: agora,
      updatedAt: agora,
    });

    // Adiciona domain event
    entity._domainEvents.push(new AuditoriaAbertaEvent(entity.props.id.value, entity.props.numero.value, entity.props.unidadeAuditadaId.value));
    return ok(entity);
  }

  // Reconstituição a partir do banco (sem validações, sem events)
  static reconstitute(props: AuditoriaProps): Auditoria {
    return new Auditoria(props);
  }

  // Getters
  get id() { return this.props.id; }
  get numero() { return this.props.numero; }
  get status() { return this.props.status; }
  get unidadeAuditadaId() { return this.props.unidadeAuditadaId; }
  get objetivo() { return this.props.objetivo; }
  get tipo() { return this.props.tipo; }
  get dataInicio() { return this.props.dataInicio; }
  get dataFim() { return this.props.dataFim; }
  get auditorLiderId() { return this.props.auditorLiderId; }
  get equipeIds() { return this.props.equipeIds; }
  get createdAt() { return this.props.createdAt; }
  get updatedAt() { return this.props.updatedAt; }

  // Comportamento de domínio — retorna Result, never throw
  iniciarExecucao(): Result<void, TransicaoStatusInvalidaError> {
    if (this.props.status !== StatusAuditoria.criar('ABERTA').value) {
      return err(new TransicaoStatusInvalidaError(this.props.status, 'EM_EXECUCAO'));
    }
    this.props.status = StatusAuditoria.criar('EM_EXECUCAO').value;
    this.props.dataInicio = new Date();
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaIniciadaEvent(this.props.id.value, this.props.numero.value));
    return ok(undefined);
  }

  concluir(): Result<void, TransicaoStatusInvalidaError> {
    if (this.props.status !== StatusAuditoria.criar('EM_EXECUCAO').value) {
      return err(new TransicaoStatusInvalidaError(this.props.status, 'CONCLUIDA'));
    }
    this.props.status = StatusAuditoria.criar('CONCLUIDA').value;
    this.props.dataFim = new Date();
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaConcluidaEvent(this.props.id.value, this.props.numero.value));
    return ok(undefined);
  }

  suspender(motivo: string): Result<void, TransicaoStatusInvalidaError> {
    if (!['ABERTA', 'EM_EXECUCAO'].includes(this.props.status)) {
      return err(new TransicaoStatusInvalidaError(this.props.status, 'SUSPENSA'));
    }
    this.props.status = StatusAuditoria.criar('SUSPENSA').value;
    this.props.updatedAt = new Date();
    this._domainEvents.push(new AuditoriaSuspensaEvent(this.props.id.value, this.props.numero.value, motivo));
    return ok(undefined);
  }

  // Domain Events
  get domainEvents() { return [...this._domainEvents]; }
  clearDomainEvents() { this._domainEvents = []; }

  // Equality por ID
  equals(other: Auditoria): boolean {
    return other instanceof Auditoria && this.props.id.equals(other.props.id);
  }
}

export type TipoAuditoria = 'CONFORMIDADE' | 'DESEMPENHO' | 'ESPECIAL';
```

#### 2.2 Value Objects — `domain/value-objects/{vo-name}.vo.ts`

```typescript
// src/auditorias/domain/value-objects/status-auditoria.vo.ts
import { ValueObject } from '../../../shared/value-object';
import { Result, ok, err } from '../../../shared/result';

export class StatusAuditoria extends ValueObject<string> {
  private static readonly VALIDOS = ['ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'SUSPENSA', 'CANCELADA'] as const;
  private static readonly TRANSICOES: Record<string, string[]> = {
    'ABERTA': ['EM_EXECUCAO', 'SUSPENSA', 'CANCELADA'],
    'EM_EXECUCAO': ['CONCLUIDA', 'SUSPENSA'],
    'CONCLUIDA': [],
    'SUSPENSA': ['ABERTA', 'EM_EXECUCAO', 'CANCELADA'],
    'CANCELADA': [],
  };

  private constructor(value: string) {
    super(value);
  }

  static criar(value: string): Result<StatusAuditoria, Error> {
    const upper = value.toUpperCase();
    if (!StatusAuditoria.VALIDOS.includes(upper as any)) {
      return err(new Error(`Status inválido: ${value}. Válidos: ${StatusAuditoria.VALIDOS.join(', ')}`));
    }
    return ok(new StatusAuditoria(upper));
  }

  static get ABERTA() { return new StatusAuditoria('ABERTA'); }
  static get EM_EXECUCAO() { return new StatusAuditoria('EM_EXECUCAO'); }
  static get CONCLUIDA() { return new StatusAuditoria('CONCLUIDA'); }
  static get SUSPENSA() { return new StatusAuditoria('SUSPENSA'); }
  static get CANCELADA() { return new StatusAuditoria('CANCELADA'); }

  podeTransicionarPara(novoStatus: StatusAuditoria): boolean {
    return StatusAuditoria.TRANSICOES[this.value].includes(novoStatus.value);
  }
}
```

#### 2.3 Domain Events — `domain/events/{entidade}-{acao}.event.ts`

```typescript
// src/auditorias/domain/events/auditoria-aberta.event.ts
import { DomainEvent } from '../../../shared/domain/domain-event';

export class AuditoriaAbertaEvent extends DomainEvent {
  constructor(
    aggregateId: string,
    public readonly numero: string,
    public readonly unidadeAuditadaId: string,
  ) {
    super(aggregateId, 'Auditoria');
  }

  static eventName = 'auditoria.aberta';
}
```

#### 2.4 Domain Errors — `domain/errors/{entidade}-{erro}.error.ts`

```typescript
// src/auditorias/domain/errors/transicao-status-invalida.error.ts
import { DomainError } from '../../../shared/errors/domain-error';

export class TransicaoStatusInvalidaError extends DomainError {
  constructor(
    public readonly statusAtual: string,
    public readonly statusTentado: string,
  ) {
    super(`Transição inválida de '${statusAtual}' para '${statusTentado}'`, 'TRANSICAO_STATUS_INVALIDA');
  }
}
```

#### 2.5 Use Case — `application/use-cases/{acao}{entidade}.use-case.ts`

```typescript
// src/auditorias/application/use-cases/abrir-auditoria.use-case.ts
import { Injectable } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { IAuditoriaRepository } from '../../domain/repositories/iauditoria.repository';
import { Auditoria } from '../../domain/entities/auditoria.entity';
import { AuditoriaNaoEncontradaError } from '../../domain/errors/auditoria-nao-encontrada.error';
import { PlanoRepository } from '../../../planos/domain/repositories/iplano.repository';

export interface AbrirAuditoriaInput {
  itemPlanoId: string;
  tipo?: 'CONFORMIDADE' | 'DESEMPENHO' | 'ESPECIAL';
  auditorLiderId: string;
  equipeIds: string[];
}

export interface AbrirAuditoriaOutput {
  auditoria: Auditoria;
}

@Injectable()
export class AbrirAuditoriaUseCase {
  constructor(
    private readonly auditoriaRepo: IAuditoriaRepository,
    private readonly planoRepo: PlanoRepository,
    private readonly eventEmitter: EventEmitter2,
  ) {}

  async execute(input: AbrirAuditoriaInput): Promise<AbrirAuditoriaOutput> {
    // 1. Validações de negócio (regras que antes estavam no service)
    const itemPlano = await this.planoRepo.findItemById(input.itemPlanoId);
    if (!itemPlano) {
      throw new AuditoriaNaoEncontradaError(`Item do plano ${input.itemPlanoId} não encontrado`);
    }
    if (!['APROVADO', 'PUBLICADO'].includes(itemPlano.plano.status)) {
      throw new Error('Item do plano deve pertencer a um plano aprovado ou publicado');
    }

    // 2. Cria entidade (factory method valida invariantes)
    const result = Auditoria.criar({
      itemPlanoId: input.itemPlanoId,
      tipo: input.tipo || 'CONFORMIDADE',
      auditorLiderId: input.auditorLiderId,
      equipeIds: input.equipeIds,
      unidadeAuditadaId: itemPlano.unidadeId,
      objetivo: itemPlano.objetivo,
    });

    if (result.isErr()) {
      throw result.error;
    }

    const auditoria = result.value;
    
    // 3. Define numero sequencial (do repository)
    auditoria.props.numero = await this.auditoriaRepo.nextNumero();

    // 4. Persiste
    const saved = await this.auditoriaRepo.save(auditoria);

    // 5. Emite domain events
    for (const event of saved.domainEvents) {
      this.eventEmitter.emit(event.constructor.eventName, event);
    }
    saved.clearDomainEvents();

    return { auditoria: saved };
  }
}
```

### 3. Atualize o PRP com o Modelo Gerado

Após gerar os arquivos, atualize `docs/prps/PRP-{NNN}.md`:

- **§7 Data Model:** Confirme/atualize com as entidades, VOs, events gerados
- **§8 Business Rules:** Liste as regras implementadas nas entidades/use cases
- **§9 Use Cases:** Liste os use cases gerados com input/output
- **§10 Architecture Compliance:** Checklist:
  - [ ] Entity em `domain/entities/` sem imports de framework
  - [ ] VOs em `domain/value-objects/` imutáveis com validação
  - [ ] Domain Events em `domain/events/` extendendo `DomainEvent`
  - [ ] Domain Errors em `domain/errors/` extendendo `DomainError`
  - [ ] Use Cases em `application/use-cases/` injetando apenas interfaces + EventEmitter2
  - [ ] Repository Interface já existe (Step 8b)
  - [ ] Mapper já existe (Step 8b)

### 4. Greenfield vs Brownfield

| Cenário | Ação |
|---------|------|
| **Greenfield** (PRP novo) | Gere modelo completo conforme template |
| **Brownfield** (PRP-A amendment) | - Leia código existente primeiro<br>- Estenda/adapte entidades existentes<br>- Adicione novos VOs, Events, Errors conforme necessário<br>- Crie novos Use Cases para nova funcionalidade<br>- Marque código legacy com `// LEGACY` |

---

## ⚠️ REGRAS CRÍTICAS

1. **Entity = Comportamento + Estado** — não anêmica. Regras de negócio DENTRO da entity.
2. **Value Object = Imutável + Validação no construtor** — equality por valor.
3. **Domain Event = Fato ocorrido** — imutável, passado, com `occurredAt`, `aggregateId`.
4. **Domain Error = Tipado** — extend `DomainError`, código de erro único.
5. **Use Case = Single Responsibility** — uma operação de negócio. Injetam: repositórios (interfaces) + EventEmitter2.
6. **Result<T, Error> pattern** — entidades/use cases retornam `Result`, never throw para regras de negócio.
6. **Naming Conventions Obrigatórias:**
   - Entity: `{Nome}.entity.ts`, classe `{Nome}`
   - VO: `{nome}.vo.ts`, classe `{Nome}VO` ou `{Nome}`
   - Event: `{entidade}-{acao}.event.ts`, classe `{Entidade}{Acao}Event`
   - Error: `{entidade}-{erro}.error.ts`, classe `{Entidade}{Erro}Error`
   - Use Case: `{acao}{Entidade}.use-case.ts`, classe `{Acao}{Entidade}UseCase`
7. **Shared Kernel:** Use `shared/result`, `shared/value-object`, `shared/domain/domain-event`, `shared/errors/domain-error` — não reimplemente.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os artefatos, **PARE** e apresente:

1. **PRP Processado:** ID e nome do PRP
2. **Tipo de PRP:** Core / Supporting / Generic
3. **Arquivos Gerados:** Lista completa por camada:
   - `domain/entities/*.entity.ts`
   - `domain/value-objects/*.vo.ts`
   - `domain/events/*.event.ts`
   - `domain/errors/*.error.ts`
   - `application/use-cases/*.use-case.ts`
4. **PRP Atualizado:** Confirmação de que §7, §8, §9, §10 do PRP foram atualizados
5. **Verificação Fitness:** `python .ace/scripts/fitness-functions.py --check domain-layer --prp PRP-{NNN}` (deve passar)
6. **Próximos Passos:** "Domain model gerado. Próximo: Step 11 (Execution) — implementar Use Cases com TDD usando este modelo."

**NÃO prossiga para o Step 11. Aguarde validação humana (Gate 11-pre).**