---
name: null-safety-report-template
description: Template para relatório de validação de null safety nos PRPs do pipeline LLC. Preenchido pela skill llc-step-12-null-safety.
version: 1.0.0
tags: [null-safety, validation, template, llc-pipeline]
---

# Relatório de Null Safety — PRPs

| Campo | Valor |
|---|---|
| **Data da validação** | {{DATE}} |
| **PRPs analisados** | {{PRP_LIST}} |
| **Total de campos** | {{TOTAL_FIELDS}} |
| **Decisão** | {{GATE_DECISION}} |

---

## 1. Sumário

- ✅ Campos com nulabilidade explícita: {{EXPLICIT_COUNT}}
- 🔴 Campos sem especificação: {{UNSPECIFIED_COUNT}}
- 🟡 Campos nuláveis sem fallback: {{NO_FALLBACK_COUNT}}
- 🟡 Inconsistências entre PRPs: {{INCONSISTENT_COUNT}}
- 🟢 Divergências com DATA_MODEL.md: {{DIVERGENT_COUNT}}

### Recomendação

{{EXECUTIVE_RECOMMENDATION}}

---

## 2. Inventário Completo

| PRP | Entidade | Campo | Tipo | Nulável? | Fallback | Status |
|---|---|---|---|---|---|---|
| {{PRP_1}} | {{ENTITY_1}} | {{FIELD_1}} | {{TYPE_1}} | {{NULLABLE_1}} | {{FALLBACK_1}} | {{STATUS_1}} |

*(Repetir linha para cada campo encontrado em todos os PRPs)*

---

## 3. Problemas Encontrados

### 3.1 Campos sem Especificação de Nulabilidade (🔴 Crítico)

| PRP | Entidade | Campo | Tipo Atual | Recomendação |
|---|---|---|---|---|
| {{U_PRP_1}} | {{U_ENTITY_1}} | {{U_FIELD_1}} | {{U_TYPE_1}} | {{U_REC_1}} |

*(Repetir linha para cada campo sem especificação)*

### 3.2 Campos Nuláveis sem Fallback (🟡 Alto)

| PRP | Entidade | Campo | Tipo | Sugestão de Fallback |
|---|---|---|---|---|
| {{F_PRP_1}} | {{F_ENTITY_1}} | {{F_FIELD_1}} | {{F_TYPE_1}} | {{F_SUGGESTION_1}} |

*(Repetir linha para cada campo nulável sem fallback)*

### 3.3 Inconsistências entre PRPs (🟡 Alto)

| Campo | PRP A | Definição A | PRP B | Definição B | Recomendação |
|---|---|---|---|---|---|
| {{I_FIELD_1}} | {{I_PRP_A}} | {{I_DEF_A}} | {{I_PRP_B}} | {{I_DEF_B}} | {{I_REC_1}} |

*(Repetir linha para cada inconsistência encontrada)*

### 3.4 Divergências com DATA_MODEL.md (🟢 Médio)

| Campo | PRP | Definição PRP | DATA_MODEL.md | Recomendação |
|---|---|---|---|---|
| {{D_FIELD_1}} | {{D_PRP_1}} | {{D_DEF_PRP}} | {{D_DEF_DM}} | {{D_REC_1}} |

*(Repetir linha para cada divergência encontrada)*

---

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

---

## 5. Fontes Analisadas

| Arquivo | Seção | Formato | Campos Encontrados |
|---|---|---|---|
| {{SOURCE_FILE_1}} | {{SOURCE_SECTION_1}} | {{SOURCE_FORMAT_1}} | {{SOURCE_COUNT_1}} |

*(Repetir para cada fonte analisada)*

---

## 6. Log de Execução

```
{{EXECUTION_LOG}}
```

---

## 7. Assinaturas

| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Validador | {{VALIDATOR_NAME}} | {{DATE}} | |
| Revisor (opcional) | {{REVIEWER_NAME}} | {{REVIEW_DATE}} | |
