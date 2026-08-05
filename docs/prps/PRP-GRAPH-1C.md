# PRP: [GRAPH-1C] — projections.py + Refatoração KanbanBoardBuilder

> **ID:** PRP-GRAPH-1C | **Trilha:** Graph Engineering | **Onda:** 3
> **Owner:** jcneto25 | **Estimativa:** 0,5 semana | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0004 §2.8, §8.3; ADR-0002 D6

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O `KanbanBoardBuilder` do PRP-WIZARD-1A lê diretamente do `PipelineDataReader`. Com o grafo pronto (PRP-GRAPH-1A/1B), o Kanban pode ser derivado do `GraphEngine` — mais preciso, com SLA baseado em timestamps reais de transição de estado. Este PRP realiza a refatoração prevista no ADR-0002 D6 e ADR-0004 §2.8 sem mudar a UI do Kanban.

### 1.2 O que é entregue

- [ ] `llc_graph/projections.py` — `to_kanban()` mapeia `NodeState` → `KanbanColumn`
- [ ] `KanbanBoardBuilder` refatorado para receber `GraphEngine` em vez de `PipelineDataSource`
- [ ] Paridade 100% verificada: board gerado pelo grafo = board gerado pelo reader antigo
- [ ] `to_impact_map()` e `to_critical_path()` como stubs (implementados em PRP-GRAPH-2B)

### 1.3 O que NÃO está no escopo

- ❌ Mudança na UI do Kanban (zero impacto visual)
- ❌ `critical_path()` completo → PRP-GRAPH-2B

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G1C.1 | `to_kanban()` mapeia `NodeState.DONE` → `KanbanColumn.DONE` | **Dado** nó DONE, **Quando** `to_kanban()`, **Então** card na coluna DONE | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.2 | `to_kanban()` mapeia todos os 7 estados corretamente | **Dado** nó em cada NodeState, **Quando** `to_kanban()`, **Então** coluna correta | Must | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |
| RF-G1C.3 | `KanbanBoardBuilder` refatorado aceita `GraphEngine` | **Dado** engine instanciado, **Quando** `KanbanBoardBuilder(engine).build()`, **Então** board válido | Must | ⏳ | `test_kanban.py` | `llc_wizard/kanban.py` |
| RF-G1C.4 | Paridade board: grafo = reader | **Dado** mesmo estado ACE, **Quando** board via grafo vs. board via reader, **Então** resultado idêntico | Must | ⏳ | `test_kanban.py` | `llc_wizard/kanban.py` |
| RF-G1C.5 | SLA (`entered_column_at`) usa timestamp real da sessão ACE | **Dado** step transitou para gate_pending às 10:00, **Quando** card gerado, **Então** `entered_column_at = 10:00` | Must | ⏳ | `test_kanban.py` | `llc_wizard/kanban.py` |

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
- PRP-WIZARD-1.1 (Kanban UI que será refatorada)

### Desbloqueia
- PRP-GRAPH-2A/2B (projeções adicionais)
- Kanban com precisão de timestamps reais

---

## 5. Definition of Done

- [ ] Todos os 5 RF com testes verdes
- [ ] Paridade 100% confirmada (RF-G1C.4)
- [ ] UI do Kanban inalterada (zero impacto visual)
- [ ] `PipelineDataReader` ainda disponível como fallback (não removido)
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
