# Test Coverage Gate Report — {{DATE}}

## Resumo Executivo
- **Gate Decision:** {{GATE_DECISION}}
- **Stack:** {{STACK}}
- **Comando de teste:** `{{TEST_CMD}}`
- **Exit code dos testes:** {{TEST_EXIT_CODE}}

## Métricas Globais
| Métrica | Valor | Threshold | Status |
|---------|-------|-----------|--------|
| Statements | {{STATEMENTS_PCT}}% | ≥ 80% | {{STATEMENTS_STATUS}} |
| Branches | {{BRANCHES_PCT}}% | ≥ 70% | {{BRANCHES_STATUS}} |
| Functions | {{FUNCTIONS_PCT}}% | ≥ 80% | {{FUNCTIONS_STATUS}} |
| Lines | {{LINES_PCT}}% | ≥ 80% | {{LINES_STATUS}} |

## Arquivos sem Cobertura (CRITICAL)
{{#if UNCOVERED_FILES}}
| Arquivo | Statements | Status |
|---------|------------|--------|
{{#each UNCOVERED_FILES}}
| {{this}} | 0% | ⛔ CRITICAL |
{{/each}}
{{else}}
✅ Nenhum arquivo de implementação sem cobertura.
{{/if}}

## Arquivos com Cobertura Baixa (WARN)
{{#if LOW_COVERAGE_FILES}}
| Arquivo | Statements | Branches | Functions | Lines | Threshold |
|---------|------------|----------|-----------|-------|-----------|
{{#each LOW_COVERAGE_FILES}}
| {{file}} | {{stmt}}% | {{br}}% | {{fn}}% | {{ln}}% | statements≥80% |
{{/each}}
{{else}}
✅ Nenhum arquivo com cobertura baixa detectado.
{{/if}}

## Caminhos Críticos (Threshold: 90%)
{{#if CRITICAL_PATH_FILES}}
| Arquivo | Statements | Status |
|---------|------------|--------|
{{#each CRITICAL_PATH_FILES}}
| {{file}} | {{stmt}}% | {{#if (gte stmt 90)}}✅{{else}}⛔{{/if}} |
{{/each}}
{{else}}
Nenhum caminho crítico identificado (projeto sem auth/payments/data-mutations).
{{/if}}

## Novos Arquivos (desde baseline)
{{#if NEW_FILES}}
| Arquivo | Cobertura | Obrigatório? |
|---------|-----------|--------------|
{{#each NEW_FILES}}
| {{file}} | {{coverage}}% | {{#if (lt coverage 80)}}SIM (CRITICAL){{else}}OK{{/if}} |
{{/each}}
{{else}}
Nenhum arquivo novo detectado desde baseline.
{{/if}}

## Recomendações
{{#each RECOMMENDATIONS}}
- {{this}}
{{/each}}

---

*Gerado automaticamente por `llc-step-10-8-test-coverage` — {{TIMESTAMP}}*