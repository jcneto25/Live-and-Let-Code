# Coverage Baseline — Baseline de Cobertura de Testes

> **Versão:** {X.Y} | **Criado em:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD}
> **Projeto:** {Nome do Projeto} | **Autor:** {QA Lead / Tech Lead}
> **Referências:** `{Comprehensive Testing Guide}`, `{Coverage Progress}`, `{CI/CD Pipeline}`

---

## 📋 Checklist Pré-Preenchimento

Antes de estabelecer o baseline:
- [ ] Comprehensive Testing Guide aprovado e seguido
- [ ] Infraestrutura de testes configurada (Jest, Vitest, MSW, jest-axe)
- [ ] Comando de cobertura testado e funcionando para TODAS as apps
- [ ] Primeira execução de `npm run test:cov` realizada com sucesso
- [ ] Resultados de cobertura extraídos de todos os apps
- [ ] Issues conhecidos documentados (falhas esperadas, skips, etc.)
- [ ] Time alinhado sobre o que o baseline representa (ponto de partida, não meta)

---

## 1. Visão Geral

### 1.1 Propósito
Este documento estabelece o **ponto zero** da cobertura de testes do projeto. Ele serve para:
- **Medir** a situação atual antes de iniciar melhorias sistemáticas
- **Comparar** progresso futuro contra este ponto de referência
- **Identificar** gaps críticos desde o início (módulos sem testes, infra quebrada)
- **Documentar** issues conhecidos que afetam a medição
- **Servir como contrato** com stakeholders sobre estado inicial de qualidade

> **Exemplo (NeuroHub):** *"Baseline estabelecido em 2026-03-18. API: 7.97% lines, Web: 0%, Mobile: 0%. Infraestrutura de testes completa, mas testes ainda sendo escritos. Issues conhecidos: controller signature mismatches, Prisma 7 setup pendente, Babel parser errors no mobile."*

### 1.2 O que é o Baseline?

O baseline **NÃO é uma meta**. É uma fotografia honesta do estado atual:

| Aspecto | Baseline | Meta (Phase 3) |
|---------|----------|----------------|
| **Propósito** | Medir ponto de partida | Definir mínimo aceitável |
| **Quando** | Início do projeto / Início de fase de qualidade | A cada release |
| **Ação** | Documentar, não julgar | Bloquear se abaixo |
| **Comunicação** | "Estamos aqui" | "Precisamos estar lá" |

> **💡 Regra:** Nunca esconder números baixos. Um baseline de 0% com infraestrutura pronta é mais honesto e útil que um baseline de 30% com testes irrelevantes.

---

## 2. Como Estabelecer o Baseline

### 2.1 Passos Obrigatórios

```bash
# 1. Garanta que a infra de testes está configurada
#    (Jest, Vitest, MSW, jest-axe, factories, mocks, templates)

# 2. Execute cobertura para TODAS as apps
npm run test:cov

# 3. Se falhar, execute individualmente para diagnosticar

# === API ===
cd apps/api
npm run test:cov
# Extrair: Statements, Branches, Functions, Lines
# Extrair: Test suites (passed/failed/skipped)
# Extrair: Tests (passed/failed/skipped)
# Documentar: Falhas conhecidas, razões, skips

# === Web ===
cd apps/web
npx vitest run --coverage
# ou
npm run test:cov
# Extrair: Statements, Branches, Functions, Lines
# Extrair: Test suites e tests
# Documentar: Falhas, MSW status, jest-axe status

# === Mobile ===
cd apps/mobile
npx jest --coverage
# ou
npm run test:cov
# Extrair: Statements, Branches, Functions, Lines
# Extrair: Test suites e tests
# Documentar: Babel/RN config issues, skips
```

### 2.2 Comando Unificado (Root)

```bash
# Todas as apps
npm run test:cov

# Apenas API
npm run test:cov --workspace=api

# Apenas Web
npm run test:cov --workspace=web

# Apenas Mobile
npm run test:cov --workspace=mobile
```

### 2.3 O que Documentar

Para cada app, documente:

| Item | Descrição | Onde encontrar |
|------|-----------|----------------|
| **Statements** | % de statements executados | `coverage/lcov-report/index.html` ou `coverage-summary.json` |
| **Branches** | % de ramificações cobertas | Mesmo local |
| **Functions** | % de funções chamadas | Mesmo local |
| **Lines** | % de lin físicas executadas | Mesmo local — **métrica principal** |
| **Suites** | Total, passed, failed, skipped | Saída do console |
| **Tests** | Total, passed, failed, skipped | Saída do console |
| **Falhas** | Quais testes falham e por quê | Saída do console + investigação |
| **Skips** | Quais testes são skipados e por quê | Código fonte (`it.skip`, `describe.skip`) |
| **Exclusões** | O que está excluído da cobertura | `jest.config.ts` / `vitest.config.ts` (exclude) |

---

## 3. Baseline por Aplicação

> **⚠️ ATENÇÃO: Preencha TODAS as colunas. Não omitir métricas mesmo que sejam 0%.**
> **Documente falhas e skips com honestidade — elas são parte do baseline.**

---

### 3.1 API Baseline (`apps/api/`)

> **Estabelecido:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD}

| Métrica | Baseline ({Data inicial}) | Atual ({Data mais recente}) | Delta | Meta (Phase 3) | Status |
|---------|---------------------------|----------------------------|-------|----------------|--------|
| **Statements** | {X%} ({executados}/{total}) | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |
| **Branches** | {X%} ({executados}/{total}) | {X%} | {+/-Ypp} | ≥ 70% | {🟢/🟡/🔴} |
| **Functions** | {X%} ({executados}/{total}) | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |
| **Lines** | {X%} ({executados}/{total}) | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |

**Test Suites:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Tests:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Falhas Conhecidas:**

| Arquivo | Falhas | Razão | Impacto na Cobertura | Ação | Prazo |
|---------|--------|-------|---------------------|------|-------|
| {patients.controller.spec.ts} | {4} | {Controller signature mismatch — método mudou mas teste não} | {Alto — controller não coberto} | {Atualizar teste para nova signature} | {Semana X} |
| {users.controller.spec.ts} | {2} | {Mesmo que acima} | {Alto} | {Atualizar teste} | {Semana X} |

**Skips Conhecidos:**

| Arquivo | Tests Skipados | Razão | Impacto | Ação | Prazo |
|---------|---------------|-------|---------|------|-------|
| {prisma.service.spec.ts} | {5} | {Prisma 7 requer setup especial de adapter} | {Médio — service de DB não testado} | {Configurar PrismaPg adapter em testes} | {Semana X} |

**Exclusões de Cobertura:**
- {Ex: `prisma/generated/` — código gerado}
- {Ex: `test-helpers/` — código de teste}
- {Ex: `*.dto.ts` — DTOs são validação, não lógica}

**Notas:**
- {Ex: Coverage exclui Prisma client gerado}
- {Ex: Factories e mocks não contam para cobertura}
- {Ex: Testes de controller falham devido a mudanças de signature — não de lógica}

---

### 3.2 Web Baseline (`apps/web/`)

> **Estabelecido:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD}

| Métrica | Baseline ({Data inicial}) | Atual ({Data mais recente}) | Delta | Meta (Phase 3) | Status |
|---------|---------------------------|----------------------------|-------|----------------|--------|
| **Statements** | {X%} | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |
| **Branches** | {X%} | {X%} | {+/-Ypp} | ≥ 70% | {🟢/🟡/🔴} |
| **Functions** | {X%} | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |
| **Lines** | {X%} | {X%} | {+/-Ypp} | ≥ 80% | {🟢/🟡/🔴} |

**Test Suites:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Tests:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Falhas Conhecidas:**

| Arquivo | Falhas | Razão | Impacto | Ação | Prazo |
|---------|--------|-------|---------|------|-------|
| {patients/[id]/pei/index.test.tsx} | {1} | {Mock assertion issue — mock não está sendo chamado como esperado} | {Baixo — página testada indiretamente} | {Revisar mock de hook} | {Semana X} |

**Skips Conhecidos:**
- {Nenhum / Listar se houver}

**Componentes/Páginas Cobertos:**
- {Ex: Hooks: useUsers, useGoals, usePatients}
- {Ex: Components: AnalyticsDashboard, PEITree, PatientsList, UsersList, TaskAnalysisForm}
- {Ex: Pages: dashboard/index, dashboard/users, dashboard/patients, dashboard/patients/[id]/pei}

**Componentes/Páginas NÃO Cobertos:**
- {Ex: LoginPage (0%) — aguardando refactor de auth}
- {Ex: InviteAcceptPage — nova, testes pendentes}

**Infraestrutura:**
- {Ex: MSW: ✅ Configurado e funcionando}
- {Ex: jest-axe: ✅ Setup completo}
- {Ex: Vitest: ✅ Configurado, mas workers timeout resolvido na Semana 5}

**Notas:**
- {Ex: MSW + jest-axe infraestrutura em place}
- {Ex: Vitest coverage command falhava por workers timeout — resolvido com Option A (reduzir workers)}

---

### 3.3 Mobile Baseline (`apps/mobile/`)

> **Estabelecido:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD}

| Métrica | Baseline ({Data inicial}) | Atual ({Data mais recente}) | Delta | Meta (Phase 3) | Status |
|---------|---------------------------|----------------------------|-------|----------------|--------|
| **Statements** | {X%} | {X%} | {+/-Ypp} | ≥ 60% | {🟢/🟡/🔴} |
| **Branches** | {X%} | {X%} | {+/-Ypp} | ≥ 50% | {🟢/🟡/🔴} |
| **Functions** | {X%} | {X%} | {+/-Ypp} | ≥ 60% | {🟢/🟡/🔴} |
| **Lines** | {X%} | {X%} | {+/-Ypp} | ≥ 60% | {🟢/🟡/🔴} |

**Test Suites:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Tests:**
- Total: {N}
- Passed: {N}
- Failed: {N}
- Skipped: {N}

**Falhas Conhecidas:**

| Arquivo | Falhas | Razão | Impacto | Ação | Prazo |
|---------|--------|-------|---------|------|-------|
| {Todas as suites} | {4 suites} | {Babel parser errors — React Native setup com Jest} | {Crítico — nenhum teste roda} | {Investigar config Babel/Jest para RN} | {Semana X} |

**Screens com Testes (mas falhando):**
- {Ex: DailyLogFormScreen — testes escritos, não rodam}
- {Ex: PLACHECKScreen — testes escritos, não rodam}
- {Ex: SessionScreen — testes escritos, não rodam}

**Infraestrutura:**
- {Ex: Jest: ✅ Instalado}
- {Ex: @testing-library/react-native: ✅ Instalado}
- {Ex: MSW: ✅ Instalado, mas não configurado para RN}
- {Ex: Babel: ⚠️ Configuração pendente para parser}

**Notas:**
- {Ex: Testing infrastructure in place, mas Babel parser errors impedem execução}
- {Ex: MSW infraestrutura em place, mas precisa de configuração específica para RN}
- {Ex: Prioridade: resolver Babel config antes de escrever mais testes}

---

## 4. Resumo Consolidado

### 4.1 Comparativo por App

| App | Baseline Lines | Atual Lines | Delta | Meta Phase 3 | Gap para Meta | Status |
|-----|---------------|-------------|-------|--------------|---------------|--------|
| **API** | {X%} | {Y%} | {+/-Zpp} | 80% | {80% - Y%} | {🟢/🟡/🔴} |
| **Web** | {X%} | {Y%} | {+/-Zpp} | 80% | {80% - Y%} | {🟢/🟡/🔴} |
| **Mobile** | {X%} | {Y%} | {+/-Zpp} | 60% | {60% - Y%} | {🟢/🟡/🔴} |

### 4.2 Análise de Issues por Severidade

| Severidade | Count | Apps Afetadas | Issues | Ação Imediata |
|------------|-------|---------------|--------|---------------|
| **Crítico** | {N} | {Mobile} | {Babel parser — nenhum teste roda} | {Investigar config RN/Jest} |
| **Alto** | {N} | {API} | {Controller signature mismatches} | {Atualizar testes} |
| **Médio** | {N} | {API} | {Prisma 7 setup skipped} | {Configurar adapter} |
| **Baixo** | {N} | {Web} | {Mock assertion issue} | {Revisar mock} |

### 4.3 Prioridade de Ação

| # | Ação | App | Impacto | Esforço | Prioridade | Owner | Prazo |
|---|------|-----|---------|---------|------------|-------|-------|
| 1 | {Resolver Babel parser errors} | Mobile | {Crítico — bloqueia todos os testes} | {Alto} | {P0} | {Mobile Dev} | {Semana 1} |
| 2 | {Atualizar controller tests} | API | {Alto — gaps de cobertura} | {Baixo} | {P1} | {Backend Dev} | {Semana 1} |
| 3 | {Configurar Prisma 7 adapter} | API | {Médio — service não testado} | {Médio} | {P1} | {Backend Dev} | {Semana 2} |
| 4 | {Revisar mock assertion} | Web | {Baixo — 1 teste falhando} | {Baixo} | {P2} | {Frontend Dev} | {Semana 2} |
| 5 | {Adicionar testes para LoginPage} | Web | {Médio — página não coberta} | {Médio} | {P2} | {Frontend Dev} | {Semana 3} |

---

## 5. Infraestrutura de Testes no Baseline

### 5.1 Status da Infra por App

| Componente | API | Web | Mobile | Status Geral |
|------------|-----|-----|--------|--------------|
| **Test Runner** | Jest ✅ | Vitest ✅ | Jest ✅ | ✅ |
| **Factories** | ✅ | ✅ | ⚠️ | 🟡 |
| **Mocks (Auth/DB)** | ✅ | ✅ | ⚠️ | 🟡 |
| **MSW** | N/A | ✅ | ⚠️ | 🟡 |
| **jest-axe** | N/A | ✅ | N/A | ✅ |
| **RTL** | N/A | ✅ | ✅ | ✅ |
| **Templates** | ✅ | ✅ | ✅ | ✅ |
| **CI/CD** | ✅ | ✅ | ✅ | ✅ |
| **Coverage Report** | ✅ | ✅ | ⚠️ | 🟡 |
| **Docker Test DB** | ✅ | N/A | N/A | ✅ |

### 5.2 Comandos de Cobertura

```bash
# === Todas as apps ===
npm run test:cov

# === API ===
cd apps/api
npm run test:cov
# Gera: coverage/lcov-report/index.html
# Gera: coverage/coverage-summary.json

# === Web ===
cd apps/web
npm run test:cov
# ou
npx vitest run --coverage
# Gera: coverage/index.html
# Gera: coverage/coverage-summary.json

# === Mobile ===
cd apps/mobile
npx jest --coverage
# ou
npm run test:cov
# Gera: coverage/lcov-report/index.html
```

---

## 6. Issues e Débito Técnico no Baseline

### 6.1 Issues que Afetam a Medição

| ID | Issue | App | Tipo | Impacto na Medição | Ação | Prazo |
|----|-------|-----|------|-------------------|------|-------|
| BL-001 | {Babel parser errors} | Mobile | {Infra} | {Mobile baseline = 0% — não reflete código não testado, mas sim infra quebrada} | {Fix Babel config} | {Semana 1} |
| BL-002 | {Controller signature mismatch} | API | {Código} | {Baseline subestima cobertura real — testes existem mas falham} | {Atualizar tests} | {Semana 1} |
| BL-003 | {Prisma 7 adapter} | API | {Infra} | {Baseline subestima — tests skipados} | {Configurar adapter} | {Semana 2} |
| BL-004 | {Vitest workers timeout} | Web | {Infra} | {Baseline não medível até Semana 5} | {Reduzir workers} | {Resolvido} |

### 6.2 Débito Técnico Identificado no Baseline

| ID | Débito | Origem | Impacto | Onda de Pagamento | Status |
|----|--------|--------|---------|-------------------|--------|
| DT-BASE-001 | {Mobile sem testes executáveis} | {Baseline} | {Crítico — não se sabe qualidade real} | {Semana 1-2} | {🔴} |
| DT-BASE-002 | {API controller tests desatualizados} | {Refactor} | {Alto — cobertura subestimada} | {Semana 1} | {🟡} |
| DT-BASE-003 | {Prisma service não testado} | {Prisma 7 migration} | {Médio — gap de confiança} | {Semana 2} | {🟡} |
| DT-BASE-004 | {Web LoginPage não coberta} | {Priorização} | {Médio — fluxo crítico não testado} | {Semana 3} | {🟡} |

---

## 7. Anexos

### Anexo A: Gráfico de Baseline vs. Atual

```mermaid
xychart-beta
    title "Coverage: Baseline vs. Atual"
    x-axis ["API", "Web", "Mobile"]
    y-axis "Coverage %" 0 --> 100
    bar [10, 0, 0]
    bar [82, 60, 0]
    legend "Baseline", "Atual"
```

### Anexo B: Breakdown por Módulo (API — Baseline)

| Módulo | Lines | Testes Escritos | Executando | Status no Baseline |
|--------|-------|-----------------|------------|-------------------|
| auth | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| users | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| patients | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| goals | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| daily-logs | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| sync | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| analytics | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| reports | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| audit | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| feedback-dimensions | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |
| invites | {X%} | {Sim/Não} | {Sim/Não} | {🟢/🟡/🔴} |

### Anexo C: Exemplo de Saída de Cobertura (Console)

```
# Exemplo de saída do console (API — Jest)

Test Suites: 19 passed, 2 failed, 1 skipped (22 total)
Tests:       127 passed, 6 failed, 5 skipped (138 total)

Coverage summary
Statements   : 10% (36/355)
Branches     : 3.48% (2/58)
Functions    : 6.25% (1/16)
Lines        : 7.97% (25/314)
```

```
# Exemplo de saída do console (Web — Vitest)

Test Files  8 passed, 1 failed (9)
     Tests  53 passed, 1 failed (54)

 % Coverage report from v8
Statements   : 0%
Branches     : 0%
Functions    : 0%
Lines        : 0%
```

```
# Exemplo de saída do console (Mobile — Jest)

Test Suites: 4 failed (4 total)
Tests:       0 passed, 0 failed (0 total)

# Erro: Babel parser error in React Native setup
```

---

## 📌 Revisões do Documento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 0.1 | {YYYY-MM-DD} | {Autor} | Baseline inicial estabelecido |
| 0.2 | {YYYY-MM-DD} | {Autor} | Atualizado com novas medições |
| 1.0 | {YYYY-MM-DD} | {Autor} | Baseline estabilizado, issues documentados |

---

## ✅ Checklist de Manutenção do Baseline

- [ ] Re-mediar baseline a cada grande milestone (MVP, Release 1.0, etc.)
- [ ] Atualizar coluna "Atual" quando houver mudança significativa
- [ ] Documentar novas falhas/skips imediatamente
- [ ] Revisar issues que afetam medição a cada sprint
- [ ] Atualizar infraestrutura quando ferramentas mudam
- [ ] Arquivar baseline antigo quando novo baseline é estabelecido
- [ ] Comunicar baseline a stakeholders no início de cada fase

---

> **Nota:** Este documento é a fotografia do ponto zero. Não julgue — documente. A versão no repositório (`docs/testing/coverage-baseline.md`) é a referência oficial. Para acompanhamento contínuo, consulte `docs/testing/coverage-progress.md`. Para estratégia de testes, consulte `docs/testing/comprehensive-testing-guide.md`.
