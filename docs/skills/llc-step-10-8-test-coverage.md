---
name: llc-step-10-8-test-coverage
description: Test Coverage Gate — verifica cobertura de testes antes da execução dos PRPs
version: 1.0.0
tags: [llc, pipeline, gate, testing, coverage, pre-execution]
---

# llc-step-10-8-test-coverage — Test Coverage Gate

## Objetivo
Executar verificação de cobertura de testes em nível de projeto **antes** da execução dos PRPs (Step 11). Garante que:
- Cobertura global ≥ 80% statements
- 0 arquivos de implementação sem cobertura (CRITICAL)
- Cobertura de branches ≥ 70%, functions ≥ 80%, lines ≥ 80%
- Caminhos críticos (auth, payments, data mutations) ≥ 90%

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-10-8-test-coverage` do pipeline LLC. Seu objetivo é realizar uma verificação completa de cobertura de testes no projeto e gerar um relatório consolidado com decisão do gate.

Esta verificação deve rodar **após** o Step 10 (Documentos do Projeto) e **antes** do Step 11 (Execução dos PRPs).

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack do projeto (Node.js/TypeScript, Python, Go, etc.)
- `docs/testing/TESTING_GUIDE.md` — comandos de teste e thresholds definidos no Step 9
- `docs/testing/COVERAGE_BASELINE.md` — baseline de cobertura (se existir)
- `package.json` / `pyproject.toml` / `go.mod` — dependências e scripts de teste

---

### 2. Execute a Verificação de Cobertura

#### 2.1 Detecção de Stack e Comando de Teste

```bash
# Detecta stack
if [[ -f "package.json" ]]; then
    STACK="typescript"
    # Tenta vitest, jest, ou npm test
    if grep -q '"vitest"' package.json; then
        TEST_CMD="npx vitest run --coverage --reporter=json --outputFile=coverage/coverage-final.json"
    elif grep -q '"jest"' package.json; then
        TEST_CMD="npx jest --coverage --coverageReporters=json --coverageDirectory=coverage --outputFile=coverage/coverage-final.json"
    else
        TEST_CMD="npm test -- --coverage --coverageReporters=json --coverageDirectory=coverage --outputFile=coverage/coverage-final.json"
    fi
elif [[ -f "pyproject.toml" ]]; then
    STACK="python"
    TEST_CMD="python -m pytest --cov --cov-report=json:coverage/coverage-final.json"
elif [[ -f "go.mod" ]]; then
    STACK="go"
    TEST_CMD="go test -coverprofile=coverage/coverage-final.out ./... && go tool cover -func=coverage/coverage-final.out"
else
    echo "❌ Stack não reconhecido. Adicione suporte em llc-step-10-8-test-coverage.md"
    exit 1
fi
```

#### 2.2 Execução dos Testes com Cobertura

```bash
mkdir -p coverage
echo "Executando: $TEST_CMD"
eval "$TEST_CMD"
TEST_EXIT_CODE=$?
```

> **Nota:** Se os testes falharem (`TEST_EXIT_CODE != 0`), o gate é **REPROVADO** imediatamente — não há cobertura se os testes não passam.

#### 2.3 Análise do Relatório de Cobertura

**Para TypeScript/JavaScript (vitest/jest - formato JSON):**

```bash
# O arquivo coverage/coverage-final.json contém dados por arquivo
# Exemplo de estrutura:
# { "src/file.ts": { "s": { "1": 5, "2": 0 }, "f": {...}, "b": {...}, "l": {...} } }
```

**Para Python (pytest-cov - formato JSON):**
```bash
# coverage/coverage-final.json com estrutura similar
```

**Para Go:**
```bash
# Converter coverage-final.out para JSON se necessário
```

---

### 3. Verificações de Gate (Bloqueantes)

#### 3.1 CRITICAL — Testes Falharam
```bash
if [[ $TEST_EXIT_CODE -ne 0 ]]; then
    GATE_DECISION="REPROVADO"
    CRITICAL_ISSUES+=("Testes falharam (exit code: $TEST_EXIT_CODE). Coverage inválido.")
fi
```

#### 3.2 CRITICAL — Arquivos de Implementação sem Cobertura (0%)
```bash
# Para cada arquivo de implementação (não teste, não config, não types):
#   se statements_covered == 0 E statements_total > 0:
#     CRITICAL_ISSUES+=("Arquivo sem cobertura: $file")
```

#### 3.3 CRITICAL — Cobertura Global Abaixo do Threshold
```bash
# statements_pct < 80%
# branches_pct < 70%
# functions_pct < 80%
# lines_pct < 80%
```

#### 3.4 CRITICAL — Caminhos Críticos Abaixo de 90%
```bash
# Identifica arquivos em caminhos críticos:
# - auth/*, security/*, payment/*, billing/*
# - models/*, repositories/*, services/* com mutação de dados
# Verifica se coverage >= 90% para esses arquivos
```

---

### 4. Gere o Relatório Consolidado

Preencha `docs/testing/COVERAGE_REPORT.md` com:

```markdown
# Test Coverage Gate Report — {{DATE}}

## Resumo Executivo
- **Gate Decision:** {{APROVADO|REPROVADO}}
- **Stack:** {{STACK}}
- **Comando de teste:** `{{TEST_CMD}}`
- **Exit code dos testes:** {{TEST_EXIT_CODE}}

## Métricas Globais
| Métrica | Valor | Threshold | Status |
|---------|-------|-----------|--------|
| Statements | {{X}}% | ≥ 80% | {{OK|FAIL}} |
| Branches | {{X}}% | ≥ 70% | {{OK|FAIL}} |
| Functions | {{X}}% | ≥ 80% | {{OK|FAIL}} |
| Lines | {{X}}% | ≥ 80% | {{OK|FAIL}} |

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
| Arquivo | Statements | Branches | Functions | Lines | Threshold |
|---------|------------|----------|-----------|-------|-----------|
{{#each LOW_COVERAGE_FILES}}
| {{file}} | {{stmt}}% | {{br}}% | {{fn}}% | {{ln}}% | statements≥80% |
{{/each}}

## Caminhos Críticos (Threshold: 90%)
| Arquivo | Statements | Status |
|---------|------------|--------|
{{#each CRITICAL_PATH_FILES}}
| {{file}} | {{stmt}}% | {{#if (gte stmt 90)}}✅{{else}}⛔{{/if}} |
{{/each}}

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
```

---

### 5. Regras Críticas (Anti-Alucinação)

- **Sempre ler output real:** Execute os comandos, leia os arquivos JSON gerados. Nunca invente métricas.
- **Thresholds vêm do TESTING_GUIDE.md:** Se o Step 9 definiu thresholds diferentes, use os definidos lá.
- **Baseline do Step 9:** Compare com `COVERAGE_BASELINE.md` para detectar regressões e arquivos novos.
- **Falsos positivos:** Arquivos de configuração (`*.config.ts`, `*.d.ts`), mocks, testes, e tipos NÃO contam como "implementação sem cobertura".
- **Idempotência:** Re-execução sobrescreve `coverage/` e `docs/testing/COVERAGE_REPORT.md`.
- **Gate bloqueante:** Qualquer CRITICAL ⇒ `REPROVADO`. Pipeline não avança para Step 11 até correção.

---

### 6. Output Esperado

```
coverage/
├── coverage-final.json     # Output bruto do vitest/jest/pytest-cov
├── lcov.info              # Para integração CI (Codecov, SonarQube)
└── index.html             # Relatório HTML (opcional, se gerado)

docs/testing/
└── COVERAGE_REPORT.md      # Relatório consolidado com decisão do gate
```

---

### 7. Ações Pós-Execução

- Se **APROVADO:** Avance para Step 11 (Execução dos PRPs).
- Se **REPROVADO:**
  - Para arquivos sem cobertura: Exija criação de testes antes de prosseguir.
  - Para cobertura global baixa: Identifique gaps e exija testes adicionais.
  - Para caminhos críticos: Priorize testes em auth, payments, data mutations.
  - Re-execute este step após correções.

---

## Template do Relatório (COVERAGE_REPORT_TEMPLATE.md)

Crie `docs/testing/COVERAGE_REPORT_TEMPLATE.md` baseado na estrutura da seção 4 acima, com placeholders `{{...}}` para preenchimento automático.