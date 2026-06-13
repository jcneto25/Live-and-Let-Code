---
name: null-safety-report
description: Relatório de validação de null safety nos PRPs do pipeline LLC. Gerado pela skill llc-step-12-null-safety. Preenchido com dados reais da análise.
version: 1.0.0
tags: [null-safety, validation, report, llc-pipeline]
---

# Relatório de Null Safety — PRPs

| Campo | Valor |
|---|---|
| **Data da validação** | 2026-06-12 |
| **PRPs analisados** | Nenhum — apenas o template PRP_TEMPLATE.md |
| **Total de campos** | 0 (campos reais em PRPs) + 8 (campos no template analisados como referência) |
| **Decisão** | **APROVADO** (sem PRPs para validar) |

---

## 1. Sumário

- ✅ Campos com nulabilidade explícita: 0 (sem PRPs reais)
- 🔴 Campos sem especificação: 0
- 🟡 Campos nuláveis sem fallback: 0
- 🟡 Inconsistências entre PRPs: 0
- 🟢 Divergências com DATA_MODEL.md: 0

### Recomendação

Nenhum PRP foi encontrado no diretório `docs/prps/`. Apenas o template `PRP_TEMPLATE.md` existe. A skill `llc-step-12-null-safety` não tem dados reais para validar. O gate está **APROVADO** por ausência de PRPs, mas com a recomendação de re-executar esta validação assim que os PRPs forem criados (Step 3). O template em si demonstra boas práticas de nulabilidade com TypeScript `?` para campos opcionais e comentários `// opcional` em JSON.

---

## 2. Inventário Completo

**Nenhum campo real encontrado.** A tabela abaixo documenta os campos identificados no template `PRP_TEMPLATE.md` como referência para futuros PRPs:

| PRP | Entidade | Campo | Tipo | Nulável? | Fallback | Status |
|---|---|---|---|---|---|---|
| TEMPLATE (API §5.1) | Request | `campo_obrigatorio` | string | NÃO | N/A | ✅ Explícito |
| TEMPLATE (API §5.1) | Request | `campo_opcional` | tipo | SIM | Não documentado | 🟡 FALLBACK AUSENTE |
| TEMPLATE (Component §6.1) | Props | `patientId` | string | NÃO | N/A | ✅ Explícito |
| TEMPLATE (Component §6.1) | Props | `onSave` | (data: FormData) => void | SIM (`?`) | Não documentado | 🟡 FALLBACK AUSENTE |
| TEMPLATE (Component §6.1) | Props | `readOnly` | boolean | SIM (`?`) | `default: false` | ✅ Completo |
| TEMPLATE (DB §7) | users | `id` | uuid | NÃO | N/A | ✅ Explícito |
| TEMPLATE (DB §7) | users | `email` | string | NÃO | N/A | ✅ Explícito |
| TEMPLATE (DB §7) | users | `password_hash` | string | NÃO | N/A | ✅ Explícito |
| TEMPLATE (DB §7) | users | `role` | enum | NÃO ESPECIFICADO | — | 🔴 NÃO ESPECIFICADO |
| TEMPLATE (DB §7) | users | `organization_id` | uuid | NÃO ESPECIFICADO | — | 🔴 NÃO ESPECIFICADO |

**Nota:** Os campos marcados como 🔴 e 🟡 acima referem-se ao template, não a PRPs reais. O template serve como guia de preenchimento e seus placeholders não representam decisões de design finalizadas.

---

## 3. Problemas Encontrados

### 3.1 Campos sem Especificação de Nulabilidade (🔴 Crítico)

**Nenhum em PRPs reais.** No template, os seguintes campos de exemplo não especificam nulabilidade:

| PRP | Entidade | Campo | Tipo Atual | Recomendação |
|---|---|---|---|---|
| TEMPLATE (DB §7) | users | `role` | `enum` | Adicionar `NOT NULL` ou `?` conforme regra de negócio |
| TEMPLATE (DB §7) | users | `organization_id` | `uuid` | Adicionar `NOT NULL` ou `?` conforme regra de negócio |

### 3.2 Campos Nuláveis sem Fallback (🟡 Alto)

**Nenhum em PRPs reais.** No template:

| PRP | Entidade | Campo | Tipo | Sugestão de Fallback |
|---|---|---|---|---|
| TEMPLATE (API §5.1) | Request | `campo_opcional` | tipo | Documentar valor default no contrato da API |
| TEMPLATE (Component §6.1) | Props | `onSave` | (data: FormData) => void | Documentar comportamento quando `undefined` (ex.: botão de save não renderiza) |

### 3.3 Inconsistências entre PRPs (🟡 Alto)

**Nenhuma.** Apenas um template existe, sem PRPs para comparar.

| Campo | PRP A | Definição A | PRP B | Definição B | Recomendação |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

### 3.4 Divergências com DATA_MODEL.md (🟢 Médio)

**Nenhuma.** `docs/architecture/DATA_MODEL.md` não existe.

| Campo | PRP | Definição PRP | DATA_MODEL.md | Recomendação |
|---|---|---|---|---|
| — | — | — | — | — |

---

## 4. Decisão do Gate

**Decisão:** **APROVADO** (sem PRPs para validar)

### Critérios
- [x] 0 campos sem especificação de nulabilidade (em PRPs reais)
- [x] 0 inconsistências entre PRPs
- [⚠] Não há PRPs para verificar fallbacks de campos nuláveis

### Bloqueios

Nenhum. O gate está aprovado.

**Observações:**
1. **Ausência de PRPs:** O diretório `docs/prps/` contém apenas `PRP_TEMPLATE.md`. Não há Product Requirements Pages para validar. Quando os PRPs forem criados (Step 3 do pipeline LLC), esta skill deve ser re-executada.
2. **Ausência de DATA_MODEL.md:** Não há modelo de dados canônico para validação de consistência entre PRPs. Recomenda-se criar `docs/architecture/DATA_MODEL.md` no Step 5.
3. **Template com boas práticas:** O `PRP_TEMPLATE.md` demonstra consciência de nulabilidade — usa TypeScript `?` para campos opcionais, comenta `// opcional` em JSON, e define `default: false` para `readOnly`. Essas práticas devem ser mantidas nos PRPs reais.

### Recomendações

1. **Criar PRPs (Step 3)** e re-executar `llc-step-12-null-safety` imediatamente após.
2. **Criar DATA_MODEL.md (Step 5)** para servir como referência canônica de nulabilidade.
3. **Adotar o padrão do template:**
   - TypeScript: usar `field?: type` para opcionais e `field: type | null` para explicitamente nulável
   - Python/Pydantic: usar `Optional[type] = None` com default explícito
   - Prisma: usar `Type?` para campos opcionais
   - Markdown tables: incluir coluna "Nulável" com SIM/NÃO
4. **Para cada campo nulável**, documentar o fallback (valor default, comportamento da UI, ou regra de negócio).
5. **Consultar `docs/planning/TASKS.md` §SEC-002** para o checklist completo de validação de null safety e gates por onda.

---

## 5. Fontes Analisadas

| Arquivo | Seção | Formato | Campos Encontrados |
|---|---|---|---|
| `docs/prps/PRP_TEMPLATE.md` | §5 API Contracts | JSON (template) | 2 campos de exemplo |
| `docs/prps/PRP_TEMPLATE.md` | §6 Component Spec | TypeScript interface | 3 props de exemplo |
| `docs/prps/PRP_TEMPLATE.md` | §7 Database Changes | Markdown table | 5 colunas de exemplo |
| `docs/architecture/DATA_MODEL.md` | — | — | Arquivo não existe |

---

## 6. Log de Execução

```
[2026-06-12] Iniciando validação de null safety (llc-step-12-null-safety)
[2026-06-12] Buscando PRPs em docs/prps/...
[2026-06-12] PRPs encontrados: 0
[2026-06-12] Arquivos no diretório: PRP_TEMPLATE.md (template, não é PRP)
[2026-06-12] Verificando DATA_MODEL.md... não encontrado
[2026-06-12] Verificando TESTING_GUIDE.md... não encontrado (apenas template)
[2026-06-12] Analisando PRP_TEMPLATE.md como referência de boas práticas...
[2026-06-12] Template usa TypeScript ? para opcionais — boa prática
[2026-06-12] Template usa comentários // opcional em JSON — boa prática
[2026-06-12] Template define default values (readOnly: false) — boa prática
[2026-06-12] 2 campos de exemplo sem especificação de nulabilidade (role, organization_id)
[2026-06-12] GATE: APROVADO — sem PRPs reais para validar
[2026-06-12] Validação concluída.
```

---

## 7. Assinaturas

| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Validador | llc-step-12-null-safety skill (automated) | 2026-06-12 | |
| Revisor (opcional) | — | — | |
