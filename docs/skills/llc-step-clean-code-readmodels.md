---
name: llc-step-clean-code-readmodels
description: Pipeline LLC — Clean Code: Read Models & Type Safety. Exige ReadModel types em todos os repositórios, elimina `any`, proíbe `as any`, garante tipagem TypeScript rigorosa. Integra com fitness functions.
version: 1.0.0
tags: [clean-code, readmodel, typescript, type-safety, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Read Models & Type Safety

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 5a, 8b, 11a, 11b  
**Referência:** *Clean Architecture* (R. Martin) — Boundary Interfaces, *TypeScript Best Practices*  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-readmodels` ou "Execute a skill llc-step-clean-code-readmodels".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-readmodels --task "Aplicar Read Models e tipagem rigorosa"`.

---

## 🎯 OBJETIVO

Garantir **tipagem TypeScript rigorosa** na camada de dados:
- **ReadModel por repositório** — tipos de retorno explícitos, não `any`
- **Zero `any`** em interfaces públicas
- **Zero `as any`** — casting explícito só quando inevitável (com comentário)
- **Mappers Prisma → Domain** — conversão tipada
- **DTOs tipados** — request/response com tipos claros

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. ReadModel Interface por Repositório

```typescript
// domain/repositories/auditoria.repository.ts
export interface AuditoriaReadModel {
    id: string;
    numero: string;
    tipo: TipoAuditoria;
    status: StatusAuditoria;
    unidadeAuditada: string;
    objetivo: string;
    dataInicio: Date;
    dataFimPrevista: Date | null;
    responsavelId: string;
    itemPlanoId: string;
    createdAt: Date;
    updatedAt: Date;
}

// Para listagens (campos reduzidos)
export interface AuditoriaListItemReadModel {
    id: string;
    numero: string;
    tipo: TipoAuditoria;
    status: StatusAuditoria;
    unidadeAuditada: string;
    dataInicio: Date;
}
```

### 2. Repository Interface Retorna ReadModel

```typescript
// domain/repositories/auditoria.repository.ts
export interface IAuditoriaRepository {
    count(): Promise<number>;
    create(entity: Auditoria): Promise<AuditoriaReadModel>;
    findMany(filter: AuditoriaFilter): Promise<AuditoriaListItemReadModel[]>;
    findUnique(id: string): Promise<AuditoriaReadModel | null>;
    update(id: string, data: Partial<AuditoriaReadModel>): Promise<AuditoriaReadModel>;
    delete(id: string): Promise<void>;
}
```

### 3. Mapper Prisma → ReadModel (na Implementação)

```typescript
// infrastructure/repositories/prisma-auditoria.repository.ts
@Injectable()
export class PrismaAuditoriaRepository implements IAuditoriaRepository {
    constructor(private readonly prisma: PrismaService) {}

    private toReadModel(auditoria: Prisma.AuditoriaGetPayload<{}>): AuditoriaReadModel {
        return {
            id: auditoria.id,
            numero: auditoria.numero,
            tipo: auditoria.tipo,
            status: auditoria.status,
            unidadeAuditada: auditoria.unidadeAuditada,
            objetivo: auditoria.objetivo,
            dataInicio: auditoria.dataInicio,
            dataFimPrevista: auditoria.dataFimPrevista,
            responsavelId: auditoria.responsavelId,
            itemPlanoId: auditoria.itemPlanoId,
            createdAt: auditoria.createdAt,
            updatedAt: auditoria.updatedAt,
        };
    }

    private toListItem(auditoria: Prisma.AuditoriaGetPayload<{}>): AuditoriaListItemReadModel {
        return {
            id: auditoria.id,
            numero: auditoria.numero,
            tipo: auditoria.tipo,
            status: auditoria.status,
            unidadeAuditada: auditoria.unidadeAuditada,
            dataInicio: auditoria.dataInicio,
        };
    }

    async findMany(filter: AuditoriaFilter): Promise<AuditoriaListItemReadModel[]> {
        const resultados = await this.prisma.auditoria.findMany({
            where: this.buildWhere(filter),
            orderBy: { createdAt: 'desc' },
        });
        return resultados.map(this.toListItem);
    }
    // ... demais métodos
}
```

### 4. Zero `any` em Interfaces Públicas

```typescript
// ❌ RUIM: any em interface pública
interface IAuditoriaRepository {
    findMany(filter: any): Promise<any[]>;
    findUnique(id: string): Promise<any>;
}

// ✅ BOM: tipos explícitos
interface IAuditoriaRepository {
    findMany(filter: AuditoriaFilter): Promise<AuditoriaListItemReadModel[]>;
    findUnique(id: string): Promise<AuditoriaReadModel | null>;
}
```

### 5. Zero `as any` — Casting Explícito Só Com Justificativa

```typescript
// ❌ RUIM: as any sem explicação
return this.generateTokens(usuario as any);

// ✅ ACEITÁVEL: casting com comentário explicando POR QUE
// Legacy: usuario vem de Prisma com campos extras, generateTokens espera UserEntity
// TODO: refatorar generateTokens para aceitar Prisma.User ou criar mapper
const userEntity: UserEntity = {
    id: usuario.id,
    email: usuario.email,
    // ... mapeamento explícito
};
return this.generateTokens(userEntity);

// ✅ MELHOR: mapper dedicado
const userEntity = toUserEntity(usuario);
return this.generateTokens(userEntity);
```

### 6. DTOs Tipados (Request/Response)

```typescript
// application/dto/criar-auditoria.dto.ts
export interface CriarAuditoriaInputDto {
    itemPlanoId: string;
    tipo?: TipoAuditoria;
    unidadeAuditada: string;
    objetivo: string;
    escopo?: string;
    dataFimPrevista?: Date;
}

export interface CriarAuditoriaOutputDto {
    auditoria: AuditoriaReadModel;
    comunicadoId: string;
}

// Controller usa tipos explícitos
@Post()
async create(
    @Body() dto: CriarAuditoriaInputDto,
    @CurrentUser() usuario: UserEntity,
): Promise<CriarAuditoriaOutputDto> {
    const resultado = await this.useCase.execute({ dto, usuarioId: usuario.id });
    return { auditoria: resultado.auditoria, comunicadoId: resultado.comunicadoId };
}
```

### 7. Type Guards para Narrowing

```typescript
// ✅ BOM: type guards para discriminar uniones
type AuditoriaStatus = 'ABERTA' | 'EM_EXECUCAO' | 'CONCLUIDA' | 'SUSPENSA';

function isStatusValido(status: string): status is AuditoriaStatus {
    return ['ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'SUSPENSA'].includes(status);
}

// Uso:
if (!isStatusValido(dto.status)) {
    throw new BadRequestException(`Status inválido: ${dto.status}`);
}
// TypeScript sabe que dto.status é AuditoriaStatus aqui
```

### 8. Constantes como `const` Assertions

```typescript
// ✅ BOM: readonly tuples para enums implícitos
export const STATUS_AUDITORIA = ['ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'SUSPENSA'] as const;
export type StatusAuditoria = typeof STATUS_AUDITORIA[number];

export const TIPOS_AUDITORIA = ['CONFORMIDADE', 'DESEMPENHO', 'ESPECIAL'] as const;
export type TipoAuditoria = typeof TIPOS_AUDITORIA[number];
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `readmodel-exists` | Todo repositório tem `*ReadModel` interface | 100% | block (core) / warn (non-core) |
| `repo-returns-readmodel` | Métodos de repo retornam ReadModel, não `any` | 100% | block |
| `no-any-in-public` | Zero `any` em interfaces públicas (repo, use case, dto) | 0 | block |
| `no-as-any` | Zero `as any` sem comentário de justificativa | 0 | block (core) / warn (non-core) |
| `mapper-exists` | Repositório Prisma tem métodos `toReadModel`/`toListItem` | 1 por repo | warn |
| `dto-typed` | DTOs de input/output têm interfaces explícitas | 100% | block |
| `const-assertions` | Enums/constantes usam `as const` | 100% | warn |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

- [ ] Todo repositório tem `ReadModel` interface?
- [ ] Métodos de repo retornam ReadModel tipado?
- [ ] Zero `any` em interfaces públicas?
- [ ] Zero `as any` injustificado?
- [ ] Mappers Prisma → ReadModel implementados?
- [ ] DTOs tipados com interfaces explícitas?
- [ ] Enums usam `as const`?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-readmodels --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | ReadModels criados junto com entidades. Mappers obrigatórios. |
| **Brownfield** | Prioridade: módulos mais usados (auth, usuarios, auditorias, achados, planos). Legacy: `any` tolerado temporariamente com `// LEGACY` + issue de migração. |

---

## 📤 SAÍDA ESPERADA

1. **ReadModels criados** para todos os repositórios (core primeiro)
2. **Mappers implementados** em `Prisma*Repository`
3. **DTOs tipados** em `application/dto/`
4. **`as any` removidos** ou justificados
5. **Fitness functions** atualizadas
6. **Aguardar Gate humano**