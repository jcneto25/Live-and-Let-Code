# PRP: [GRAPH-1C] — projections.py + Adapter `GraphPipelineDataSource` (Kanban sobre o Grafo)

> **ID:** PRP-GRAPH-1C | **Trilha:** Graph Engineering | **Onda:** 3
> **Owner:** jcneto25 | **Estimativa:** 0,5 semana | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0004 §2.8, §8.3 (emendado GOV-003/R3); ADR-0002 D6/P7
> **Emenda:** GOV-003 / R3 — estratégia **adapter** (sem refactor do `KanbanBoardBuilder`)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O `KanbanBoardBuilder` do PRP-WIZARD-1A recebe o Protocol `PipelineDataSource` (hoje implementado pelo `PipelineDataReader`). Com o grafo pronto (PRP-GRAPH-1A/1B), o Kanban pode ser alimentado pelo `GraphEngine` — mais preciso, com SLA baseado em timestamps reais de transição de estado. Este PRP entrega o **adapter** previsto no ADR-0002 D6/P7 e ADR-0004 §2.8: `GraphPipelineDataSource`, uma implementação do Protocol sobre o `GraphEngine`, injetada no builder **sem mudar `kanban.py`, `app.py` ou a UI do Kanban**.

### 1.2 O que é entregue

- [ ] `llc_graph/projections.py` — `to_kanban()` mapeia `NodeState` → `KanbanColumn`
- [ ] `llc_graph/projections.py` — `GraphPipelineDataSource`: adapter que implementa o Protocol `PipelineDataSource` (ADR-0002 §7.1) sobre o `GraphEngine`
- [ ] Troca da implementação injetada no `WizardApp` (`PipelineDataReader` → `GraphPipelineDataSource`) — **zero mudança** em `kanban.py` e na assinatura do builder
- [ ] Paridade 100% verificada: board gerado pelo adapter (grafo) = board gerado pelo reader antigo
- [ ] `to_impact_map()` e `to_critical_path()` como stubs (implementados em PRP-GRAPH-2B)

### 1.3 O que NÃO está no escopo

- ❌ Mudança na UI do Kanban (zero impacto visual)
- ❌ Refactor de assinatura do `KanbanBoardBuilder` ou de `kanban.py`/`app.py` — a integração é via adapter (GOV-003/R3)
- ❌ `critical_path()` completo → PRP-GRAPH-2B

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G1C.1 | `to_kanban()` mapeia `NodeState.DONE` → `KanbanColumn.DONE` | **Dado** nó DONE, **Quando** `to_kanban()`, **Então** card na coluna DONE | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.2 | `to_kanban()` mapeia todos os 7 estados corretamente | **Dado** nó em cada NodeState, **Quando** `to_kanban()`, **Então** coluna correta | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.3 | `GraphPipelineDataSource` implementa o Protocol `PipelineDataSource` completo | **Dado** engine instanciado, **Quando** `KanbanBoardBuilder(GraphPipelineDataSource(engine)).build()`, **Então** board válido **e** `kanban.py`/`app.py` sem alteração de assinatura (apenas a implementação injetada muda) | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.4 | Paridade board: adapter (grafo) = reader | **Dado** mesmo estado ACE, **Quando** board via `GraphPipelineDataSource` vs. board via `PipelineDataReader`, **Então** resultado idêntico | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.5 | SLA (`entered_column_at`) usa timestamp real da sessão ACE | **Dado** step transitou para gate_pending às 10:00, **Quando** card gerado, **Então** `entered_column_at = 10:00` | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |

---

## 3. Mapeamento de Estados

```python
NODE_STATE_TO_COLUMN = {
    NodeState.PENDING:        KanbanColumn.BACKLOG,
    NodeState.READY:          KanbanColumn.BACKLOG,
    NodeState.RUNNING:        KanbanColumn.RUNNING,
    NodeState.AWAITING_HUMAN: KanbanColumn.AWAITING_HUMAN,
    NodeState.FAILED:         KanbanColumn.REWORK,
    NodeState.DONE:           KanbanColumn.DONE,
    NodeState.SKIPPED:        KanbanColumn.SKIPPED,
}
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-1B (engine com `node_state()`)
- PRP-WIZARD-1.1 (Kanban UI que receberá o adapter — sem refactor, GOV-003/R3)

### Desbloqueia
- PRP-GRAPH-2A/2B (projeções adicionais)
- Kanban com precisão de timestamps reais

---

## 5. Definition of Done

- [ ] Todos os 5 RF com testes verdes
- [ ] Paridade 100% confirmada (RF-G1C.4)
- [ ] UI do Kanban inalterada (zero impacto visual)
- [ ] `kanban.py` e `app.py` sem alteração de assinatura — integração exclusivamente via adapter injetado (GOV-003/R3)
- [ ] `PipelineDataReader` ainda disponível como fallback (não removido)
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
