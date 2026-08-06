# PRP: [WIZARD-1.2] — Drag & Drop Backlog + `--export-flow-metrics` + Temas

> **ID:** PRP-WIZARD-1.2 | **Trilha:** Wizard | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0002 §2.5 D5, §2.6 D5

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com PRP-WIZARD-1.1 o Kanban está funcional mas read-only. Este PRP adiciona a única exceção ao movimento state-driven: reordenação de prioridade dentro do `BACKLOG` via drag & drop. Também entrega o flag `--export-flow-metrics` que exporta Cycle Time, Block Time e Stale Rate para análise externa, e suporte a temas visuais.

### 1.2 O que é entregue

- [x] Drag & drop dentro da coluna `BACKLOG` para reordenar prioridade
- [x] Bloqueio explícito de drag para outras colunas (notificação educativa)
- [x] `llc wizard --export-flow-metrics` gera `.ace/evals/results/flow-metrics-{date}.yaml`
- [x] Suporte a tema dark/light via `wizard.tcss` + config

### 1.3 O que NÃO está no escopo

- ❌ Drag entre colunas (state-driven por design — ADR-0002 §2.5)
- ❌ Swimlanes por wave → PRP-WIZARD-2.0

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-W1.2.1 | Drag dentro de BACKLOG reordena cards | **Quando** drag card de pos 3 para pos 1 em BACKLOG, **Então** ordem persistida na sessão | Must | ✅ | `test_app.py` | `llc_wizard/kanban_board.py` |
| RF-W1.2.2 | Drag para outra coluna exibe notificação e cancela | **Quando** drag card de BACKLOG para RUNNING, **Então** notificação "movimento bloqueado" e card retorna | Must | ✅ | `test_app.py` | `llc_wizard/kanban_board.py` |
| RF-W1.2.3 | `--export-flow-metrics` gera YAML com Cycle Time e Block Time | **Dado** pipeline com histórico, **Quando** `llc wizard --export-flow-metrics`, **Então** arquivo YAML criado em `.ace/evals/results/` | Must | ✅ | `test_app.py` + `test_flow_metrics.py` | `llc_wizard/flow_metrics.py` + `llc/cli.py` |
| RF-W1.2.4 | Métricas exportadas incluem baseline da v1.2 (primeira execução) | **Quando** exportado pela primeira vez, **Então** arquivo contém tag `baseline: true` | Should | ✅ | `test_flow_metrics.py` | `llc_wizard/flow_metrics.py` |

---

## 3. Formato de exportação

```yaml
# .ace/evals/results/flow-metrics-2026-08-05.yaml
generated_at: "2026-08-05T15:00:00"
baseline: true   # marcado na primeira execução
metrics:
  cycle_time_avg_minutes: 142
  block_time_avg_minutes: 28
  stale_rate_percent: 12
  first_pass_rate_percent: 74
by_step:
  "5": { cycle_time: 180, block_time: 35, first_pass: true }
  "1": { cycle_time: 95, block_time: 20, first_pass: false, rework_count: 1 }
```

---

## 4. Dependências

### Bloqueado por
- PRP-WIZARD-1.1

### Desbloqueia
- Métricas de fluxo disponíveis para análise (baseline estabelecido)

---

## 5. Definition of Done

- [x] Drag dentro de BACKLOG funcional; drag para outras colunas bloqueado com notificação
- [x] `--export-flow-metrics` gera YAML válido
- [x] Primeiro export marcado como `baseline: true`
- [x] Temas dark/light alternáveis
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

---

## 6. Execução (2026-08-06)

**Sessão:** `2026-08-06-023` (step 10.9 Domain Modeling, wave 2) · **15 testes novos** (10 FTDD em `test_app.py` + 5 unit em `test_flow_metrics.py`) · **cobertura TOTAL 97%** (`flow_metrics.py` 100%, `kanban_board.py` 96%, `app.py` 90%) · **fitness 41/41** · full suite **521 passed**.

### Implementação

| Componente | Conteúdo |
|-----------|----------|
| `kanban_board.py` | `reorder()` (RF-W1.2.1 — reordena BACKLOG e retorna nova ordem persistida) + `try_move()` (RF-W1.2.2 — bloqueia movimentos state-driven com notificação educativa) |
| `flow_metrics.py` (novo) | `compute_flow_metrics()` (cycle/block time, stale rate, first-pass rate por step) + `export_flow_metrics()` (grava `flow-metrics-{date}.yaml`; `baseline: true` só na 1ª execução — RF-W1.2.4) |
| `app.py` | `drag_card()`/`reorder_backlog()` (persistência `_backlog_order` + sync do painel), `export_flow_metrics()`, tema (`_load_theme` via `gates.json → wizard.theme`, `toggle_theme()`) |
| `wizard.tcss` (novo) | Temas dark/light com blocos `.dark`/`.light` (DoD temas) |
| `llc/cli.py` | Flag `--export-flow-metrics` no comando `wizard` (gera YAML sem abrir a TUI) |

### Notas
- **DIP limpo:** `flow_metrics.py` e `kanban_board.py` usam o Protocol `PipelineDataSource` (ADR-0004 §2.3) — zero imports de infra/harness.
- **Drag & drop é a única exceção ao state-driven** (ADR-0002 §2.5 D5): reordenação de prioridade dentro do BACKLOG; mover para outras colunas é bloqueado por design.
