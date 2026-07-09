---
name: llc-step-clean-code-naming
description: Pipeline LLC — Clean Code: Naming (Cap. 2 Clean Code). Regras para nomes que revelam intenção, sem dissonância, consistentes, pronunciáveis e pesquisáveis. Integra com fitness functions.
version: 1.0.0
tags: [clean-code, naming, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Naming

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 3, 5a, 6, 8b, 11a, 11b  
**Referência:** *Clean Code* (R. Martin) — Capítulo 2  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-naming` ou "Execute a skill llc-step-clean-code-naming".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-naming --task "Aplicar regras de naming Clean Code"`.

---

## 🎯 OBJETIVO

Garantir que **todos os identificadores** (variáveis, funções, classes, arquivos, constantes) sigam princípios de Clean Code:
- **Revelam intenção** — o nome diz *o que é*, *por que existe*, *como usar*
- **Evitam dissonância** — nome corresponde ao que o código faz
- **Consistentes** — mesmo conceito = mesmo nome em todo o código
- **Pronunciáveis** — pode-se falar em code review
- **Pesquisáveis** — fácil de encontrar com grep/IDE

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Nomes Revelam Intenção

```typescript
// ❌ RUIM: não revela nada
const d = await this.repo.find(id);
const data = dto;
const result = service.process(info);

// ✅ BOM: revela intenção e tipo
const auditoriaEncontrada = await this.auditoriaRepo.findUnique(auditoriaId);
const criacaoAuditoriaDto = dto;
const auditoriaCriada = await this.abrirAuditoriaUseCase.execute({ ... });
```

### 2. Proibidos Nomes Genéricos

**Lista bloqueada (fitness function `no-generic-names`):**

| Genérico | Substituição Sugerida |
|----------|----------------------|
| `data` | `auditoria`, `usuario`, `plano`, `achado`, `itemPlano` |
| `dto` | `criacaoAuditoriaDto`, `atualizacaoPlanoDto`, `manifestacaoAchadoDto` |
| `result` | `auditoriaCriada`, `tokensGerados`, `validacaoResultado` |
| `info` | `dadosAuditoria`, `detalhesAchado`, `configuracaoModulo` |
| `obj` | `entidadeAuditoria`, `valueObjectEndereco` |
| `item` | `itemPlano`, `itemChecklist`, `linhaRelatorio` |
| `entity` | `auditoria`, `achado`, `recomendacao` |
| `model` | `dominioAuditoria`, `readModelPlano` |
| `temp` / `tmp` | **nunca usar** — nomeie o que é |
| `value` | `statusAuditoria`, `prioridadeAchado`, `nivelRisco` |

### 3. Classes: Substantivos/Substantivos Compostos

```typescript
// ✅ BOM: substantivo que identifica a entidade/conceito
class Auditoria { ... }
class ItemPlanoAuditoria { ... }
class CriarAuditoriaUseCase { ... }
class AuditoriaRepository { ... }
class PrismaAuditoriaRepository { ... }
class AuditoriaAbertaEvent { ... }
class StatusAuditoriaInvalidoError { ... }
```

### 4. Métodos/Funções: Verbos/Verbos Compostos

```typescript
// ✅ BOM: verbo que descreve a ação
async findUnique(id: string): Promise<Auditoria | null>
async create(dados: CriacaoAuditoriaDto): Promise<Auditoria>
async iniciarExecucao(): Promise<Result<Auditoria, Error>>
async emitirEventoAuditoriaAberta(auditoria: Auditoria): Promise<void>
async calcularPrazoManifestacao(achado: Achado): Promise<Date>
```

### 5. Booleans: Prefixos `is`/`has`/`can`/`should`

```typescript
// ✅ BOM
const isAuditoriaAberta = auditoria.status === 'ABERTA';
const hasEvidencias = auditoria.evidencias.length > 0;
const canConcluir = auditoria.podeSerConcluida();
const shouldNotificar = achado.prazoVencido();
```

### 6. Constantes: UPPER_SNAKE_CASE com Contexto

```typescript
// ❌ RUIM: magic numbers, sem contexto
const PRAZO = 5;
const DIAS = 30;

// ✅ BOM: contexto + unidade + propósito
const PRAZO_MANIFESTACAO_DIAS_UTEIS = 5;
const TOKEN_EXPIRACAO_MINUTOS = 30;
const REFRESH_TOKEN_EXPIRACAO_HORAS = 8;
const MAX_TENTATIVAS_LOGIN = 5;
const SALT_ROUNDS_BCRYPT = 10;
```

### 7. Arquivos: kebab-case, Sufixos Padronizados

| Tipo | Sufixo | Exemplo |
|------|--------|---------|
| Entity | `.entity.ts` | `auditoria.entity.ts` |
| Value Object | `.value-object.ts` | `email.value-object.ts` |
| Repository Interface | `.repository.ts` | `auditoria.repository.ts` |
| Repository Impl | `-repository.ts` | `prisma-auditoria-repository.ts` |
| Use Case | `.use-case.ts` | `abrir-auditoria.use-case.ts` |
| Domain Event | `.event.ts` | `auditoria-aberta.event.ts` |
| Domain Error | `.error.ts` | `auditoria-nao-encontrada.error.ts` |
| DTO | `.dto.ts` | `criar-auditoria.dto.ts` |
| Enum | `.enum.ts` | `status-auditoria.enum.ts` |
| Constants | `.constants.ts` | `auditoria.constants.ts` |
| Controller | `.controller.ts` | `auditorias.controller.ts` |
| Module | `.module.ts` | `auditorias.module.ts` |
| Service (legacy) | `.service.ts` | `auditorias.service.ts` |

### 8. Pastas: kebab-case, Plural para Coleções

```
src/auditorias/
├── domain/
│   ├── entities/
│   ├── value-objects/
│   ├── events/
│   ├── errors/
│   └── repositories/
├── application/
│   ├── use-cases/
│   ├── dto/
│   └── ports/
├── infrastructure/
│   ├── repositories/
│   └── persistence/
└── presentation/
    └── controllers/
```

### 9. Consistência Cross-Module

| Conceito | Nome Padrão | Módulos Aplicáveis |
|----------|-------------|-------------------|
| Repository Interface | `I{Nome}Repository` | Todos |
| Repository Impl | `Prisma{Nome}Repository` | Todos |
| Use Case | `{Acao}{Nome}UseCase` | Módulos com regras |
| Domain Event | `{Nome}{Acao}Event` | Todos |
| Domain Error | `{Nome}{Erro}Error` | Todos |
| Read Model | `{Nome}ReadModel` | Todos |
| Mapper | `{Nome}Mapper` | Todos |

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `no-generic-names` | Bloqueia `data`, `dto`, `result`, `info`, `obj`, `item`, `entity`, `model`, `temp`, `value` | lista fixa | block (core) / warn (non-core) |
| `naming-convention-classes` | Classes PascalCase, sufixos padronizados | regex | block |
| `naming-convention-methods` | Métodos camelCase, verbos | regex | block |
| `naming-convention-files` | Arquivos kebab-case, sufixos corretos | regex | block |
| `naming-convention-constants` | Constantes UPPER_SNAKE_CASE | regex | warn |
| `boolean-prefix` | Booleans começam com is/has/can/should | regex | warn |
| `consistent-terminology` | Mesmo conceito = mesmo nome cross-module | glossary | warn |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

- [ ] Zero variáveis `data`/`dto`/`result`/`info`/`obj`/`item`/`entity`/`model`/`temp`/`value`?
- [ ] Classes em PascalCase com sufixos corretos?
- [ ] Métodos em camelCase começando com verbo?
- [ ] Booleans com prefixo `is`/`has`/`can`/`should`?
- [ ] Constantes em UPPER_SNAKE_CASE com contexto?
- [ ] Arquivos em kebab-case com sufixos padronizados?
- [ ] Terminologia consistente entre módulos?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-naming --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todo código novo** desde o primeiro commit |
| **Brownfield** | Aplicar a **novos arquivos** e **arquivos modificados**. Legacy marcado com `// LEGACY` tem tolerância mas requer ADR de migração |

---

## 📤 SAÍDA ESPERADA

1. **Relatório de violações** com arquivo, linha, nome atual, sugestão
2. **Glossário de termos** do projeto (ex: `Auditoria` ≠ `AuditoriaProcesso`, `Achado` ≠ `NaoConformidade`)
3. **Fitness functions** atualizadas no `.ace/arch-config.yaml`
4. **Aguardar Gate humano** antes de prosseguir