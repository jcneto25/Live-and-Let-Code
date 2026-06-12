---
name: llc-step-12-null-safety
description: Pipeline LLC — Validação de null safety nos PRPs antes do início da implementação. Verifica campos opcionais, fallbacks e contratos de nulabilidade no design de dados.
version: 1.0.0
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
- [ ] `docs/prps/PRP-*.md` — PRPs com seção `data_model` ou `model` preenchida (Step 3)
- [ ] `docs/testing/TESTING_GUIDE.md` — contratos de entrada/saída (Step 9)
- [ ] `docs/architecture/DATA_MODEL.md` — modelo de dados canônico (Step 5, se existir)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-12-null-safety` do pipeline LLC. Seu objetivo é validar que todos os PRPs (Product Requirements Pages) definem contratos de nulabilidade claros para cada campo antes que a implementação comece.

Campos sem especificação explícita de nulabilidade são a principal fonte de `NullPointerException`, `undefined is not a function` e `Cannot read properties of null` em produção. Esta skill previne esses bugs na fase de design.

### 1. Leia as Entradas

- `docs/prps/PRP-*.md` — todos os PRPs. Para cada PRP, localize a seção `data_model` ou `model`.
- `docs/architecture/DATA_MODEL.md` — modelo de dados canônico do projeto (se existir). Use como referência para validar consistência entre PRPs.
- `docs/testing/TESTING_GUIDE.md` — contratos de entrada/saída definidos nos testes.

### 2. Extraia Definições de Dados

Para cada PRP, extraia todas as definições de entidades, tabelas, tipos ou interfaces. Exemplos de formatos a reconhecer:

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

**Plain markdown tables:**
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

| PRP | Entidade | Campo | Tipo | Nulável? | Fallback Definido? | Fonte |
|---|---|---|---|---|---|---|
| PRP-001 | User | id | string | NÃO | N/A | PRP-001 §data_model |
| PRP-001 | User | name | string | NÃO | N/A | PRP-001 §data_model |
| PRP-001 | User | email | string | SIM | "Usar avatar default" | PRP-001 §data_model |
| PRP-001 | User | avatar | string? | NÃO ESPECIFICADO | NÃO | — |

#### Estágio 2: Verificação de Contratos

Para cada campo, verifique:

1. **Nulabilidade explícita:** O campo declara se pode ser nulo? (`?`, `| null`, `Optional`, `String?`, coluna "Nulável" em tabela)
   - Se NÃO: marcar como 🔴 `NÃO ESPECIFICADO`.

2. **Fallback para campos nuláveis:** Se o campo é nulável, existe um valor de fallback documentado?
   - Se NÃO: marcar como 🟡 `FALLBACK AUSENTE`.
   - O fallback pode ser: valor default no modelo, descrição em §design_decisions, regra de negócio em §business_rules.

3. **Consistência entre PRPs:** O mesmo campo aparece em múltiplos PRPs com a mesma definição de nulabilidade?
   - Se NÃO: marcar como 🔴 `INCONSISTENTE`.

4. **Consistência com DATA_MODEL.md:** Se `DATA_MODEL.md` existe, o campo no PRP bate com o modelo canônico?
   - Se NÃO: marcar como 🟡 `DIVERGENTE`.

#### Estágio 3: Classificação e Relatório

Classifique cada problema encontrado:

- 🔴 **Crítico:** Campo sem especificação de nulabilidade (risco de NPE).
- 🟡 **Alto:** Campo nulável sem fallback documentado.
- 🟡 **Alto:** Inconsistência entre PRPs para o mesmo campo.
- 🟢 **Médio:** Divergência com DATA_MODEL.md (se existir).
- ⚪ **Info:** Campo com nulabilidade explícita e fallback — OK.

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
- 🟡 Campos nuláveis sem fallback: {{NO_FALLBACK_COUNT}}
- 🟡 Inconsistências entre PRPs: {{INCONSISTENT_COUNT}}
- 🟢 Divergências com DATA_MODEL.md: {{DIVERGENT_COUNT}}

## 2. Inventário Completo

| PRP | Entidade | Campo | Tipo | Nulável? | Fallback | Status |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## 3. Problemas Encontrados

### 3.1 Campos sem Especificação de Nulabilidade (🔴 Crítico)

| PRP | Entidade | Campo | Tipo Atual | Recomendação |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### 3.2 Campos Nuláveis sem Fallback (🟡 Alto)

| PRP | Entidade | Campo | Tipo | Sugestão de Fallback |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### 3.3 Inconsistências entre PRPs (🟡 Alto)

| Campo | PRP A | Definição A | PRP B | Definição B | Recomendação |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

### 3.4 Divergências com DATA_MODEL.md (🟢 Médio)

| Campo | PRP | Definição PRP | DATA_MODEL.md | Recomendação |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 4. Decisão do Gate

**Decisão:** {{GATE_DECISION}}

### Critérios
- [ ] 0 campos sem especificação de nulabilidade
- [ ] 0 inconsistências entre PRPs
- [ ] Todos os campos nuláveis possuem fallback documentado

### Bloqueios

{{BLOCKERS}}

### Recomendações

{{RECOMMENDATIONS}}
```

### 6. Regras Críticas

- **Anti-alucinação:** Só reporte campos que REALMENTE existem nos PRPs. Se um PRP não tem seção `data_model`, reporte como 🟡 `PRP SEM MODELO DE DADOS`.
- **Parsing flexível:** Aceite múltiplos formatos de definição de dados (TypeScript, Python, Prisma, Markdown tables, JSON Schema). Documente qual formato foi encontrado em cada PRP.
- **Campos herdados:** Se um PRP referencia entidade definida em outro PRP ("Ver User em PRP-001"), herde a definição e não marque como duplicata.
- **Idempotência:** Re-execução do step sobrescreve `docs/security/NULL_SAFETY_REPORT.md`. Avise antes de sobrescrever.
- **Gate bloqueante:** Se houver 1+ campo 🔴 (sem especificação), o relatório deve marcar `REPROVADO`. O pipeline não avança para implementação até que todos os campos tenham nulabilidade explícita.

### 7. Ações Pós-Execução

- Se **APROVADO:** Avance para Step 13 (Code Generation).
- Se **REPROVADO:**
  - Para cada campo 🔴: adicione `| null`, `?`, `Optional` ou equivalente no PRP correspondente.
  - Para cada campo 🟡 sem fallback: documente o valor default na seção `data_model` do PRP.
  - Para cada inconsistência 🟡 entre PRPs: escolha uma definição canônica e atualize os PRPs divergentes.
  - Após correções, re-execute esta skill para revalidação.
