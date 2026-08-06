# PRP: [GRAPH-1A] — `llc_graph`: model.py + builder.py + state.py

> **ID:** PRP-GRAPH-1A | **Trilha:** Graph Engineering | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0004 §2.3, §2.9

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O LLC tem ~60% dos ingredientes de um grafo mas tudo fragmentado: `dependency-graph.yaml`, ordem sequencial do `REGISTRY` de steps, `llc_wave.py`, `impact-analyzer.py`. Este PRP cria o pacote `llc_graph` unificando essas fontes em um modelo de grafo dirigido acíclico (DAG). É a fundação para o engine (PRP-GRAPH-1B) e para a integração do Kanban via adapter (PRP-GRAPH-1C).

> **Nota (GOV-003 / R2):** `StepSpec` **não possui** campo `depends_on` (verificado em `llc_steps/models.py`). As arestas N1 do grafo são derivadas da **ordem sequencial do REGISTRY** (`StepSpec.number`) — zero mudança no harness.

### 1.2 O que é entregue

- [x] `llc_graph/model.py` — `GraphNode`, `GraphEdge`, `NodeKind`, `NodeState`, `EdgeKind`, `Graph`
- [x] `llc_graph/builder.py` — `GraphBuilder`: unifica `dependency-graph.yaml` + ordem sequencial do `REGISTRY` (`StepSpec.number`) + `gates.json`
- [x] `llc_graph/state.py` — `AceStateReader`: deriva `NodeState` das sessões ACE (`.ace/index.json`)
- [x] Suite de testes TDD com cobertura ≥ 85%

### 1.3 O que NÃO está no escopo

- ❌ `engine.py` (`ready_nodes`, `impact_of`) → PRP-GRAPH-1B
- ❌ Projeções e refatoração Kanban → PRP-GRAPH-1C
- ❌ `parallel_frontier` → PRP-GRAPH-2A

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G1A.1 | `GraphNode` é imutável (frozen dataclass) | **Dado** instância, **Quando** mutação tentada, **Então** `FrozenInstanceError` | Must | ✅ | `tests/test_model.py` | `llc_graph/model.py` |
| RF-G1A.2 | `GraphBuilder` marca gates com `requires_human=True` | **Dado** step com gate em `gates.json`, **Quando** `build()`, **Então** nó gate com `requires_human=True` | Must | ✅ | `tests/test_builder.py` | `llc_graph/builder.py` |
| RF-G1A.3 | `GraphBuilder` deriva arestas N1 da ordem do `REGISTRY` e unifica `dependency-graph.yaml` | **Dado** REGISTRY com steps 0.5→1→2 e `dependency-graph.yaml` com artefatos, **Quando** `build()`, **Então** arestas N1 seguem `StepSpec.number` e nenhuma dependência do yaml é perdida | Must | ✅ | `tests/test_builder.py` | `llc_graph/builder.py` |
| RF-G1A.4 | `GraphBuilder` detecta nós órfãos | **Dado** dependência apontando para nó inexistente, **Quando** `build()`, **Então** warning registrado | Should | ✅ | `tests/test_builder.py` | `llc_graph/builder.py` |
| RF-G1A.5 | `AceStateReader` deriva `NodeState.DONE` de sessão `completed` | **Dado** `index.json` com step completed, **Quando** `node_state("step-5")`, **Então** `NodeState.DONE` | Must | ✅ | `tests/test_state.py` | `llc_graph/state.py` |
| RF-G1A.6 | `AceStateReader` tolera `index.json` ausente | **Dado** arquivo ausente, **Quando** `node_state()`, **Então** retorna `NodeState.PENDING` sem exceção | Must | ✅ | `tests/test_state.py` | `llc_graph/state.py` |
| RF-G1A.7 | Rework cria nova instância com `retry_of` preenchido | **Dado** gate rejeitado, **Quando** `add_rework_node()`, **Então** novo nó com `retry_of="step-5"` e aresta `REWORK` | Must | ✅ | `tests/test_builder.py` | `llc_graph/builder.py` |

---

## 3. Estrutura de Arquivos

```
.ace/scripts/llc_graph/
├── __init__.py
├── model.py     # NodeKind, NodeState, EdgeKind, GraphNode, GraphEdge, Graph
├── builder.py   # GraphBuilder
├── state.py     # AceStateReader
└── tests/
    ├── test_model.py
    ├── test_builder.py
    └── test_state.py
```

---

## 4. Dependências

### Bloqueado por
- PRP-WIZARD-1A — `PipelineDataSource` Protocol define o contrato que `AceStateReader` deve satisfazer

### Desbloqueia
- PRP-GRAPH-1B (engine)

---

## 5. Definition of Done

- [x] Todos os 7 RF com testes verdes
- [x] `llc_graph` não importa de `llc_wizard` nem de `llc_harness` (DIP)
- [x] `GraphNode` e `GraphEdge` frozen (imutáveis)
- [x] Cobertura ≥ 85% em `model.py`, `builder.py`, `state.py`
- [x] Harness existente intocado
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

> **Nota de execução (2026-08-06):** implementado em sessão 2026-08-06-012
> (step 10.9). 21 testes verdes; cobertura `model.py` 100%, `builder.py` 90%,
> `state.py` 88% (TOTAL 96%); fitness 41/41; suite geral 356 passed. Rework
> testado com `retry_of` + aresta `REWORK` sem criar ciclo (D4/§2.5).
