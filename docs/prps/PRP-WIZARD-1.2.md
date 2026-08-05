# PRP: [WIZARD-1.2] — Drag & Drop Backlog + `--export-flow-metrics` + Temas

> **ID:** PRP-WIZARD-1.2 | **Trilha:** Wizard | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0002 §2.5 D5, §2.6 D5

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com PRP-WIZARD-1.1 o Kanban está funcional mas read-only. Este PRP adiciona a única exceção ao movimento state-driven: reordenação de prioridade dentro do `BACKLOG` via drag & drop. Também entrega o flag `--export-flow-metrics` que exporta Cycle Time, Block Time e Stale Rate para análise externa, e suporte a temas visuais.

### 1.2 O que é entregue

- [ ] Drag & drop dentro da coluna `BACKLOG` para reordenar prioridade
- [ ] Bloqueio explícito de drag para outras colunas (notificação educativa)
- [ ] `llc wizard --export-flow-metrics` gera `.ace/evals/results/flow-metrics-{date}.yaml`
- [ ] Suporte a tema dark/light via `wizard.tcss` + config

### 1.3 O que NÃO está no escopo

- ❌ Drag entre colunas (state-driven por design — ADR-0002 §2.5)
- ❌ Swimlanes por wave → PRP-WIZARD-2.0

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-W1.2.1 | Drag dentro de BACKLOG reordena cards | **Quando** drag card de pos 3 para pos 1 em BACKLOG, **Então** ordem persistida na sessão | Must | ⏳ | `test_app.py` | `llc_wizard/widgets/kanban_board.py` |
| RF-W1.2.2 | Drag para outra coluna exibe notificação e cancela | **Quando** drag card de BACKLOG para RUNNING, **Então** notificação "movimento bloqueado" e card retorna | Must | ⏳ | `test_app.py` | `llc_wizard/widgets/kanban_board.py` |
| RF-W1.2.3 | `--export-flow-metrics` gera YAML com Cycle Time e Block Time | **Dado** pipeline com histórico, **Quando** `llc wizard --export-flow-metrics`, **Então** arquivo YAML criado em `.ace/evals/results/` | Must | ⏳ | `test_app.py` | `.ace/scripts/llc.py` |
| RF-W1.2.4 | Métricas exportadas incluem baseline da v1.2 (primeira execução) | **Quando** exportado pela primeira vez, **Então** arquivo contém tag `baseline: true` | Should | ⏳ | `test_app.py` | `llc_wizard/kanban.py` |

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

- [ ] Drag dentro de BACKLOG funcional; drag para outras colunas bloqueado com notificação
- [ ] `--export-flow-metrics` gera YAML válido
- [ ] Primeiro export marcado como `baseline: true`
- [ ] Temas dark/light alternáveis
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
