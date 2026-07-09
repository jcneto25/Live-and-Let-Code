---
name: llc-step-8b-repository-pattern
description: Pipeline LLC Step 8b — Gera estrutura Repository Pattern em todos os módulos: interfaces em domain/repositories/, implementações Prisma em infrastructure/repositories/, bindings DI nos modules. Estende Step 8 (setup + mocks) com Ports & Adapters.
version: 1.0.0
tags: [repository-pattern, ports-adapters, dependency-injection, setup, llc-pipeline]
---

# LLC Skill: Step 8b — Repository Pattern Setup

**Pipeline:** Live and Let Code (LLC)  
**Fase:** MVP / Fundação (sub-step of Step 8)  
**Depende de:** Step 5a (Architecture Patterns), Step 8 (Setup + Mock Data)  
**Executa antes de:** Step 11 (Execution)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-8b` ou "Execute a skill llc-step-8b".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 8b --task "Gerar Repository Pattern em todos os módulos"`.

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — com §7 (Domain Layer) e §9 (Fitness Functions) preenchidos (Step 5a)
- [ ] `.ace/arch-config.yaml` — módulos core e regras definidas (Step 5a)
- [ ] `docs/planning/TASKS.md` — tarefas de setup por módulo (Step 6)
- [ ] `docs/prps/PRP-*.md` — PRPs da Wave 1 para identificar aggregate roots
- [ ] `docs/business/specs/glossario.md` — nomes oficiais das entidades
- [ ] Projeto já inicializado com stack definido (Step 8.1–8.2 concluído)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 8b** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-8b.md`:
     ```markdown
     # Skip Note: Step 8b — Repository Pattern
     **Decisão:** Step pulado — Repository Pattern já implementado nos módulos existentes.
     **Gate:** ✅ Auto-aprovado (reaproveitando aprovação anterior de {data})
     ```
   - **PARE** e informe: "Step 8b pulado via Smart Skip. Repositories existentes reaproveitados."
3. Se **Step 8b** estiver listado como "executar": gere repositories apenas para **novos módulos** ou **módulos alterados** identificados no DELTA_REPORT.md §3.
4. Se DELTA_REPORT.md não existir: prossiga normalmente (todos os módulos).

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-8b-repository-pattern` do pipeline LLC. Seu objetivo é **implementar o Repository Pattern com interfaces (Ports & Adapters) em todos os módulos do projeto**, seguindo os padrões definidos no Step 5a.

### 1. Leia as Entradas e Identifique Aggregate Roots

Leia:
- `docs/architecture/ARCHITECTURE.md` §7 — estrutura de pastas, naming conventions
- `.ace/arch-config.yaml` — módulos core, regras de enforcement
- `docs/prps/PRP-*.md` — identifique aggregate roots por PRP
- `docs/business/specs/glossario.md` — nomes canônicos das entidades

**Para cada módulo listado em `ARCHITECTURE.md` ou identificado nos PRPs da Wave 1:**

1. Identifique o(s) **Aggregate Root(s)** do módulo
   - Ex.: `Auditoria` (auditorias), `Achado` (achados), `Plano` (planos), `Usuario` (usuarios)
2. Para módulos com múltiplas entidades relacionadas, defina **um repository por aggregate root**
   - Ex.: `IAuditoriaRepository`, `IAchadoRepository` (mesmo módulo `auditorias`)

### 2. Gere a Estrutura Repository Pattern por Módulo

Para **cada módulo** identificado, crie a seguinte estrutura:

```
src/{modulo}/
├── domain/
│   └── repositories/
│       ├── i{entidade}.repository.ts          # Interface (Port)
│       └── index.ts                           # Export barrel
├── infrastructure/
│   └── repositories/
│       ├── prisma-{entidade}.repository.ts    # Implementação concreta (Adapter)
│       └── index.ts                           # Export barrel
├── {modulo}.module.ts                         # ATUALIZAR: bindings DI
└── {modulo}.service.ts                        # ATUALIZAR: injetar interface
```

#### 2.1 Interface do Repository (Port) — `domain/repositories/i{entidade}.repository.ts`

```typescript
// src/auditorias/domain/repositories/iauditoria.repository.ts
import { AuditoriaFilter, AuditoriaPagination } from '../dto/auditoria-filters.dto';

export interface IAuditoriaRepository {
  // Commands
  save(auditoria: Auditoria): Promise<Auditoria>;
  delete(id: string): Promise<void>;
  
  // Queries
  findById(id: string): Promise<Auditoria | null>;
  findMany(filter: AuditoriaFilter, pagination?: AuditoriaPagination): Promise<Auditoria[]>;
  count(filter: AuditoriaFilter): Promise<number>;
  
  // Domain-specific
  findByNumero(numero: string): Promise<Auditoria | null>;
  findByUnidade(unidadeId: string): Promise<Auditoria[]>;
  nextNumero(): Promise<string>;
  
  // Para Use Cases que precisam de transação
  withTransaction<T>(fn: (repo: IAuditoriaRepository) => Promise<T>): Promise<T>;
}
```

**Regras:**
- Interface **NÃO** importa `PrismaService`, `@prisma/client`, decorators NestJS
- Métodos retornam **entidades de domínio** (não Prisma models)
- Filtros e paginação via DTOs tipados (em `domain/dto/`)
- Inclua `withTransaction` para suporte a transações multi-repository

#### 2.2 Implementação Prisma (Adapter) — `infrastructure/repositories/prisma-{entidade}.repository.ts`

```typescript
// src/auditorias/infrastructure/repositories/prisma-auditoria.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { IAuditoriaRepository } from '../../domain/repositories/iauditoria.repository';
import { Auditoria } from '../../domain/entities/auditoria.entity';
import { AuditoriaFilter, AuditoriaPagination } from '../../domain/dto/auditoria-filters.dto';
import { AuditoriaMapper } from '../mappers/auditoria.mapper';

@Injectable()
export class PrismaAuditoriaRepository implements IAuditoriaRepository {
  constructor(private readonly prisma: PrismaService) {}

  async save(auditoria: Auditoria): Promise<Auditoria> {
    const data = AuditoriaMapper.toPersistence(auditoria);
    const saved = await this.prisma.auditoria.upsert({
      where: { id: auditoria.id },
      create: data,
      update: data,
    });
    return AuditoriaMapper.toDomain(saved);
  }

  async delete(id: string): Promise<void> {
    await this.prisma.auditoria.delete({ where: { id } });
  }

  async findById(id: string): Promise<Auditoria | null> {
    const found = await this.prisma.auditoria.findUnique({ where: { id } });
    return found ? AuditoriaMapper.toDomain(found) : null;
  }

  async findMany(filter: AuditoriaFilter, pagination?: AuditoriaPagination): Promise<Auditoria[]> {
    const where = this.buildWhere(filter);
    const found = await this.prisma.auditoria.findMany({
      where,
      skip: pagination?.skip,
      take: pagination?.take,
      orderBy: { createdAt: 'desc' },
    });
    return found.map(AuditoriaMapper.toDomain);
  }

  async count(filter: AuditoriaFilter): Promise<number> {
    return this.prisma.auditoria.count({ where: this.buildWhere(filter) });
  }

  async findByNumero(numero: string): Promise<Auditoria | null> {
    const found = await this.prisma.auditoria.findUnique({ where: { numero } });
    return found ? AuditoriaMapper.toDomain(found) : null;
  }

  async findByUnidade(unidadeId: string): Promise<Auditoria[]> {
    const found = await this.prisma.auditoria.findMany({ where: { unidadeAuditadaId: unidadeId } });
    return found.map(AuditoriaMapper.toDomain);
  }

  async nextNumero(): Promise<string> {
    const count = await this.prisma.auditoria.count();
    const year = new Date().getFullYear();
    return `AUD-${year}-${String(count + 1).padStart(4, '0')}`;
  }

  async withTransaction<T>(fn: (repo: IAuditoriaRepository) => Promise<T>): Promise<T> {
    return this.prisma.$transaction(async (tx) => {
      const txRepo = new PrismaAuditoriaRepository(tx as any);
      return fn(txRepo);
    });
  }

  private buildWhere(filter: AuditoriaFilter) {
    const where: any = {};
    if (filter.status) where.status = filter.status;
    if (filter.unidade) where.unidadeAuditadaId = filter.unidade;
    if (filter.search) {
      where.OR = [
        { numero: { contains: filter.search, mode: 'insensitive' } },
        { objetivo: { contains: filter.search, mode: 'insensitive' } },
      ];
    }
    return where;
  }
}
```

**Regras:**
- **SÓ** aqui importa `PrismaService` e `@prisma/client`
- Use **Mapper** para converter Prisma model ↔ Domain entity
- Implemente **todos** métodos da interface
- `withTransaction` delega para `prisma.$transaction`

#### 2.3 Mapper — `infrastructure/mappers/{entidade}.mapper.ts`

```typescript
// src/auditorias/infrastructure/mappers/auditoria.mapper.ts
import { Auditoria } from '../../domain/entities/auditoria.entity';
import { Auditoria as PrismaAuditoria, StatusAuditoria as PrismaStatus } from '@prisma/client';

export class AuditoriaMapper {
  static toDomain(prisma: PrismaAuditoria): Auditoria {
    return new Auditoria({
      id: prisma.id,
      numero: prisma.numero,
      status: prisma.status as any,
      unidadeAuditadaId: prisma.unidadeAuditadaId,
      objetivo: prisma.objetivo,
      // ... demais campos
      createdAt: prisma.createdAt,
      updatedAt: prisma.updatedAt,
    });
  }

  static toPersistence(domain: Auditoria): any {
    return {
      id: domain.id,
      numero: domain.numero,
      status: domain.status,
      unidadeAuditadaId: domain.unidadeAuditadaId,
      objetivo: domain.objetivo,
      // ... demais campos
    };
  }
}
```

#### 2.4 Atualize o Module — `{modulo}.module.ts`

```typescript
// src/auditorias/auditorias.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { AuditoriasController } from './auditorias.controller';
import { AuditoriasService } from './auditorias.service';
import { IAuditoriaRepository } from './domain/repositories/iauditoria.repository';
import { PrismaAuditoriaRepository } from './infrastructure/repositories/prisma-auditoria.repository';
import { AbrirAuditoriaUseCase } from './application/use-cases/abrir-auditoria.use-case';
// ... outros use cases

@Module({
  imports: [PrismaModule],
  controllers: [AuditoriasController],
  providers: [
    AuditoriasService,
    // Repository binding
    { provide: IAuditoriaRepository, useClass: PrismaAuditoriaRepository },
    // Use Cases
    AbrirAuditoriaUseCase,
    IniciarExecucaoUseCase,
    ConcluirAuditoriaUseCase,
    SuspenderAuditoriaUseCase,
    ListarAuditoriasUseCase,
  ],
  exports: [AuditoriasService, IAuditoriaRepository],
})
export class AuditoriasModule {}
```

#### 2.5 Atualize o Service (Legacy Compatibility) — `{modulo}.service.ts`

```typescript
// src/auditorias/auditorias.service.ts
import { Injectable } from '@nestjs/common';
import { IAuditoriaRepository } from './domain/repositories/iauditoria.repository';
import { Auditoria } from './domain/entities/auditoria.entity';

@Injectable()
export class AuditoriasService {
  constructor(
    @Inject(IAuditoriaRepository)
    private readonly auditoriaRepo: IAuditoriaRepository,
  ) {}

  // Delega para Use Cases ou mantém API legada para compatibilidade
  async findAll(): Promise<Auditoria[]> {
    return this.auditoriaRepo.findMany({});
  }
  
  async findById(id: string): Promise<Auditoria | null> {
    return this.auditoriaRepo.findById(id);
  }
  
  // ... demais métodos legados delegam para repo
}
```

### 3. Greenfield vs Brownfield

| Cenário | Ação |
|---------|------|
| **Greenfield** (projeto novo) | Gere estrutura completa para **todos** módulos identificados |
| **Brownfield** (projeto existente) | - Módulos **novos** (PRPs novos): estrutura completa<br>- Módulos **alterados** (PRP-A): adicione repository se não existe<br>- Módulos **legados** inalterados: marque com `// LEGACY` no service, crie issue de migração |

### 4. Verificação Pós-Geração

Execute os checks para confirmar conformidade:

```bash
# 1. Verificar se interfaces existem
find src -name "i*.repository.ts" -path "*/domain/repositories/*" | wc -l

# 2. Verificar se implementations existem
find src -name "prisma-*.repository.ts" -path "*/infrastructure/repositories/*" | wc -l

# 3. Verificar bindings DI nos modules
grep -r "provide: I.*Repository" src/*/module.ts

# 4. Verificar se NENHUM service/use-case injeta PrismaService diretamente
grep -r "PrismaService" src/*/application/ src/*/domain/ src/*/use-cases/ 2>/dev/null || echo "OK: Nenhum PrismaService na camada de domínio/application"

# 5. Rodar fitness function (se configurado)
python .ace/scripts/fitness-functions.py --check repository-pattern
```

---

## ⚠️ REGRAS CRÍTICAS

1. **Uma interface por Aggregate Root** — não crie repository para Value Objects ou Entities filhas
2. **Interface no Domain, Impl na Infrastructure** — separação física obrigatória
3. **Mapper obrigatório** — Prisma model ≠ Domain entity
4. **DI Binding no Module** — `provide: I{Entidade}Repository, useClass: Prisma{Entidade}Repository`
5. **Service legada injeta interface** — não `PrismaService`
6. **Naming Convention Obrigatória:**
   - Interface: `I{NomeAgregado}Repository` → arquivo `i{nome-agregado}.repository.ts`
   - Impl: `Prisma{NomeAgregado}Repository` → arquivo `prisma-{nome-agregado}.repository.ts`
   - Mapper: `{NomeAgregado}Mapper` → arquivo `{nome-agregado}.mapper.ts`
7. **Transações:** `withTransaction` na interface, implementado via `prisma.$transaction`

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os artefatos, **PARE** e apresente:

1. **Resumo por Módulo:** Tabela com módulo, aggregate roots, arquivos criados
2. **Arquivos Gerados:** Lista completa de `i*.repository.ts`, `prisma-*.repository.ts`, `*.mapper.ts`, modules atualizados
3. **Verificação Automática:** Resultado dos 5 checks acima (todos devem passar)
4. **Módulos Legacy:** Lista de módulos não migrados (com issue # para migração futura)
5. **Próximos Passos:** Confirmação para prosseguir ao Step 11 (Execution)

**NÃO prossiga para o Step 11. Aguarde validação humana (Gate 9).**