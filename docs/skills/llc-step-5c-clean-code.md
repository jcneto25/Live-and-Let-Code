---
name: llc-step-5c-clean-code
description: Pipeline LLC Step 5c — Clean Code Enforcement consolidando Functions, Classes, Naming, Errors, Smells, ReadModels. Baseado em Clean Code (R. Martin), Clean Architecture, Software Design & Architecture (Stemmler). Executa 21+ fitness functions automatizadas.
version: 1.0.0
tags: [clean-code, functions, classes, naming, errors, smells, readmodels, solid, dip, srp, llc-pipeline, code-quality]
---

# LLC Skill: Step 5c — Clean Code Enforcement

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Architecture (sub-step of Step 5 — after Step 5b API Design Enforcement)  
**Depende de:** Step 5b (API Design Enforcement validado)  
**Executa antes de:** Step 6 (Tasks) e Step 8 (Setup + Mock)  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5c-clean-code` ou "Execute a skill llc-step-5c-clean-code".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 5c --task "Enforcar Clean Code"`.

---

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — overview arquitetural (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — padrões arquiteturais (Step 5a)
- [ ] `docs/api/openapi.yaml` — spec OpenAPI (Step 5b)
- [ ] `docs/planning/PLAN.md` — módulos core e ondas (para enforcement block)
- [ ] `.ace/arch-config.yaml` — configuração de fitness functions (módulos core, thresholds)
- [ ] Skills componentes (disponíveis em `docs/skills/`):
    - `llc-step-clean-code-functions.md`
    - `llc-step-clean-code-classes.md`
    - `llc-step-clean-code-naming.md`
    - `llc-step-clean-code-errors.md`
    - `llc-step-clean-code-smells.md`
    - `llc-step-clean-code-readmodels.md`

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.3 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 5c** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-5c.md`:
     ```markdown
     # Skip Note: Step 5c — Clean Code Enforcement
     **Decisão:** Step pulado — código já em conformidade desde última execução.
     **Evidência:** Fitness functions `--check-clean-code` passam sem violações novas.
     **Validador:** [Nome] | **Data:** [YYYY-MM-DD]
     ```
   - **Não execute** as verificações nem aguarde Gate 8.5.
   - Avance para Step 6.

---

## 🎯 OBJETIVO

Consolidar e executar **todas as verificações de Clean Code** através de **21+ fitness functions automatizadas**, cobrindo 6 dimensões:

| Dimensão | Skill Componente | Fitness Functions | Referência |
|----------|------------------|-------------------|------------|
| **Functions** | `llc-step-clean-code-functions` | `function-max-lines`, `function-max-params`, `no-generic-names`, `no-side-effects` | Clean Code Ch.3 |
| **Classes** | `llc-step-clean-code-classes` | `class-max-lines`, `class-max-deps`, `dip-violation`, `anemic-domain`, `use-case-per-operation` | Clean Code Ch.10, Clean Arch |
| **Naming** | `llc-step-clean-code-naming` | `naming-consistency`, `no-generic-names` | Clean Code Ch.2 |
| **Errors** | `llc-step-clean-code-errors` | `no-empty-exceptions`, `no-empty-catch`, `result-pattern` | Clean Code Ch.7 |
| **Smells** | `llc-step-clean-code-smells` | `no-magic-numbers`, `no-dead-code`, `no-noise-comments`, `prefer-const` | Clean Code Ch.17 |
| **ReadModels** | `llc-step-clean-code-readmodels` | `readmodel-exists`, `repo-returns-readmodel`, `no-any-in-public`, `no-as-any` | Clean Architecture |

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS (21 Checks)

### Functions (4 checks)
| Check | Descrição | Threshold | Severidade Core/Non-core |
|-------|-----------|-----------|--------------------------|
| `function-max-lines` | Funções ≤ 20 linhas efetivas | 20 | block / warn |
| `function-max-params` | Funções ≤ 3 parâmetros | 3 | block / warn |
| `no-generic-names` | Proíbe `data`, `dto`, `result`, `info`, `obj`, `item`, `entity` | lista | block / warn |
| `no-side-effects` | Detecta atribuições a `this.*` em funções puras | heurística | warn |

### Classes (6 checks)
| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `class-max-lines` | Classes ≤ 100 linhas efetivas | 100 | block / warn |
| `class-max-deps` | Constructor ≤ 5 dependências injetadas | 5 | block / warn |
| `class-srp` | Coesão: métodos usam campos da classe | ≥ 80% | warn |
| `dip-violation` | Zero injeção de `PrismaService`, `@prisma/client` em services/use-cases | regex | block / warn |
| `anemic-domain` | Entidades têm métodos de negócio (não só propriedades) | > 0 métodos | warn |
| `use-case-per-operation` | Módulos core têm Use Cases separados por operação | - | block |

### Naming (1 check consolidado)
| Check | Descrição | Severidade |
|-------|-----------|------------|
| `naming-consistency` | PT/EN mixing, camelCase vs snake_case em query params | block / warn |

### Errors (3 checks)
| Check | Descrição | Severidade |
|-------|-----------|------------|
| `no-empty-exceptions` | Zero `throw new NotFoundException('')` ou `BadRequestException('')` | block |
| `no-empty-catch` | Zero `catch { }` ou `catch (e) { }` sem tratamento | block |
| `result-pattern` | Regras de negócio retornam `Result<T, E>` não throw | warn |

### Smells (4 checks)
| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `no-magic-numbers` | Constantes nomeadas para timeouts, limites, etc. | regex | warn |
| `no-dead-code` | Zero métodos stub (`throw new UnimplementedException`), código inalcançável | heurística | warn |
| `no-noise-comments` | Zero comentários de seção (`// ── Foo ────`) | regex | warn |
| `prefer-const` | `let` só onde há reatribuição real | heurística | warn |

### ReadModels / Type Safety (4 checks)
| Check | Descrição | Severidade |
|-------|-----------|------------|
| `readmodel-exists` | 100% interfaces de repositório têm `XxxReadModel` | block |
| `repo-returns-readmodel` | Métodos de repo retornam tipagem explícita (não `any`) | block |
| `no-any-in-public` | Zero `any` em signatures públicas (params, returns, props) | block |
| `no-as-any` | Zero casts `as any` (exceto 2 permitidos no global filter) | block |

---

## 📊 COMANDO DE EXECUÇÃO

```bash
# Executa todos os 21 checks de Clean Code
python .ace/scripts/fitness-functions.py --check-clean-code --strict

# Ou por dimensão:
python .ace/scripts/fitness-functions.py --check-functions --strict
python .ace/scripts/fitness-functions.py --check-classes --strict
python .ace/scripts/fitness-functions.py --check-naming --strict
python .ace/scripts/fitness-functions.py --check-errors --strict
python .ace/scripts/fitness-functions.py --check-smells --strict
python .ace/scripts/fitness-functions.py --check-readmodels --strict
```

**Opções:**
- `--strict` — falha se houver qualquer violação block
- `--verbose` — detalhes por arquivo/módulo
- `--module <nome>` — filtrar módulo específico
- `--config <path>` — usar `.ace/arch-config.yaml` customizado

---

## 📝 ARTEFATOS GERADOS/ATUALIZADOS

| Artefato | Descrição |
|----------|-----------|
| `.ace/arch-config.yaml` | Regras de Clean Code ativadas/ajustadas por módulo |
| `docs/architecture/adr/ADR-012` a `ADR-017` | ADRs para Functions, Classes, Naming, Errors, Smells, ReadModels |
| `docs/code-quality/CLEAN_CODE_REPORT.md` | Relatório consolidado de violações por dimensão |
| `docs/delta/skip-notes/step-5c.md` | Skip note se modo delta aplicável |

---

## 👤 GATE 8.5 — VALIDAÇÃO HUMANA

**Você valida:**
- [ ] Fitness functions `--check-clean-code --strict` passam sem bloqueios?
- [ ] Violações `warn` em módulos non-core têm plano de migração documentado?
- [ ] ADRs 012-017 criados e justificados?
- [ ] Módulos core (auditorias, achados, planos, relatórios, notificações) têm **zero** violações block?
- [ ] `Result<T, E>` pattern adotado em novos use cases?
- [ ] Repository interfaces retornam `XxxReadModel` tipado (zero `any`)?
- [ ] Código legacy marcado `// LEGACY` tem plano de migração em `docs/tech-debt/MIGRATION_PLAN.md`?

**Só avance quando aprovar.**

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todo código novo** desde o primeiro commit. Estrutura de pastas já prevê `domain/`, `application/`, `infrastructure/` por módulo. |
| **Brownfield** | Aplicar a **novos módulos** e **módulos alterados** (PRP-A). Código legacy marcado com `// LEGACY` tem tolerância temporária (warn apenas), mas **deve ter plano de migração** em `docs/tech-debt/MIGRATION_PLAN.md`. |

---

## 📤 SAÍDA ESPERADA

Ao executar esta skill, o agente deve:

1. **Verificar** código existente contra as 21 rules via `fitness-functions.py --check-clean-code`
2. **Reportar** violações com localização exata (arquivo, linha, regra, sugestão de fix)
3. **Agrupar** por dimensão (Functions, Classes, Naming, Errors, Smells, ReadModels)
4. **Priorizar**: block em core → block em non-core → warn
5. **Sugerir** refatoração padrão (extract use case, extract interface, introduce ReadModel, etc.)
6. **Validar** via fitness functions automatizadas
7. **Aguardar** validação humana (Gate 8.5) antes de prosseguir

**NÃO prossiga para Step 6 (Tasks) sem Gate 8.5 aprovado.**

---

## 🔗 INTEGRAÇÃO COM OUTROS STEPS

| Step | Integração |
|------|------------|
| **5a Architecture Patterns** | Repository Pattern (interfaces), Domain Layer, Use Cases — base para Clean Code |
| **5b API Design** | Naming consistency (PT/EN), camelCase query params — overlap com naming |
| **8b Repository Pattern** | DIP enforcement — `PrismaService` só em `Prisma*Repository` |
| **11a Domain Modeling** | Entidades ricas, Use Cases SRP — base para class checks |
| **11b Arch Fitness** | Re-executa clean code checks pós-execução (regressão) |

---

## 📚 REFERÊNCIAS

- **Clean Code** (Robert C. Martin) — Cap. 2 (Nomes), 3 (Funções), 7 (Erros), 10 (Classes), 17 (Smells)
- **Clean Architecture** (Robert C. Martin) — Dependency Rule, DIP
- **Software Design & Architecture** (Khalil Stemmler) — SRP, Coesão, Entidades de Domínio, Use Cases
- **Software Architect's Handbook** (Joseph Ingeno) — Fitness Functions, ADRs
- **Domain-Driven Design Distilled** (Vaughn Vernon) — Entidades, Value Objects, Aggregates