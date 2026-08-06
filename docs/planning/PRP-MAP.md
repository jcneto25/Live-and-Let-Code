# Mapa de PRPs — LLC Fábrica Agêntica

**Documento:** `docs/planning/PRP-MAP.md`
**Versão:** 1.1.0 · **Data:** 2026-08-06 · **Status:** Referência ativa

> **Atualização 2026-08-06:** WIZARD-1A e WIZARD-1B concluídos (1B resolveu o
> DD-W1A-01 da 1A). Cleanup de governança GOV-002 executado (12 sessões órfãs
> removidas, sentinel `is_placeholder_task` endurecido, drift de índice
> reconciliado) e débito `observability.py` (R2) saldo. **EVALS-F1 concluído e
> verificado** (11 testes verdes, fitness 41/41, `<eval_metrics>` append-only via
> `finalize_session` dry-run end-to-end OK). **Tracks ativos agora:** EVALS-F2
> (paralelo) e GRAPH-1A (próximo no caminho crítico).

> Este documento é a fonte de verdade para o planejamento de implementação das novas
> funcionalidades do LLC. Derivado dos ADRs 0002, 0004, 0005, 0006 e do
> `factory-evolution.md` v0.2.0.

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | PRP criado e aprovado |
| 🔄 | Em implementação (sessão ACE aberta) |
| 📋 | PRP a criar |
| 🔒 | Condicional — só inicia com evidência registrada em sessões ACE |
| ⛔ | Fora do escopo (não fazer) |

---

## Trilha 0 — Governança (pré-requisito de tudo)

**ADR de origem:** ADR-0006
**Critério de saída da trilha:** `fitness-functions.py --check dependency-governance` passa.

| PRP | Entrega | Esforço | Depende de | Status |
|-----|---------|---------|------------|--------|
| PRP-ACE-TAGS | Taxonomia de tags ACE no `validate-tags.py` (`user_response`, `eval_metrics`, `task_completed`, `waiver`) + emendas ADR-0002 §7.2 e pipeline-design §8.4 | 2d | GOV-003 (R1) | ✅ done (2026-08-05) |
| GOV-002 fix (R7) | Fail-fast anti sessão-placeholder: `is_placeholder_task()` + guarda em `initialize_session/cli.py` e `llc_harness/session.py` (era bloqueio de WIZARD-1A — GOV-003/R7; ver também PRP-GOV-004 para o ciclo de vida GOV no harness) | 0,5d | GOV-002 Decisão item 2 | ✅ done (2026-08-05) |
| PRP-GOV-T1 | Criar `.ace/config/dependencies.yaml` com `click`, `pyyaml`, `textual`, `tiktoken` | 0,5d | ADR-0006 aceito | ✅ done (2026-08-05) |
| PRP-GOV-T2 | Retro-classificar todas as dependências em `.ace/scripts/` | 0,5d | PRP-GOV-T1 | ✅ done (2026-08-05) |
| PRP-GOV-T3 | Fitness function `dependency-governance` em `fitness-functions.py` (TDD) | 1d | PRP-GOV-T2 | ✅ done (2026-08-05) |

**Total: ~4 dias** (inclui PRP-ACE-TAGS, originado do GOV-003/R1 — pré-requisito de WIZARD-1B e EVALS-F1)

> **Progresso de governança (2026-08-06, fora de PRP — higiene):** GOV-002 teve
> reincidência com sessões `"tarefa"` (08-06-005/006), que escaparam do sentinel
> `"Step N"`-only. O guard `is_placeholder_task()` foi **endurecido** (token-placeholder
> genérico case-insensitive, TDD 26 passed), **12 sessões órfãs históricas foram
> removidas**, drift de `index.json` reconciliado, e o módulo first-party ausente
> **`observability.py` (R2) foi implementado** (saldo do débito; `test_observability`
> 6 passed). Governança segue verde (`fitness --check dependency-governance`).


---

## Trilha 1 — Wizard TUI (ADR-0002)

**ADR de origem:** ADR-0002
**Critério de saída da trilha:** `llc wizard` completo com HITL, Kanban UI, métricas de fluxo.

| PRP | Entrega | Esforço | Depende de | Status |
|-----|---------|---------|------------|--------|
| PRP-WIZARD-1A | `data.py` + `kanban.py` + `runner.py` + `app.py` MVP + CLI `llc wizard` | 4 sem | PRP-GOV-T3 | ✅ done (2026-08-06) · waiver item saída `--from 0` (gates interativas) → PRP-WIZARD-1B (DD-W1A-01) |
| PRP-WIZARD-1B | HITL: `decisions.py` + `commands.py` + `RealtimePromptCollector` | 2 sem | PRP-WIZARD-1A | ✅ done (2026-08-06) · **saldou o DD-W1A-01 da 1A** (exit gate `--from 0` / gates interativas) |
| PRP-WIZARD-1C | Artifact Review + Scope Confirmation + rerun automático | 2 sem | PRP-WIZARD-1B | 📋 |
| PRP-WIZARD-1.1 | Kanban UI board (toggle K + SLA visual + WIP) | 2 sem | PRP-WIZARD-1A + PRP-EVALS-F1 | 📋 |
| PRP-WIZARD-1.2 | Drag & drop backlog + `--export-flow-metrics` + temas | 1 sem | PRP-WIZARD-1.1 | 📋 |

**Total: ~11 semanas**

---

## Trilha 2 — Eval Harness (ADR-0005)

**ADR de origem:** ADR-0005 (transversal — não é pré-requisito de nenhum ADR, mas enriquece todos)
**Entrega mínima de valor:** F1+F2 em ~2 semanas, **em paralelo ao WIZARD-1A** (GOV-003/R6: a
dependência "Wizard MVP" era artificial — sessões ACE já existem hoje; as reais são a taxonomia
`<eval_metrics>` do PRP-ACE-TAGS e o registro do `tiktoken` na governança).

| PRP | Entrega | Esforço | Depende de | Status |
|-----|---------|---------|------------|--------|
| PRP-EVALS-F1 | Instrumentação de tokens (3 níveis) + `<eval_metrics>` append-only | 1 sem | PRP-ACE-TAGS ✅ + PRP-GOV-T3 (tiktoken N1 registrado) | ✅ done (2026-08-06) · 11 testes, fitness 41/41 |
| PRP-EVALS-F2 | `CodeEvaluator` — agrega `pass_rate` + `fitness_score` + `coverage` | 1 sem | PRP-EVALS-F1 | 📋 |
| PRP-EVALS-F3 | `DocJudge` — LLM-as-judge + rubrics YAML por step | 2 sem | PRP-EVALS-F2 | 📋 |
| PRP-EVALS-F4 | Baselines + regressão (warm-up N_MIN=5/N_STABLE=10) | 1 sem | PRP-EVALS-F3 | 📋 |
| PRP-EVALS-F5 | Dashboard Pareto (custo×qualidade) + ranking | 1 sem | PRP-EVALS-F4 | 📋 |

**Total: ~6 semanas**

---

## Trilha 3 — Graph Engineering (ADR-0004)

**ADR de origem:** ADR-0004
**Critério de saída:** Kanban derivado do grafo; Smart Skip formal; `parallel_frontier()` agnóstico.

| PRP | Entrega | Esforço | Depende de | Status |
|-----|---------|---------|------------|--------|
| PRP-GRAPH-1A | `model.py` + `builder.py` + `state.py` | 1 sem | PRP-WIZARD-1A | 📋 · **desbloqueado** (único pré-req ✅ desde 2026-08-06) |
| PRP-GRAPH-1B | `engine.py` — `ready_nodes()` + `impact_of()` + delta | 1,5 sem | PRP-GRAPH-1A | 📋 |
| PRP-GRAPH-1C | `projections.py` — `to_kanban()` substitui `PipelineDataReader` no Wizard | 0,5 sem | PRP-GRAPH-1B + PRP-WIZARD-1.1 | 📋 |
| PRP-GRAPH-2A | `parallel_frontier()` — dados puros agnósticos de runtime | 1 sem | PRP-GRAPH-1B | 📋 |
| PRP-GRAPH-2B | `critical_path()` + métricas de gargalo | 0,5 sem | PRP-GRAPH-2A | 📋 |

**Total: ~4,5 semanas**

---

## Trilha 4 — Wave Coordinator (Condicional)

**Gate de entrada:** ≥3 sessões ACE com retrabalho documentado por `DEPENDENCY_MATRIX` estático.

| PRP | Entrega | Esforço | Gate | Status |
|-----|---------|---------|------|--------|
| PRP-WAVE-COORD | `wave_coordinator.py` — polling + sugestão textual estritamente sugestiva | 1 sem | Ver acima | 🔒 |

---

## Trilha 5 — Herdr / Visibilidade Multi-Agente (Condicional)

**Gate de entrada:** ≥4 semanas de uso da Fase 1 + dor multi-agente registrada em sessões ACE.

| PRP | Entrega | Esforço | Gate | Status |
|-----|---------|---------|------|--------|
| PRP-HERDR-SKILL | Skill `llc-wave-observability.md` + feature detection + fallback | 2 sem | Ver acima | 🔒 |

---

## Grafo de Dependências

```
PRP-GOV-T1 ──► PRP-GOV-T2 ──► PRP-GOV-T3
                                    │
              ┌─────────────────────┤
              │                     │
              ▼                     ▼
        PRP-WIZARD-1A          PRP-EVALS-F1 ──► PRP-EVALS-F2
              │                     │                 │
       ┌──────┤                     └─────────────────┤
       │      │                                       ▼
       │  PRP-WIZARD-1B                          PRP-EVALS-F3
       │      │                                       │
       │  PRP-WIZARD-1C                          PRP-EVALS-F4
       │                                              │
       ▼                                         PRP-EVALS-F5
  PRP-WIZARD-1.1 ◄──── PRP-EVALS-F1
       │
  PRP-WIZARD-1.2
       │
  PRP-GRAPH-1A ──► PRP-GRAPH-1B ──► PRP-GRAPH-1C (refatora Wizard)
                        │
                   PRP-GRAPH-2A ──► PRP-GRAPH-2B
                        │
         🔒 PRP-WAVE-COORD (condicional)
         🔒 PRP-HERDR-SKILL (condicional)
```

---

## Caminho Crítico

```
GOV-T1 → GOV-T2 → GOV-T3 → WIZARD-1A → GRAPH-1A → GRAPH-1B → GRAPH-1C
```

> **Correção (GOV-003/R6):** o caminho anterior omitia GRAPH-1A (1 sem) e GRAPH-1B
> (1,5 sem), pré-requisitos de GRAPH-1C. Comparando as cadeias pós-WIZARD-1A:
> via WIZARD-1.1 = 2 sem; via GRAPH-1A→1B = 2,5 sem — **a cadeia Graph domina**
> o caminho crítico até GRAPH-1C.

**Paralelismo imediato disponível após GOV-T3 (+ PRP-ACE-TAGS ✅):**
- WIZARD-1A (Trilha 1)
- EVALS-F1 → F2 (Trilha 2 — transversal, não depende do Wizard)

**Paralelismo imediato disponível após WIZARD-1A:**
- WIZARD-1B/1C (HITL)
- GRAPH-1A (modelo de grafo)

**Paralelismo ATIVO (2026-08-06 — WIZARD-1A/1B e EVALS-F1 concluídos):**
- **EVALS-F2** (Trilha 2 — `CodeEvaluator`: pass_rate + fitness_score + coverage; dep `PRP-EVALS-F1 ✅`)
- **GRAPH-1A** (Trilha 3 — próximo node do caminho crítico; pré-req `PRP-WIZARD-1A ✅`)
- WIZARD-1C (HITL avançado — Artifact Review/Scope/rerun) após 1B ✅

---

## Resumo Executivo

| Trilha | PRPs | Esforço | Resultado |
|--------|------|---------|-----------|
| Governança | 3 | ~2d | ADR-0006 operacional |
| Wizard | 5 | ~11 sem | Observabilidade + HITL + Kanban |
| Evals | 5 | ~6 sem | Custo + qualidade + regressão |
| Graph | 5 | ~4,5 sem | Coordenação reativa |
| Wave Coord | 1 | 1 sem | Sugestão reativa (condicional) |
| Herdr | 1 | 2 sem | Visibilidade multi-agente (condicional) |
| **Total núcleo** | **18** | **~24 sem** | Fábrica agêntica base |

> **Narrativa de investimento (GOV-003/R12):** o **~24 sem** cobre o programa completo (incluindo Fase 2/3 condicionais — Wave Coordinator, Herdr). O horizonte **~12 sem** da factory-evolution (§4) representa o núcleo MVP de 1ª geração (Governança + Wizard MVP + Eval F1/F2 + Graph). As cifras são complementares: 24 sem = roadmap total, 12 sem = primeira entrega observável.

> **Progresso real (2026-08-06):** **Trilha 0 (Governança) ✅ e Trilha 1 (Wizard) 2/5 ✅** — WIZARD-1A e 1B entregues (61 + 61 testes, fitness 41/41); **WIZARD-1C, 1.1 e 1.2 pendentes**. **Trilha 2 (Evals) 1/5 ✅** — EVALS-F1 entregue e verificado (11 testes, fitness 41/41, integração `<eval_metrics>` no finalize OK); **EVALS-F2 desbloqueado**. **Trilha 3 (Graph) ainda 📋** — GRAPH-1A desbloqueado.

---

## Referências

- `docs/architecture/adr/ADR-0002-llc-wizard-tui-hitl-kanban.md`
- `docs/architecture/adr/ADR-0004-graph-engineering-orchestration.md`
- `docs/architecture/adr/ADR-0005-eval-harness.md`
- `docs/architecture/adr/ADR-0006-external-dependency-governance.md`
- `docs/architecture/factory-evolution.md` v0.2.0
- `docs/prps/PRP-WIZARD-1A.md` (PRP de referência para formato)
