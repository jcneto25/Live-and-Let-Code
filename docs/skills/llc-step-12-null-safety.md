---
name: llc-step-12-null-safety
description: Pipeline LLC — Validação de null safety nos PRPs antes do início da implementação. Verifica nulabilidade (NOT NULL/NULL/DEFAULT), fallbacks e contratos de dados.
version: 1.1.0
tags: [null-safety, validation, data-design, contracts, llc-pipeline]
---

# LLC Skill: Step 12-Null-Safety — Validação de Null Safety nos PRPs

**Pipeline:** Live and Let Code (LLC)
**Fase:** Pre-Implementation Validation (início do Step 12)
**Depende de:** Step 6 (TASKS.md — tarefas), Step 3 (PRPs — definição de dados), Step 9 (Testing Docs — contratos)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-12-null-safety` ou "Execute a skill llc-step-12-null-safety".

## 📋 Pré-requisitos

- [ ] `docs/planning/TASKS.md` — tarefas de implementação (Step 6)
- [ ] `docs/prps/PRP-*.md` — PRPs com seção **§7 (Data Model)** preenchida (Step 3)
- [ ] `docs/testing/TESTING_GUIDE.md` — contratos de entrada/saída (Step 9)
- [ ] `docs/architecture/ARCHITECTURE.md §6.1 (Entidades principais)` — modelo de dados canônico (Step 5, se definido)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-12-null-safety` do pipeline LLC. Seu objetivo é validar que todos os PRPs definem contratos de nulabilidade claros para cada campo antes que a implementação comece.

Campos sem especificação explícita de nulabilidade são a principal fonte de `NullPointerException`, `undefined is not a function` e `Cannot read properties of null` em produção. Esta skill previne esses bugs na fase de design.

### 1. Leia as Entradas

- `docs/prps/PRP-*.md` — todos os PRPs. Para cada PRP, localize a seção **§7 (Data Model)** como fonte primária. Se o PRP não tiver §7, busque `data_model` ou `model` (legacy).
- `docs/architecture/ARCHITECTURE.md §6.1 (Entidades principais)` — modelo de dados canônico do projeto (se definido no documento de arquitetura gerado no Step 5). Use como referência para validar consistência entre PRPs. **Nota:** o template atual traz apenas um placeholder de entidades; um modelo per-campo canônico pode ainda não existir — nesse caso, pule a verificação de consistência (Estágio 2, item 4).
- `docs/testing/TESTING_GUIDE.md` — contratos de entrada/saída definidos nos testes.
- `docs/business/specs/regras_negocio.md` — regras de negócio que podem definir fallbacks para campos nuláveis.

### 2. Extraia Definições de Dados

Para cada PRP, extraia todas as definições de entidades, tabelas, tipos ou interfaces a partir da seção **§7 (Data Model)**.

**Fonte primária — tabela do §7 Data Model:**

```markdown
| Campo | Tipo | Nulabilidade | Fallback (se NULL) |
|-------|------|:------------:|--------------------|
| id | UUID | NOT NULL | N/A |
| email | varchar | NULL | "anon@example.com" |
| role | enum | DEFAULT 'viewer' | — |
```

**Legenda dos 3 estados de Nulabilidade:**
- `NOT NULL` — campo obrigatório, nunca é nulo. Fallback: N/A.
- `NULL` — campo pode ser nulo; **exige fallback** documentado.
- `DEFAULT <valor>` — banco atribui valor padrão na INSERT; código nunca vê null vindo do DB. Fallback: —.

**Formatos legados aceitos (para PRPs que ainda usam `data_model` ou `model`):**

**TypeScript:**
```typescript
interface User {
  id: string;
  name: string;
  email?: string;        // opcional — precisa de fallback
  avatar: string | null; // explicitamente nulável — OK
}
```

**Python (Pydantic):**
```python
class User(BaseModel):
    id: str
    name: str
    email: Optional[str] = None  # OK: nulabilidade explícita
```

**Prisma (schema.prisma):**
```prisma
model User {
  id     String  @id
  name   String
  email  String?  // opcional — OK
}
```

**Plain markdown tables (legado):**
```markdown
| Campo | Tipo | Nulável |
|---|---|---|
| id | string | NÃO |
| name | string | NÃO |
| email | string | SIM |
```

### 3. Execute a Validação (3 Estágios)

#### Estágio 1: Inventário de Campos

Para cada PRP, construa um inventário:

| PRP | Entidade | Campo | Tipo | Nulabilidade | Fallback | Fonte |
|---|---|---|---|---|---|---|
| PRP-001 | User | id | UUID | NOT NULL | N/A | PRP-001 §7.1 |
| PRP-001 | User | email | varchar | NULL | "anon@example.com" | PRP-001 §7.1 |
| PRP-001 | User | role | enum | DEFAULT 'viewer' | — | PRP-001 §7.1 |
| PRP-001 | User | avatar | string | NÃO ESPECIFICADO | NÃO | — |

#### Estágio 2: Verificação de Contratos

Para cada campo, verifique:

1. **Nulabilidade explícita:** O campo declara um dos 3 estados (`NOT NULL`, `NULL`, `DEFAULT <valor>`)?
   - Se NÃO: marcar como 🔴 `NÃO ESPECIFICADO`.

2. **Fallback para campos NULL:** Se o campo é `NULL`, existe um valor de fallback documentado?
   - Se NÃO: marcar como 🟡 `FALLBACK AUSENTE`.
   - O fallback pode ser: inline (`"anon@example.com"`), referência a outro PRP (`→ PRP-001 §7.1 email`), decisão técnica na seção **§11 (Dívida Técnica e Decisões)** do PRP, ou regra de negócio em `docs/business/specs/regras_negocio.md`.

3. **Consistência entre PRPs:** O mesmo campo aparece em múltiplos PRPs com a mesma definição de nulabilidade?
   - Se NÃO: marcar como 🔴 `INCONSISTENTE`.

4. **Consistência com ARCHITECTURE.md:** Se o documento de arquitetura contém modelo de dados canônico (`§6.1 — Entidades principais`), o campo no PRP bate com ele?
   - Se NÃO: marcar como 🟡 `DIVERGENTE`.

#### Estágio 3: Classificação e Relatório

Classifique cada problema encontrado:

- 🔴 **Crítico:** Campo sem especificação de nulabilidade (risco de NPE).
- 🔴 **Crítico:** Inconsistência entre PRPs para o mesmo campo.
- 🟡 **Alto:** Campo NULL sem fallback documentado.
- 🟢 **Médio:** Divergência com ARCHITECTURE.md §6.1 (Entidades principais) (se existir).
- ⚪ **Info:** Campo com nulabilidade explícita e fallback (se aplicável) — OK.

### 4. Output Esperado

```
docs/security/
└── NULL_SAFETY_REPORT.md
```

### 5. Formato do Relatório

Gere `docs/security/NULL_SAFETY_REPORT.md` com a seguinte estrutura:

```markdown
# Relatório de Null Safety — PRPs

| Campo | Valor |
|---|---|
| **Data da validação** | {{DATE}} |
| **PRPs analisados** | {{PRP_LIST}} |
| **Total de campos** | {{TOTAL_FIELDS}} |
| **Decisão** | {{GATE_DECISION}} |

## 1. Sumário

- ✅ Campos com nulabilidade explícita: {{EXPLICIT_COUNT}}
- 🔴 Campos sem especificação: {{UNSPECIFIED_COUNT}}
- 🔴 Inconsistências entre PRPs: {{INCONSISTENT_COUNT}}
- 🟡 Campos NULL sem fallback: {{NO_FALLBACK_COUNT}}
- 🟢 Divergências com ARCHITECTURE.md: {{DIVERGENT_COUNT}}

## 2. Inventário Completo

| PRP | Entidade | Campo | Tipo | Nulabilidade | Fallback | Status |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## 3. Problemas Encontrados

### 3.1 Campos sem Especificação de Nulabilidade (🔴 Crítico)

| PRP | Entidade | Campo | Tipo Atual | Recomendação |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### 3.2 Inconsistências entre PRPs (🔴 Crítico)

| Campo | PRP A | Definição A | PRP B | Definição B | Recomendação |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

### 3.3 Campos NULL sem Fallback (🟡 Alto)

| PRP | Entidade | Campo | Tipo | Sugestão de Fallback |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### 3.4 Divergências com ARCHITECTURE.md (🟢 Médio)

| Campo | PRP | Definição PRP | ARCHITECTURE.md | Recomendação |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 4. Decisão do Gate

**Decisão:** {{GATE_DECISION}}

### Critérios
- [ ] 0 campos sem especificação de nulabilidade
- [ ] 0 inconsistências entre PRPs
- [ ] Todos os campos NULL possuem fallback documentado

### Bloqueios

{{BLOCKERS}}

### Recomendações

{{RECOMMENDATIONS}}
```

### 6. Regras Críticas

- **Anti-alucinação:** Só reporte campos que REALMENTE existem nos PRPs. Se um PRP não tem seção §7 (Data Model) e nem `data_model`/`model` legacy, reporte como 🟡 `PRP SEM MODELO DE DADOS`.
- **Parsing flexível:** A fonte primária é a tabela do §7 (colunas `Campo | Tipo | Nulabilidade | Fallback`). Aceite formatos legados como fallback (TypeScript, Python, Prisma, markdown tables simples). Documente qual formato foi encontrado em cada PRP na coluna "Fonte" do inventário.
- **Campos herdados:** Se um PRP referencia entidade definida em outro PRP ("Ver User em PRP-001 §7.1"), herde a definição e não marque como duplicata.
- **Idempotência:** Re-execução do step sobrescreve `docs/security/NULL_SAFETY_REPORT.md`. Avise antes de sobrescrever.
- **Gate bloqueante:** Se houver 1+ campo 🔴 (sem especificação ou inconsistente), o relatório deve marcar `REPROVADO`. O pipeline não avança para implementação até que todos os campos tenham nulabilidade explícita.

### 7. Ações Pós-Execução

- Se **APROVADO:** Avance para Step 13 (Code Generation).
- Se **REPROVADO:**
  - Para cada campo 🔴: adicione `NOT NULL`, `NULL` ou `DEFAULT <valor>` na seção §7 do PRP correspondente.
  - Para cada campo 🟡 NULL sem fallback: documente o valor default na coluna "Fallback (se NULL)" da seção §7 do PRP, ou referencie a fonte (`→ PRP-NNN §7 campo`, `→ regras_negocio.md §N`, `→ §11 Dívida Técnica`).
  - Para cada inconsistência 🔴 entre PRPs: escolha uma definição canônica e atualize os PRPs divergentes.
  - Após correções, re-execute esta skill para revalidação.
