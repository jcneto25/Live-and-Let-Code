---
name: llc-step-clean-code-classes
description: Pipeline LLC — Clean Code: Classes (Cap. 10 Clean Code). Regras para SRP, ≤5 dependências, ≤100 linhas, DIP, coesão alta, acoplamento baixo. Integra com fitness functions.
version: 1.0.0
tags: [clean-code, classes, solid, srp, dip, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Classes

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 5a, 8b, 11a, 11b  
**Referência:** *Clean Code* (R. Martin) — Capítulo 10, *Clean Architecture* — Dependency Rule  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-classes` ou "Execute a skill llc-step-clean-code-classes".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-classes --task "Aplicar regras de Clean Code para classes"`.

---

## 🎯 OBJETIVO

Garantir que **todas as classes** sigam princípios de Clean Code e SOLID:
- **SRP (Single Responsibility)** — uma razão para mudar
- **≤ 5 dependências injetadas** no constructor
- **≤ 100 linhas** por classe (excluindo imports, decorators, linhas em branco)
- **DIP (Dependency Inversion)** — dependem de abstrações, não concreções
- **Coesão alta** — métodos usam campos da classe
- **Acoplamento baixo** — não conhecem detalhes de implementação

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Single Responsibility Principle (SRP)

Uma classe deve ter **UMA** razão para mudar.

```typescript
// ❌ RUIM: AuditoriasService faz 5 coisas diferentes
@Injectable()
export class AuditoriasService {
    constructor(
        private readonly auditoriaRepo: PrismaService,
        private readonly evidenciasRepo: PrismaService,
        private readonly papeisRepo: PrismaService,
        private readonly requisicoesRepo: PrismaService,
        private readonly comunicadosRepo: PrismaService,
        private readonly eventEmitter: EventEmitter2,
    ) {}
    
    // 15+ métodos: CRUD auditoria + evidencias + papeis + requisicoes + comunicados
}

// ✅ BOM: Responsabilidades separadas
@Injectable()
export class AuditoriasService {
    constructor(
        private readonly auditoriaRepo: IAuditoriaRepository,
        private readonly eventEmitter: EventEmitter2,
    ) {}
    // Só métodos core do agregado: create, findAll, findOne, iniciar, concluir, suspender
}

@Injectable()
export class EvidenciasService {
    constructor(private readonly evidenciasRepo: IEvidenciaRepository) {}
    // Só evidencias
}

@Injectable()
export class PapeisTrabalhoService {
    constructor(private readonly papeisRepo: IPapelTrabalhoRepository) {}
    // Só papéis de trabalho
}
```

### 2. Máximo 5 Dependências no Constructor

```typescript
// ❌ RUIM: 6 dependências = viola SRP
constructor(
    private readonly repo1: Repo1,
    private readonly repo2: Repo2,
    private readonly repo3: Repo3,
    private readonly repo4: Repo4,
    private readonly repo5: Repo5,
    private readonly eventEmitter: EventEmitter2,
) {}

// ✅ BOM: ≤ 5, idealmente 1-3
constructor(
    private readonly auditoriaRepo: IAuditoriaRepository,
    private readonly eventEmitter: EventEmitter2,
) {}

// Se precisa de mais: extrair para outro service/use case
```

### 3. Máximo 100 Linhas por Classe

```typescript
// Contagem: linhas de código efetivo (exclui imports, decorators, blank lines, closing braces)

// ❌ RUIM: 171 linhas
@Injectable()
export class AuditoriasService { ... }

// ✅ BOM: ~70 linhas
@Injectable()
export class AuditoriasService { ... }
```

### 4. Dependency Inversion Principle (DIP)

**Dependam de abstrações, não de concreções.**

```typescript
// ❌ RUIM: Injeta concreção (PrismaService)
@Injectable()
export class AuditoriasService {
    constructor(private readonly prisma: PrismaService) {}
    async create(...) { return this.prisma.auditoria.create(...); }
}

// ✅ BOM: Injeta interface (Port)
@Injectable()
export class AuditoriasService {
    constructor(private readonly repo: IAuditoriaRepository) {}
    async create(...) { return this.repo.create(...); }
}

// Binding no Module:
@Module({
    providers: [
        AuditoriasService,
        { provide: IAuditoriaRepository, useClass: PrismaAuditoriaRepository },
    ],
})
export class AuditoriasModule {}
```

### 5. Coesão Alta

Métodos da classe devem usar os campos (dependências) da classe.

```typescript
// ❌ RUIM: Baixa coesão — método não usa this.repo
@Injectable()
export class AuditoriasService {
    constructor(private readonly auditoriaRepo: IAuditoriaRepository) {}
    
    async calcularEstatisticasGlobais(): Promise<Stats> {
        // Não usa this.auditoriaRepo! Deveria estar em outro service
        return this.externalApi.getStats();
    }
}

// ✅ BOM: Alta coesão — todos métodos usam this.repo
@Injectable()
export class AuditoriasService {
    constructor(private readonly auditoriaRepo: IAuditoriaRepository) {}
    
    async create(...) { return this.auditoriaRepo.create(...); }
    async findAll(...) { return this.auditoriaRepo.findMany(...); }
    async findOne(id) { return this.auditoriaRepo.findUnique(id); }
    async iniciarExecucao(id) { return this.auditoriaRepo.update(id, { status: 'EM_EXECUCAO' }); }
}
```

### 6. Entidades de Domínio: Comportamento, Não Anêmicas

```typescript
// ❌ RUIM: Anêmica — só dados, lógica no service
export class Auditoria {
    id: string;
    status: StatusAuditoria;
    // ...
}

// ✅ BOA: Rica — encapsula regras de negócio
export class Auditoria {
    constructor(
        public readonly id: string,
        public readonly numero: string,
        public status: StatusAuditoria,
        // ...
    ) {}
    
    iniciarExecucao(): Result<Auditoria, TransicaoInvalidaError> {
        if (this.status !== 'ABERTA')
            return err(new TransicaoInvalidaError('ABERTA', 'EM_EXECUCAO'));
        this.status = 'EM_EXECUCAO';
        return ok(this);
    }
    
    concluir(): Result<Auditoria, TransicaoInvalidaError> {
        if (this.status !== 'EM_EXECUCAO')
            return err(new TransicaoInvalidaError('EM_EXECUCAO', 'CONCLUIDA'));
        this.status = 'CONCLUIDA';
        return ok(this);
    }
}
```

### 7. Use Cases: Uma Classe por Operação

```typescript
// ✅ BOM: SRP no nível de Use Case
@Injectable()
export class AbrirAuditoriaUseCase {
    constructor(
        private readonly auditoriaRepo: IAuditoriaRepository,
        private readonly eventEmitter: EventEmitter2,
    ) {}
    
    async execute(dto: CriarAuditoriaDto, context: ExecutionContext): Promise<Auditoria> { ... }
}

@Injectable()
export class IniciarAuditoriaUseCase {
    constructor(private readonly auditoriaRepo: IAuditoriaRepository) {}
    async execute(id: string, context: ExecutionContext): Promise<Auditoria> { ... }
}

@Injectable()
export class ConcluirAuditoriaUseCase { ... }
@Injectable()
export class SuspenderAuditoriaUseCase { ... }
@Injectable()
export class ListarAuditoriasUseCase { ... }
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `class-max-lines` | Classes não excedem 100 linhas efetivas | 100 | block (core) / warn (non-core) |
| `class-max-deps` | Constructor tem ≤ 5 dependências injetadas | 5 | block (core) / warn (non-core) |
| `class-srp` | Heurística: métodos usam campos da classe (coesão) | ≥ 80% | warn |
| `dip-violation` | Detecta injeção de `PrismaService`, `@prisma/client` em services/use-cases | regex | block (core) / warn (non-core) |
| `anemic-domain` | Entidades sem métodos de negócio (só propriedades) | 0 métodos | warn |
| `use-case-per-operation` | Módulos core têm Use Cases separados por operação | - | block (core) |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

- [ ] Cada classe tem responsabilidade única clara?
- [ ] ≤ 5 dependências no constructor?
- [ ] ≤ 100 linhas efetivas por classe?
- [ ] Zero injeção de `PrismaService` em services/use cases?
- [ ] Todas as dependências são interfaces (Ports)?
- [ ] Entidades de domínio têm métodos de negócio (não anêmicas)?
- [ ] Use Cases separados por operação (não CRUD service monolítico)?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-classes --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todo código novo**. Estrutura de pastas já prevê domain/application/infrastructure |
| **Brownfield** | Aplicar a **novos módulos** e **módulos alterados** (PRP-A). Legacy marcado `// LEGACY` — criar interfaces progressivamente. Use `AuditoriasService` como facade temporária se necessário. |

---

## 📤 SAÍDA ESPERADA

1. **Relatório de violações** por classe: arquivo, linhas, deps, coesão, anêmica?
2. **Plano de refatoração** sugerido (extrair services, criar use cases, interfaces)
3. **Fitness functions** atualizadas no `.ace/arch-config.yaml`
4. **Aguardar Gate humano** antes de prosseguir