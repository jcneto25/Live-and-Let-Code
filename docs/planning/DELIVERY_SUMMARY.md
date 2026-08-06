# Relatório de Entrega — Trilhas Wizard, Evals e Graph

> **Data:** 2026-08-06 · **Status:** ✅ Roadmap PRP 100% entregue
> **Referência:** ADR-0002 (Wizard TUI/HITL), ADR-0005 (Evals), ADR-0004 (Graph Engineering)
> **Mapa de origem:** `docs/planning/PRP-MAP.md`

---

## 1. Resumo Executivo

As **3 trilhas de engenharia do roadmap** — Wizard (5/5), Evals (5/5) e Graph (5/5) — foram
completamente entregues em **15 PRPs**, seguindo TDD/FTDD com revisão de código obrigatória
(`code-reviewer-deepseek-flash`) em cada sessão ACE. Junto com a Trilha 0 (Governança, já
entregue), **o roadmap de PRPs do Live and Let Code está 100% concluído**.

| Métrica | Valor |
|---------|-------|
| PRPs entregues | **15** (Wizard 5 + Evals 5 + Graph 5) |
| Sessões ACE abertas/fechadas | 12 (2026-08-06-012 → 023) |
| Testes nas 3 trilhas | **257** (wizard 109 + evals 74 + graph 74) |
| Suíte completa | **525 passed** |
| Cobertura agregada (3 trilhas) | **97%** |
| Fitness functions (`--all --strict`) | **41/41** ✅ |
| Findings de revisão corrigidos | **12+** (incl. 2 bugs 🔴 de produção) |

---

## 2. Trilha 1 — Wizard TUI / HITL (ADR-0002) — 5/5 ✅

**Critério de saída:** `llc wizard` completo com HITL, Kanban UI e métricas de fluxo.

| PRP | Entrega principal | Testes | Destaques |
|-----|-------------------|--------|-----------|
| **WIZARD-1A** | `data.py` + `kanban.py` + `runner.py` + `app.py` MVP + CLI `llc wizard` | 61 | PipelineDataReader read-only (RNF-W1A.15: nunca escreve em `.ace/sessions/`); runner Harness/Fallback |
| **WIZARD-1B** | HITL: `decisions.py` + `commands.py` + `RealtimePromptCollector` | 61 | Saldou o débito DD-W1A-01 da 1A (exit gate `--from 0` / gates interativas); append-only preservado |
| **WIZARD-1C** | Artifact Review + Scope Confirmation + rerun automático | 11 | `FailureRecoveryScreen` real (3 opções `[r]/[s]/[q]`); `approved`/`feedback`; scope blocking; rerun sem sair da TUI |
| **WIZARD-1.1** | Kanban UI board (toggle K + SLA visual + WIP) | 15 | `KanbanBoardWidget` 6 colunas, WIP `3/2 🔴`, `card-stale`, scores `Q:/T:`, SKIPPED colapsada, seleção preservada |
| **WIZARD-1.2** | Drag & drop backlog + `--export-flow-metrics` + temas | 19 | `reorder()`/`try_move()` (única exceção ao state-driven); `flow_metrics.py` YAML com baseline; temas dark/light `wizard.tcss` |

**Módulos entregues:** `app.py`, `data.py`, `kanban.py`, `kanban_board.py`, `runner.py`,
`decisions.py`, `commands.py`, `flow_metrics.py`, `screens/failure_recovery.py`,
`widgets/decision_modal.py`, `wizard.tcss`.

### Commandos disponíveis
- `llc wizard` — inicia a TUI
- `llc wizard --export-flow-metrics` — gera `.ace/evals/results/flow-metrics-{date}.yaml`
  (cycle time, block time, stale rate, first-pass rate; `baseline: true` na 1ª execução)
- `llc wizard --from N --auto-approve` — flags do pipeline

---

## 3. Trilha 2 — Eval Harness (ADR-0005) — 5/5 ✅

**Entrega mínima de valor:** F1+F2 em ~2 semanas, em paralelo ao Wizard.

| PRP | Entrega principal | Testes | Destaques |
|-----|-------------------|--------|-----------|
| **EVALS-F1** | Instrumentação de tokens (3 níveis) + `<eval_metrics>` append-only | 11 | `source` level_1/2/3 com `precision: estimated`; escritor único = `finalize_session.py` (GOV-003/R8) |
| **EVALS-F2** | `CodeEvaluator` — agrega `pass_rate` + `fitness_score` + `coverage` | 14 | `aggregate.py`; integração com `code-health` |
| **EVALS-F3** | `DocJudge` — LLM-as-judge + rubrics YAML por step | 15 | 5 rubrics YAML; sampling; contrato de veredito |
| **EVALS-F4** | Baselines + regressão (warm-up N_MIN=5 / N_STABLE=10) | 17 | `BaselineManager`; buckets por nível de precisão; reset/migração |
| **EVALS-F5** | Dashboard Pareto (custo×qualidade) + ranking | 8 | `rank_by_efficiency`/`rework_waste`; `llc eval --report`; Eval Summary no code-health |

**Módulos entregues:** `instrument.py`, `aggregate.py`, `report.py`, `evaluators/`
(efficiency_meter + rubrics), estrutura `.ace/evals/` (`baselines/`, `results/`, `golden/`).

### Métricas disponíveis
- `EfficiencyScore = QualityScore / log10(TokenCost)` (ADR-0005 §2.3 — exemplo corrigido ≈20.5, não 18.9)
- `ReworkWaste` — % de tokens em retries
- `llc eval --report` — relatório Pareto Markdown em `.ace/evals/results/report-{date}.md`

---

## 4. Trilha 3 — Graph Engineering (ADR-0004) — 5/5 ✅

**Critério de saída:** Kanban derivado do grafo; Smart Skip formal; `parallel_frontier()`
agnóstico de runtime.

| PRP | Entrega principal | Testes | Destaques |
|-----|-------------------|--------|-----------|
| **GRAPH-1A** | `model.py` + `builder.py` + `state.py` | 21 | Grafo DAG do pipeline; contratos de dependência |
| **GRAPH-1B** | `engine.py` — `ready_nodes()` + `impact_of()` + delta | 13 | Contrato BLOCKS; determinismo (min-heap por id) |
| **GRAPH-1C** | `projections.py` — `to_kanban()` + `GraphPipelineDataSource` | 22 | Paridade §7.6 100% (gate rejeitado→FAILED, pending→GATE_PENDING); adapter substitui `PipelineDataReader` no Wizard |
| **GRAPH-2A** | `parallel_frontier()` — dados puros agnósticos de runtime | 7 | Sem imports de runtime; Q2 confirmado |
| **GRAPH-2B** | `critical_path()` + métricas de gargalo | 12 | Kahn O(V+E) com pesos SKIPPED=0/GATE=2.0; `to_critical_path`/`to_impact_map`; ciclo → `ValueError` |

**Módulos entregues:** `model.py`, `builder.py`, `state.py`, `engine.py`, `projections.py`.

---

## 5. Qualidade: revisões que pegaram bugs reais

Cada PRP passou por revisão crítica (`code-reviewer-deepseek-flash`); os achados mais
relevantes foram corrigidos com teste de regressão:

| 🔴 Bug | PRP | Correção |
|--------|-----|----------|
| **Double-count de pesos** no `critical_path()` | GRAPH-2B | `cand = dist[nid]` (peso entra 1×, ao processar o nó) — grafos mistos gate/skipped invertiam caminho |
| **Epoch-1970 explodia cycle time** | WIZARD-1.2 | Steps sem sessão (`get_status_since` → 1970) geravam ~29M min; excluídos das métricas |
| **Feedback em branco aprovava rejeição** | WIZARD-1C | `any(str(item).strip())` + teste de regressão |
| **`rerun_step` removia topo errado do stack** | WIZARD-1C | `remove("FailureRecoveryScreen")` preserva DecisionModal empilhado |
| **`_backlog_order` dead state** (reorder perdido no toggle) | WIZARD-1.2 | Re-aplicado no `_build_kanban()` |
| **`wizard.tcss` dead** (tema sem efeito) | WIZARD-1.2 | Tema renderizado `[tema: dark/light]` + re-sync do painel |

---

## 6. Sessões ACE e histórico

Todas as entregas foram embrulhadas em sessões ACE (ciclo `initialize → work → finalize`),
com `<eval_metrics>` appendado pelo `finalize_session.py` e gate registrado.

| Sessão | PRP | Commit |
|--------|-----|--------|
| 2026-08-06-012 | EVALS-F1 | `f6a7d74` |
| 2026-08-06-013 | EVALS-F2 | `0c8e5ae` |
| 2026-08-06-014 | GRAPH-1B | `799f327` |
| 2026-08-06-015 | EVALS-F3 | `cf68917` |
| 2026-08-06-016 | GRAPH-1C | `1099af0` |
| 2026-08-06-017 | EVALS-F4 | `543a7fd` |
| 2026-08-06-018 | GRAPH-2A | `50c3ef5` |
| 2026-08-06-019 | EVALS-F5 | `28791af` |
| 2026-08-06-020 | GRAPH-2B | `9aea9f4` |
| 2026-08-06-021 | WIZARD-1C | `f92ddde` |
| 2026-08-06-022 | WIZARD-1.1 | `6c10c2c` |
| 2026-08-06-023 | WIZARD-1.2 | `33afe40` |

> WIZARD-1A e 1B foram entregues em sessões anteriores (fase 1 do Wizard).

---

## 7. Próximos passos sugeridos

O roadmap de PRPs está **100% entregue**. Candidatos naturais de continuação:

1. **PRP-WIZARD-2.0** — swimlanes por wave (fora de escopo da 1.2 por design)
2. **Métricas de fluxo em ação** — consumir `flow-metrics-*.yaml` do WIZARD-1.2 nas
   análises de gargalo do GRAPH-2B
3. **Warm-up real de baselines** — executar EVALS-F4 em steps reais (N_MIN=5/N_STABLE=10)
   para popular `.ace/evals/baselines/`
4. **Integração Graph → Wizard definitiva** — trocar `PipelineDataReader` pelo
   `GraphPipelineDataSource` (GRAPH-1C) no app padrão
