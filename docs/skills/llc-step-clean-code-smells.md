---
name: llc-step-clean-code-smells
description: Pipeline LLC — Clean Code: Smells & Heuristics (Cap. 17 Clean Code). Detecta magic numbers, dead code, comentários desnecessários, duplicação, feature envy, data clumps. Integra com fitness functions.
version: 1.0.0
tags: [clean-code, smells, heuristics, refactoring, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Smells & Heuristics

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 5a, 8b, 11a, 11b  
**Referência:** *Clean Code* (R. Martin) — Capítulo 17 (Smells and Heuristics)  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-smells` ou "Execute a skill llc-step-clean-code-smells".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-smells --task "Detectar e corrigir code smells"`.

---

## 🎯 OBJETIVO

Detectar e eliminar **code smells** sistematicamente via fitness functions automatizadas:

| Categoria | Smells Principais |
|-----------|------------------|
| **Nomes** | G1-G4: Ininteligíveis, enganosos, ruído, inconsistentes |
| **Funções** | G5-G9: Muitos args, flag args, dead function, saída inesperada |
| **Comentários** | G10-G13: Inadequados, obsoletos, ruído, diários |
| **Ambiente** | G14-G15: Build/test complexos |
| **Funções (cont.)** | G16-G21: Muitas linhas, nesting, parâmetros, duplicação |
| **Geral** | G22-G33: Dead code, variáveis não usadas, magic numbers, etc. |
| **Classes** | G34-G37: Coesão, acoplamento, herança, encapsulamento |

---

## 📋 SMELLS CRÍTICOS (Bloqueiam CI)

### S1 — Magic Numbers / Strings (G25)

```typescript
// ❌ RUIM: magic numbers
const TOKEN_EXPIRACAO = 30 * 60 * 1000; // 30min em ms
const REFRESH_EXPIRACAO = 8 * 60 * 60 * 1000; // 8h
if (tentativas >= 5) bloquear();
if (!['APROVADO', 'PUBLICADO'].includes(status)) ...

// ✅ BOM: constantes nomeadas com contexto
const TOKEN_EXPIRACAO_MINUTOS = 30;
const TOKEN_EXPIRACAO_MS = TOKEN_EXPIRACAO_MINUTOS * 60 * 1000;
const REFRESH_TOKEN_EXPIRACAO_HORAS = 8;
const MAX_TENTATIVAS_LOGIN = 5;
const STATUS_PLANO_VALIDOS_PARA_AUDITORIA = ['APROVADO', 'PUBLICADO'] as const;
```

**Regra:** Zero literais numéricos/strings em lógica de negócio. Constantes em `domain/constants.ts`.

### S2 — Dead Code (G9)

```typescript
// ❌ RUIM: stubs não implementados
async setupMfa(usuarioId: string, senha: string) {
    throw new UnauthorizedException('Método não implementado');
}
async changePassword(usuarioId: string, senhaAtual: string, novaSenha: string) {
    throw new UnauthorizedException('Método não implementado');
}

// ✅ BOM: implementar OU remover (se não usado)
// Se planejado para futuro: marcar com @TODO + issue number
```

**Regra:** Zero `throw new ...('não implementado')` ou `// TODO` em produção.

### S3 — Comentários Ruído/Obsolescentes (G10-G13)

```typescript
// ❌��� RUIM: timestamp comments
// ── Evidências ────────────────────────────────
// ── Papéis de Trabalho ────────────────────────

// ❌ RUIM: comentário óbvio
// incrementa contador
contador++;

// ❌ RUIM: código comentado (dead code)
/*
async oldMethod() { ... }
*/

// ✅ BOM: comentário explica POR QUE, não O QUÊ
// Regra de negócio: auditoria só pode iniciar se status ABERTA
// (regra definida no Requisito NF-003)
if (auditoria.status !== 'ABERTA') ...
```

**Regra:** Zero comentários de seção (`// ──`), zero código comentado, zero comentários óbvios.

### S4 — Variáveis `let` Onde `const` Serve (G27)

```typescript
// ❌ RUIM: let sem reatribuição
let status = 'ONLINE';
let erro: string | null = null;
let resultado = await this.service.call();

// ✅ BOM: const por padrão
const status = 'ONLINE';
const erro: string | null = null;
const resultado = await this.service.call();
```

**Regra:** `const` por padrão. `let` só se houver reatribuição real.

### S5 — Objetos Grandes Inline (G21)

```typescript
// ❌ RUIM: 10+ campos inline
const auditoria = await this.prisma.auditoria.create({
    data: {
        numero: numeroGerado,
        tipo: 'CONFORMIDADE',
        status: 'ABERTA',
        unidadeAuditada: dto.unidadeAuditada,
        objetivo: dto.objetivo,
        escopo: dto.escopo,
        dataInicio: new Date(),
        dataFimPrevista: dto.dataFimPrevista,
        responsavelId: criadoPorId,
        itemPlanoId: dto.itemPlanoId,
    },
});

// ✅ BOM: factory ou builder
const auditoria = Auditoria.criar({
    itemPlanoId: dto.itemPlanoId,
    numero: await this.gerarNumero(),
    tipo: dto.tipo || 'CONFORMIDADE',
    // ...
});
const salva = await this.repo.save(auditoria);
```

### S6 — Array `includes` O(n) para Lookups Frequentes (G32)

```typescript
// ❌ RUIM: O(n) a cada validação
if (!STATUS_VALIDOS.includes(status)) ...

// ✅ BOM: Set para O(1)
const STATUS_VALIDOS_SET = new Set(['ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'SUSPENSA']);
if (!STATUS_VALIDOS_SET.has(status)) ...
```

### S7 — Feature Envy / Data Clumps (G22, G30)

```typescript
// ❌ RUIM: método usa mais dados de outro objeto que do seu
class AuditoriaService {
    gerarComunicado(auditoria: Auditoria, usuario: Usuario) {
        // usa 5 campos de auditoria, 3 de usuario — inveja!
        const msg = `${auditoria.numero} - ${auditoria.unidadeAuditada} - ${usuario.nome}...`;
    }
}

// ✅ BOM: mover para onde os dados estão (Auditoria entity ou ComunicadoService)
class Auditoria {
    gerarTextoComunicado(usuario: Usuario): string { ... }
}
```

### S8 — Duplicação (G20)

```typescript
// ❌ RUIM: validação duplicada em 5 use cases
if (!['APROVADO', 'PUBLICADO'].includes(itemPlano.plano.status)) ...

// ✅ BOM: extrair para constante + helper
const STATUS_PLANO_VALIDOS = ['APROVADO', 'PUBLICADO'] as const;
function validarPlanoParaAuditoria(plano: Plano): Result<void, PlanoInvalidoError> { ... }
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `no-magic-numbers` | Detecta literais numéricos/strings em lógica de negócio | 0 | block (core) / warn (non-core) |
| `no-dead-code` | Detecta `throw ... não implementado`, `// TODO` em prod | 0 | block |
| `no-noise-comments` | Detecta `// ──`, código comentado, comentários óbvios | 0 | warn |
| `prefer-const` | Detecta `let` sem reatribuição | 0 | warn |
| `no-large-inline-objects` | Detecta objetos com > 5 propriedades inline em chamadas | 5 | warn |
| `use-set-for-lookups` | Detecta `array.includes()` para validações frequentes | - | warn |
| `no-duplication` | Detecção heurística de blocos duplicados (> 3 linhas) | - | warn |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

- [ ] Zero magic numbers/strings em lógica de negócio?
- [ ] Zero stubs `throw ... não implementado`?
- [ ] Zero comentários ruído (`// ──`, código comentado)?
- [ ] `const` por padrão, `let` só quando necessário?
- [ ] Objetos grandes usam factory/builder?
- [ ] Lookups frequentes usam `Set`?
- [ ] Duplicação extraída para helpers/constants?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-smells --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Todas as regras desde o início. Constants em `domain/constants.ts` criadas junto com entidades. |
| **Brownfield** | Novos arquivos seguem regras. Legacy: extrair magic numbers progressivamente, remover dead code ao tocar arquivos. |

---

## 📤 SAÍDA ESPERADA

1. **Relatório de smells** por categoria: arquivo, linha, smell, sugestão
2. **Constants extraídas** para `domain/constants.ts` por módulo
3. **Dead code removido** ou implementado
4. **Fitness functions** atualizadas no `.ace/arch-config.yaml`
5. **Aguardar Gate humano**