# ADR-0004: Graph Engineering como Camada de Orquestração do Pipeline LLC

**Arquivo:** `docs/architecture/adr/ADR-0004-graph-engineering-orchestration.md`

```yaml
---
adr: "0004"
title: "Graph Engineering como Camada de Orquestração do Pipeline LLC"
status: accepted
date: 2026-08-05
last_updated: 2026-08-05
deciders:
  - jcneto25
supersedes: null
related:
  - ADR-0001
  - ADR-0002
  - "issue #22"
prerequisite_for:
  - ADR-0003   # Integração Herdr (em elaboração) consome este modelo
tags: [graph, orchestration, dag, scheduler, impact-analysis, parallelism, kanban]
compliance:
  fitness_functions: [arch, clean-code, deep-clean]
  gates: [5, 5a, 5c, 11.3]
---
```

> **Nota de numeração:** este ADR estabelece a camada de orquestração que será consumida pelo ADR-0003 (integração Herdr, em elaboração). A numeração reflete ordem de solicitação, não ordem de dependência: **ADR-0004 é pré-requisito lógico de ADR-0003**, pois o scheduler paralelo do Herdr opera sobre o modelo de grafo aqui definido.

---

## 1. Contexto

### 1.1 Situação Atual — Fragmentação Graph-Aware

O LLC já possui múltiplos mecanismos com natureza de grafo, porém **fragmentados e não usados como fonte de verdade da execução**:

| Artefato Existente | Natureza | Limitação Atual |
|---|---|---|
| `dependency-graph.yaml` (`dependency-graph-generator.py`) | DAG de PRPs/tasks | Gerado, mas não dirige execução |
| `DEPENDENCY_MATRIX_TEMPLATE.md` | Matriz de dependências | Documental, não executável |
| `EXECUTION_WAVES_TEMPLATE.md` | Topological sort manual | Waves definidas à mão |
| `impact-analyzer.py` | Propagação de mudanças | Heurístico, desconectado do scheduler |
| Smart Skip (`llc-smart-skip.md`) | Skip por impacto | Não usa propagação formal |
| `step.depends_on` no registry | Arestas implícitas | Não unificadas com PRPs |
| `llc_wave.py` | Paralelismo agrupado | Agrupamento manual, não derivado |

**Diagnóstico:** o LLC tem ~60% dos ingredientes de um grafo, mas o pipeline ainda é operado como lista sequencial e o paralelismo é definido manualmente. Não há um modelo único que una dependências de steps e de PRPs, nem um scheduler que derive "o que pode rodar agora" dessas dependências.

### 1.2 Forças em Jogo

| Força | Direção |
|---|---|
| **Human-in-control** | Gates humanos não podem ser auto-avançados por scheduler |
| **Integridade ACE** | Estado continua escrito pelos scripts sancionados |
| **Paralelismo para fábrica** | Fábrica agentica exige escalonamento automático |
| **Análise de impacto** | Smart Skip e Delta precisam de propagação formal |
| **Baixa complexidade** | Não introduzir framework pesado prematuramente |
| **Preparar Fase 2/3** | Modelo deve mapear para Herdr e workflow engines |

### 1.3 Escopo

Este ADR define o **modelo de grafo, o engine de escalonamento e as projeções derivadas** como camada de orquestração do LLC. Não cobre a execução paralela em si (ADR-0003/Herdr) nem workflow engines distribuídos (Fase 3). Cobre a fundação que ambos consumirão.

---

## 2. Decisão

Adotar **graph engineering** como camada de orquestração do LLC: um modelo de grafo dirigido que unifica dependências de steps e PRPs, um engine que deriva o estado de execução, e projeções (Kanban, timeline, impacto) calculadas a partir desse grafo. O grafo é uma **camada sobre o pipeline**, não uma reescrita: o backbone sequencial e os gates permanecem; o grafo os organiza e escalona.

### 2.1 Princípios de Design (não negociáveis)

| # | Princípio |
|---|---|
| **P1** | **Estrutura declarada, estado derivado** — nós/arestas vêm de fontes declarativas; estado é calculado das sessões ACE |
| **P2** | **Gates são cidadãos de primeira classe** — nós `requires_human` nunca são auto-avançados |
| **P3** | **Grafo é projeção, não fonte primária de estado** — single source of truth do estado permanece nas sessões ACE |
| **P4** | **DAG preservado** — rework cria nova instância, nunca ciclo |
| **P5** | **Projeções são read-only** — Kanban/timeline derivam do grafo, nunca o mutam |
| **P6** | **Implementação leve** — Python puro no MVP; nenhum framework externo pesado |
| **P7** | **Tool-agnostic preservado** — o grafo não acopla a cliente de IA ou runtime específico |

### 2.2 Conceito Central: Estrutura Declarada + Estado Derivado

A decisão arquitetural mais importante é a separação entre **estrutura** e **estado**:

- **Estrutura do grafo** (nós + arestas): declarada em `dependency-graph.yaml` + `depends_on` do registry de steps. Relativamente estática por projeto.
- **Estado do grafo** (status de cada nó): **derivado em tempo real** das sessões ACE (`.ace/index.json` + `.ace/sessions/`). Nunca persistido como fonte primária.

Consequência direta: o grafo é uma **lente** que organiza estrutura + estado. Se o cache de estado ficar inconsistente, ele é reconstruído a partir das sessões ACE — que permanecem a fonte de verdade. Isso preserva integridade ACE (P3) e elimina dessincronização.

```
ESTRUTURA (declarada)                ESTADO (derivado)
dependency-graph.yaml      ──┐
registry.depends_on        ──┼──►  GRAFO  ◄──  sessões ACE (.ace/index.json)
gates.json                 ──┘        │
                                       ├──► Projeção: Kanban (ADR-0002)
                                       ├──► Projeção: ready_nodes / frontier
                                       ├──► Projeção: impact_of
                                       └──► Projeção: critical_path
```

### 2.3 Modelo de Nós e Arestas

```python
# .ace/scripts/llc_graph/model.py

class NodeKind(str, Enum):
    STEP = "step"      # unidade do pipeline macro
    PRP = "prp"        # unidade paralelizável de execução
    GATE = "gate"      # decisão humana (ESPECIAL)
    HITL = "hitl"      # pergunta/review durante execução

class NodeState(str, Enum):
    PENDING = "pending"
    READY = "ready"                 # deps satisfeitas, elegível
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"  # gate/hitl parado p/ humano
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"

class EdgeKind(str, Enum):
    DEPENDS_ON = "depends_on"   # aresta de controle
    PRODUCES = "produces"        # aresta de data-flow (artefato)
    BLOCKS = "blocks"            # gate bloqueia sucessores até aprovação
    REWORK = "rework"            # liga instância original à retry

@dataclass(frozen=True)
class GraphNode:
    id: str                        # "step-5" | "prp-004" | "gate-5" | "hitl-q123"
    kind: NodeKind
    requires_human: bool           # True para GATE e HITL
    auto_parallelizable: bool      # True para PRP; False p/ step com gate
    depends_on: tuple[str, ...]    # arestas de entrada (imutável)
    produces: tuple[str, ...]      # artefatos gerados
    retry_of: Optional[str] = None # aponta p/ instância original se for rework

@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    kind: EdgeKind
```

**A chave do modelo é `requires_human`:** ele particiona o grafo em nós *agentico-executáveis* (STEP sem gate, PRP) e nós *de decisão humana* (GATE, HITL). O scheduler trata esses dois grupos de forma fundamentalmente diferente (ver 2.7).

### 2.4 Gates como Nós Especiais

Um gate não "executa" — ele **bloqueia até decisão humana**. Tratá-lo como nó comum faria o scheduler tentar executá-lo ou paralelizá-lo, quebrando o *human-in-control*.

- Todo `GATE` e `HITL` tem `requires_human=True` e `auto_parallelizable=False`.
- Ao satisfazer dependências, um nó `requires_human` transita para `AWAITING_HUMAN` e **estaciona na fila do humano** (coluna `AWAITING_HUMAN` do Kanban, ADR-0002).
- A única transição de saída é via `UserDecisionWriter` (ADR-0002) — nunca pelo scheduler.
- Gates emitem arestas `BLOCKS` para seus sucessores: nenhum sucessor fica `READY` enquanto o gate não for aprovado.

### 2.5 Rework como Nova Instância (DAG Preservado)

Rejeitar um gate → re-executar um step criaria um ciclo, incompatível com DAG e com análise de critical path. Três alternativas foram avaliadas (ver §4); a decisão é:

> **Rework gera uma nova instância imutável do nó**, ligada ao original por aresta `REWORK` e marcada com `retry_of`.

```
step-5 ──REWORK──► step-5-retry-1 ──REWORK──► step-5-retry-2
```

Benefícios: preserva DAG e critical-path simples; mantém auditoria completa (quantidade e histórico de retries visíveis); o Kanban mostra o card original em `REWORK` e a nova instância em `RUNNING`.

### 2.6 Granularidade em Dois Níveis

Grafo muito fino gera overhead de estado; muito grosso perde paralelismo. Decisão: **dois níveis**, espelhando a realidade do LLC (steps sequenciais, PRPs paralelos):

| Nível | Nós | Uso |
|---|---|---|
| **N1 — Pipeline** | Steps + Gates | Backbone macro, Kanban de alto nível, critical path do fluxo |
| **N2 — Execução** | PRPs + tasks | Paralelismo via Herdr (Step 11), frontier de execução |

O scheduler opera em N1 para o fluxo macro e "desce" para N2 dentro de steps de execução. Os dois níveis são conectados: um step de execução (N1) tem seus PRPs (N2) como subgrafo.

### 2.7 Graph Engine (Scheduler)

```python
# .ace/scripts/llc_graph/engine.py

class GraphEngine:
    """Scheduler read-only: deriva estado e elegibilidade a partir do grafo + sessões ACE."""

    def __init__(self, graph: Graph, state_reader: "AceStateReader"):
        self.graph = graph
        self.state_reader = state_reader  # lê .ace/index.json + sessions

    def node_state(self, node_id: str) -> NodeState:
        """Deriva estado atual de um nó a partir das sessões ACE."""
        ...

    def ready_nodes(self) -> list[GraphNode]:
        """Nós cujas dependências estão satisfeitas.
        - requires_human  -> transita p/ AWAITING_HUMAN (fila do humano)
        - caso contrário  -> elegível para agente/Herdr
        NUNCA auto-avança gate/hitl."""
        ...

    def parallel_frontier(self) -> list[GraphNode]:
        """Subconjunto de ready_nodes com auto_parallelizable=True,
        independentes entre si. Consumido pelo Herdr (ADR-0003) para
        disparar panes paralelos."""
        ...

    def impact_of(self, node_id: str) -> set[str]:
        """Propagação descendente: todos os nós afetados por mudança em node_id.
        Base formal para Smart Skip e Delta (Δ.0)."""
        ...

    def critical_path(self) -> list[GraphNode]:
        """Caminho crítico do DAG: sequência que determina a duração total.
        Responde 'onde está o gargalo?'."""
        ...
```

**Contratos críticos:**
- `ready_nodes()` **nunca** retorna nó `requires_human` como auto-executável.
- `parallel_frontier()` retorna apenas nós mutuamente independentes (sem arestas entre eles).
- `impact_of()` é puro (sem efeitos colaterais) — é query, não command (CQS, fitness deep-clean).
- Todo método é determinístico dado o mesmo estado ACE (testabilidade).

### 2.8 Projeções Derivadas

Toda visualização consome o grafo; nenhuma o muta:

| Projeção | Fonte | Consumidor |
|---|---|---|
| **Kanban Board** | `node_state()` por nó | Wizard (ADR-0002) — substitui derivação por `index.json` direto |
| **Timeline / Gantt** | `node_state()` + timestamps | Wizard v1.2+ |
| **Impact Map** | `impact_of()` | Delta Δ.0, Smart Skip |
| **Critical Path View** | `critical_path()` | Dashboard de fábrica (Fase 3) |
| **Parallel Frontier** | `parallel_frontier()` | Herdr (ADR-0003) |

> **Integração com ADR-0002:** o `KanbanBoardBuilder` do Wizard passa a ser uma projeção do `GraphEngine`, não mais uma leitura direta de `index.json`. Isso torna o Kanban preciso (colunas = estados de nós; SLA = timestamps de estado). A mudança é interna ao builder; a UI do Kanban permanece idêntica.

### 2.11 Domínios de `ready_nodes()` vs. Fitness Functions (sem conflito)

O `GraphEngine` e o `fitness-functions.py` operam em **domínios distintos e consecutivos**, não concorrentes:

| Sistema | Domínio | Pergunta que responde | Momento |
|---|---|---|---|
| `ready_nodes()` | **Elegibilidade de execução** | "As dependências de DAG estão satisfeitas?" | Antes de iniciar um step/PRP |
| `fitness-functions.py --strict` | **Qualidade de merge** | "O código tem violações arquiteturais ou de coverage?" | Antes de fechar o gate de qualidade |

Um nó pode estar `READY` no grafo e ainda assim falhar no gate de qualidade — isso é correto. O grafo libera *execução*, o fitness gate libera *merge*. `ready_nodes()` **nunca substitui nem bypassa** os gates de fitness. As duas camadas são sempre consecutivas.

**Invariante do contrato de `ready_nodes()`:**
```
ready_nodes() → elegível para EXECUÇÃO.
Nó em READY não implica aprovação de qualidade.
Qualidade é responsabilidade dos gates de fitness (Gate 10.8, 11.3).
Os dois sistemas são camadas consecutivas, nunca alternativas.
```

### 2.12 Modelagem do Fluxo Delta (Δ) no Grafo

**Smart Skip → nó `SKIPPED`:**
- Nós marcados via skip **permanecem no grafo** com estado `SKIPPED` — nunca removidos.
- Para fins de dependência, `SKIPPED` é equivalente a `DONE`: sucessores ficam `READY`.
- `impact_of(node_id)` propaga por descendentes de nós `SKIPPED` — análise de impacto funciona mesmo com skip parcial.

**PRP Amendment → novo nó:**
- PRPs criados via Amendment são adicionados como **novos nós** com `retry_of=None`.
- Arestas `DEPENDS_ON` apontam para nós existentes que originaram o Amendment.
- DAG permanece acíclico: novos nós só apontam para nós existentes.

**Comportamento de `ready_nodes()` com grafo parcialmente skipped:**
```python
# deps satisfeitas = todas as deps em DONE ou SKIPPED
deps_satisfied = all(
    self.node_state(dep) in (NodeState.DONE, NodeState.SKIPPED)
    for dep in node.depends_on
)
```

**Teste obrigatório:**
```python
def test_ready_nodes_with_skipped_dependencies():
    """Nós com todas as deps SKIPPED ficam READY (não bloqueados)."""
    # Grafo: A → B → C, B marcado SKIPPED via Smart Skip
    # C deve ficar READY
```

### 2.9 Arquitetura e Estrutura de Arquivos

```
.ace/scripts/
├── llc_graph/                     # NOVO pacote
│   ├── __init__.py
│   ├── model.py                   # NodeKind, NodeState, EdgeKind, GraphNode, GraphEdge, Graph
│   ├── builder.py                 # GraphBuilder: unifica dependency-graph.yaml + depends_on
│   ├── engine.py                  # GraphEngine (scheduler read-only)
│   ├── state.py                   # AceStateReader: deriva NodeState de sessões ACE
│   ├── projections.py             # to_kanban(), to_impact_map(), to_critical_path()
│   └── tests/
│       ├── test_model.py
│       ├── test_builder.py
│       ├── test_engine.py
│       └── test_projections.py
├── llc_wizard/                    # ADR-0002 (existente)
│   └── kanban.py                  # MODIFICADO: KanbanBoardBuilder vira projeção do grafo
└── (llc_harness, llc_steps, llc_delta, llc_wave — intocados)
```

**Dependência (DIP):** `llc_graph` depende apenas de leitura de `.ace/` e dos artefatos declarativos; `llc_wizard` passa a depender de `llc_graph` para projeções; `llc_harness` permanece intocado. Nenhuma seta aponta para camadas superiores.

### 2.10 Decisões Vinculantes

| # | Decisão | Valor |
|---|---|---|
| **D1** | Fonte de verdade do **estado** | Sessões ACE (grafo é projeção derivada) |
| **D2** | Fonte da **estrutura** | `dependency-graph.yaml` + `depends_on` do registry + `gates.json` |
| **D3** | Gates/HITL | Nunca auto-avançados (`requires_human` estaciona em `AWAITING_HUMAN`) |
| **D4** | Rework | Nova instância + aresta `REWORK` (DAG preservado) |
| **D5** | Granularidade | Dois níveis: N1 pipeline (steps) + N2 execução (PRPs) |
| **D6** | Implementação MVP | Python puro (dataclasses + adjacência); **sem** networkx/framework externo |
| **D7** | Projeções | Read-only; Kanban do ADR-0002 vira projeção do grafo |
| **D8** | Cache de estado | Opcional em `.ace/graph-state.yaml`, sempre reconstruível a partir de ACE |

---

## 3. Consequências

### 3.1 Positivas

- **Unificação:** 5+ mecanismos fragmentados (waves, impact, smart skip, dependency) passam a derivar de um único modelo.
- **Paralelismo automático:** `parallel_frontier()` substitui waves manuais — pré-requisito da fábrica e do Herdr.
- **Kanban preciso:** projeção exata do estado, com SLA derivado de timestamps reais.
- **Smart Skip formal:** `impact_of()` substitui heurística por propagação determinística.
- **Critical path:** responde "onde está o gargalo?" — métrica central de fábrica.
- **Resiliência:** estado derivado de ACE permite reconstruir o grafo após qualquer interrupção.
- **Migração futura trivial:** modelo de grafo mapeia 1:1 para Temporal/Argo/Prefect na Fase 3.

### 3.2 Negativas / Custos

- **Complexidade conceitual:** equipe precisa internalizar modelo de grafo (mitigado por documentação e projeções visuais).
- **Superfície de teste ampliada:** novo pacote `llc_graph` exige cobertura ≥ 85%.
- **Refatoração do Kanban:** `KanbanBoardBuilder` (ADR-0002) precisa ser adaptado para projetar do grafo.
- **Dois níveis de granularidade** exigem cuidado para não dessincronizar N1 e N2.

### 3.3 Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Dessincronização grafo ↔ ACE | Estado sempre derivado de ACE (D1); cache reconstruível (D8) |
| Scheduler auto-avança gate | `requires_human` + contrato de `ready_nodes()` (D3) |
| Ciclos de rework quebram DAG | Nova instância + aresta `REWORK` (D4) |
| Over-engineering em projetos pequenos | Grafo é camada opcional; backbone linear segue disponível (P6) |
| Adoção prematura de framework pesado | Python puro no MVP (D6); framework só se justificado na Fase 3 |
| Perda da simplicidade mental do pipeline | Visão linear (sidebar) permanece padrão; grafo é visão avançada |

---

## 4. Alternativas Consideradas

| Alternativa | Descrição | Motivo da Rejeição |
|---|---|---|
| **Manter pipeline puramente sequencial** | Operar sempre como lista linear com waves manuais | Não escala para fábrica; paralelismo manual; smart skip heurístico |
| **Grafo cíclico / state-machine (LangGraph-style)** | Arestas de retorno para rework | Perde critical-path simples; complexidade de análise; rejeitado em favor de instâncias de rework |
| **Rework como mutação do mesmo nó** | Resetar estado do nó ao rejeitar | Perde histórico de retries; quebra auditoria |
| **Grafo como fonte primária de estado** | Persistir estado no grafo, ACE espelha | Viola integridade ACE; risco de dessincronização; rejeitado em favor de estado derivado (D1) |
| **Adotar Airflow/Temporal/Prefect agora** | Workflow engine externo como runtime | Infraestrutura pesada; prematuro para Fase 1; apropriado só na Fase 3 |
| **Usar networkx desde o início** | Biblioteca de grafos para tudo | Dependência desnecessária no MVP; algoritmos necessários (topo sort, critical path) são simples em DAG puro |
| **Granularidade única (só steps ou só PRPs)** | Um único nível de nó | Perde paralelismo (só steps) ou overhead macro (só PRPs) |

---

## 5. Compliance

### 5.1 Fitness Functions

- **Architecture:** `llc_graph` não importa de `llc_wizard`/`llc_harness` (DIP); projeções são funções puras.
- **Clean Code:** funções < 50 linhas; sem god-classes; `GraphEngine` coeso.
- **Deep Clean:** CQS respeitado — `impact_of`, `critical_path`, `ready_nodes` são queries puras; nenhuma flag booleana em assinaturas públicas.
- **Naming:** nós e arestas com identificadores estáveis (`step-5`, `prp-004`, `gate-5`).

### 5.2 Gates Aplicáveis

| Gate | Aplicação |
|---|---|
| Gate 5 | Arquitetura do modelo de grafo documentada neste ADR |
| Gate 5a | Padrões: Builder (GraphBuilder), Strategy (projeções), dataclasses imutáveis |
| Gate 5c | Clean code aplicado a `llc_graph` |
| Gate 9a (TDD) | Todo módulo segue RED → GREEN → REFACTOR |
| Gate 10.8 | Cobertura ≥ 85% em `model.py`, `builder.py`, `engine.py` |
| Gate 11.3 | `fitness-functions.py --all --strict` verde |

### 5.3 Testes Obrigatórios (TDD)

**`model.py`:** imutabilidade de `GraphNode`; validação de `depends_on`; `retry_of` consistente.

**`builder.py`:** unifica `dependency-graph.yaml` + `depends_on`; marca `requires_human` para gates; detecta nós órfãos.

**`engine.py` (crítico):**
- `ready_nodes()` retorna apenas nós com deps satisfeitas.
- `ready_nodes()` **não** auto-avança gate/hitl (transita para `AWAITING_HUMAN`).
- `parallel_frontier()` retorna nós mutuamente independentes.
- `impact_of()` propaga corretamente para descendentes.
- `critical_path()` identifica o caminho mais longo.
- Rework cria nova instância sem ciclo.
- Estado derivado bate com sessões ACE.

**`projections.py`:** `to_kanban()` mapeia estados para colunas do ADR-0002 corretamente.

---

## 6. Roadmap de Entrega (Integrado às Fases)

| Momento | Entrega | Benefício |
|---|---|---|
| **Fase 1A (agora)** | `model.py` + `builder.py` + `state.py` | Modelo de grafo unificado |
| **Fase 1 (v1.1)** | `engine.py`: `ready_nodes()`, `impact_of()` | Smart Skip por propagação real |
| **Fase 1 (v1.1)** | `projections.to_kanban()` | Kanban do ADR-0002 vira projeção precisa |
| **Fase 2 (Herdr)** | `parallel_frontier()` → scheduler do Herdr | Paralelismo automático de PRPs |
| **Fase 2** | `critical_path()` + métricas | Dashboard de fábrica (gargalo/throughput) |
| **Fase 3 (Temporal)** | Modelo de grafo → workflow engine | Migração trivial multi-projeto |

**Entrega mínima imediata (desbloqueia tudo):** `model.py` + `builder.py` (~1 semana). Unifica `dependency-graph.yaml` e `depends_on`, já melhora o Kanban e prepara a Fase 2, com baixo custo e zero risco ao harness.

---

## 7. Métricas de Sucesso

| Categoria | Métrica | Meta |
|---|---|---|
| Técnica | Cobertura `llc_graph` | ≥ 85% |
| Técnica | Determinismo do engine | 100% (mesmo estado ACE → mesmo resultado) |
| Técnica | Dessincronizações grafo↔ACE | 0 (estado sempre derivado) |
| Fluxo | Smart Skip preciso (falsos positivos) | −50% vs. heurístico |
| Fluxo | Paralelismo automático (PRPs/wave) | ≥ 80% dos PRPs independentes detectados |
| Fluxo | Critical path identificado | baseline medido na Fase 2 |

---

## 8. Anexos

### 8.1 Exemplo de Grafo (N1 + N2)

```
N1 — Pipeline (macro):
  step-0.5 ─► step-1 ─► gate-1 ─► step-2 ─► gate-2 ─► step-5 ─► gate-5 ─► step-11
                (BLOCKS)              (BLOCKS)              (BLOCKS)

N2 — Execução (dentro de step-11):
  step-11 ─► prp-001 ─┐
           ├► prp-002 ─┼─► step-11.1 (hardening)
           └► prp-003 ─┘
  (prp-001, prp-002, prp-003 independentes → parallel_frontier)

Rework:
  gate-5 rejeitado ─► step-5-retry-1 (retry_of="step-5") ─► gate-5-retry-1
```

### 8.2 Cache de Estado Opcional (`.ace/graph-state.yaml`)

```yaml
# Reconstruível a partir de ACE — nunca fonte primária
generated_at: "2026-08-05T10:00:00"
source: "derived-from-ace"
nodes:
  step-5: { state: done, since: "2026-08-05T09:10:00" }
  gate-5: { state: awaiting_human, since: "2026-08-05T09:12:00" }
  prp-001: { state: running, since: "2026-08-05T09:30:00" }
```

### 8.3 Contrato de Integração Kanban (ADR-0002)

```python
# llc_wizard/kanban.py — KanbanBoardBuilder passa a projetar do grafo
class KanbanBoardBuilder:
    def __init__(self, engine: GraphEngine):
        self.engine = engine

    def build(self):
        board = {col: [] for col in KanbanColumn}
        for node in self.engine.graph.nodes:
            state = self.engine.node_state(node.id)
            col = NODE_STATE_TO_COLUMN[state]
            board[col].append(self._to_card(node, state))
        board[AWAITING_HUMAN].sort(key=lambda c: c.entered_column_at)  # SLA
        return board
```

---

## 9. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-05 |
| claude | Co-autor da especificação | 2026-08-05 |

**Status:** `accepted`
**Dependências:** ADR-0002 (Kanban como projeção) · Pré-requisito para ADR-0003 (Herdr)
**Próximo passo sugerido:** Especificar `llc_graph` em tasks TDD granulares (modelo → builder → engine → projeções), nos moldes da quebra da Fase 1A.

---

## 10. Decisões de Aprovação — Questões Resolvidas

As quatro questões levantadas durante a revisão foram incorporadas ao corpo do ADR. Registro explícito das resoluções:

### Q1 — Fonte de verdade do estado (G4)

**Questão:** o ADR não decidia se o grafo é derivado das sessões ACE ou se vira fonte primária.

**Resolução (incorporada em D1 e P3):** o grafo é **estritamente derivado** das sessões ACE — nunca fonte primária. `.ace/sessions/*.md` é o único lugar onde fatos são escritos. `graph-state.yaml` (D8) é um cache reconstruível, análogo ao `index.json`, nunca mantido independentemente. Isso elimina o risco de duas fontes de verdade por construção, não por disciplina.

### Q2 — Acoplamento ao Herdr em `parallel_frontier()`

**Questão:** a formulação original tornava o grafo dependente do Herdr como consumidor específico.

**Resolução (incorporada em D5 e §2.7):** `parallel_frontier()` retorna **dados puros** (lista de `GraphNode` com `auto_parallelizable=True`, independentes entre si). Não sabe que o Herdr existe. Qualquer runtime — Herdr, worktrees manuais, ou nenhuma ferramenta — pode consumir essa lista. O grafo não é acoplado a nenhum runtime específico.

### Q3 — Conflito de oráculos: grafo vs. fitness functions

**Questão:** `ready_nodes()` e `fitness-functions.py --strict` podem discordar sobre "pronto para avançar" — qual vence?

**Resolução (nova seção §2.11):** os dois sistemas têm **domínios distintos e não sobrepostos**:
- `ready_nodes()` decide **elegibilidade de execução** (dependências de DAG satisfeitas).
- `fitness-functions.py --strict` decide **qualidade de merge** (violações arquiteturais, coverage).

Um PRP pode estar `READY` no grafo (todas as dependências satisfeitas) e ainda assim falhar no gate de qualidade. Isso é o comportamento correto: o grafo libera a execução, o gate de qualidade libera o merge. Não há conflito — são camadas consecutivas, não alternativas. O `ready_nodes()` nunca substitui nem bypassa os gates de fitness.

### Q4 — Fluxo Delta (Δ) não modelado como nó

**Questão:** Smart Skip e PRP Amendment mudam a topologia do grafo em tempo de execução; `ready_nodes()` não tratava isso explicitamente.

**Resolução (nova seção §2.12):** nós `SKIPPED` permanecem no grafo com estado `SKIPPED` — não são removidos. `ready_nodes()` trata `SKIPPED` como satisfeito para fins de dependência (equivalente a `DONE`). PRPs criados via PRP Amendment são adicionados como novos nós com `retry_of=None` e arestas `DEPENDS_ON` para os nós que os originaram. A topologia muda, mas o DAG permanece acíclico porque nós novos só apontam para nós existentes (nunca o contrário).
