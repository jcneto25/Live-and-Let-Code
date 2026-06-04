---
name: llc-step-9
description: Pipeline LLC Passo 9: Gera documentação de testes (Guia, Baseline e Progresso) a partir dos templates de testing.
version: 1.0.0
tags: [testing, quality, coverage, llc-pipeline]
---

# LLC Skill: Step 9 — Documentação de Testes

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Quality Foundation  
**Depende de:** Step 5 (Arquitetura — stack e ferramentas), Step 8 (Camada Mock), Subfluxo de Prototipagem  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-9` ou "Execute a skill llc-step-9".

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack e ferramentas de teste (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas priorizadas (Step 6)
- [ ] `docs/prps/PRP-*.md` — PRPs com estratégias de teste individuais (Step 3)
- [ ] `mocks/` — camada mock configurada para testes (Step 8)
- [ ] `docs/testing/TESTING_GUIDE_TEMPLATE.md`
- [ ] `docs/testing/COVERAGE_BASELINE_TEMPLATE.md`
- [ ] `docs/testing/COVERAGE_PROGRESS_TEMPLATE.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-9` do pipeline LLC. Seu objetivo é gerar a documentação de testes do projeto, estabelecendo padrões, baseline de cobertura e metas de progresso.

### Documentos a Gerar

| # | Documento | Template | Destino |
|---|-----------|----------|---------|
| 1 | Guia de Testes | `docs/testing/TESTING_GUIDE_TEMPLATE.md` | `docs/testing/TESTING_GUIDE.md` |
| 2 | Baseline de Cobertura | `docs/testing/COVERAGE_BASELINE_TEMPLATE.md` | `docs/testing/COVERAGE_BASELINE.md` |
| 3 | Progresso de Cobertura | `docs/testing/COVERAGE_PROGRESS_TEMPLATE.md` | `docs/testing/COVERAGE_PROGRESS.md` |

### 1. Leia as Entradas

- `docs/testing/TESTING_GUIDE_TEMPLATE.md` — estrutura do guia de testes.
- `docs/testing/COVERAGE_BASELINE_TEMPLATE.md` — estrutura da baseline.
- `docs/testing/COVERAGE_PROGRESS_TEMPLATE.md` — estrutura do progresso.
- `docs/architecture/ARCHITECTURE.md` — stack (Jest/Vitest, Playwright/Cypress, testing libraries).
- `docs/prps/PRP-*.md` — PRPs para extrair requisitos de teste por módulo.
- `docs/planning/TASKS.md` — tarefas de teste já planejadas.

### 2. Gere o Guia de Testes (TESTING_GUIDE.md)

Preencha o template com:

#### Filosofia e Pirâmide de Testes
- Defina a pirâmide: unitários (base) → integração → E2E (topo).
- Proporção recomendada: 60% unitários, 30% integração, 10% E2E.

#### TDD — Red, Green, Refactor
- Explique o ciclo TDD com exemplos práticos no stack do projeto.
- Inclua prompts de IA para gerar testes (service, controller, component, hook).
- Liste red flags para IA: mockar o que está sendo testado, testar implementação em vez de comportamento.

#### Setup por Aplicação
- **Backend:** Framework de teste (Jest/Vitest), mock library, supertest, Prisma/ORM test setup.
- **Frontend:** Vitest + React Testing Library + MSW + jest-axe.
- Inclua configurações reais (arquivos de config) adaptados ao stack do projeto.

#### Templates de Teste
- Template para teste de serviço backend (completo, pronto para copiar).
- Template para teste de controller/rota.
- Template para teste de componente frontend com MSW.
- Template para teste de hook.
- Template para teste E2E (Playwright/Cypress).

#### Estratégia de Mocks
- Quando mockar Prisma/ORM vs. usar banco real vs. teste de integração.
- Como usar os handlers de `mocks/handlers/` nos testes.

#### Acessibilidade (a11y)
- Setup do jest-axe.
- Testes automatizados e manuais.
- Checklist de acessibilidade.

#### Gestão de Dados de Teste
- Factories (faker-based) para gerar dados realistas.
- Multi-tenancy nos testes.
- Limpeza de banco entre testes.

#### CI/CD e Quality Gates
- Pipeline de CI (GitHub Actions ou equivalente).
- Gates: lint, type-check, testes unitários, cobertura, testes E2E.
- Thresholds: unitários ≥ 80%, integração ≥ 70%, E2E fluxos críticos.

#### Troubleshooting
- Problemas comuns e soluções específicas para o stack.

### 3. Gere a Baseline de Cobertura (COVERAGE_BASELINE.md)

Preencha o template com:

#### Como Estabelecer a Baseline
- Comandos exatos para gerar relatório de cobertura (adaptados ao stack).
- Scripts npm: `test:api:coverage`, `test:web:coverage`, `test:coverage`.

#### Baseline por Aplicação
- Estrutura de tabela: Statements, Branches, Functions, Lines.
- Valores iniciais como 0% (a baseline é estabelecida na primeira execução de testes).
- Colunas para known failures e known skips (vazias inicialmente).

#### Infraestrutura de Teste
- Status de cada ferramenta: Jest/Vitest, MSW, Playwright, jest-axe.
- Comandos de execução documentados.

#### Baseline Consolidada
- Tabela comparativa entre aplicações (API, Web, Mobile se houver).
- Issues por severidade (vazio inicialmente).
- Lista de ações prioritárias.

### 4. Gere o Progresso de Cobertura (COVERAGE_PROGRESS.md)

Preencha o template com:

#### Metas por Fase
- Fase 1 (MVP): unitários ≥ 80%, integração ≥ 70%.
- Fase 2 (Pós-MVP): unitários ≥ 85%, integração ≥ 75%, E2E fluxos críticos.
- Fase 3 (Produção): unitários ≥ 90%, integração ≥ 80%, E2E ≥ 60%.

#### Como Atualizar
- Passo a passo semanal.
- Comandos para medir cobertura.
- O que documentar.

#### Tabela de Progresso Semanal
- Semana 1 em branco (a ser preenchida após primeira execução).
- Colunas: Semana, Data, API (lines%, branches%), Web (lines%, branches%), Status, Notas.

#### Quality Gates por Ambiente
- Dev: lint + type-check.
- Staging: unitários ≥ 80% + integração ≥ 70%.
- Prod: unitários ≥ 90% + integração ≥ 80% + E2E críticos + security audit.

### 5. Integração com o Planejamento

- Vincule os thresholds de cobertura às Definition of Done dos PRPs.
- Referencie `docs/testing/TESTING_GUIDE.md` nas tarefas de teste do TASKS.md.
- Adicione tarefas de setup de infraestrutura de teste se ainda não existirem.

---

## ⚠️ REGRAS CRÍTICAS

1. **Stack-aware:** Todos os comandos, configurações e exemplos devem usar as ferramentas exatas definidas em `ARCHITECTURE.md`.
2. **Pronto para usar:** Templates de teste devem ser completos — copiar, colar, adaptar o nome da função.
3. **Thresholds realistas:** Use os valores padrão do LLC (80% unitários, 70% integração).
4. **Baseline é ponto zero:** COVERAGE_BASELINE.md começa com 0%. Os números reais virão da execução.
5. **Progresso é vivo:** COVERAGE_PROGRESS.md será atualizado semanalmente pela equipe/agentes.
6. **Idempotência:** Verifique existência dos arquivos de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os 3 documentos, **PARE** e apresente:

1. **TESTING_GUIDE.md:** Estrutura gerada — seções, templates de teste incluídos, comandos documentados.
2. **COVERAGE_BASELINE.md:** Estrutura pronta para primeira medição.
3. **COVERAGE_PROGRESS.md:** Metas por fase e estrutura da tabela de progresso.
4. **Integração:** Quais tarefas em TASKS.md foram vinculadas aos thresholds de cobertura?
5. **Próximos Passos:** "Execute `npm test:coverage` para estabelecer a baseline inicial de cobertura."

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
