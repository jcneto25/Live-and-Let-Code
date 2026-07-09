---
name: llc-step-clean-code-functions
description: Pipeline LLC — Clean Code: Functions (Cap. 3 Clean Code). Regras para funções pequenas, uma responsabilidade, poucos parâmetros, sem efeitos colaterais ocultos. Integra com fitness functions para validação automatizada.
version: 1.0.0
tags: [clean-code, functions, solid, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Functions

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 5a, 8b, 11a, 11b  
**Referência:** *Clean Code* (R. Martin) — Capítulo 3  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-functions` ou "Execute a skill llc-step-clean-code-functions".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-functions --task "Aplicar regras de Clean Code para funções"`.

---

## 🎯 OBJETIVO

Garantir que **todas as funções/métodos** no código sigam os princípios de Clean Code para funções:
- **Pequenas** (≤ 20 linhas)
- **Fazem uma coisa** (Single Responsibility)
- **Poucos parâmetros** (≤ 3, usar objeto se mais)
- **Sem efeitos colaterais ocultos**
- **Nomes descritivos** que revelam intenção

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Tamanho Máximo: 20 Linhas

```typescript
// ❌ RUIM: 45 linhas, múltiplas responsabilidades
async create(dto: CreateAuditoriaDto, criadoPorId: string) {
    const itemPlano = await this.auditoriaRepo.findUnique(...);
    if (!itemPlano) throw new NotFoundException('Item do plano não encontrado');
    if (!['APROVADO', 'PUBLICADO'].includes(itemPlano.plano?.status)) ...
    const numero = await this.gerarNumeroSequencial();
    const auditoria = await this.auditoriaRepo.create({...});
    await this.gerarComunicado(auditoria.id, criadoPorId);
    this.eventEmitter.emit('auditoria.aberta', new AuditoriaAbertaEvent(...));
    return auditoria;
}

// ✅ BOM: 1 responsabilidade, delega para use cases
async create(dto: CreateAuditoriaDto, criadoPorId: string): Promise<Auditoria> {
    return this.abrirAuditoriaUseCase.execute({ dto, criadoPorId });
}
```

### 2. Uma Coisa Só (Single Responsibility)

Uma função deve fazer **UMA** coisa e fazer bem feito.

```typescript
// ❌ RUIM: valida + cria + notifica + emite evento
async abrirAuditoria(dto, autorId) { ... }

// ✅ BOM: cada um faz uma coisa
async validarItemPlano(itemPlanoId: string): Promise<ItemPlano>
async gerarNumeroSequencial(): Promise<string>
async criarEntidadeAuditoria(dados: DadosAuditoria): Promise<Auditoria>
async notificarGestores(auditoria: Auditoria): Promise<void>
async emitirEventoAuditoriaAberta(auditoria: Auditoria): Promise<void>
```

### 3. Parâmetros: Máximo 3

```typescript
// ❌ RUIM: 4+ parâmetros posicionais
async execute(achadoId: string, dto: CreateManifestacaoDto, autorId: string, unidadeEscopo?: string | null)

// ✅ BOM: objeto de parâmetros nomeado
interface CriarManifestacaoParams {
  achadoId: string;
  dto: CreateManifestacaoDto;
  autorId: string;
  unidadeEscopo?: string | null;
}

async execute(params: CriarManifestacaoParams): Promise<Manifestacao>
```

### 4. Nomes Descritivos

```typescript
// ❌ RUIM: nomes genéricos
const data = await this.repo.findUnique(id);
const result = await this.service.process(data);
const info = await this.api.fetch();

// ✅ BOM: nomes que revelam intenção
const auditoriaEncontrada = await this.auditoriaRepo.findUnique(auditoriaId);
const auditoriaCriada = await this.abrirAuditoriaUseCase.execute({ ... });
const tokensGerados = await this.authService.gerarTokens(usuario);
```

### 5. Sem Efeitos Colaterais Ocultos

```typescript
// ❌ RUIM: modifica estado global sem ser óbvio
function validarToken(token: string): boolean {
    this.ultimoTokenValidado = token; // side effect oculto!
    return this.jwt.verify(token);
}

// ✅ BOM: pura ou efeito colateral explícito no nome
function validarEToken(token: string): { valido: boolean; token: string } {
    return { valido: this.jwt.verify(token), token };
}
```

### 6. Retorno Consistente

```typescript
// ❌ RUIM: mistura throw e return para controle de fluxo
async find(id: string) {
    const entity = await this.repo.find(id);
    if (!entity) throw new NotFoundException('Não encontrado');
    return entity;
}

// ✅ BOM: usa Result<T, E> para regras de negócio
async find(id: string): Promise<Result<Entity, NotFoundError>> {
    const entity = await this.repo.find(id);
    if (!entity) return err(new NotFoundError(id));
    return ok(entity);
}
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

Esta skill integra com `fitness-functions.py` através dos seguintes checks:

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `function-max-lines` | Funções não excedem 20 linhas | 20 | block (core) / warn (non-core) |
| `function-max-params` | Funções têm ≤ 3 parâmetros | 3 | block (core) / warn (non-core) |
| `function-single-responsibility` | Detecção heurística de múltiplas responsabilidades | - | warn |
| `no-generic-names` | Proíbe `data`, `dto`, `result`, `info`, `obj` | lista | block (core) / warn (non-core) |
| `no-side-effects` | Detecta atribuições a `this.*` em funções puras | - | warn |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

Antes de aprovar código que use esta skill:

- [ ] Todas as funções ≤ 20 linhas?
- [ ] Cada função tem responsabilidade única clara?
- [ ] Parâmetros ≤ 3 (ou objeto nomeado)?
- [ ] Nomes de variáveis/parâmetros revelam intenção?
- [ ] Zero `data`/`dto`/`result`/`info`/`obj` genéricos?
- [ ] Funções puras não têm side effects?
- [ ] Retorno usa `Result<T, E>` para regras de negócio?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-functions --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todo código novo** desde o primeiro commit |
| **Brownfield** | Aplicar a **novos arquivos** e **arquivos modificados** (PRP-A). Código legacy marcado com `// LEGACY` tem tolerância temporária, mas deve ter plano de migração |

---

## 📤 SAÍDA ESPERADA

Ao executar esta skill, o agente deve:

1. **Verificar** código existente contra as regras
2. **Reportar** violações com localização exata e sugestão de fix
3. **Sugerir** refatoração para use cases quando service > 20 linhas
4. **Validar** via fitness functions automatizadas
5. **Aguardar** validação humana (Gate) antes de prosseguir

**NÃO prossiga para execução sem Gate aprovado.**