# REPOSITORY_PATTERN_TEMPLATE.md

Template para implementação do Repository Pattern com Interfaces (Ports & Adapters).
**Versão:** 1.0 | **Gerado por:** llc-step-8b-repository-pattern | **Usado em:** Step 8b

---

## Visão Geral

Este template define a estrutura obrigatória para implementar o Repository Pattern em cada módulo do projeto, seguindo a arquitetura Ports & Adapters (Hexagonal/Clean Architecture) definida no Step 5a.

**Princípio:** O domínio define **O QUÊ** (interfaces), a infraestrutura implementa **COMO** (Prisma, SQL, etc.).

---

## Estrutura de Arquivos por Módulo

```
src/{modulo}/
├── domain/
│   └── repositories/
│       ├── i{nome-agregado}.repository.ts    # Interface (Port)
│       └── index.ts                          # Barrel export
├── infrastructure/
│   ├── repositories/
│   │   ├── prisma-{nome-agregado}.repository.ts  # Implementação (Adapter)
│   │   └── index.ts                          # Barrel export
│   └── mappers/
│       └── {nome-agregado}.mapper.ts         # Prisma ↔ Domain
├── {modulo}.module.ts                        # DI Bindings
└── {modulo}.service.ts                       # Legacy compatibility (injeta interface)
```

---

## 1. Interface do Repository (Port) — `domain/repositories/i{nome-agregado}.repository.ts`

```typescript
// src/{modulo}/domain/repositories/i{nome-agregado}.repository.ts
import { {NomeAgregado}Filter, {NomeAgregado}Pagination } from '../dto/{nome-agregado}-filters.dto';
import { {NomeAgregado} } from '../entities/{nome-agregado}.entity';
import { {NomeAgregado}Id } from '../value-objects/{nome-agregado}-id.vo';

export interface I{NomeAgregado}Repository {
  // ========== Commands ==========
  
  /**
   * Salva (create ou update) uma entidade
   * @param entity Entidade de domínio a persistir
   * @returns Entidade salva com ID gerado/atualizado
   */
  save(entity: {NomeAgregado}): Promise<{NomeAgregado}>;
  
  /**
   * Remove uma entidade por ID
   * @param id ID da entidade
   */
  delete(id: string): Promise<void>;
  
  // ========== Queries ==========
  
  /**
   * Busca entidade por ID
   * @param id ID da entidade
   * @returns Entidade ou null se não encontrada
   */
  findById(id: string): Promise<{NomeAgregado} | null>;
  
  /**
   * Busca múltiplas entidades com filtros e paginação
   * @param filter Filtros de busca
   * @param pagination Paginação opcional
   * @returns Lista de entidades
   */
  findMany(filter: {NomeAgregado}Filter, pagination?: {NomeAgregado}Pagination): Promise<{NomeAgregado}[]>;
  
  /**
   * Conta entidades com filtros
   * @param filter Filtros de busca
   * @returns Total de entidades
   */
  count(filter: {NomeAgregado}Filter): Promise<number>;
  
  // ========== Domain-Specific Queries ==========
  // Adicionar conforme necessidade do domínio
  
  /**
   * Busca por campo único (ex: numero, email, cpf)
   * @param valor Valor do campo único
   * @returns Entidade ou null
   */
  findBy{CampoUnico}(valor: string): Promise<{NomeAgregado} | null>;
  
  /**
   * Gera próximo identificador sequencial (ex: numero da auditoria)
   * @returns Identificador formatado
   */
  nextIdentificador(): Promise<string>;
  
  // ========== Transaction Support ==========
  
  /**
   * Executa função dentro de transação
   * @param fn Função que recebe repository transacional
   * @returns Resultado da função
   */
  withTransaction<T>(fn: (repo: I{NomeAgregado}Repository) => Promise<T>): Promise<T>;
}
```

### DTOs de Filtro e Paginação (em `domain/dto/`)

```typescript
// src/{modulo}/domain/dto/{nome-agregado}-filters.dto.ts
export interface {NomeAgregado}Filter {
  // Filtros comuns
  search?: string;           // Busca textual genérica
  status?: string;           // Filtro por status
  unidadeId?: string;        // Escopo organizacional
  dataInicio?: Date;         // Range de data
  dataFim?: Date;
  
  // Filtros específicos do domínio
  // {campoEspecifico}?: {tipo};
}

export interface {NomeAgregado}Pagination {
  page?: number;             // Default: 1
  limit?: number;            // Default: 20, max: 100
  sort?: string;             // Campo para ordenação
  order?: 'asc' | 'desc';    // Direção
  
  // Computados
  get skip(): number {
    return ((this.page || 1) - 1) * (this.limit || 20);
  }
  get take(): number {
    return Math.min(this.limit || 20, 100);
  }
}
```

---

## 2. Implementação Prisma (Adapter) — `infrastructure/repositories/prisma-{nome-agregado}.repository.ts`

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

  // ========== Commands ==========
  
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

  // ========== Queries ==========
  
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
      orderBy: { [pagination?.sort || 'createdAt']: pagination?.order || 'desc' },
    });
    return found.map({NomeAgregado}Mapper.toDomain);
  }

  async count(filter: {NomeAgregado}Filter): Promise<number> {
    return this.prisma.{nomeAgregado}.count({ where: this.buildWhere(filter) });
  }

  // ========== Domain-Specific ==========
  
  async findBy{CampoUnico}(valor: string): Promise<{NomeAgregado} | null> {
    const found = await this.prisma.{nomeAgregado}.findUnique({ 
      where: { {campoUnico}: valor } 
    });
    return found ? {NomeAgregado}Mapper.toDomain(found) : null;
  }

  async nextIdentificador(): Promise<string> {
    const count = await this.prisma.{nomeAgregado}.count();
    const year = new Date().getFullYear();
    const prefix = '{PREFIX}'; // Ex: 'AUD', 'PLN', 'ACH'
    return `${prefix}-${year}-${String(count + 1).padStart(4, '0')}`;
  }

  // ========== Transaction Support ==========
  
  async withTransaction<T>(fn: (repo: I{NomeAgregado}Repository) => Promise<T>): Promise<T> {
    return this.prisma.$transaction(async (tx) => {
      // Cria instância do repository usando transaction client
      const txRepo = new Prisma{NomeAgregado}Repository(tx as any);
      return fn(txRepo);
    });
  }

  // ========== Private Helpers ==========
  
  private buildWhere(filter: {NomeAgregado}Filter): any {
    const where: any = {};
    
    if (filter.search) {
      where.OR = [
        { {campoBusca1}: { contains: filter.search, mode: 'insensitive' } },
        { {campoBusca2}: { contains: filter.search, mode: 'insensitive' } },
      ];
    }
    
    if (filter.status) {
      where.status = filter.status;
    }
    
    if (filter.unidadeId) {
      where.unidadeId = filter.unidadeId;
    }
    
    if (filter.dataInicio || filter.dataFim) {
      where.createdAt = {};
      if (filter.dataInicio) where.createdAt.gte = filter.dataInicio;
      if (filter.dataFim) where.createdAt.lte = filter.dataFim;
    }
    
    // Filtros específicos do domínio
    // if (filter.{campoEspecifico}) where.{campoEspecifico} = filter.{campoEspecifico};
    
    return where;
  }
}
```

---

## 3. Mapper — `infrastructure/mappers/{nome-agregado}.mapper.ts`

```typescript
// src/{modulo}/infrastructure/mappers/{nome-agregado}.mapper.ts
import { {NomeAgregado} } from '../../domain/entities/{nome-agregado}.entity';
import { {NomeAgregado}Id } from '../../domain/value-objects/{nome-agregado}-id.vo';
import { {OutroVO} } from '../../domain/value-objects/{outro-vo}.vo';
import { {NomeAgregado} as Prisma{NomeAgregado}, {EnumTipo} as Prisma{EnumTipo} } from '@prisma/client';

export class {NomeAgregado}Mapper {
  /**
   * Converte modelo Prisma → Entidade de Domínio
   * Usa Value Objects para tipagem forte
   */
  static toDomain(prisma: Prisma{NomeAgregado}): {NomeAgregado} {
    return new {NomeAgregado}({
      id: {NomeAgregado}Id.fromString(prisma.id),
      {campo1}: {OutroVO}.criar(prisma.{campo1}).value, // Se for VO
      {campo2}: prisma.{campo2}, // Se for primitivo
      // ... mapear todos os campos
      status: prisma.status as any, // Se enum compatível
      createdAt: prisma.createdAt,
      updatedAt: prisma.updatedAt,
    });
  }

  /**
   * Converte Entidade de Domínio → Dados para persistência Prisma
   * Remove Value Objects, converte para primitivos
   */
  static toPersistence(domain: {NomeAgregado}): any {
    return {
      id: domain.id.value,
      {campo1}: domain.{campo1}?.value ?? domain.{campo1}, // VO ou primitivo
      {campo2}: domain.{campo2},
      // ... mapear todos os campos
      status: domain.status,
      // Não incluir createdAt/updatedAt no update (Prisma gerencia via @updatedAt)
    };
  }
  
  /**
   * Converte lista Prisma → lista Domain
   */
  static toDomainList(prismaList: Prisma{NomeAgregado}[]): {NomeAgregado}[] {
    return prismaList.map(this.toDomain);
  }
}
```

---

## 4. Module Bindings — `{modulo}.module.ts`

```typescript
// src/{modulo}/{modulo}.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { {Modulo}Controller } from './{modulo}.controller';
import { {Modulo}Service } from './{modulo}.service';
import { I{NomeAgregado}Repository } from './domain/repositories/i{nome-agregado}.repository';
import { Prisma{NomeAgregado}Repository } from './infrastructure/repositories/prisma-{nome-agregado}.repository';

// Use Cases (se módulo core)
import { {Acao}{NomeAgregado}UseCase } from './application/use-cases/{acao}{nome-agregado}.use-case';
// ... importar todos os use cases do módulo

@Module({
  imports: [PrismaModule],
  controllers: [{Modulo}Controller],
  providers: [
    // Service (legacy compatibility)
    {Modulo}Service,
    
    // ========== Repository Binding (OBRIGATÓRIO) ==========
    {
      provide: I{NomeAgregado}Repository,
      useClass: Prisma{NomeAgregado}Repository,
    },
    
    // ========== Use Cases (para módulos core) ==========
    {Acao}{NomeAgregado}UseCase,
    // {OutraAcao}{NomeAgregado}UseCase,
    // ...
  ],
  exports: [
    {Modulo}Service,
    I{NomeAgregado}Repository, // Exportar para outros módulos usarem (se necessário)
    // Use Cases não precisam ser exportados (injetados via módulo)
  ],
})
export class {Modulo}Module {}
```

---

## 5. Service Legado (Compatibilidade) — `{modulo}.service.ts`

```typescript
// src/{modulo}/{modulo}.service.ts
import { Injectable, Inject } from '@nestjs/common';
import { I{NomeAgregado}Repository } from './domain/repositories/i{nome-agregado}.repository';
import { {NomeAgregado} } from './domain/entities/{nome-agregado}.entity';
import { {NomeAgregado}Filter, {NomeAgregado}Pagination } from './domain/dto/{nome-agregado}-filters.dto';

@Injectable()
export class {Modulo}Service {
  constructor(
    @Inject(I{NomeAgregado}Repository)
    private readonly {nomeAgregado}Repo: I{NomeAgregado}Repository,
  ) {}

  // ========== Delega para Repository (API legada) ==========
  
  async findAll(filter?: {NomeAgregado}Filter, pagination?: {NomeAgregado}Pagination): Promise<{NomeAgregado}[]> {
    return this.{nomeAgregado}Repo.findMany(filter || {}, pagination);
  }
  
  async findById(id: string): Promise<{NomeAgregado} | null> {
    return this.{nomeAgregado}Repo.findById(id);
  }
  
  async create(data: any): Promise<{NomeAgregado}> {
    // Para criação, Use Cases são preferidos
    // Este método mantém compatibilidade com código legado
    throw new Error('Use {Acao}{NomeAgregado}UseCase para criar entidades');
  }
  
  async update(id: string, data: any): Promise<{NomeAgregado}> {
    throw new Error('Use {Acao}{NomeAgregado}UseCase para atualizar entidades');
  }
  
  async delete(id: string): Promise<void> {
    return this.{nomeAgregado}Repo.delete(id);
  }
  
  // Métodos específicos legados (delegam para repo)
  async findBy{CampoUnico}(valor: string): Promise<{NomeAgregado} | null> {
    return this.{nomeAgregado}Repo.findBy{CampoUnico}(valor);
  }
}
```

---

## 6. Controller (Presentation) — `{modulo}.controller.ts`

```typescript
// src/{modulo}/{modulo}.controller.ts
import { Controller, Get, Post, Put, Delete, Param, Query, Body, ParseUUIDPipe } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { {Modulo}Service } from './{modulo}.service';
import { {Acao}{NomeAgregado}UseCase } from './application/use-cases/{acao}{nome-agregado}.use-case';
import { {NomeAgregado}Filter, {NomeAgregado}Pagination } from './domain/dto/{nome-agregado}-filters.dto';
import { Create{NomeAgregado}Dto, Update{NomeAgregado}Dto } from './dto/{nome-agregado}.dto';

@ApiTags('{Modulo}')
@Controller('{modulo}')
export class {Modulo}Controller {
  constructor(
    private readonly {modulo}Service: {Modulo}Service,
    // Injetar Use Cases diretamente (preferido para novas features)
    private readonly {acao}{NomeAgregado}UseCase: {Acao}{NomeAgregado}UseCase,
  ) {}

  @Get()
  @ApiOperation({ summary: 'Listar {modulo}s' })
  async findAll(
    @Query() filter: {NomeAgregado}Filter,
    @Query() pagination: {NomeAgregado}Pagination,
  ) {
    return this.{modulo}Service.findAll(filter, pagination);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Buscar {modulo} por ID' })
  async findById(@Param('id', ParseUUIDPipe) id: string) {
    return this.{modulo}Service.findById(id);
  }

  @Post()
  @ApiOperation({ summary: 'Criar {modulo}' })
  async create(@Body() dto: Create{NomeAgregado}Dto) {
    // Delega para Use Case (nova arquitetura)
    const result = await this.{acao}{NomeAgregado}UseCase.execute({
      // mapear dto para input do use case
    });
    return result.{nomeAgregado};
  }

  @Put(':id')
  @ApiOperation({ summary: 'Atualizar {modulo}' })
  async update(@Param('id', ParseUUIDPipe) id: string, @Body() dto: Update{NomeAgregado}Dto) {
    // Delega para Use Case
    throw new Error('Implementar via Use Case');
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Remover {modulo}' })
  async delete(@Param('id', ParseUUIDPipe) id: string) {
    return this.{modulo}Service.delete(id);
  }
}
```

---

## 7. Checklist de Validação por Módulo (Gate 9)

Para cada módulo, confirme:

- [ ] **Interface:** `src/{modulo}/domain/repositories/i{nome-agregado}.repository.ts` existe
- [ ] **Implementação:** `src/{modulo}/infrastructure/repositories/prisma-{nome-agregado}.repository.ts` existe
- [ ] **Mapper:** `src/{modulo}/infrastructure/mappers/{nome-agregado}.mapper.ts` existe
- [ ] **Module Binding:** `{provide: I{NomeAgregado}Repository, useClass: Prisma{NomeAgregado}Repository}` no module
- [ ] **Service injeta Interface:** `@Inject(I{NomeAgregado}Repository)` no service
- [ ] **Controller usa Use Cases:** Novas operações delegam para Use Cases
- [ ] **Zero PrismaService em Domain/Application:** `grep -r "PrismaService" src/{modulo}/domain/ src/{modulo}/application/` retorna vazio
- [ ] **Testes:** `prisma-{nome-agregado}.repository.spec.ts` criado com mocks

---

## 8. Greenfield vs Brownfield

| Cenário | Módulos Novos | Módulos Legados (inalterados) |
|---------|---------------|-------------------------------|
| **Greenfield** | Estrutura completa obrigatória | N/A |
| **Brownfield** | Estrutura completa obrigatória | Marcar service com `// LEGACY`<br/>Criar issue de migração<br/>Manter funcionando até PRP-A |

---

## 9. Exemplo Concreto: Módulo Auditorias

### Interface
```typescript
// src/auditorias/domain/repositories/iauditoria.repository.ts
export interface IAuditoriaRepository {
  save(auditoria: Auditoria): Promise<Auditoria>;
  delete(id: string): Promise<void>;
  findById(id: string): Promise<Auditoria | null>;
  findMany(filter: AuditoriaFilter, pagination?: AuditoriaPagination): Promise<Auditoria[]>;
  count(filter: AuditoriaFilter): Promise<number>;
  findByNumero(numero: string): Promise<Auditoria | null>;
  findByUnidade(unidadeId: string): Promise<Auditoria[]>;
  nextNumero(): Promise<string>;
  withTransaction<T>(fn: (repo: IAuditoriaRepository) => Promise<T>): Promise<T>;
}
```

### Implementação
```typescript
// src/auditorias/infrastructure/repositories/prisma-auditoria.repository.ts
@Injectable()
export class PrismaAuditoriaRepository implements IAuditoriaRepository {
  constructor(private readonly prisma: PrismaService) {}
  // ... implementação completa
}
```

### Module
```typescript
// src/auditorias/auditorias.module.ts
providers: [
  AuditoriasService,
  { provide: IAuditoriaRepository, useClass: PrismaAuditoriaRepository },
  AbrirAuditoriaUseCase,
  IniciarExecucaoUseCase,
  ConcluirAuditoriaUseCase,
  SuspenderAuditoriaUseCase,
  ListarAuditoriasUseCase,
]
```

---

## 10. Fitness Function Rules (referência para .ace/arch-config.yaml)

```yaml
rules:
  - name: "repository-interface-exists"
    check: "file_exists"
    path: "**/domain/repositories/I*Repository.ts"
    message: "Cada aggregate root deve ter interface de repository"
    
  - name: "repository-impl-exists"
    check: "file_exists"
    path: "**/infrastructure/repositories/Prisma*Repository.ts"
    message: "Cada interface deve ter implementação Prisma"
    
  - name: "repository-binding-in-module"
    pattern: "provide: I.*Repository"
    required_in: ["**/*.module.ts"]
    message: "Module deve ter binding DI para repository"
    
  - name: "no-prisma-in-domain"
    pattern: "import.*PrismaService|@prisma/client"
    forbidden_in: ["**/domain/**"]
    message: "Domain não pode importar Prisma"
    
  - name: "no-prisma-in-use-cases"
    pattern: "import.*PrismaService"
    forbidden_in: ["**/application/**", "**/use-cases/**"]
    message: "Use Cases não podem injetar PrismaService"
```